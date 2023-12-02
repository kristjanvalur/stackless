/*[clinic input]
preserve
[clinic start generated code]*/

#if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)
#  include "pycore_gc.h"          // PyGC_Head
#  include "pycore_runtime.h"     // _Py_ID()
#endif
#include "pycore_abstract.h"      // _PyNumber_Index()
#include "pycore_modsupport.h"    // _PyArg_UnpackKeywords()

PyDoc_STRVAR(_heapq_heappush__doc__,
"heappush($module, heap, item, /, *, heapmap=<unrepresentable>)\n"
"--\n"
"\n"
"Push item onto heap, maintaining the heap invariant.");

#define _HEAPQ_HEAPPUSH_METHODDEF    \
    {"heappush", _PyCFunction_CAST(_heapq_heappush), METH_FASTCALL|METH_KEYWORDS, _heapq_heappush__doc__},

static PyObject *
_heapq_heappush_impl(PyObject *module, PyObject *heap, PyObject *item,
                     PyObject *heapmap);

static PyObject *
_heapq_heappush(PyObject *module, PyObject *const *args, Py_ssize_t nargs, PyObject *kwnames)
{
    PyObject *return_value = NULL;
    #if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)

    #define NUM_KEYWORDS 1
    static struct {
        PyGC_Head _this_is_not_used;
        PyObject_VAR_HEAD
        PyObject *ob_item[NUM_KEYWORDS];
    } _kwtuple = {
        .ob_base = PyVarObject_HEAD_INIT(&PyTuple_Type, NUM_KEYWORDS)
        .ob_item = { &_Py_ID(heapmap), },
    };
    #undef NUM_KEYWORDS
    #define KWTUPLE (&_kwtuple.ob_base.ob_base)

    #else  // !Py_BUILD_CORE
    #  define KWTUPLE NULL
    #endif  // !Py_BUILD_CORE

    static const char * const _keywords[] = {"", "", "heapmap", NULL};
    static _PyArg_Parser _parser = {
        .keywords = _keywords,
        .fname = "heappush",
        .kwtuple = KWTUPLE,
    };
    #undef KWTUPLE
    PyObject *argsbuf[3];
    Py_ssize_t noptargs = nargs + (kwnames ? PyTuple_GET_SIZE(kwnames) : 0) - 2;
    PyObject *heap;
    PyObject *item;
    PyObject *heapmap = NULL;

    args = _PyArg_UnpackKeywords(args, nargs, NULL, kwnames, &_parser, 2, 2, 0, argsbuf);
    if (!args) {
        goto exit;
    }
    if (!PyList_Check(args[0])) {
        _PyArg_BadArgument("heappush", "argument 1", "list", args[0]);
        goto exit;
    }
    heap = args[0];
    item = args[1];
    if (!noptargs) {
        goto skip_optional_kwonly;
    }
    if (!PyDict_Check(args[2])) {
        _PyArg_BadArgument("heappush", "argument 'heapmap'", "dict", args[2]);
        goto exit;
    }
    heapmap = args[2];
skip_optional_kwonly:
    return_value = _heapq_heappush_impl(module, heap, item, heapmap);

exit:
    return return_value;
}

PyDoc_STRVAR(_heapq_heappop__doc__,
"heappop($module, heap, /, *, heapmap=<unrepresentable>)\n"
"--\n"
"\n"
"Pop the smallest item off the heap, maintaining the heap invariant.");

#define _HEAPQ_HEAPPOP_METHODDEF    \
    {"heappop", _PyCFunction_CAST(_heapq_heappop), METH_FASTCALL|METH_KEYWORDS, _heapq_heappop__doc__},

static PyObject *
_heapq_heappop_impl(PyObject *module, PyObject *heap, PyObject *heapmap);

static PyObject *
_heapq_heappop(PyObject *module, PyObject *const *args, Py_ssize_t nargs, PyObject *kwnames)
{
    PyObject *return_value = NULL;
    #if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)

    #define NUM_KEYWORDS 1
    static struct {
        PyGC_Head _this_is_not_used;
        PyObject_VAR_HEAD
        PyObject *ob_item[NUM_KEYWORDS];
    } _kwtuple = {
        .ob_base = PyVarObject_HEAD_INIT(&PyTuple_Type, NUM_KEYWORDS)
        .ob_item = { &_Py_ID(heapmap), },
    };
    #undef NUM_KEYWORDS
    #define KWTUPLE (&_kwtuple.ob_base.ob_base)

    #else  // !Py_BUILD_CORE
    #  define KWTUPLE NULL
    #endif  // !Py_BUILD_CORE

    static const char * const _keywords[] = {"", "heapmap", NULL};
    static _PyArg_Parser _parser = {
        .keywords = _keywords,
        .fname = "heappop",
        .kwtuple = KWTUPLE,
    };
    #undef KWTUPLE
    PyObject *argsbuf[2];
    Py_ssize_t noptargs = nargs + (kwnames ? PyTuple_GET_SIZE(kwnames) : 0) - 1;
    PyObject *heap;
    PyObject *heapmap = NULL;

    args = _PyArg_UnpackKeywords(args, nargs, NULL, kwnames, &_parser, 1, 1, 0, argsbuf);
    if (!args) {
        goto exit;
    }
    if (!PyList_Check(args[0])) {
        _PyArg_BadArgument("heappop", "argument 1", "list", args[0]);
        goto exit;
    }
    heap = args[0];
    if (!noptargs) {
        goto skip_optional_kwonly;
    }
    if (!PyDict_Check(args[1])) {
        _PyArg_BadArgument("heappop", "argument 'heapmap'", "dict", args[1]);
        goto exit;
    }
    heapmap = args[1];
skip_optional_kwonly:
    return_value = _heapq_heappop_impl(module, heap, heapmap);

exit:
    return return_value;
}

PyDoc_STRVAR(_heapq_heapreplace__doc__,
"heapreplace($module, heap, item, /, *, heapmap=<unrepresentable>)\n"
"--\n"
"\n"
"Pop and return the current smallest value, and add the new item.\n"
"\n"
"This is more efficient than heappop() followed by heappush(), and can be\n"
"more appropriate when using a fixed-size heap.  Note that the value\n"
"returned may be larger than item!  That constrains reasonable uses of\n"
"this routine unless written as part of a conditional replacement:\n"
"\n"
"    if item > heap[0]:\n"
"        item = heapreplace(heap, item)");

#define _HEAPQ_HEAPREPLACE_METHODDEF    \
    {"heapreplace", _PyCFunction_CAST(_heapq_heapreplace), METH_FASTCALL|METH_KEYWORDS, _heapq_heapreplace__doc__},

static PyObject *
_heapq_heapreplace_impl(PyObject *module, PyObject *heap, PyObject *item,
                        PyObject *heapmap);

static PyObject *
_heapq_heapreplace(PyObject *module, PyObject *const *args, Py_ssize_t nargs, PyObject *kwnames)
{
    PyObject *return_value = NULL;
    #if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)

    #define NUM_KEYWORDS 1
    static struct {
        PyGC_Head _this_is_not_used;
        PyObject_VAR_HEAD
        PyObject *ob_item[NUM_KEYWORDS];
    } _kwtuple = {
        .ob_base = PyVarObject_HEAD_INIT(&PyTuple_Type, NUM_KEYWORDS)
        .ob_item = { &_Py_ID(heapmap), },
    };
    #undef NUM_KEYWORDS
    #define KWTUPLE (&_kwtuple.ob_base.ob_base)

    #else  // !Py_BUILD_CORE
    #  define KWTUPLE NULL
    #endif  // !Py_BUILD_CORE

    static const char * const _keywords[] = {"", "", "heapmap", NULL};
    static _PyArg_Parser _parser = {
        .keywords = _keywords,
        .fname = "heapreplace",
        .kwtuple = KWTUPLE,
    };
    #undef KWTUPLE
    PyObject *argsbuf[3];
    Py_ssize_t noptargs = nargs + (kwnames ? PyTuple_GET_SIZE(kwnames) : 0) - 2;
    PyObject *heap;
    PyObject *item;
    PyObject *heapmap = NULL;

    args = _PyArg_UnpackKeywords(args, nargs, NULL, kwnames, &_parser, 2, 2, 0, argsbuf);
    if (!args) {
        goto exit;
    }
    if (!PyList_Check(args[0])) {
        _PyArg_BadArgument("heapreplace", "argument 1", "list", args[0]);
        goto exit;
    }
    heap = args[0];
    item = args[1];
    if (!noptargs) {
        goto skip_optional_kwonly;
    }
    if (!PyDict_Check(args[2])) {
        _PyArg_BadArgument("heapreplace", "argument 'heapmap'", "dict", args[2]);
        goto exit;
    }
    heapmap = args[2];
skip_optional_kwonly:
    return_value = _heapq_heapreplace_impl(module, heap, item, heapmap);

exit:
    return return_value;
}

PyDoc_STRVAR(_heapq_heappushpop__doc__,
"heappushpop($module, heap, item, /, *, heapmap=<unrepresentable>)\n"
"--\n"
"\n"
"Push item on the heap, then pop and return the smallest item from the heap.\n"
"\n"
"The combined action runs more efficiently than heappush() followed by\n"
"a separate call to heappop().");

#define _HEAPQ_HEAPPUSHPOP_METHODDEF    \
    {"heappushpop", _PyCFunction_CAST(_heapq_heappushpop), METH_FASTCALL|METH_KEYWORDS, _heapq_heappushpop__doc__},

static PyObject *
_heapq_heappushpop_impl(PyObject *module, PyObject *heap, PyObject *item,
                        PyObject *heapmap);

static PyObject *
_heapq_heappushpop(PyObject *module, PyObject *const *args, Py_ssize_t nargs, PyObject *kwnames)
{
    PyObject *return_value = NULL;
    #if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)

    #define NUM_KEYWORDS 1
    static struct {
        PyGC_Head _this_is_not_used;
        PyObject_VAR_HEAD
        PyObject *ob_item[NUM_KEYWORDS];
    } _kwtuple = {
        .ob_base = PyVarObject_HEAD_INIT(&PyTuple_Type, NUM_KEYWORDS)
        .ob_item = { &_Py_ID(heapmap), },
    };
    #undef NUM_KEYWORDS
    #define KWTUPLE (&_kwtuple.ob_base.ob_base)

    #else  // !Py_BUILD_CORE
    #  define KWTUPLE NULL
    #endif  // !Py_BUILD_CORE

    static const char * const _keywords[] = {"", "", "heapmap", NULL};
    static _PyArg_Parser _parser = {
        .keywords = _keywords,
        .fname = "heappushpop",
        .kwtuple = KWTUPLE,
    };
    #undef KWTUPLE
    PyObject *argsbuf[3];
    Py_ssize_t noptargs = nargs + (kwnames ? PyTuple_GET_SIZE(kwnames) : 0) - 2;
    PyObject *heap;
    PyObject *item;
    PyObject *heapmap = NULL;

    args = _PyArg_UnpackKeywords(args, nargs, NULL, kwnames, &_parser, 2, 2, 0, argsbuf);
    if (!args) {
        goto exit;
    }
    if (!PyList_Check(args[0])) {
        _PyArg_BadArgument("heappushpop", "argument 1", "list", args[0]);
        goto exit;
    }
    heap = args[0];
    item = args[1];
    if (!noptargs) {
        goto skip_optional_kwonly;
    }
    if (!PyDict_Check(args[2])) {
        _PyArg_BadArgument("heappushpop", "argument 'heapmap'", "dict", args[2]);
        goto exit;
    }
    heapmap = args[2];
skip_optional_kwonly:
    return_value = _heapq_heappushpop_impl(module, heap, item, heapmap);

exit:
    return return_value;
}

PyDoc_STRVAR(_heapq_heapremove__doc__,
"heapremove($module, heap, index, /, *, heapmap=<unrepresentable>)\n"
"--\n"
"\n"
"Remove the element at the given index maintaining the heap invariant.\n"
"\n"
"Returns the removed item.");

#define _HEAPQ_HEAPREMOVE_METHODDEF    \
    {"heapremove", _PyCFunction_CAST(_heapq_heapremove), METH_FASTCALL|METH_KEYWORDS, _heapq_heapremove__doc__},

static PyObject *
_heapq_heapremove_impl(PyObject *module, PyObject *heap, Py_ssize_t index,
                       PyObject *heapmap);

static PyObject *
_heapq_heapremove(PyObject *module, PyObject *const *args, Py_ssize_t nargs, PyObject *kwnames)
{
    PyObject *return_value = NULL;
    #if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)

    #define NUM_KEYWORDS 1
    static struct {
        PyGC_Head _this_is_not_used;
        PyObject_VAR_HEAD
        PyObject *ob_item[NUM_KEYWORDS];
    } _kwtuple = {
        .ob_base = PyVarObject_HEAD_INIT(&PyTuple_Type, NUM_KEYWORDS)
        .ob_item = { &_Py_ID(heapmap), },
    };
    #undef NUM_KEYWORDS
    #define KWTUPLE (&_kwtuple.ob_base.ob_base)

    #else  // !Py_BUILD_CORE
    #  define KWTUPLE NULL
    #endif  // !Py_BUILD_CORE

    static const char * const _keywords[] = {"", "", "heapmap", NULL};
    static _PyArg_Parser _parser = {
        .keywords = _keywords,
        .fname = "heapremove",
        .kwtuple = KWTUPLE,
    };
    #undef KWTUPLE
    PyObject *argsbuf[3];
    Py_ssize_t noptargs = nargs + (kwnames ? PyTuple_GET_SIZE(kwnames) : 0) - 2;
    PyObject *heap;
    Py_ssize_t index;
    PyObject *heapmap = NULL;

    args = _PyArg_UnpackKeywords(args, nargs, NULL, kwnames, &_parser, 2, 2, 0, argsbuf);
    if (!args) {
        goto exit;
    }
    if (!PyList_Check(args[0])) {
        _PyArg_BadArgument("heapremove", "argument 1", "list", args[0]);
        goto exit;
    }
    heap = args[0];
    {
        Py_ssize_t ival = -1;
        PyObject *iobj = _PyNumber_Index(args[1]);
        if (iobj != NULL) {
            ival = PyLong_AsSsize_t(iobj);
            Py_DECREF(iobj);
        }
        if (ival == -1 && PyErr_Occurred()) {
            goto exit;
        }
        index = ival;
    }
    if (!noptargs) {
        goto skip_optional_kwonly;
    }
    if (!PyDict_Check(args[2])) {
        _PyArg_BadArgument("heapremove", "argument 'heapmap'", "dict", args[2]);
        goto exit;
    }
    heapmap = args[2];
skip_optional_kwonly:
    return_value = _heapq_heapremove_impl(module, heap, index, heapmap);

exit:
    return return_value;
}

PyDoc_STRVAR(_heapq_heapfix__doc__,
"heapfix($module, heap, index, /, *, heapmap=<unrepresentable>)\n"
"--\n"
"\n"
"Restore the heap invariant when the element at the given index has been modified.");

#define _HEAPQ_HEAPFIX_METHODDEF    \
    {"heapfix", _PyCFunction_CAST(_heapq_heapfix), METH_FASTCALL|METH_KEYWORDS, _heapq_heapfix__doc__},

static PyObject *
_heapq_heapfix_impl(PyObject *module, PyObject *heap, Py_ssize_t index,
                    PyObject *heapmap);

static PyObject *
_heapq_heapfix(PyObject *module, PyObject *const *args, Py_ssize_t nargs, PyObject *kwnames)
{
    PyObject *return_value = NULL;
    #if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)

    #define NUM_KEYWORDS 1
    static struct {
        PyGC_Head _this_is_not_used;
        PyObject_VAR_HEAD
        PyObject *ob_item[NUM_KEYWORDS];
    } _kwtuple = {
        .ob_base = PyVarObject_HEAD_INIT(&PyTuple_Type, NUM_KEYWORDS)
        .ob_item = { &_Py_ID(heapmap), },
    };
    #undef NUM_KEYWORDS
    #define KWTUPLE (&_kwtuple.ob_base.ob_base)

    #else  // !Py_BUILD_CORE
    #  define KWTUPLE NULL
    #endif  // !Py_BUILD_CORE

    static const char * const _keywords[] = {"", "", "heapmap", NULL};
    static _PyArg_Parser _parser = {
        .keywords = _keywords,
        .fname = "heapfix",
        .kwtuple = KWTUPLE,
    };
    #undef KWTUPLE
    PyObject *argsbuf[3];
    Py_ssize_t noptargs = nargs + (kwnames ? PyTuple_GET_SIZE(kwnames) : 0) - 2;
    PyObject *heap;
    Py_ssize_t index;
    PyObject *heapmap = NULL;

    args = _PyArg_UnpackKeywords(args, nargs, NULL, kwnames, &_parser, 2, 2, 0, argsbuf);
    if (!args) {
        goto exit;
    }
    if (!PyList_Check(args[0])) {
        _PyArg_BadArgument("heapfix", "argument 1", "list", args[0]);
        goto exit;
    }
    heap = args[0];
    {
        Py_ssize_t ival = -1;
        PyObject *iobj = _PyNumber_Index(args[1]);
        if (iobj != NULL) {
            ival = PyLong_AsSsize_t(iobj);
            Py_DECREF(iobj);
        }
        if (ival == -1 && PyErr_Occurred()) {
            goto exit;
        }
        index = ival;
    }
    if (!noptargs) {
        goto skip_optional_kwonly;
    }
    if (!PyDict_Check(args[2])) {
        _PyArg_BadArgument("heapfix", "argument 'heapmap'", "dict", args[2]);
        goto exit;
    }
    heapmap = args[2];
skip_optional_kwonly:
    return_value = _heapq_heapfix_impl(module, heap, index, heapmap);

exit:
    return return_value;
}

PyDoc_STRVAR(_heapq_heapify__doc__,
"heapify($module, heap, /, *, heapmap=<unrepresentable>)\n"
"--\n"
"\n"
"Transform list into a heap, in-place, in O(len(heap)) time.");

#define _HEAPQ_HEAPIFY_METHODDEF    \
    {"heapify", _PyCFunction_CAST(_heapq_heapify), METH_FASTCALL|METH_KEYWORDS, _heapq_heapify__doc__},

static PyObject *
_heapq_heapify_impl(PyObject *module, PyObject *heap, PyObject *heapmap);

static PyObject *
_heapq_heapify(PyObject *module, PyObject *const *args, Py_ssize_t nargs, PyObject *kwnames)
{
    PyObject *return_value = NULL;
    #if defined(Py_BUILD_CORE) && !defined(Py_BUILD_CORE_MODULE)

    #define NUM_KEYWORDS 1
    static struct {
        PyGC_Head _this_is_not_used;
        PyObject_VAR_HEAD
        PyObject *ob_item[NUM_KEYWORDS];
    } _kwtuple = {
        .ob_base = PyVarObject_HEAD_INIT(&PyTuple_Type, NUM_KEYWORDS)
        .ob_item = { &_Py_ID(heapmap), },
    };
    #undef NUM_KEYWORDS
    #define KWTUPLE (&_kwtuple.ob_base.ob_base)

    #else  // !Py_BUILD_CORE
    #  define KWTUPLE NULL
    #endif  // !Py_BUILD_CORE

    static const char * const _keywords[] = {"", "heapmap", NULL};
    static _PyArg_Parser _parser = {
        .keywords = _keywords,
        .fname = "heapify",
        .kwtuple = KWTUPLE,
    };
    #undef KWTUPLE
    PyObject *argsbuf[2];
    Py_ssize_t noptargs = nargs + (kwnames ? PyTuple_GET_SIZE(kwnames) : 0) - 1;
    PyObject *heap;
    PyObject *heapmap = NULL;

    args = _PyArg_UnpackKeywords(args, nargs, NULL, kwnames, &_parser, 1, 1, 0, argsbuf);
    if (!args) {
        goto exit;
    }
    if (!PyList_Check(args[0])) {
        _PyArg_BadArgument("heapify", "argument 1", "list", args[0]);
        goto exit;
    }
    heap = args[0];
    if (!noptargs) {
        goto skip_optional_kwonly;
    }
    if (!PyDict_Check(args[1])) {
        _PyArg_BadArgument("heapify", "argument 'heapmap'", "dict", args[1]);
        goto exit;
    }
    heapmap = args[1];
skip_optional_kwonly:
    return_value = _heapq_heapify_impl(module, heap, heapmap);

exit:
    return return_value;
}

PyDoc_STRVAR(_heapq__heappop_max__doc__,
"_heappop_max($module, heap, /)\n"
"--\n"
"\n"
"Maxheap variant of heappop.");

#define _HEAPQ__HEAPPOP_MAX_METHODDEF    \
    {"_heappop_max", (PyCFunction)_heapq__heappop_max, METH_O, _heapq__heappop_max__doc__},

static PyObject *
_heapq__heappop_max_impl(PyObject *module, PyObject *heap);

static PyObject *
_heapq__heappop_max(PyObject *module, PyObject *arg)
{
    PyObject *return_value = NULL;
    PyObject *heap;

    if (!PyList_Check(arg)) {
        _PyArg_BadArgument("_heappop_max", "argument", "list", arg);
        goto exit;
    }
    heap = arg;
    return_value = _heapq__heappop_max_impl(module, heap);

exit:
    return return_value;
}

PyDoc_STRVAR(_heapq__heapreplace_max__doc__,
"_heapreplace_max($module, heap, item, /)\n"
"--\n"
"\n"
"Maxheap variant of heapreplace.");

#define _HEAPQ__HEAPREPLACE_MAX_METHODDEF    \
    {"_heapreplace_max", _PyCFunction_CAST(_heapq__heapreplace_max), METH_FASTCALL, _heapq__heapreplace_max__doc__},

static PyObject *
_heapq__heapreplace_max_impl(PyObject *module, PyObject *heap,
                             PyObject *item);

static PyObject *
_heapq__heapreplace_max(PyObject *module, PyObject *const *args, Py_ssize_t nargs)
{
    PyObject *return_value = NULL;
    PyObject *heap;
    PyObject *item;

    if (!_PyArg_CheckPositional("_heapreplace_max", nargs, 2, 2)) {
        goto exit;
    }
    if (!PyList_Check(args[0])) {
        _PyArg_BadArgument("_heapreplace_max", "argument 1", "list", args[0]);
        goto exit;
    }
    heap = args[0];
    item = args[1];
    return_value = _heapq__heapreplace_max_impl(module, heap, item);

exit:
    return return_value;
}

PyDoc_STRVAR(_heapq__heapify_max__doc__,
"_heapify_max($module, heap, /)\n"
"--\n"
"\n"
"Maxheap variant of heapify.");

#define _HEAPQ__HEAPIFY_MAX_METHODDEF    \
    {"_heapify_max", (PyCFunction)_heapq__heapify_max, METH_O, _heapq__heapify_max__doc__},

static PyObject *
_heapq__heapify_max_impl(PyObject *module, PyObject *heap);

static PyObject *
_heapq__heapify_max(PyObject *module, PyObject *arg)
{
    PyObject *return_value = NULL;
    PyObject *heap;

    if (!PyList_Check(arg)) {
        _PyArg_BadArgument("_heapify_max", "argument", "list", arg);
        goto exit;
    }
    heap = arg;
    return_value = _heapq__heapify_max_impl(module, heap);

exit:
    return return_value;
}
/*[clinic end generated code: output=ca06046bb3a0ee8d input=a9049054013a1b77]*/
