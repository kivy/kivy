"""
Asynchronous downloader using libcurl
works also to preload image in background
"""

include "../lib/sdl2.pxi"


from libc.stdio cimport printf
from libc.stdlib cimport calloc, free, realloc
from libc.string cimport memset, strdup, memcpy
from libcpp cimport bool


cdef extern from * nogil:
    bool __sync_bool_compare_and_swap(void **ptr, void *oldval, void *newval)
    ctypedef unsigned int size_t


cdef extern from "curl/curl.h" nogil:
    enum CURLoption:
        CURLOPT_URL
        CURLOPT_VERBOSE
        CURLOPT_WRITEFUNCTION
        CURLOPT_WRITEDATA
        CURLOPT_FOLLOWLOCATION
        CURLOPT_HTTPHEADER
    enum CURLSHcode:
        CURLSHE_OK
    struct CURL:
        pass
    struct curl_slist:
        pass
    int CURLcode
    CURL *curl_easy_init()
    CURLSHcode curl_easy_setopt(CURL *, CURLoption, ...)
    CURLSHcode curl_easy_cleanup(CURL *)
    CURLSHcode curl_easy_perform(CURL *)
    curl_slist *curl_slist_append(curl_slist *, char *)
    void curl_slist_free_all(curl_slist *)


cdef extern from "SDL2/SDL.h" nogil:
    ctypedef struct SDL_Thread
    ctypedef struct SDL_mutex
    ctypedef int SDL_atomic_t
    ctypedef struct SDL_sem

    ctypedef long SDL_threadID
    ctypedef int (*SDL_ThreadFunction)(void *data)
    SDL_Thread *SDL_CreateThread(SDL_ThreadFunction fn, char *name, void *data)
    void SDL_DetachThread(SDL_Thread *thread)
    SDL_threadID SDL_GetThreadID(SDL_Thread *thread)
    void SDL_WaitThread(SDL_Thread *thread, int *status)

    int SDL_AtomicGet(SDL_atomic_t *)
    int SDL_AtomicSet(SDL_atomic_t *, int v)
    int SDL_SemWait(SDL_sem *)
    int SDL_SemPost(SDL_sem *)
    SDL_sem *SDL_CreateSemaphore(int)
    void SDL_DestroySemaphore(SDL_sem *)


ctypedef struct dl_queue_data:
    int status_code
    char *url
    char *data
    int size
    void *callback
    curl_slist *headers


ctypedef struct dl_queue_node:
    void *data
    dl_queue_node *next


ctypedef struct dl_queue_ctx:
    dl_queue_node *head
    dl_queue_node *tail


cdef dl_queue_ctx dl_ctx
cdef dl_queue_ctx result_ctx
cdef dl_queue_ctx thread_ctx
cdef int dl_running = 0
cdef int dl_stop = 0
cdef SDL_sem *dl_sem
cdef SDL_atomic_t dl_done


cdef void dl_queue_init(dl_queue_ctx *ctx) nogil:
    cdef dl_queue_node *node = <dl_queue_node *>calloc(1, sizeof(dl_queue_node))
    memset(ctx, 0, sizeof(dl_queue_ctx))
    ctx.head = ctx.tail = node


cdef void dl_queue_clean(dl_queue_ctx *ctx) nogil:
    cdef dl_queue_node *node
    cdef dl_queue_node *tmp
    if ctx.tail != NULL or ctx.head != NULL:
        node = ctx.head
        while node != ctx.tail:
            tmp = node.next
            free(node)
            node = tmp
        free(ctx.head)
        memset(ctx, 0, sizeof(dl_queue_ctx))


cdef int dl_queue_enqueue(dl_queue_ctx *ctx, void *data) nogil:
    cdef dl_queue_node *p
    cdef dl_queue_node *node = <dl_queue_node *>calloc(1, sizeof(dl_queue_node))
    if node == NULL:
        return -1

    node.data = data
    while True:
        p = ctx.tail
        if __sync_bool_compare_and_swap(<void **>&ctx.tail, p, node):
            p.next = node
            break

    return 0


cdef void *dl_queue_dequeue(dl_queue_ctx *ctx) nogil:
    cdef void *ret = NULL
    cdef dl_queue_node *p
    while True:
        p = ctx.head
        if p == NULL:
            continue
        if not __sync_bool_compare_and_swap(<void **>&ctx.head, p, NULL):
            continue
        break
    if p.next == NULL:
        ctx.head = p
        return NULL
    ret = p.next.data
    ctx.head = p.next
    free(p)
    return ret


cdef void dl_queue_data_clean(dl_queue_data **data) nogil:
    if data is NULL:
        return
    free(data[0].url)
    if data[0].size > 0:
        free(data[0].data)
    if data[0].headers != NULL:
        curl_slist_free_all(data[0].headers)
    free(data[0])


cdef size_t write_data(void *ptr, size_t size, size_t nmemb, dl_queue_data *data):
    cdef:
        size_t index = data.size
        size_t n = (size * nmemb)
        char* tmp;
    data.size += (size * nmemb)
    tmp = <char *>realloc(data.data, data.size + 1)

    if tmp != NULL:
        data.data = tmp
    else:
        if data.data != NULL:
            free(data.data)
        return 0

    memcpy((data.data + index), ptr, n)
    data.data[data.size] = '\0'
    return size * nmemb


cdef int dl_run_job(void *arg) nogil:
    cdef dl_queue_data *data
    cdef CURL *curl

    curl = curl_easy_init()
    if not curl:
        return -1

    while SDL_AtomicGet(&dl_done) == 0:
        SDL_SemWait(dl_sem)
        data = <dl_queue_data *>dl_queue_dequeue(&dl_ctx)
        if data == NULL:
            continue

        curl_easy_setopt(curl, CURLOPT_URL, data.url)
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_data)
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, data)
        curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, <void *><long>1L)
        curl_easy_setopt(curl, CURLOPT_VERBOSE, <void *><long>1L)
        if data.headers != NULL:
            curl_easy_setopt(curl, CURLOPT_HTTPHEADER, data.headers)
        data.status_code = curl_easy_perform(curl)

        dl_queue_enqueue(&result_ctx, data)

    curl_easy_cleanup(curl)
    return 0


cpdef void dl_init(int num_threads) nogil:
    cdef SDL_Thread *thread
    cdef int index
    global dl_sem, dl_running
    dl_queue_init(&dl_ctx)
    dl_queue_init(&result_ctx)
    dl_queue_init(&thread_ctx)
    SDL_AtomicSet(&dl_done, 0)
    dl_sem = SDL_CreateSemaphore(0)

    for index in range(num_threads):
        thread = SDL_CreateThread(dl_run_job, "curl", NULL)
        dl_queue_enqueue(&thread_ctx, thread)

    dl_running = 1


cdef void dl_ensure_init() nogil:
    if dl_running:
        return
    dl_init(4)


def download(url, on_complete, headers=None):
    cdef dl_queue_data *data = <dl_queue_data *>calloc(1, sizeof(dl_queue_data))
    cdef char *c_url = url
    cdef char *c_header
    data.status_code = -1
    data.data = NULL
    data.callback = NULL
    data.url = strdup(c_url)
    if headers is not None:
        for key, value in headers.iteritems():
            header = "{}: {}".format(key, value)
            c_header = header
            data.headers = curl_slist_append(
                data.headers, c_header)

    if on_complete:
        data.callback = <void *>on_complete

    dl_ensure_init()
    dl_queue_enqueue(&dl_ctx, data)
    SDL_SemPost(dl_sem)


def process():
    cdef dl_queue_data *data
    cdef bytes b_data = None
    cdef object callback
    while True:
        data = <dl_queue_data *>dl_queue_dequeue(&result_ctx)
        if data == NULL:
            break
        if data.size > 0:
            b_data = data.data[:data.size]
        callback = <object><void *>data.callback
        callback(data.url, data.status_code, b_data)
        dl_queue_data_clean(&data)


def stop():
    SDL_AtomicSet(&dl_done, 1)
    SDL_SemPost(dl_sem)
    SDL_DestroySemaphore(dl_sem)
