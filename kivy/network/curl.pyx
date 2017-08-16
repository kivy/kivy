"""
Asynchronous downloader using libcurl
works also to preload image in background
"""

include "../lib/sdl2.pxi"

from libc.stdio cimport printf, FILE, fopen, fwrite, fclose
from libc.stdlib cimport calloc, free, realloc
from libc.string cimport memset, strdup, memcpy
from cpython.ref cimport PyObject, Py_XINCREF, Py_XDECREF
from posix.unistd cimport access, F_OK
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
    # http request
    int status_code
    char *url
    char *data
    int size
    void *callback
    curl_slist *headers

    # image loading if wanted
    int preload_image
    SDL_Surface *image
    char *image_error

    # caching
    char *cache_fn


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


cdef void dl_queue_data_clean(dl_queue_data **data):
    if data is NULL:
        return
    free(data[0].url)
    if data[0].cache_fn != NULL:
        free(data[0].cache_fn)
    if data[0].data != NULL:
        free(data[0].data)
    if data[0].headers != NULL:
        curl_slist_free_all(data[0].headers)
    if data[0].callback != NULL:
        Py_XDECREF(<PyObject *>data[0].callback)
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
    cdef:
        dl_queue_data *data
        CURL *curl
        SDL_RWops *rw
        int require_download
        FILE *fp


    curl = curl_easy_init()
    if not curl:
        return -1

    while SDL_AtomicGet(&dl_done) == 0:
        SDL_SemWait(dl_sem)
        data = <dl_queue_data *>dl_queue_dequeue(&dl_ctx)
        if data == NULL:
            continue

        require_download = 1

        if data.cache_fn != NULL and access(data.cache_fn, F_OK) != -1:
            require_download = 0

        if require_download:
            # download from url
            curl_easy_setopt(curl, CURLOPT_URL, data.url)
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_data)
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, data)
            curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, <void *><long>1L)
            # curl_easy_setopt(curl, CURLOPT_VERBOSE, <void *><long>1L)
            if data.headers != NULL:
                curl_easy_setopt(curl, CURLOPT_HTTPHEADER, data.headers)
            data.status_code = curl_easy_perform(curl)

            if data.cache_fn != NULL and data.size > 0:
                fp = fopen(data.cache_fn, "wb")
                fwrite(data.data, data.size, 1, fp)
                fclose(fp)

        # dynamically load the image too ?
        if data.preload_image:
            rw = NULL
            if data.size > 0:
                rw = SDL_RWFromMem(data.data, data.size)
            elif data.cache_fn != NULL:
                rw = SDL_RWFromFile(data.cache_fn, "rb")
            if rw:
                data.image = IMG_Load_RW(rw, 1)
                if data.image == NULL:
                    data.image_error = IMG_GetError()
                if data.data != NULL:
                    free(data.data)
                data.data = NULL

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


cdef load_from_surface(SDL_Surface *image):
    # taken from _img_sdl2, just for test.
    cdef SDL_Surface *image2 = NULL
    cdef SDL_Surface *fimage = NULL
    cdef SDL_PixelFormat pf
    cdef bytes pixels

    try:
        if image == NULL:
            return None

        fmt = ''
        if image.format.BytesPerPixel == 3:
            fmt = 'rgb'
        elif image.format.BytesPerPixel == 4:
            fmt = 'rgba'

        # FIXME the format might be 3 or 4, but it doesn't mean it's rgb/rgba.
        # It could be argb, bgra etc. it needs to be detected correctly. I guess
        # we could even let the original pass, bgra / argb support exists in
        # some opengl card.

        if fmt not in ('rgb', 'rgba'):
            if fmt == 'rgb':
                pf.format = SDL_PIXELFORMAT_BGR888
                fmt = 'rgb'
            else:
                pf.format = SDL_PIXELFORMAT_ABGR8888
                fmt = 'rgba'

            image2 = SDL_ConvertSurfaceFormat(image, pf.format, 0)
            if image2 == NULL:
                return

            fimage = image2
        else:
            if (image.format.Rshift > image.format.Bshift):
                memset(&pf, 0, sizeof(pf))
                pf.BitsPerPixel = 32
                pf.Rmask = 0x000000FF
                pf.Gmask = 0x0000FF00
                pf.Bmask = 0x00FF0000
                pf.Amask = 0xFF000000
                image2 = SDL_ConvertSurface(image, &pf, 0)
                fimage = image2
            else:
                fimage = image

        pixels = (<char *>fimage.pixels)[:fimage.pitch * fimage.h]
        return (fimage.w, fimage.h, fmt, pixels, fimage.pitch)

    finally:
        if image2:
            SDL_FreeSurface(image2)


def download(url, on_complete, headers=None, cache_fn=None, preload_image=False):
    cdef:
        dl_queue_data *data = <dl_queue_data *>calloc(1, sizeof(dl_queue_data))
        char *c_url = url
        char *c_header
        char *c_cache_fn
    data.status_code = -1
    data.data = NULL
    data.callback = NULL
    data.preload_image = int(preload_image)
    data.url = strdup(c_url)
    if cache_fn is not None:
        c_cache_fn = cache_fn
        data.cache_fn = strdup(c_cache_fn)
    if headers is not None:
        for key, value in headers.iteritems():
            header = "{}: {}".format(key, value)
            c_header = header
            data.headers = curl_slist_append(
                data.headers, c_header)

    if on_complete:
        data.callback = <void *>on_complete
        Py_XINCREF(<PyObject *>data.callback)

    dl_ensure_init()
    dl_queue_enqueue(&dl_ctx, data)
    SDL_SemPost(dl_sem)


def download_image(*args, **kwargs):
    kwargs["preload_image"] = True
    download(*args, **kwargs)


from kivy.core.image import Image as CoreImage
from kivy.core.image import ImageLoaderBase, ImageData


class ImageLoaderMemory(ImageLoaderBase):
    def __init__(self, filename, data, **kwargs):
        w, h, fmt, pixels, rowlength = data
        self._data = [ImageData(
            w, h, fmt, pixels, source=filename, rowlength=rowlength)]
        super(ImageLoaderMemory, self).__init__(filename, **kwargs)

    def load(self, kwargs):
        return self._data


def process():
    cdef dl_queue_data *data
    cdef bytes b_data = None
    cdef object callback
    while True:
        data = <dl_queue_data *>dl_queue_dequeue(&result_ctx)
        if data == NULL:
            break

        callback = <object><void *>data.callback
        if not callback:
            continue

        if data.preload_image:
            # send back an image
            # FIXME: optimization would be to prevent any conversion
            # here, but rather in the thread, if anything has to be done.
            # So using the load_from_surface will disapear somehow to have
            # a fully C version that doesn't require python.
            if data.image == NULL:
                callback(data.url, None, error=data.image_error)
            else:
                result = load_from_surface(data.image)
                loader = ImageLoaderMemory(data.url, result)
                image = CoreImage(loader)
                callback(data.url, image)
        else:
            # send back the data
            if data.size > 0:
                b_data = data.data[:data.size]
            callback(data.url, data.status_code, b_data)

        dl_queue_data_clean(&data)


def stop():
    SDL_AtomicSet(&dl_done, 1)
    SDL_SemPost(dl_sem)
    SDL_DestroySemaphore(dl_sem)
