/* C-based Tracer for Coverage. */

#include "Python.h"
#include "compile.h"        /* in 2.3, this wasn't part of Python.h */
#include "eval.h"           /* or this. */
#include "structmember.h"
#include "frameobject.h"

/* Compile-time debugging helpers */
#undef WHAT_LOG         /* Define to log the WHAT params in the trace function. */
#undef TRACE_LOG        /* Define to log our bookkeeping. */
#undef COLLECT_STATS    /* Collect counters: stats are printed when tracer is stopped. */

#if COLLECT_STATS
#define STATS(x)        x
#else
#define STATS(x)
#endif

/* Py 2.x and 3.x compatibility */

#ifndef Py_TYPE
#define Py_TYPE(o)    (((PyObject*)(o))->ob_type)
#endif

#if PY_MAJOR_VERSION >= 3

#define MyText_Type         PyUnicode_Type
#define MyText_Check(o)     PyUnicode_Check(o)
#define MyText_AS_STRING(o) PyBytes_AS_STRING(PyUnicode_AsASCIIString(o))
#define MyInt_FromLong(l)   PyLong_FromLong(l)

#define MyType_HEAD_INIT    PyVarObject_HEAD_INIT(NULL, 0)

#else

#define MyText_Type         PyString_Type
#define MyText_Check(o)     PyString_Check(o)
#define MyText_AS_STRING(o) PyString_AS_STRING(o)
#define MyInt_FromLong(l)   PyInt_FromLong(l)

#define MyType_HEAD_INIT    PyObject_HEAD_INIT(NULL)  0,

#endif /* Py3k */

/* The values returned to indicate ok or error. */
#define RET_OK      0
#define RET_ERROR   -1

/* An entry on the data stack.  For each call frame, we need to record the
    dictionary to capture data, and the last line number executed in that
    frame.
*/
typedef struct {
    PyObject * file_data;  /* PyMem_Malloc'ed, a borrowed ref. */
    int last_line;
} DataStackEntry;

/* The Tracer type. */

typedef struct {
    PyObject_HEAD

    /* Python objects manipulated directly by the Collector class. */
    PyObject * should_trace;
    PyObject * data;
    PyObject * should_trace_cache;
    PyObject * arcs;

    /* Has the tracer been started? */
    int started;
    /* Are we tracing arcs, or just lines? */
    int tracing_arcs;

    /*
        The data stack is a stack of dictionaries.  Each dictionary collects
        data for a single source file.  The data stack parallels the call stack:
        each call pushes the new frame's file data onto the data stack, and each
        return pops file data off.

        The file data is a dictionary whose form depends on the tracing options.
        If tracing arcs, the keys are line number pairs.  If not tracing arcs,
        the keys are line numbers.  In both cases, the value is irrelevant
        (None).
    */
    /* The index of the last-used entry in data_stack. */
    int depth;
    /* The file data at each level, or NULL if not recording. */
    DataStackEntry * data_stack;
    int data_stack_alloc;       /* number of entries allocated at data_stack. */

    /* The current file_data dictionary.  Borrowed. */
    PyObject * cur_file_data;

    /* The line number of the last line recorded, for tracing arcs.
        -1 means there was no previous line, as when entering a code object.
    */
    int last_line;

    /* The parent frame for the last exception event, to fix missing returns. */
    PyFrameObject * last_exc_back;
    int last_exc_firstlineno;

#if COLLECT_STATS
    struct {
        unsigned int calls;
        unsigned int lines;
        unsigned int returns;
        unsigned int exceptions;
        unsigned int others;
        unsigned int new_files;
        unsigned int missed_returns;
        unsigned int stack_reallocs;
        unsigned int errors;
    } stats;
#endif /* COLLECT_STATS */
} Tracer;

#define STACK_DELTA    100

static int
Tracer_init(Tracer *self, PyObject *args_unused, PyObject *kwds_unused)
{
#if COLLECT_STATS
    self->stats.calls = 0;
    self->stats.lines = 0;
    self->stats.returns = 0;
    self->stats.exceptions = 0;
    self->stats.others = 0;
    self->stats.new_files = 0;
    self->stats.missed_returns = 0;
    self->stats.stack_reallocs = 0;
    self->stats.errors = 0;
#endif /* COLLECT_STATS */

    self->should_trace = NULL;
    self->data = NULL;
    self->should_trace_cache = NULL;
    self->arcs = NULL;

    self->started = 0;
    self->tracing_arcs = 0;

    self->depth = -1;
    self->data_stack = PyMem_Malloc(STACK_DELTA*sizeof(DataStackEntry));
    if (self->data_stack == NULL) {
        STATS( self->stats.errors++; )
        PyErr_NoMemory();
        return RET_ERROR;
    }
    self->data_stack_alloc = STACK_DELTA;

    self->cur_file_data = NULL;
    self->last_line = -1;

    self->last_exc_back = NULL;

    return RET_OK;
}

static void
Tracer_dealloc(Tracer *self)
{
    if (self->started) {
        PyEval_SetTrace(NULL, NULL);
    }

    Py_XDECREF(self->should_trace);
    Py_XDECREF(self->data);
    Py_XDECREF(self->should_trace_cache);

    PyMem_Free(self->data_stack);

    Py_TYPE(self)->tp_free((PyObject*)self);
}

#if TRACE_LOG
static const char *
indent(int n)
{
    static const char * spaces =
        "                                                                    "
        "                                                                    "
        "                                                                    "
        "                                                                    "
        ;
    return spaces + strlen(spaces) - n*2;
}

static int logging = 0;
/* Set these constants to be a file substring and line number to start logging. */
static const char * start_file = "tests/views";
static int start_line = 27;

static void
showlog(int depth, int lineno, PyObject * filename, const char * msg)
{
    if (logging) {
        printf("%s%3d ", indent(depth), depth);
        if (lineno) {
            printf("%4d", lineno);
        }
        else {
            printf("    ");
        }
        if (filename) {
            printf(" %s", MyText_AS_STRING(filename));
        }
        if (msg) {
            printf(" %s", msg);
        }
        printf("\n");
    }
}

#define SHOWLOG(a,b,c,d)    showlog(a,b,c,d)
#else
#define SHOWLOG(a,b,c,d)
#endif /* TRACE_LOG */

#if WHAT_LOG
static const char * what_sym[] = {"CALL", "EXC ", "LINE", "RET "};
#endif

/* Record a pair of integers in self->cur_file_data. */
static int
Tracer_record_pair(Tracer *self, int l1, int l2)
{
    int ret = RET_OK;

    PyObject * t = PyTuple_New(2);
    if (t != NULL) {
        PyTuple_SET_ITEM(t, 0, MyInt_FromLong(l1));
        PyTuple_SET_ITEM(t, 1, MyInt_FromLong(l2));
        if (PyDict_SetItem(self->cur_file_data, t, Py_None) < 0) {
            STATS( self->stats.errors++; )
            ret = RET_ERROR;
        }
        Py_DECREF(t);
    }
    else {
        STATS( self->stats.errors++; )
        ret = RET_ERROR;
    }
    return ret;
}

/*
 * The Trace Function
 */
static int
Tracer_trace(Tracer *self, PyFrameObject *frame, int what, PyObject *arg_unused)
{
    int ret = RET_OK;
    PyObject * filename = NULL;
    PyObject * tracename = NULL;

    #if WHAT_LOG
    if (what <= sizeof(what_sym)/sizeof(const char *)) {
        printf("trace: %s @ %s %d\n", what_sym[what], MyText_AS_STRING(frame->f_code->co_filename), frame->f_lineno);
    }
    #endif

    #if TRACE_LOG
    if (strstr(MyText_AS_STRING(frame->f_code->co_filename), start_file) && frame->f_lineno == start_line) {
        logging = 1;
    }
    #endif

    /* See below for details on missing-return detection. */
    if (self->last_exc_back) {
        if (frame == self->last_exc_back) {
            /* Looks like someone forgot to send a return event. We'll clear
               the exception state and do the RETURN code here.  Notice that the
               frame we have in hand here is not the correct frame for the RETURN,
               that frame is gone.  Our handling for RETURN doesn't need the
               actual frame, but we do log it, so that will look a little off if
               you're looking at the detailed log.

               If someday we need to examine the frame when doing RETURN, then
               we'll need to keep more of the missed frame's state.
            */
            STATS( self->stats.missed_returns++; )
            if (self->depth >= 0) {
                if (self->tracing_arcs && self->cur_file_data) {
                    if (Tracer_record_pair(self, self->last_line, -self->last_exc_firstlineno) < 0) {
                        return RET_ERROR;
                    }
                }
                SHOWLOG(self->depth, frame->f_lineno, frame->f_code->co_filename, "missedreturn");
                self->cur_file_data = self->data_stack[self->depth].file_data;
                self->last_line = self->data_stack[self->depth].last_line;
                self->depth--;
            }
        }
        self->last_exc_back = NULL;
    }


    switch (what) {
    case PyTrace_CALL:      /* 0 */
        STATS( self->stats.calls++; )
        /* Grow the stack. */
        self->depth++;
        if (self->depth >= self->data_stack_alloc) {
            STATS( self->stats.stack_reallocs++; )
            /* We've outgrown our data_stack array: make it bigger. */
            int bigger = self->data_stack_alloc + STACK_DELTA;
            DataStackEntry * bigger_data_stack = PyMem_Realloc(self->data_stack, bigger * sizeof(DataStackEntry));
            if (bigger_data_stack == NULL) {
                STATS( self->stats.errors++; )
                PyErr_NoMemory();
                self->depth--;
                return RET_ERROR;
            }
            self->data_stack = bigger_data_stack;
            self->data_stack_alloc = bigger;
        }

        /* Push the current state on the stack. */
        self->data_stack[self->depth].file_data = self->cur_file_data;
        self->data_stack[self->depth].last_line = self->last_line;

        /* Check if we should trace this line. */
        filename = frame->f_code->co_filename;
        tracename = PyDict_GetItem(self->should_trace_cache, filename);
        if (tracename == NULL) {
            STATS( self->stats.new_files++; )
            /* We've never considered this file before. */
            /* Ask should_trace about it. */
            PyObject * args = Py_BuildValue("(OO)", filename, frame);
            tracename = PyObject_Call(self->should_trace, args, NULL);
            Py_DECREF(args);
            if (tracename == NULL) {
                /* An error occurred inside should_trace. */
                STATS( self->stats.errors++; )
                return RET_ERROR;
            }
            if (PyDict_SetItem(self->should_trace_cache, filename, tracename) < 0) {
                STATS( self->stats.errors++; )
                return RET_ERROR;
            }
        }
        else {
            Py_INCREF(tracename);
        }

        /* If tracename is a string, then we're supposed to trace. */
        if (MyText_Check(tracename)) {
            PyObject * file_data = PyDict_GetItem(self->data, tracename);
            if (file_data == NULL) {
                file_data = PyDict_New();
                if (file_data == NULL) {
                    STATS( self->stats.errors++; )
                    return RET_ERROR;
                }
                ret = PyDict_SetItem(self->data, tracename, file_data);
                Py_DECREF(file_data);
                if (ret < 0) {
                    STATS( self->stats.errors++; )
                    return RET_ERROR;
                }
            }
            self->cur_file_data = file_data;
            SHOWLOG(self->depth, frame->f_lineno, filename, "traced");
        }
        else {
            self->cur_file_data = NULL;
            SHOWLOG(self->depth, frame->f_lineno, filename, "skipped");
        }

        Py_DECREF(tracename);

        self->last_line = -1;
        break;

    case PyTrace_RETURN:    /* 3 */
        STATS( self->stats.returns++; )
        /* A near-copy of this code is above in the missing-return handler. */
        if (self->depth >= 0) {
            if (self->tracing_arcs && self->cur_file_data) {
                int first = frame->f_code->co_firstlineno;
                if (Tracer_record_pair(self, self->last_line, -first) < 0) {
                    return RET_ERROR;
                }
            }

            SHOWLOG(self->depth, frame->f_lineno, frame->f_code->co_filename, "return");
            self->cur_file_data = self->data_stack[self->depth].file_data;
            self->last_line = self->data_stack[self->depth].last_line;
            self->depth--;
        }
        break;

    case PyTrace_LINE:      /* 2 */
        STATS( self->stats.lines++; )
        if (self->depth >= 0) {
            SHOWLOG(self->depth, frame->f_lineno, frame->f_code->co_filename, "line");
            if (self->cur_file_data) {
                /* We're tracing in this frame: record something. */
                if (self->tracing_arcs) {
                    /* Tracing arcs: key is (last_line,this_line). */
                    if (Tracer_record_pair(self, self->last_line, frame->f_lineno) < 0) {
                        return RET_ERROR;
                    }
                }
                else {
                    /* Tracing lines: key is simply this_line. */
                    PyObject * this_line = MyInt_FromLong(frame->f_lineno);
                    if (this_line == NULL) {
                        STATS( self->stats.errors++; )
                        return RET_ERROR;
                    }
                    ret = PyDict_SetItem(self->cur_file_data, this_line, Py_None);
                    Py_DECREF(this_line);
                    if (ret < 0) {
                        STATS( self->stats.errors++; )
                        return RET_ERROR;
                    }
                }
            }
            self->last_line = frame->f_lineno;
        }
        break;

    case PyTrace_EXCEPTION:
        /* Some code (Python 2.3, and pyexpat anywhere) fires an exception event
           without a return event.  To detect that, we'll keep a copy of the
           parent frame for an exception event.  If the next event is in that
           frame, then we must have returned without a return event.  We can
           synthesize the missing event then.

           Python itself fixed this problem in 2.4.  Pyexpat still has the bug.
           I've reported the problem with pyexpat as http://bugs.python.org/issue6359 .
           If it gets fixed, this code should still work properly.  Maybe some day
           the bug will be fixed everywhere coverage.py is supported, and we can
           remove this missing-return detection.

           More about this fix: http://nedbatchelder.com/blog/200907/a_nasty_little_bug.html
        */
        STATS( self->stats.exceptions++; )
        self->last_exc_back = frame->f_back;
        self->last_exc_firstlineno = frame->f_code->co_firstlineno;
        break;

    default:
        STATS( self->stats.others++; )
        break;
    }

    return RET_OK;
}

/*
 * A sys.settrace-compatible function that invokes our C trace function.
 */
static PyObject *
Tracer_pytrace(Tracer *self, PyObject *args)
{
    PyFrameObject *frame;
    PyObject *what_str;
    PyObject *arg_unused;
    int what;
    static char *what_names[] = {
        "call", "exception", "line", "return",
        "c_call", "c_exception", "c_return",
        NULL
        };

    if (!PyArg_ParseTuple(args, "O!O!O:Tracer_pytrace",
            &PyFrame_Type, &frame, &MyText_Type, &what_str, &arg_unused)) {
        goto done;
    }

    /* In Python, the what argument is a string, we need to find an int
       for the C function. */
    for (what = 0; what_names[what]; what++) {
        if (!strcmp(MyText_AS_STRING(what_str), what_names[what])) {
            break;
        }
    }

    /* Invoke the C function, and return ourselves. */
    if (Tracer_trace(self, frame, what, arg_unused) == RET_OK) {
        return PyObject_GetAttrString((PyObject*)self, "pytrace");
    }

done:
    return NULL;
}

static PyObject *
Tracer_start(Tracer *self, PyObject *args_unused)
{
    PyEval_SetTrace((Py_tracefunc)Tracer_trace, (PyObject*)self);
    self->started = 1;
    self->tracing_arcs = self->arcs && PyObject_IsTrue(self->arcs);
    self->last_line = -1;

    /* start() returns a trace function usable with sys.settrace() */
    return PyObject_GetAttrString((PyObject*)self, "pytrace");
}

static PyObject *
Tracer_stop(Tracer *self, PyObject *args_unused)
{
    if (self->started) {
        PyEval_SetTrace(NULL, NULL);
        self->started = 0;
    }

    return Py_BuildValue("");
}

static PyObject *
Tracer_get_stats(Tracer *self)
{
#if COLLECT_STATS
    return Py_BuildValue(
        "{sI,sI,sI,sI,sI,sI,sI,sI,si,sI}",
        "calls", self->stats.calls,
        "lines", self->stats.lines,
        "returns", self->stats.returns,
        "exceptions", self->stats.exceptions,
        "others", self->stats.others,
        "new_files", self->stats.new_files,
        "missed_returns", self->stats.missed_returns,
        "stack_reallocs", self->stats.stack_reallocs,
        "stack_alloc", self->data_stack_alloc,
        "errors", self->stats.errors
        );
#else
    return Py_BuildValue("");
#endif /* COLLECT_STATS */
}

static PyMemberDef
Tracer_members[] = {
    { "should_trace",       T_OBJECT, offsetof(Tracer, should_trace), 0,
            PyDoc_STR("Function indicating whether to trace a file.") },

    { "data",               T_OBJECT, offsetof(Tracer, data), 0,
            PyDoc_STR("The raw dictionary of trace data.") },

    { "should_trace_cache", T_OBJECT, offsetof(Tracer, should_trace_cache), 0,
            PyDoc_STR("Dictionary caching should_trace results.") },

    { "arcs",               T_OBJECT, offsetof(Tracer, arcs), 0,
            PyDoc_STR("Should we trace arcs, or just lines?") },

    { NULL }
};

static PyMethodDef
Tracer_methods[] = {
    { "pytrace",    (PyCFunction) Tracer_pytrace,       METH_VARARGS,
            PyDoc_STR("A trace function compatible with sys.settrace()") },

    { "start",      (PyCFunction) Tracer_start,         METH_VARARGS,
            PyDoc_STR("Start the tracer") },

    { "stop",       (PyCFunction) Tracer_stop,          METH_VARARGS,
            PyDoc_STR("Stop the tracer") },

    { "get_stats",  (PyCFunction) Tracer_get_stats,     METH_VARARGS,
            PyDoc_STR("Get statistics about the tracing") },

    { NULL }
};

static PyTypeObject
TracerType = {
    MyType_HEAD_INIT
    "coverage.Tracer",         /*tp_name*/
    sizeof(Tracer),            /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)Tracer_dealloc, /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "Tracer objects",          /* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    0,                         /* tp_iter */
    0,                         /* tp_iternext */
    Tracer_methods,            /* tp_methods */
    Tracer_members,            /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)Tracer_init,     /* tp_init */
    0,                         /* tp_alloc */
    0,                         /* tp_new */
};

/* Module definition */

#define MODULE_DOC PyDoc_STR("Fast coverage tracer.")

#if PY_MAJOR_VERSION >= 3

static PyModuleDef
moduledef = {
    PyModuleDef_HEAD_INIT,
    "coverage.tracer",
    MODULE_DOC,
    -1,
    NULL,       /* methods */
    NULL,
    NULL,       /* traverse */
    NULL,       /* clear */
    NULL
};


PyObject *
PyInit_tracer(void)
{
    PyObject * mod = PyModule_Create(&moduledef);
    if (mod == NULL) {
        return NULL;
    }

    TracerType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&TracerType) < 0) {
        Py_DECREF(mod);
        return NULL;
    }

    Py_INCREF(&TracerType);
    PyModule_AddObject(mod, "Tracer", (PyObject *)&TracerType);

    return mod;
}

#else

void
inittracer(void)
{
    PyObject * mod;

    mod = Py_InitModule3("coverage.tracer", NULL, MODULE_DOC);
    if (mod == NULL) {
        return;
    }

    TracerType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&TracerType) < 0) {
        return;
    }

    Py_INCREF(&TracerType);
    PyModule_AddObject(mod, "Tracer", (PyObject *)&TracerType);
}

#endif /* Py3k */
