import sys
import types
import unittest
import gc
import inspect
import copy
import contextlib
import threading
import contextvars
import ctypes
import importlib.util
import struct
import warnings
import subprocess
import numbers
import stackless

from textwrap import dedent
from stackless import schedule, tasklet

from support import test_main  # @UnusedImport
from support import StacklessTestCase, StacklessPickleTestCase, get_reduce_frame


# because test runner instances in the testsuite contain copies of the old stdin/stdout thingies,
# we need to make it appear that pickling them is ok, otherwise we will fail when pickling
# closures that refer to test runner instances
import copyreg
from _warnings import warn


def reduce(obj):
    return object, ()  # just create an empty object instance
copyreg.pickle(type(sys.stdout), reduce, object)  # @IgnorePep8

VERBOSE = False
glist = []


def nothing():
    pass


def accumulate(ident, func, *args):
    rval = (ident, func(*args))
    glist.append(rval)


def get_result():
    return glist.pop()


def is_empty():
    return len(glist) == 0


def reset():
    glist[:] = []


def rectest(nrec, lev=0, lst=None):
    if lst is None:
        lst = []
    lst.append(lev)
    if lev < nrec:
        rectest(nrec, lev + 1, lst)
    else:
        schedule()
    return lst


class TaskletChannel:

    def __init__(self):
        self.channel = stackless.channel()

    def run(self):
        self.channel.receive()


class CustomTasklet(tasklet):
    __slots__ = ["name"]


def listtest(n, when):
    for i in range(n):
        if i == when:
            schedule()
    return i


def xrangetest(n, when):
    for i in range(n):
        if i == when:
            schedule()
    return i


def enumeratetest(n, when):
    for i, ig in enumerate([None] * n):
        if i == when:
            schedule()
    return i


def dicttestiterkeys(n, when):
    for i in dict([(i, i) for i in range(n)]).keys():
        if i == when:
            schedule()
    return n


def dicttestitervalues(n, when):
    for i in dict([(i, i) for i in range(n)]).values():
        if i == when:
            schedule()
    return n


def dicttestiteritems(n, when):
    for (i, j) in dict([(i, i) for i in range(n)]).items():
        if i == when:
            schedule()
    return n


def settest(n, when):
    for i in set(range(n)):
        if i == when:
            schedule()
    return i


def tupletest(n, when):
    for i in tuple(range(n)):
        if i == when:
            schedule()
    return i


def genschedinnertest(n, when):
    for i in range(n):
        if i == when:
            schedule()
        yield i


def genschedoutertest(n, when):
    for x in genschedinnertest(n, when):
        pass
    return x


def geninnertest(n):
    for x in range(n):
        yield x


def genoutertest(n, when):
    for i in geninnertest(n):
        if i == when:
            schedule()
    return i


def cellpickling():
    """defect:  Initializing a function object with a partially constructed
       cell object
    """
    def closure():
        localvar = the_closure
        return
    the_closure = closure
    del closure
    schedule()
    return the_closure()


class CtxManager(object):

    def __init__(self, n, when, expect_type, suppress_exc):
        self.n = n
        assert when in ('enter', 'body', 'exit')
        self.when = when
        self.expect_type = expect_type
        self.suppress_exc = suppress_exc
        self.ran_enter = self.ran_exit = False

    def __enter__(self):
        self.ran_enter = True
        if self.when == 'enter':
            lst = rectest(self.n)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ran_exit = True
        if not is_soft() and isinstance(exc_val, SystemExit):
            return False
        self.exc_type = exc_type
        if self.when == 'exit':
            lst = rectest(self.n)
        return self.suppress_exc


def ctxpickling(testCase, n, when, expect_type, suppress_exc):
    ctxmgr = CtxManager(n, when, expect_type, suppress_exc)

    ran_body = False
    try:
        with ctxmgr as c:
            ran_body = True
            if when == 'body':
                rectest(n)
            if expect_type:
                raise expect_type("raised by ctxpickling")
    except SystemExit:
        raise
    except:  # @IgnorePep8
        exc_info = sys.exc_info()
    else:
        exc_info = (None, None, None)

    testCase.assertEqual(ctxmgr.ran_enter, True, "__enter__ did not run")
    testCase.assertTrue(ctxmgr.ran_exit, "__exit__ did not run")
    if expect_type is not None:
        testCase.assertEqual(ctxmgr.exc_type, expect_type, "incorrect ctxmgr.exc_type: expected %r got %r" % (expect_type, ctxmgr.exc_type))
        if suppress_exc:
            testCase.assertEqual(exc_info, (None, None, None), "Suppress didn't work")
        else:
            testCase.assertEqual(exc_info[0], expect_type, "incorrect exc_type")
    else:
        testCase.assertEqual(ctxmgr.exc_type, None, "ctxmgr.exc_type is not None: %r" % (ctxmgr.exc_type,))
        testCase.assertEqual(exc_info, (None, None, None), "unexpected exception: " + repr(exc_info[1]))

    testCase.assertTrue(ran_body, "with block did not run")
    testCase.assertEqual(ctxmgr, c, "__enter__ returned wrong value")
    return "OK"


class InitTestClass:
    def __init__(self, testcase):
        testcase.started = True
        schedule()


def inittest(testcase, cls):
    # test pickling of stackless __init__
    testcase.started = False
    obj = cls(testcase)
    testcase.assertTrue(testcase.started)
    return "OK"


def is_soft():
    softswitch = stackless.enable_softswitch(0)
    stackless.enable_softswitch(softswitch)
    return softswitch


class TestPickledTasklets(StacklessPickleTestCase):

    def setUp(self):
        super(TestPickledTasklets, self).setUp()
        self.verbose = VERBOSE

    def tearDown(self):
        # Tasklets created in pickling tests can be left in the scheduler when they finish.  We can feel free to
        # clean them up for the tests.
        mainTasklet = stackless.getmain()
        current = mainTasklet.next
        while current is not mainTasklet:
            next = current.next
            current.kill()
            current = next

        super(TestPickledTasklets, self).tearDown()

        del self.verbose

    def run_pickled(self, func, *args):
        ident = object()
        t = tasklet(accumulate)(ident, func, *args)

        # clear out old errors
        reset()

        if self.verbose:
            print("starting tasklet")
        t.run()

        self.assertEqual(is_empty(), True)

        # do we want to do this??
        #t.tempval = None

        if self.verbose:
            print("pickling")
        pi = self.dumps(t)

        # if self.verbose: print repr(pi)
        # why do we want to remove it?
        # t.remove()

        if self.verbose:
            print("unpickling")
        ip = self.loads(pi)

        if self.verbose:
            print("starting unpickled tasklet")
        if is_soft():
            ip.run()
        else:
            self.assertRaises(RuntimeError, ip.run)
            return
        new_ident, new_rval = get_result()
        t.run()
        old_ident, old_rval = get_result()
        self.assertEqual(old_ident, ident)
        self.assertEqual(new_rval, old_rval)
        self.assertNotEqual(new_ident, old_ident)
        self.assertEqual(is_empty(), True)

    def testClassPersistence(self):
        t1 = CustomTasklet(nothing)()
        s = self.dumps(t1)
        t2 = self.loads(s)
        self.assertEqual(t1.__class__, t2.__class__)

    def testGenerator(self):
        self.run_pickled(genoutertest, 20, 13)

    def testList(self):
        self.run_pickled(listtest, 20, 13)

    def testXrange(self):
        self.run_pickled(xrangetest, 20, 13)

    def testXrangeExhausted(self):
        self.run_pickled(xrangetest, 20, 19)

    def testRecursive(self):
        self.run_pickled(rectest, 13)

    # Pickling of all three dictionary iterator types.

    # Test picking of the dictionary keys iterator.
    def testDictIterkeys(self):
        self.run_pickled(dicttestiterkeys, 20, 13)

    # Test picking of the dictionary values iterator.
    def testDictItervalues(self):
        self.run_pickled(dicttestitervalues, 20, 13)

    # Test picking of the dictionary items iterator.
    def testDictIteritems(self):
        self.run_pickled(dicttestiteritems, 20, 13)

    # Test pickling of iteration over the set type.
    def testSet(self):
        self.run_pickled(settest, 20, 13)

    def testEnumerate(self):
        self.run_pickled(enumeratetest, 20, 13)

    def testTuple(self):
        self.run_pickled(tupletest, 20, 13)

    def testGeneratorScheduling(self):
        self.run_pickled(genschedoutertest, 20, 13)

    def testRecursiveLambda(self):
        recurse = lambda self, next: next - 1 and self(self, next - 1) or (schedule(), 42)[1]  # @IgnorePep8
        self.loads(self.dumps(recurse))
        self.run_pickled(recurse, recurse, 13)

    def testRecursiveEmbedded(self):
        # Avoid self references in this function, to prevent crappy unit testing framework
        # magic from getting pickled and refusing to unpickle.
        def rectest(verbose, nrec, lev=0):
            if verbose:
                print(str(nrec), lev)
            if lev < nrec:
                rectest(verbose, nrec, lev + 1)
            else:
                schedule()
        self.run_pickled(rectest, self.verbose, 13)

    def testCell(self):
        self.run_pickled(cellpickling)

    def testCtx_enter_0(self):
        self.run_pickled(ctxpickling, self, 0, 'enter', None, False)

    def testCtx_enter_1(self):
        self.run_pickled(ctxpickling, self, 1, 'enter', None, False)

    def testCtx_enter_2(self):
        self.run_pickled(ctxpickling, self, 2, 'enter', RuntimeError, False)

    def testCtx_enter_3(self):
        self.run_pickled(ctxpickling, self, 1, 'enter', RuntimeError, True)

    def testCtx_body_0(self):
        self.run_pickled(ctxpickling, self, 0, 'body', None, False)

    def testCtx_body_1(self):
        self.run_pickled(ctxpickling, self, 1, 'body', None, False)

    def testCtx_body_2(self):
        self.run_pickled(ctxpickling, self, 2, 'body', RuntimeError, False)

    def testCtx_body_3(self):
        self.run_pickled(ctxpickling, self, 1, 'body', RuntimeError, True)

    def testCtx_body_4(self):
        self.run_pickled(ctxpickling, self, 2, 'body', RuntimeError, True)

    def testCtx_body_5(self):
        self.run_pickled(ctxpickling, self, 1, 'body', RuntimeError, False)

    def testCtx_body_6(self):
        self.run_pickled(ctxpickling, self, 0, 'body', RuntimeError, True)

    def testCtx_body_7(self):
        self.run_pickled(ctxpickling, self, 0, 'body', RuntimeError, False)

    def testCtx_exit_0(self):
        self.run_pickled(ctxpickling, self, 0, 'exit', None, False)

    def testCtx_exit_1(self):
        self.run_pickled(ctxpickling, self, 1, 'exit', None, False)

    def testCtx_exit_2(self):
        self.run_pickled(ctxpickling, self, 2, 'exit', RuntimeError, False)

    def testCtx_exit_3(self):
        self.run_pickled(ctxpickling, self, 0, 'exit', RuntimeError, True)

    def testCtx_exit_4(self):
        self.run_pickled(ctxpickling, self, 1, 'exit', RuntimeError, True)

    def test__init__(self):
        self.run_pickled(inittest, self, InitTestClass)

    def testFakeModules(self):
        types.ModuleType('fakemodule!')

    # Crash bug.  See SVN revision 45902.
    # Unpickling race condition where a tasklet unexpectedly had setstate
    # called on it before the channel it was blocked on.  This left it
    # linked to the channel but not blocked, which meant that when it was
    # scheduled it was not linked to the scheduler, and this caused a
    # crash when the scheduler tried to remove it when it exited.
    def testGarbageCollection(self):
        # Make a class that holds onto a reference to a channel
        # and then block it on that channel.
        tc = TaskletChannel()
        t = stackless.tasklet(tc.run)()
        t.run()
        # Pickle the tasklet that is blocking.
        s = self.dumps(t)
        # Unpickle it again, but don't hold a reference.
        self.loads(s)
        # Force the collection of the unpickled tasklet.
        gc.collect()

    def testSendSequence(self):
        # Send sequence when pickled was not handled.  It uses
        # a custom cframe execute function which was not recognised
        # by the pickling.
        #
        # Traceback (most recent call last):
        #   File ".\test_pickle.py", line 283, in testSendSequence
        #     pickle.dumps(t1)
        # ValueError: frame exec function at 1e00bf40 is not registered!

        def sender(chan):
            li = [1, 2, 3, 4]
            chan.send_sequence(li)

        def receiver(chan):
            length = 4
            while length:
                v = chan.receive()
                length -= 1

        c = stackless.channel()
        t1 = stackless.tasklet(sender)(c)
        t2 = stackless.tasklet(receiver)(c)
        t1.run()

        self.dumps(t1)

    def testSubmoduleImporting(self):
        # When a submodule was pickled, it would unpickle as the
        # module instead.
        import xml.sax
        m1 = xml.sax
        m2 = self.loads(self.dumps(m1))
        self.assertEqual(m1, m2)


class TestFramePickling(StacklessTestCase):
    def test_get_set_reduce_frame(self):
        # test setting / getting the reduce frame function
        rf = get_reduce_frame()
        self.assertTrue(callable(rf))
        stackless._stackless._wrap.set_reduce_frame(None)
        self.assertIsNone(get_reduce_frame())
        stackless._stackless._wrap.set_reduce_frame(rf)
        self.assertIs(get_reduce_frame(), rf)

    def testLocalplus(self):
        result = []

        def reduce_current():
            """This function has exactly one local variable (func), one cellvar (result2) and one freevar (result)"""
            result2 = result  # create the cell variable

            def func(current):
                result2.append(stackless._stackless._wrap.frame.__reduce__(current.frame))
            stackless.tasklet().bind(func, (stackless.current,)).run()
            return result[0]

        cell_type = type(reduce_current.__closure__[0])

        state = reduce_current()[2]
        self.assertIsInstance(state, tuple)
        self.assertEqual(len(state), 11)

        code = state[0]
        self.assertIsInstance(code, types.CodeType)
        ncellvars = len(code.co_cellvars)
        nfreevars = len(code.co_freevars)
        self.assertEqual(ncellvars, 1)
        self.assertEqual(nfreevars, 1)

        localsplus_as_tuple = state[-1]
        valid = state[1]

        self.assertEqual(valid, int(stackless.enable_softswitch(None) and
                                    stackless.current.nesting_level == 0))
        self.assertIsInstance(localsplus_as_tuple, tuple)
        self.assertGreaterEqual(len(localsplus_as_tuple), 1 + code.co_nlocals + ncellvars + nfreevars)
        for i in range(ncellvars + nfreevars):
            cell = localsplus_as_tuple[1 + code.co_nlocals + i]
            self.assertIsInstance(cell, cell_type)
            self.assertIs(cell.cell_contents, result)

    def _test_setstate_prepare(self):
        foo = "foo"

        def f1(bar="bar"):
            try:
                1 / 0
            except ZeroDivisionError:
                x = foo
                locals()
                return stackless._stackless._wrap.frame.__reduce__(sys._getframe())
            assert False

        def f2():
            try:
                1 / 0
            except ZeroDivisionError:
                return f1()

        r = f2()
        self.assertEqual(len(r), 3)

        # r is a tuple (frame_type, (f_code), (state))
        # state is a tuple of the form
        # ('f_code', 'valid', 'f_executing', 'f_globals', 'have_locals',
        #  'f_locals', 'f_trace', 'f_lasti', 'f_lineno',
        #  'blockstack_as_tuple', 'localsplus_as_tuple')
        return r

    def test_setstate_OK(self):
        r = self._test_setstate_prepare()
        wrap_frame = r[0](*r[1])
        self.assertIsInstance(wrap_frame, stackless._stackless._wrap.frame)
        # must not raise an assertion
        wrap_frame.__setstate__(r[2])
        self.assertIs(type(wrap_frame), types.FrameType)

    def test_setstate_invalid_blockstack(self):
        r = self._test_setstate_prepare()
        # incomplete, just one of many failure modes of stackless._stackless._wrap.frame.__setstate__
        wrap_frame = r[0](*r[1])
        invalid_state = r[2][:-2] + ((("Not a", "tuple of 3", "integers"),), r[2][-1])
        self.assertRaisesRegex(TypeError, "an integer is required", wrap_frame.__setstate__, invalid_state)

    def test_setstate_invalid_state(self):
        r = self._test_setstate_prepare()
        # incomplete, just one of many failure modes of stackless._stackless._wrap.frame.__setstate__
        wrap_frame = r[0](*r[1])
        invalid_state = ('completely', 'wrong')
        self.assertRaisesRegex(TypeError, "takes exactly 11 arguments", wrap_frame.__setstate__, invalid_state)

    def test_setstate_different_code(self):
        r = self._test_setstate_prepare()
        # incomplete, just one of many failure modes of stackless._stackless._wrap.frame.__setstate__
        wrap_frame = r[0]((lambda:None).__code__)
        invalid_state = r[2]
        self.assertRaisesRegex(TypeError, "invalid code object for frame_setstate", wrap_frame.__setstate__, invalid_state)


class TestDictViewPickling(StacklessPickleTestCase):

    def testDictKeyViewPickling(self):
        # stackless python prior to 2.7.3 used to register its own __reduce__
        d = {1: 2}
        view1 = d.keys()
        view2 = self.loads(self.dumps(view1))
        self.assertEqual(list(view1), list(view2))

    def testDictItemViewPickling(self):
        d = {1: 2}
        view1 = d.items()
        view2 = self.loads(self.dumps(view1))
        self.assertEqual(list(view1), list(view2))

    def testDictValueViewPickling(self):
        d = {1: 2}
        view1 = d.values()
        view2 = self.loads(self.dumps(view1))
        self.assertEqual(list(view1), list(view2))


class TestTraceback(StacklessPickleTestCase):
    def testTracebackFrameLinkage(self):
        def a():
            # raise an exception
            1 // 0

        def b():
            return a()

        def c():
            return b()

        def d():
            try:
                c()
            except ZeroDivisionError:
                return sys.exc_info()[2]

        tb = d()  # this way tb dosn't reference the current frame
        innerframes_orig = inspect.getinnerframes(tb)
        p = self.dumps(tb)
        tb2 = self.loads(p)
        # basics
        innerframes_orig = inspect.getinnerframes(tb)
        self.assertIs(type(tb), type(tb2))
        self.assertIsNot(tb, tb2)
        innerframes = inspect.getinnerframes(tb2)
        # compare the content
        self.assertListEqual([i[1:] for i in innerframes_orig], [i[1:] for i in innerframes])
        # check linkage
        all_outerframes_orig = inspect.getouterframes(innerframes_orig[-1][0])
        all_outerframes = inspect.getouterframes(innerframes[-1][0])
        l = len(innerframes_orig)  # @IgnorePep8
        self.assertGreater(len(all_outerframes_orig), l)
        self.assertGreaterEqual(len(all_outerframes), l)
        # compare the content
        self.assertListEqual([i[1:] for i in all_outerframes_orig[:l - 1]], [i[1:] for i in all_outerframes[:l - 1]])


class TestCoroutinePickling(StacklessPickleTestCase):
    @types.coroutine
    def yield1(self, value):
        yield value

    async def c(self):
        await self.yield1(1)

    def test_without_pickling(self):
        c = self.c()
        self.assertIsInstance(c, types.CoroutineType)
        self.assertIsNone(c.cr_await)
        self.assertIsNotNone(c.cr_frame)
        self.assertEqual(c.send(None), 1)
        self.assertIsNotNone(c.cr_await)
        self.assertIsNotNone(c.cr_frame)
        self.assertRaises(StopIteration, c.send, None)
        self.assertIsNone(c.cr_await)
        self.assertIsNone(c.cr_frame)
        self.assertRaisesRegex(RuntimeError, "cannot reuse already awaited coroutine", c.send, None)

    def test_pickling1(self):
        c = self.c()
        p = self.dumps(c)
        c.send(None)
        c = self.loads(p)
        self.assertIsInstance(c, types.CoroutineType)
        self.assertIsNone(c.cr_await)
        self.assertIsNotNone(c.cr_frame)
        self.assertEqual(c.send(None), 1)
        self.assertRaises(StopIteration, c.send, None)

    def test_pickling2(self):
        c = self.c()
        self.assertEqual(c.send(None), 1)
        p = self.dumps(c)
        c = self.loads(p)
        self.assertIsInstance(c, types.CoroutineType)
        self.assertIsNotNone(c.cr_await)
        self.assertIsNotNone(c.cr_frame)
        self.assertRaises(StopIteration, c.send, None)

    def test_pickling3(self):
        c = self.c()
        self.assertEqual(c.send(None), 1)
        self.assertRaises(StopIteration, c.send, None)
        p = self.dumps(c)
        c = self.loads(p)
        self.assertIsInstance(c, types.CoroutineType)
        self.assertIsNone(c.cr_await)
        self.assertIsNone(c.cr_frame)
        self.assertRaisesRegex(RuntimeError, "cannot reuse already awaited coroutine", c.send, None)

    def test_pickling_origin(self):
        old_coroutine_origin_tracking_depth = sys.get_coroutine_origin_tracking_depth()
        self.addCleanup(sys.set_coroutine_origin_tracking_depth, old_coroutine_origin_tracking_depth)
        sys.set_coroutine_origin_tracking_depth(5)
        c = self.c()
        self.assertEqual(c.send(None), 1)
        orig_origin = c.cr_origin
        self.assertIsInstance(orig_origin, tuple)
        p = self.dumps(c)
        c = self.loads(p)
        self.assertIsInstance(c, types.CoroutineType)
        self.assertIsNotNone(c.cr_await)
        self.assertIsNotNone(c.cr_frame)
        origin = c.cr_origin
        self.assertIsInstance(origin, tuple)
        self.assertIsNot(origin, orig_origin)
        self.assertTupleEqual(orig_origin, origin)
        self.assertRaises(StopIteration, c.send, None)

    def test_coro_wrapper_pickling(self):
        c = self.c()
        cw = c.__await__()
        cw_type = type(cw)
        self.assertEqual(cw_type.__name__, "coroutine_wrapper")
        p = self.dumps(cw)
        self.assertEqual(c.send(None), 1)
        self.assertRaises(StopIteration, c.send, None)

        cw = self.loads(p)
        self.assertIsInstance(cw, cw_type)
        self.assertEqual(cw.send(None), 1)
        self.assertRaises(StopIteration, cw.send, None)
        self.assertRaisesRegex(RuntimeError, "cannot reuse already awaited coroutine", cw.send, None)


async_gen_finalize_counter = 0


def async_gen_finalize(async_gen):
    global async_gen_finalize_counter
    async_gen_finalize_counter += 1
    # print("async_gen_finalize: ", async_gen_finalize_counter)


class TestAsyncGenPickling(StacklessPickleTestCase):
    async def ag(self):
        yield 100

    @contextlib.contextmanager
    def asyncgen_hooks(self, finalizer):
        old_agen_hooks = sys.get_asyncgen_hooks()
        sys.set_asyncgen_hooks(firstiter=lambda agen: None,
                               finalizer=finalizer)
        try:
            yield None
        finally:
            sys.set_asyncgen_hooks(*old_agen_hooks)

    @contextlib.contextmanager
    def pickle_flags(self, preserve_finalizer=False, reset_finalizer=False):
        old_flags = stackless.pickle_flags()
        new_flags = ((old_flags & ~(stackless.PICKLEFLAGS_PRESERVE_AG_FINALIZER |
                                    stackless.PICKLEFLAGS_RESET_AG_FINALIZER)) |
                     (stackless.PICKLEFLAGS_PRESERVE_AG_FINALIZER if preserve_finalizer else 0) |
                     (stackless.PICKLEFLAGS_RESET_AG_FINALIZER if reset_finalizer else 0))
        old_flags = stackless.pickle_flags(new_flags)
        try:
            yield old_flags
        finally:
            stackless.pickle_flags(old_flags)

    def test_without_pickling(self):
        ag = self.ag()
        self.assertIsInstance(ag, types.AsyncGeneratorType)
        self.assertIs(ag, ag.__aiter__())
        self.assertIsNotNone(ag.ag_frame)
        c = ag.__anext__()
        with self.assertRaises(StopIteration) as cm:
            c.send(None)
        self.assertEqual(cm.exception.value, 100)
        self.assertIsNotNone(ag.ag_frame)
        c = ag.__anext__()
        self.assertRaises(StopAsyncIteration, c.send, None)
        self.assertIsNone(ag.ag_frame)
        self.assertRaises(StopIteration, c.send, None)
        c = ag.__anext__()
        self.assertRaises(StopAsyncIteration, c.send, None)

    def test_pickling1(self):
        ag = self.ag()
        p = self.dumps(ag)
        ag = self.loads(p)
        self.assertIsInstance(ag, types.AsyncGeneratorType)
        self.assertIs(ag, ag.__aiter__())
        self.assertIsNotNone(ag.ag_frame)
        c = ag.__anext__()
        with self.assertRaises(StopIteration) as cm:
            c.send(None)
        self.assertEqual(cm.exception.value, 100)
        self.assertIsNotNone(ag.ag_frame)
        c = ag.__anext__()
        self.assertRaises(StopAsyncIteration, c.send, None)
        self.assertIsNone(ag.ag_frame)
        self.assertRaises(StopIteration, c.send, None)
        c = ag.__anext__()
        self.assertRaises(StopAsyncIteration, c.send, None)

    def test_pickling2(self):
        ag = self.ag()
        with self.asyncgen_hooks(async_gen_finalize):
            c = ag.__anext__()
        self.assertRaises(StopIteration, c.send, None)
        with self.pickle_flags(preserve_finalizer=True):
            p = self.dumps(ag)
            # import pickletools; pickletools.dis(pickletools.optimize(p))
            old = async_gen_finalize_counter
            del ag
            del c
            gc.collect()
            self.assertEqual(async_gen_finalize_counter, old + 1)
            ag = self.loads(p)
            self.assertIsNotNone(ag.ag_frame)
            c = ag.__anext__()
            self.assertRaises(StopAsyncIteration, c.send, None)
            self.assertIsNone(ag.ag_frame)
            self.assertRaises(StopIteration, c.send, None)
            c = ag.__anext__()
            self.assertRaises(StopAsyncIteration, c.send, None)
            ag = self.loads(p)
            old = async_gen_finalize_counter
            del ag
            gc.collect()
            self.assertEqual(async_gen_finalize_counter, old + 1)

    def test_pickling3(self):
        old_agen_hooks = sys.get_asyncgen_hooks()
        sys.set_asyncgen_hooks(firstiter=lambda agen: None,
                               finalizer=async_gen_finalize)
        try:
            ag = self.ag()
        finally:
            sys.set_asyncgen_hooks(*old_agen_hooks)

        c = ag.__anext__()
        self.assertRaises(StopIteration, c.send, None)
        c = ag.__anext__()
        self.assertRaises(StopAsyncIteration, c.send, None)
        p = self.dumps(ag)
        ag = self.loads(p)
        self.assertIsNone(ag.ag_frame)
        self.assertRaises(StopIteration, c.send, None)
        c = ag.__anext__()
        self.assertRaises(StopAsyncIteration, c.send, None)


class TestAsyncGenASendPickling(StacklessPickleTestCase):
    async def ag(self):
        yield 100

    def inspect(self, ags):
        r = stackless._stackless._wrap.async_generator_asend.__reduce__(ags)
        self.assertIs(r[0], stackless._stackless._wrap.async_generator_asend)
        self.assertIsInstance(r[2][0], types.AsyncGeneratorType)
        return r[2][1:]

    def test_without_pickling(self):
        ags = self.ag().__anext__()
        self.assertTupleEqual(self.inspect(ags), (None, 0, False))
        with self.assertRaises(StopIteration) as cm:
            ags.__next__()
        self.assertEqual(cm.exception.value, 100)
        self.assertTupleEqual(self.inspect(ags), (None, 2, False))

    def test_pickling1(self):
        ags = self.ag().__anext__()
        p = self.dumps(ags)
        ags = self.loads(p)
        self.assertTupleEqual(self.inspect(ags), (None, 0, False))
        with self.assertRaises(StopIteration) as cm:
            ags.__next__()
        self.assertEqual(cm.exception.value, 100)
        self.assertTupleEqual(self.inspect(ags), (None, 2, False))

    def test_pickling2(self):
        ags = self.ag().asend(NotImplemented)
        p = self.dumps(ags)
        ags = self.loads(p)
        self.assertTupleEqual(self.inspect(ags), (NotImplemented, 0, True))
        self.assertRaises(TypeError, ags.__next__)
        self.assertTupleEqual(self.inspect(ags), (NotImplemented, 2, True))


class TestAsyncGenAThrowPickling(StacklessPickleTestCase):
    async def ag(self):
        yield 100
        yield 200

    def inspect(self, ags):
        r = stackless._stackless._wrap.async_generator_athrow.__reduce__(ags)
        self.assertIs(r[0], stackless._stackless._wrap.async_generator_athrow)
        self.assertIsInstance(r[2][0], types.AsyncGeneratorType)
        return r[2][1:]

    def test_without_pickling(self):
        a = self.ag()
        ags = a.__anext__()
        with self.assertRaises(StopIteration) as cm:
            ags.__next__()
        self.assertEqual(cm.exception.value, 100)
        e = ZeroDivisionError("bla bla")
        agt = a.athrow(e)
        self.assertTupleEqual(self.inspect(agt), ((e, ), 0, True))
        with self.assertRaises(ZeroDivisionError) as cm:
            agt.__next__()
        self.assertIs(cm.exception, e)
        self.assertTupleEqual(self.inspect(agt), ((e, ), 1, True))

    def test_pickling1(self):
        a = self.ag()
        ags = a.__anext__()
        with self.assertRaises(StopIteration) as cm:
            ags.__next__()
        self.assertEqual(cm.exception.value, 100)
        e = ZeroDivisionError("bla bla")
        agt = a.athrow(e)
        p = self.dumps(agt)
        agt = self.loads(p)
        x = self.inspect(agt)
        self.assertIsInstance(x[0][0], ZeroDivisionError)
        self.assertIsNot(x[0][0], e)
        e = x[0][0]
        self.assertTupleEqual(x, ((e, ), 0, True))
        with self.assertRaises(ZeroDivisionError) as cm:
            agt.__next__()
        self.assertIs(cm.exception, e)
        self.assertTupleEqual(self.inspect(agt), ((e, ), 1, True))


class TestContextRunCallbackPickling(StacklessTestCase):
    # Actually we test cframe.__reduce__ for cframes with exec function "context_run_callback"
    # We can't pickle a contextvars.Context object.

    # declare int PyContext_Exit(PyObject *octx)
    PyContext_Exit =  ctypes.pythonapi.PyContext_Exit
    PyContext_Exit.argtypes = [ctypes.py_object]
    PyContext_Exit.restype = ctypes.c_int

    # make sure, a context exists and contains an var whose value can't be pickled
    cvar = contextvars.ContextVar("TestContextPickling.cvar", default="unset")
    cvar.set(object())

    @classmethod
    def task(cls):
        v = cls.cvar.get()
        v = stackless.schedule_remove(v)
        cls.cvar.set(v)

    def _test_pickle_in_context_run(self, ctx1):
        # test cframe.__reduce__ for "context_run_callback" called in Context.run
        ctx2 = contextvars.Context()
        t = stackless.tasklet(ctx2.run)(self.task)

        stackless.run()
        self.assertEqual(t.tempval, "unset")
        self.assertTrue(t.alive)
        self.assertTrue(t.paused)
        if is_soft():
            self.assertTrue(t.restorable)

        # now ctx2 must be in state entered
        self.assertRaisesRegex(RuntimeError, "cannot enter context:.*is already entered", ctx2.run, lambda: None)
        frames = t.__reduce__()[2][3]
        self.assertIsInstance(frames, list)

        for f in frames:
            if not isinstance(f, stackless.cframe):
                continue
            valid, exec_name, params, i, n = f.__reduce__()[2]
            if exec_name != 'context_run_callback':
                continue
            self.assertEqual(valid, 1)
            self.assertEqual(f.n, 0)
            self.assertEqual(n, 0)
            # now check, that context to switch to is in the state
            # the original cframe has the currently active context
            self.assertIs(f.ob1, ctx2)
            self.assertTupleEqual(params, ((1, 2), ctx1, None, None))
            self.assertEqual(f.i, 0)
            self.assertEqual(i, 1)
            break
        else:
            self.assertFalse(is_soft(), "no cframe 'context_run_callback'")

        if is_soft():
            t.bind(None)
            self.assertRaisesRegex(RuntimeError, "the current context of the tasklet has been entered", t.set_context, contextvars.Context())
            t.context_run(self.PyContext_Exit, ctx2)
            t.set_context(contextvars.Context())

    def test_pickle_in_context_run(self):
        # test cframe.__reduce__ for "context_run_callback" called in Context.run
        ctx1 = contextvars.copy_context()
        ctx1.run(self._test_pickle_in_context_run, ctx1)

    def _test_pickle_in_tasklet_context_run(self, ctx1):
        # test cframe.__reduce__ for "context_run_callback" called in tasklet.context_run
        ctx2 = contextvars.Context()
        t_run = stackless.tasklet().set_context(ctx2)
        t = stackless.tasklet(t_run.context_run)(self.task)

        stackless.run()
        self.assertEqual(t.tempval, "unset")
        self.assertTrue(t.alive)
        self.assertTrue(t.paused)
        if is_soft():
            self.assertTrue(t.restorable)

        # now ctx2 must not be in state entered
        ctx2.run(lambda:None)
        frames = t.__reduce__()[2][3]
        self.assertIsInstance(frames, list)

        for f in frames:
            if not isinstance(f, stackless.cframe):
                continue
            valid, exec_name, params, i, n = f.__reduce__()[2]
            if exec_name != 'context_run_callback':
                continue
            self.assertEqual(valid, 1)
            self.assertEqual(f.n, 0)
            self.assertEqual(n, 0)
            # now check, that context to switch to is in the state
            # the original cframe has the currently active context
            self.assertIs(f.ob1, ctx1)
            self.assertTupleEqual(params, ((1, 2), ctx1, None, None))
            self.assertEqual(f.i, 1)
            self.assertEqual(i, 1)
            break
        else:
            self.assertFalse(is_soft(), "no cframe 'context_run_callback'")

        if is_soft():
            t.bind(None)
            t.set_context(contextvars.Context())

    def test_pickle_in_tasklet_context_run(self):
        # test cframe.__reduce__ for "context_run_callback" called in tasklet.context_run
        ctx1 = contextvars.copy_context()
        ctx1.run(self._test_pickle_in_tasklet_context_run, ctx1)

    def test_tasklet_get_unpicklable_state(self):
        cid = stackless.current.context_id
        ctx = stackless._tasklet_get_unpicklable_state(stackless.current)['context']
        self.assertEqual(stackless.current.context_id, cid)
        self.assertIsInstance(ctx, contextvars.Context)
        self.assertEqual(id(ctx), cid)


class TestContextPickling(StacklessPickleTestCase):
    # We can't pickle a contextvars.Context object.

    # declare int PyContext_Exit(PyObject *octx)
    PyContext_Exit =  ctypes.pythonapi.PyContext_Exit
    PyContext_Exit.argtypes = [ctypes.py_object]
    PyContext_Exit.restype = ctypes.c_int

    # make sure, a context exists and contains an var whose value can't be pickled
    cvar = contextvars.ContextVar("TestContextPickling.cvar", default="unset")
    sentinel = object()
    cvar.set(sentinel)

    def setUp(self):
        super().setUp()
        stackless.pickle_flags(stackless.PICKLEFLAGS_PICKLE_CONTEXT, stackless.PICKLEFLAGS_PICKLE_CONTEXT)

    def tearDown(self):
        super().tearDown()
        stackless.pickle_flags(0, stackless.PICKLEFLAGS_PICKLE_CONTEXT)

    @classmethod
    def task(cls, arg):
        v = cls.cvar.get()
        cls.cvar.set(arg)
        v = stackless.schedule_remove(v)
        cls.cvar.set(v)

    def test_pickle_tasklet_with_context(self):
        ctx = contextvars.copy_context()
        t = stackless.tasklet(self.task)("changed").set_context(ctx)
        stackless.run()
        self.assertTrue(t.alive)
        self.assertIs(t.tempval, self.sentinel)
        self.assertEqual(ctx[self.cvar], "changed")

        external_map = {"context ctx": ctx}

        p = self.dumps(t, external_map = external_map)
        # import pickletools; pickletools.dis(pickletools.optimize(p))
        t.kill()

        t = self.loads(p, external_map = external_map)
        self.assertEqual(t.context_id, id(ctx))
        self.assertTrue(t.alive)
        t.insert()
        t.tempval = "after unpickling"
        if is_soft():
            stackless.run()
            self.assertFalse(t.alive)
            self.assertEqual(ctx[self.cvar], "after unpickling")

    def test_pickle_tasklet_in_tasklet_context_run(self):
        ctx1 = contextvars.copy_context()
        ctx2 = contextvars.Context()
        t = stackless.tasklet(stackless.tasklet().set_context(ctx2).context_run)(self.task, "changed").set_context(ctx1)
        self.assertEqual(t.context_id, id(ctx1))
        stackless.run()
        self.assertTrue(t.alive)
        self.assertIs(ctx1[self.cvar], self.sentinel)
        self.assertEqual(t.tempval, "unset")
        self.assertEqual(ctx2[self.cvar], "changed")

        external_map = {"context ctx1": ctx1, "context ctx2": ctx2,}

        p = self.dumps(t, external_map = external_map)
        # import pickletools; pickletools.dis(pickletools.optimize(p))
        t.kill()

        t = self.loads(p, external_map = external_map)
        self.assertEqual(t.context_id, id(ctx2))
        self.assertTrue(t.alive)
        t.insert()
        t.tempval = "after unpickling"
        if is_soft():
            stackless.run()
            self.assertFalse(t.alive)
            self.assertEqual(t.context_id, id(ctx1))
            self.assertEqual(ctx2[self.cvar], "after unpickling")
        self.assertIs(ctx1[self.cvar], self.sentinel)


class TestCopy(StacklessTestCase):
    ITERATOR_TYPE = type(iter("abc"))

    def _test(self, obj, *attributes, **kw):
        expected_type = kw.get("expected_type", type(obj))
        copier = copy._copy_dispatch.pop(type(obj), None)
        try:
            c = copy.copy(obj)
        finally:
            if copier is not None:
                copy._copy_dispatch[type(obj)] = copier
        try:
            obj_hash = hash(obj)
        except TypeError:
            obj_hash = None
        if obj_hash is None:
            self.assertIsNot(c, obj)
        if c is obj:
            return
        self.assertIs(type(c), expected_type)
        for name in attributes:
            value_obj = getattr(obj, name)
            value_c = getattr(c, name)
            # it is a shallow copy, therefore the attributes should
            # refer to the same objects
            if type(value_obj) is type(value_c) and isinstance(value_obj, numbers.Number):
                self.assertEqual(value_c, value_obj, "{!r} != {!r} (attribute {})".format(value_c, value_obj, name))
            else:
                self.assertIs(value_c, value_obj, "{!r} is not {!r} (attribute {})".format(value_c, value_obj, name))
        return c

    def test_module_stackless(self):
        # test for issue 128
        self.assertIs(stackless, copy.copy(stackless))

    def test_code(self):
        def f():
            pass
        obj = f.__code__
        self._test(obj, "co_argcount", "co_nlocals", "co_stacksize", "co_flags",
                   "co_code", "co_consts", "co_names", "co_varnames", "co_filename",
                   "co_name", "co_firstlineno", "co_lnotab", "co_freevars", "co_cellvars")

    def test_cell(self):
        def create_cell(obj):
            return (lambda: obj).__closure__[0]
        obj = create_cell(None)
        self._test(obj, 'cell_contents')

    def test_function(self):
        v = 123
        def obj(a, b, c=4711, *, d=815):
            "a test function"
            return v
        obj.__annotations__ = {'bla': 'fasel'}
        self._test(obj, '__code__', '__globals__', '__name__', '__defaults__',
                   '__closure__', '__module__', '__kwdefaults__', '__doc__',
                   '__dict__', '__annotations__', '__qualname__')

    def test_frame(self):
        obj = sys._getframe()
        # changed in version 3.4.4: Stackless no longer pretends to be able to
        # pickle arbitrary frames
        self.assertRaises(TypeError, self._test, obj)

    def test_traceback(self):
        try:
            1 // 0
        except ZeroDivisionError:
            obj = sys.exc_info()[2]
        self._test(obj, 'tb_frame', 'tb_next')

    def test_module(self):
        import tabnanny as obj
        self._test(obj, '__name__', '__dict__')

    def test_method(self):
        obj = self.id
        self._test(obj, '__func__', '__self__')

    def test_method_wrapper(self):
        obj = [].__len__
        self._test(obj, '__objclass__', '__self__')

    def test_generator(self):
        def g():
            yield 1
        obj = g()
        self._test(obj, 'gi_running', 'gi_code', '__name__', '__qualname__')

    def test_dict_keys(self):
        d = {1: 10, "a": "ABC"}
        obj = d.keys()
        self._test(obj)

    def test_dict_values(self):
        d = {1: 10, "a": "ABC"}
        obj = d.values()
        self._test(obj)

    def test_dict_items(self):
        d = {1: 10, "a": "ABC"}
        obj = d.items()
        self._test(obj)

    def test_coroutine(self):
        async def c():
            return 1
        obj = c()
        c = self._test(obj, 'cr_running', 'cr_code', '__name__', '__qualname__', 'cr_origin')
        self.assertRaises(StopIteration, obj.send, None)
        self.assertRaises(StopIteration, c.send, None)

    def test_coro_wrapper(self):
        async def c():
            return 1
        obj = c().__await__()
        cw = self._test(obj)
        self.assertRaises(StopIteration, cw.send, None)
        self.assertRaisesRegex(RuntimeError, "cannot reuse already awaited coroutine", obj.send, None)

    def test_async_generator(self):
        async def ag():
            yield 100
        obj = ag()
        ag = self._test(obj, 'ag_running', 'ag_code', '__name__', '__qualname__')
        with self.assertRaises(StopIteration):
            ag.aclose().send(None)

    def test_async_gen_asend(self):
        async def ag():
            yield 100
        obj = ag().__anext__()
        ags = self._test(obj)
        with self.assertRaises(StopIteration) as cm:
            ags.send(None)
        self.assertEqual(cm.exception.value, 100)

    def test_async_gen_athrow(self):
        async def ag():
            yield 100
        a = ag()
        self.assertRaises(StopIteration, a.__anext__().__next__)
        obj = a.athrow(ZeroDivisionError("foo"))
        agt = self._test(obj)
        with self.assertRaises(ZeroDivisionError) as cm:
            agt.__next__()
        self.assertTupleEqual(cm.exception.args, ("foo",))


class TestPickleFlags(unittest.TestCase):
    def _test_pickle_flags(self, func):
        old = func()
        n_flags = sum(1 for k in dir(stackless) if k.startswith('PICKLEFLAGS_'))
        m = 1 << n_flags
        self.assertEqual(old, 0)
        self.assertEqual(func(-1), 0)
        self.assertEqual(func(-1, -1), 0)
        self.assertEqual(func(0xffffff, 0), 0)
        self.assertEqual(func(0), 0)
        for i in range(1, m):
            self.assertEqual(func(i), i - 1)
        self.assertEqual(func(0), m - 1)
        self.assertRaises(ValueError, func, -2)
        self.assertRaises(ValueError, func, m)
        self.assertEqual(func(-1), old)

    def test_pickle_flags(self):
        self._test_pickle_flags(stackless.pickle_flags)

    def test_pickle_flags_default(self):
        self._test_pickle_flags(stackless.pickle_flags_default)

    def test_new_thread(self):
        def run():
            self.pickle_flags = stackless.pickle_flags()

        current = stackless.pickle_flags()
        old = stackless.pickle_flags_default(0)
        self.assertEqual(stackless.pickle_flags(), current)
        self.addCleanup(stackless.pickle_flags_default, old)

        t = threading.Thread(target=run)
        t.start()
        t.join(10)
        self.assertFalse(t.is_alive())
        self.assertEqual(self.pickle_flags, 0)
        self.pickle_flags = None

        stackless.pickle_flags_default(1)
        self.assertEqual(stackless.pickle_flags(), current)

        t = threading.Thread(target=run)
        t.start()
        t.join(10)
        self.assertFalse(t.is_alive())

        self.assertEqual(self.pickle_flags, 1)
        self.assertEqual(stackless.pickle_flags(), current)


class TestCodePickling(unittest.TestCase):
    def test_reduce_magic(self):
        code = (lambda :None).__code__
        reduce = stackless._stackless._wrap.code.__reduce__
        reduced = reduce(code)
        self.assertIsInstance(reduced, tuple)
        self.assertEqual(len(reduced), 3)
        self.assertIsInstance(reduced[1], tuple)
        self.assertGreater(len(reduced[1]), 0)
        self.assertIsInstance(reduced[1][0], int)
        # see Python C-API documentation for PyImport_GetMagicNumber()
        self.assertEqual(reduced[1][0], struct.unpack("<l", importlib.util.MAGIC_NUMBER)[0])

    def test_new_with_wrong_magic_error(self):
        code = (lambda :None).__code__
        reduce = stackless._stackless._wrap.code.__reduce__
        reduced = reduce(code)
        args = (reduced[1][0] + 1,) + reduced[1][1:]
        self.assertIsInstance(reduced[0](*reduced[1]), type(code))
        with self.assertRaisesRegex(RuntimeWarning, "Unpickling code object with invalid magic number"):
            with stackless.atomic():
                with warnings.catch_warnings():
                    warnings.simplefilter("error", RuntimeWarning)
                    reduced[0](*args)

    def test_new_without_magic(self):
        code = (lambda :None).__code__
        reduce = stackless._stackless._wrap.code.__reduce__
        reduced = reduce(code)
        args = reduced[1][1:]
        with self.assertRaisesRegex(RuntimeWarning, "Unpickling code object with invalid magic number 0"):
            with stackless.atomic():
                with warnings.catch_warnings():
                    warnings.simplefilter("error", RuntimeWarning)
                    reduced[0](*args)

    def test_func_with_wrong_magic(self):
        l = (lambda :None)
        code = l.__code__
        reduce = stackless._stackless._wrap.code.__reduce__
        reduced = reduce(code)
        args = (reduced[1][0] + 1,) + reduced[1][1:]
        self.assertIsInstance(reduced[0](*reduced[1]), type(code))
        with stackless.atomic():
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                code2 = reduced[0](*args)
        code2.__setstate__(())
        self.assertIs(type(code2), type(code))

        reduce = stackless._stackless._wrap.function.__reduce__
        reduced_func = reduce(l)
        f = reduced_func[0](*reduced_func[1])
        args = (code2,) + reduced_func[2][1:]
        with self.assertRaisesRegex(RuntimeWarning, "Unpickling function with invalid code object:"):
            with stackless.atomic():
                with warnings.catch_warnings():
                    warnings.simplefilter("error", RuntimeWarning)
                    f = f.__setstate__(args)

    def test_run_with_wrong_magic(self):
        # run this test as a subprocess, because it triggers a fprintf(stderr, ...) in ceval.c
        # and I don't like this output in our test suite.
        args = []
        if not stackless.enable_softswitch(None):
            args.append("--hard")

        rc = subprocess.call([sys.executable, "-s", "-S", "-E", "-c", dedent("""
            import stackless
            import warnings
            import sys

            sys.stderr = sys.stdout
            if "--hard" in sys.argv:
                stackless.enable_softswitch(False)
            l = (lambda :None)
            code = l.__code__
            reduce = stackless._stackless._wrap.code.__reduce__
            reduced = reduce(code)
            args = (reduced[1][0] + 1,) + reduced[1][1:]
            with stackless.atomic():
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    code2 = reduced[0](*args)
            code2.__setstate__(())
            assert(type(code2) is type(code))
            # now execute code 2, first create a function from code2
            f = type(l)(code2, globals())
            # f should raise
            try:
                f()
            except SystemError as e:
                assert(str(e) == 'unknown opcode')
            else:
                assert(0, "expected exception not raised")
            sys.exit(42)
            """)] + args, stderr=subprocess.DEVNULL)
        self.assertEqual(rc, 42)


class TestFunctionPickling(StacklessPickleTestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def testFunctionModulePreservation(self):
        # The 'module' name on the function was not being preserved.
        f1 = lambda: None  # @IgnorePep8
        f2 = self.loads(self.dumps(f1))
        self.assertEqual(f1.__module__, f2.__module__)

    def test_unpickle_pre38(self):
        def obj():
            pass

        reduced = stackless._stackless._wrap.function.__reduce__(obj)
        obj2 = reduced[0](*reduced[1])
        args = reduced[2][:6]
        obj2.__setstate__(args)
        self.assertIs(type(obj2), type(obj))


if __name__ == '__main__':
    if not sys.argv[1:]:
        sys.argv.append('-v')
    unittest.main()
