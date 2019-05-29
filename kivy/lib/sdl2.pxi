#Copyright (c) 2010-2012, Gabriel Jacobo
#All rights reserved.
#Permission to use this file is granted under the conditions of the Ignifuga Game Engine License
#whose terms are available in the LICENSE file or at http://www.ignifuga.org/license

include "../include/config.pxi"

cdef extern from "SDL_joystick.h":
    cdef struct SDL_Joystick
    cdef int SDL_HAT_CENTERED = 0x00
    cdef int SDL_HAT_UP = 0x01
    cdef int SDL_HAT_RIGHT = 0x02
    cdef int SDL_HAT_DOWN = 0x04
    cdef int SDL_HAT_LEFT = 0x08

cdef extern from "SDL.h":
    ctypedef unsigned char Uint8
    ctypedef unsigned long Uint32
    ctypedef signed long Sint32
    ctypedef unsigned long long Uint64
    ctypedef signed long long Sint64
    ctypedef signed short Sint16
    ctypedef unsigned short Uint16
    ctypedef void *SDL_GLContext
    ctypedef Uint32 SDL_Keycode
    ctypedef Sint32 SDL_JoystickID

    int SDL_WINDOWPOS_UNDEFINED

    ctypedef enum:
        SDL_PIXELFORMAT_BGRA8888
        SDL_PIXELFORMAT_ARGB8888
        SDL_PIXELFORMAT_RGBA8888
        SDL_PIXELFORMAT_ABGR8888
        SDL_PIXELFORMAT_RGB24
        SDL_PIXELFORMAT_BGR24

    ctypedef enum SDL_GLattr:
        SDL_GL_RED_SIZE
        SDL_GL_GREEN_SIZE
        SDL_GL_BLUE_SIZE
        SDL_GL_ALPHA_SIZE
        SDL_GL_BUFFER_SIZE
        SDL_GL_DOUBLEBUFFER
        SDL_GL_DEPTH_SIZE
        SDL_GL_STENCIL_SIZE
        SDL_GL_ACCUM_RED_SIZE
        SDL_GL_ACCUM_GREEN_SIZE
        SDL_GL_ACCUM_BLUE_SIZE
        SDL_GL_ACCUM_ALPHA_SIZE
        SDL_GL_STEREO
        SDL_GL_MULTISAMPLEBUFFERS
        SDL_GL_MULTISAMPLESAMPLES
        SDL_GL_ACCELERATED_VISUAL
        SDL_GL_RETAINED_BACKING
        SDL_GL_CONTEXT_MAJOR_VERSION
        SDL_GL_CONTEXT_MINOR_VERSION
        SDL_GL_CONTEXT_EGL
        SDL_GL_CONTEXT_FLAGS
        SDL_GL_CONTEXT_PROFILE_MASK

    ctypedef enum SDL_SystemCursor:
        SDL_SYSTEM_CURSOR_ARROW
        SDL_SYSTEM_CURSOR_IBEAM
        SDL_SYSTEM_CURSOR_WAIT
        SDL_SYSTEM_CURSOR_CROSSHAIR
        SDL_SYSTEM_CURSOR_WAITARROW
        SDL_SYSTEM_CURSOR_SIZENWSE
        SDL_SYSTEM_CURSOR_SIZENESW
        SDL_SYSTEM_CURSOR_SIZEWE
        SDL_SYSTEM_CURSOR_SIZENS
        SDL_SYSTEM_CURSOR_SIZEALL
        SDL_SYSTEM_CURSOR_NO
        SDL_SYSTEM_CURSOR_HAND

    ctypedef enum SDL_BlendMode:
        SDL_BLENDMODE_NONE = 0x00000000
        SDL_BLENDMODE_BLEND = 0x00000001
        SDL_BLENDMODE_ADD = 0x00000002
        SDL_BLENDMODE_MOD = 0x00000004

    ctypedef enum SDL_TextureAccess:
        SDL_TEXTUREACCESS_STATIC
        SDL_TEXTUREACCESS_STREAMING
        SDL_TEXTUREACCESS_TARGET

    ctypedef enum SDL_RendererFlags:
        SDL_RENDERER_SOFTWARE = 0x00000001
        SDL_RENDERER_ACCELERATED = 0x00000002
        SDL_RENDERER_PRESENTVSYNC = 0x00000004

    ctypedef enum SDL_bool:
        SDL_FALSE = 0
        SDL_TRUE = 1

    cdef struct SDL_version:
        Uint8 major
        Uint8 minor
        Uint8 patch

    cdef struct SDL_Rect:
        int x, y
        int w, h

    ctypedef struct SDL_Point:
        int x, y

    cdef struct SDL_Color:
        Uint8 r
        Uint8 g
        Uint8 b
        Uint8 a

    cdef struct SDL_Palette:
        int ncolors
        SDL_Color *colors
        Uint32 version
        int refcount

    cdef struct SDL_PixelFormat:
        Uint32 format
        SDL_Palette *palette
        Uint8 BitsPerPixel
        Uint8 BytesPerPixel
        Uint8 padding[2]
        Uint32 Rmask
        Uint32 Gmask
        Uint32 Bmask
        Uint32 Amask
        Uint8 Rloss
        Uint8 Gloss
        Uint8 Bloss
        Uint8 Aloss
        Uint8 Rshift
        Uint8 Gshift
        Uint8 Bshift
        Uint8 Ashift
        int refcount
        SDL_PixelFormat *next


    cdef struct SDL_BlitMap

    cdef struct SDL_Cursor

    cdef struct SDL_Surface:
        Uint32 flags
        SDL_PixelFormat *format
        int w, h
        int pitch
        void *pixels
        void *userdata
        int locked
        void *lock_data
        SDL_Rect clip_rect
        SDL_BlitMap *map
        int refcount


    ctypedef enum SDL_EventType:
        SDL_FIRSTEVENT     = 0,
        SDL_DROPFILE       = 0x1000,
        SDL_QUIT           = 0x100
        SDL_WINDOWEVENT    = 0x200
        SDL_SYSWMEVENT
        SDL_KEYDOWN        = 0x300
        SDL_KEYUP
        SDL_TEXTEDITING
        SDL_TEXTINPUT
        SDL_MOUSEMOTION     = 0x400
        SDL_MOUSEBUTTONDOWN = 0x401
        SDL_MOUSEBUTTONUP   = 0x402
        SDL_MOUSEWHEEL      = 0x403
        SDL_INPUTMOTION     = 0x500
        SDL_INPUTBUTTONDOWN
        SDL_INPUTBUTTONUP
        SDL_INPUTWHEEL
        SDL_INPUTPROXIMITYIN
        SDL_INPUTPROXIMITYOUT
        SDL_JOYAXISMOTION  = 0x600
        SDL_JOYBALLMOTION
        SDL_JOYHATMOTION
        SDL_JOYBUTTONDOWN
        SDL_JOYBUTTONUP
        SDL_FINGERDOWN      = 0x700
        SDL_FINGERUP
        SDL_FINGERMOTION
        SDL_TOUCHBUTTONDOWN
        SDL_TOUCHBUTTONUP
        SDL_DOLLARGESTURE   = 0x800
        SDL_DOLLARRECORD
        SDL_MULTIGESTURE
        SDL_CLIPBOARDUPDATE = 0x900
        SDL_EVENT_COMPAT1 = 0x7000
        SDL_EVENT_COMPAT2
        SDL_EVENT_COMPAT3
        SDL_USEREVENT    = 0x8000
        SDL_LASTEVENT    = 0xFFFF
        SDL_APP_TERMINATING
        SDL_APP_LOWMEMORY
        SDL_APP_WILLENTERBACKGROUND
        SDL_APP_DIDENTERBACKGROUND
        SDL_APP_WILLENTERFOREGROUND
        SDL_APP_DIDENTERFOREGROUND

    ctypedef enum SDL_WindowEventID:
        SDL_WINDOWEVENT_NONE           #< Never used */
        SDL_WINDOWEVENT_SHOWN          #< Window has been shown */
        SDL_WINDOWEVENT_HIDDEN         #< Window has been hidden */
        SDL_WINDOWEVENT_EXPOSED        #< Window has been exposed and should be
                                        #     redrawn */
        SDL_WINDOWEVENT_MOVED          #< Window has been moved to data1, data2
                                        # */
        SDL_WINDOWEVENT_RESIZED        #< Window has been resized to data1xdata2 */
        SDL_WINDOWEVENT_SIZE_CHANGED   #< The window size has changed, either as a result of an API call or through the system or user changing the window size. */
        SDL_WINDOWEVENT_MINIMIZED      #< Window has been minimized */
        SDL_WINDOWEVENT_MAXIMIZED      #< Window has been maximized */
        SDL_WINDOWEVENT_RESTORED       #< Window has been restored to normal size
                                        # and position */
        SDL_WINDOWEVENT_ENTER          #< Window has gained mouse focus */
        SDL_WINDOWEVENT_LEAVE          #< Window has lost mouse focus */
        SDL_WINDOWEVENT_FOCUS_GAINED   #< Window has gained keyboard focus */
        SDL_WINDOWEVENT_FOCUS_LOST     #< Window has lost keyboard focus */
        SDL_WINDOWEVENT_CLOSE           #< The window manager requests that the
                                        # window be closed */

    ctypedef enum SDL_HintPriority:
        SDL_HINT_DEFAULT
        SDL_HINT_NORMAL
        SDL_HINT_OVERRIDE

    ctypedef enum SDL_RendererFlip:
        SDL_FLIP_NONE = 0x00000000
        SDL_FLIP_HORIZONTAL = 0x00000001
        SDL_FLIP_VERTICAL = 0x00000002

    ctypedef enum SDL_WindowFlags:
        SDL_WINDOW_FULLSCREEN = 0x00000001      #,         /**< fullscreen window */
        SDL_WINDOW_OPENGL = 0x00000002          #,             /**< window usable with OpenGL context */
        SDL_WINDOW_SHOWN = 0x00000004           #,              /**< window is visible */
        SDL_WINDOW_HIDDEN = 0x00000008          #,             /**< window is not visible */
        SDL_WINDOW_BORDERLESS = 0x00000010      #,         /**< no window decoration */
        SDL_WINDOW_RESIZABLE = 0x00000020       #,          /**< window can be resized */
        SDL_WINDOW_MINIMIZED = 0x00000040       #,          /**< window is minimized */
        SDL_WINDOW_MAXIMIZED = 0x00000080       #,          /**< window is maximized */
        SDL_WINDOW_INPUT_GRABBED = 0x00000100   #,      /**< window has grabbed input focus */
        SDL_WINDOW_INPUT_FOCUS = 0x00000200     #,        /**< window has input focus */
        SDL_WINDOW_MOUSE_FOCUS = 0x00000400     #,        /**< window has mouse focus */
        SDL_WINDOW_FOREIGN = 0x00000800         #            /**< window not created by SDL */
        SDL_WINDOW_FULLSCREEN_DESKTOP
        SDL_WINDOW_ALLOW_HIGHDPI

    cdef struct SDL_DropEvent:
        Uint32 type
        Uint32 timestamp
        char* file

    cdef struct SDL_MouseMotionEvent:
        Uint32 type
        Uint32 timestamp
        Uint32 windowID
        Uint32 which
        Uint32 state
        Sint32 x
        Sint32 y
        Sint32 xrel
        Sint32 yrel

    cdef struct SDL_MouseButtonEvent:
        Uint32 type
        Uint32 timestamp
        Uint32 windowID
        Uint32 which
        Uint8 button
        Uint8 state
        Uint8 clicks
        Sint32 x
        Sint32 y

    cdef struct SDL_WindowEvent:
        Uint32 type
        Uint32 timestamp
        Uint32 windowID
        Uint8 event
        Sint32 data1
        Sint32 data2

    ctypedef Sint64 SDL_TouchID
    ctypedef Sint64 SDL_FingerID

    cdef struct SDL_TouchFingerEvent:
        Uint32 type
        Uint32 windowID
        SDL_TouchID touchId
        SDL_FingerID fingerId
        float x
        float y
        float dx
        float dy
        float pressure

    cdef struct SDL_Keysym:
        SDL_Scancode scancode       # SDL physical key code - see ::SDL_Scancode for details */
        SDL_Keycode sym             # SDL virtual key code - see ::SDL_Keycode for details */
        Uint16 mod                  # current key modifiers */
        Uint32 unused

    cdef struct SDL_KeyboardEvent:
        Uint32 type         # ::SDL_KEYDOWN or ::SDL_KEYUP
        Uint32 timestamp
        Uint32 windowID     # The window with keyboard focus, if any
        Uint8 state         # ::SDL_PRESSED or ::SDL_RELEASED
        Uint8 repeat        # Non-zero if this is a key repeat
        SDL_Keysym keysym   # The key that was pressed or released

    cdef struct SDL_TextEditingEvent:
        Uint32 type                                 # ::SDL_TEXTEDITING */
        Uint32 timestamp
        Uint32 windowID                             # The window with keyboard focus, if any */
        char *text                                  # The editing text */
        Sint32 start                                # The start cursor of selected editing text */
        Sint32 length                               # The length of selected editing text */

    cdef struct SDL_TextInputEvent:
        Uint32 type                               # ::SDL_TEXTINPUT */
        Uint32 timestamp
        Uint32 windowID                           # The window with keyboard focus, if any */
        char *text                                # The input text */

    cdef struct SDL_MouseWheelEvent:
        Uint32 type
        Uint32 windowID
        int x
        int y
    cdef struct SDL_JoyAxisEvent:
        Uint32 type
        Uint32 timestamp
        SDL_JoystickID which
        Uint8 axis
        Sint16 value
    cdef struct SDL_JoyBallEvent:
        Uint32 type
        Uint32 timestamp
        SDL_JoystickID which
        Uint8 ball
        Sint16  xrel
        Sint16  yrel
    cdef struct SDL_JoyHatEvent:
        Uint32 type
        Uint32 timestamp
        SDL_JoystickID which
        Uint8 hat
        Uint8 value
    cdef struct SDL_JoyButtonEvent:
        Uint32 type
        Uint32 timestamp
        SDL_JoystickID which
        Uint8 button
        Uint8 state
    cdef struct SDL_QuitEvent:
        pass
    cdef struct SDL_UserEvent:
        Uint32 type
        Uint32 timestamp
        Uint32 windowID
        int code
        void *data1
        void *data2

    cdef struct SDL_SysWMEvent:
        pass
    cdef struct SDL_TouchButtonEvent:
        pass
    cdef struct SDL_MultiGestureEvent:
        pass
    cdef struct SDL_DollarGestureEvent:
        pass

    cdef union SDL_Event:
        Uint32 type
        SDL_WindowEvent window
        SDL_KeyboardEvent key
        SDL_TextEditingEvent edit
        SDL_TextInputEvent text
        SDL_MouseMotionEvent motion
        SDL_MouseButtonEvent button
        SDL_DropEvent drop
        SDL_MouseWheelEvent wheel
        SDL_JoyAxisEvent jaxis
        SDL_JoyBallEvent jball
        SDL_JoyHatEvent jhat
        SDL_JoyButtonEvent jbutton
        SDL_QuitEvent quit
        SDL_UserEvent user
        SDL_SysWMEvent syswm
        SDL_TouchFingerEvent tfinger
        SDL_TouchButtonEvent tbutton
        SDL_MultiGestureEvent mgesture
        SDL_DollarGestureEvent dgesture

    cdef struct SDL_RendererInfo:
        char *name
        Uint32 flags
        Uint32 num_texture_formats
        Uint32 texture_formats[16]
        int max_texture_width
        int max_texture_height

    ctypedef struct SDL_Texture
    ctypedef struct SDL_Renderer
    ctypedef struct SDL_Window
    ctypedef struct SDL_DisplayMode:
        Uint32 format
        int w
        int h
        int refresh_rate
        void *driverdata

    cdef struct SDL_RWops_union_unknown:
        void *data1

    cdef union SDL_RWops_union:
        SDL_RWops_union_unknown unknown

    cdef struct SDL_RWops:
        Sint64 (* seek) (SDL_RWops * context, Sint64 offset,int whence)
        size_t(* read) ( SDL_RWops * context, void *ptr, size_t size, size_t maxnum)
        size_t(* write) (SDL_RWops * context, void *ptr,size_t size, size_t num)
        int (* close) (SDL_RWops * context)
        int type
        SDL_RWops_union hidden

    cdef enum SDL_Keymod:
        KMOD_NONE
        KMOD_LSHIFT
        KMOD_RSHIFT
        KMOD_LCTRL
        KMOD_RCTRL
        KMOD_LALT
        KMOD_RALT
        KMOD_LGUI
        KMOD_RGUI
        KMOD_NUM
        KMOD_CAPS
        KMOD_MODE
        KMOD_RESERVED

    ctypedef enum SDL_Scancode:
        pass

    ctypedef int SDL_EventFilter(void* userdata, SDL_Event* event)

    cdef char *SDL_HINT_ORIENTATIONS
    cdef char *SDL_HINT_VIDEO_WIN_D3DCOMPILER
    cdef char *SDL_HINT_ACCELEROMETER_AS_JOYSTICK
    cdef char *SDL_HINT_ANDROID_TRAP_BACK_BUTTON

    cdef int SDL_QUERY               = -1
    cdef int SDL_IGNORE              =  0
    cdef int SDL_DISABLE             =  0
    cdef int SDL_ENABLE              =  1
    cdef int SDL_INIT_TIMER          = 0x00000001
    cdef int SDL_INIT_AUDIO          = 0x00000010
    cdef int SDL_INIT_VIDEO          = 0x00000020  # SDL_INIT_VIDEO implies SDL_INIT_EVENTS */
    cdef int SDL_INIT_JOYSTICK       = 0x00000200  # SDL_INIT_JOYSTICK implies SDL_INIT_EVENTS */
    cdef int SDL_INIT_HAPTIC         = 0x00001000
    cdef int SDL_INIT_GAMECONTROLLER = 0x00002000  # SDL_INIT_GAMECONTROLLER implies SDL_INIT_JOYSTICK */
    cdef int SDL_INIT_EVENTS         = 0x00004000
    cdef int SDL_INIT_NOPARACHUTE    = 0x00100000  # Don't catch fatal signals */

    cdef void SDL_GetVersion(SDL_version * ver)
    cdef SDL_Renderer * SDL_CreateRenderer(SDL_Window * window, int index, Uint32 flags)
    cdef void SDL_DestroyRenderer (SDL_Renderer * renderer)
    cdef SDL_Texture * SDL_CreateTexture(SDL_Renderer * renderer, Uint32 format, int access, int w, int h)
    cdef SDL_Texture * SDL_CreateTextureFromSurface(SDL_Renderer * renderer, SDL_Surface * surface)
    cdef SDL_Surface * SDL_CreateRGBSurface(Uint32 flags, int width, int height, int depth, Uint32 Rmask, Uint32 Gmask, Uint32 Bmask, Uint32 Amask) nogil
    cdef int SDL_RenderCopy(SDL_Renderer * renderer, SDL_Texture * texture, SDL_Rect * srcrect, SDL_Rect * dstrect)
    cdef int SDL_RenderCopyEx(SDL_Renderer * renderer, SDL_Texture * texture, SDL_Rect * srcrect, SDL_Rect * dstrect, double angle, SDL_Point *center, SDL_RendererFlip flip)
    cdef void SDL_RenderPresent(SDL_Renderer * renderer)
    cdef SDL_bool SDL_RenderTargetSupported(SDL_Renderer *renderer)
    cdef int SDL_SetRenderTarget(SDL_Renderer *renderer, SDL_Texture *texture)
    cdef void SDL_DestroyTexture(SDL_Texture * texture)
    cdef void SDL_FreeSurface(SDL_Surface * surface) nogil
    cdef int SDL_SetSurfaceBlendMode(SDL_Surface * surface, int blendMode)
    cdef int SDL_SetSurfaceAlphaMod(SDL_Surface * surface, char alpha)
    cdef int SDL_UpperBlit (SDL_Surface * src, SDL_Rect * srcrect, SDL_Surface * dst, SDL_Rect * dstrect)
    cdef int SDL_BlitSurface(SDL_Surface * src, SDL_Rect * srcrect, SDL_Surface * dst, SDL_Rect * dstrect)
    cdef int SDL_LockTexture(SDL_Texture * texture, SDL_Rect * rect, void **pixels, int *pitch)
    cdef void SDL_UnlockTexture(SDL_Texture * texture)
    cdef void SDL_GetWindowSize(SDL_Window * window, int *w, int *h)
    cdef Uint32 SDL_GetWindowFlags(SDL_Window * window)
    cdef SDL_Window * SDL_CreateWindow(char *title, int x, int y, int w, int h, Uint32 flags)
    cdef void SDL_DestroyWindow (SDL_Window * window)
    cdef int SDL_SetRenderDrawColor(SDL_Renderer * renderer, Uint8 r, Uint8 g, Uint8 b, Uint8 a)
    cdef int SDL_RenderClear(SDL_Renderer * renderer)
    cdef int SDL_SetTextureBlendMode(SDL_Texture * texture, SDL_BlendMode blendMode)
    cdef int SDL_GetTextureBlendMode(SDL_Texture * texture, SDL_BlendMode *blendMode)
    cdef SDL_Surface * SDL_CreateRGBSurfaceFrom(void *pixels, int width, int height, int depth, int pitch, Uint32 Rmask, Uint32 Gmask, Uint32 Bmask, Uint32 Amask)
    cdef SDL_Surface* SDL_ConvertSurfaceFormat(SDL_Surface* src, Uint32 pixel_format, Uint32 flags) nogil
    cdef const char* SDL_GetPixelFormatName(Uint32 format)
    cdef int SDL_GetColorKey(SDL_Surface *surface, Uint32 *key)
    cdef int SDL_Init(Uint32 flags)
    cdef void SDL_Quit()
    cdef int SDL_EnableUNICODE(int enable)
    cdef Uint32 SDL_GetTicks()
    cdef void SDL_Delay(Uint32 ms) nogil
    cdef Uint8 SDL_EventState(Uint32 type, int state)
    cdef int SDL_PollEvent(SDL_Event * event) nogil
    cdef void SDL_SetEventFilter(SDL_EventFilter *filter, void* userdata)
    cdef SDL_RWops * SDL_RWFromFile(char *file, char *mode)
    cdef SDL_RWops * SDL_RWFromMem(void *mem, int size)
    cdef SDL_RWops * SDL_RWFromConstMem(void *mem, int size)
    cdef SDL_RWops * SDL_AllocRW()
    cdef void SDL_FreeRW(SDL_RWops *area)
    cdef int SDL_GetRendererInfo(SDL_Renderer *renderer, SDL_RendererInfo *info)
    cdef int SDL_RenderSetViewport(SDL_Renderer * renderer, SDL_Rect * rect)
    cdef int SDL_GetCurrentDisplayMode(int displayIndex, SDL_DisplayMode * mode)
    cdef int SDL_GetDesktopDisplayMode(int displayIndex, SDL_DisplayMode * mode)
    cdef int SDL_SetTextureColorMod(SDL_Texture * texture, Uint8 r, Uint8 g, Uint8 b)
    cdef int SDL_SetTextureAlphaMod(SDL_Texture * texture, Uint8 alpha)
    cdef char * SDL_GetError()
    cdef SDL_bool SDL_SetHint(char *name, char *value)
    cdef SDL_bool SDL_SetHintWithPriority(char *name, char *value, SDL_HintPriority priority)
    cdef Uint8 SDL_GetMouseState(int* x,int* y)
    cdef SDL_GLContext SDL_GL_CreateContext(SDL_Window* window)
    cdef int SDL_GetNumVideoDisplays()
    cdef int SDL_GetNumDisplayModes(int displayIndex)
    cdef int SDL_GetDisplayMode(int displayIndex, int index, SDL_DisplayMode * mode)
    cdef SDL_bool SDL_HasIntersection(SDL_Rect * A, SDL_Rect * B) nogil
    cdef SDL_bool SDL_IntersectRect(SDL_Rect * A, SDL_Rect * B, SDL_Rect * result) nogil
    cdef void SDL_UnionRect(SDL_Rect * A, SDL_Rect * B, SDL_Rect * result) nogil
    cdef Uint64 SDL_GetPerformanceCounter() nogil
    cdef Uint64 SDL_GetPerformanceFrequency() nogil
    cdef int SDL_GL_SetAttribute(SDL_GLattr attr, int value)
    cdef int SDL_GetNumRenderDrivers()
    cdef int SDL_GetRenderDriverInfo(int index, SDL_RendererInfo* info)
    cdef int SDL_GL_BindTexture(SDL_Texture *texture, float *texw, float *texh)
    cdef int SDL_GL_UnbindTexture(SDL_Texture *texture)
    cdef int SDL_RenderReadPixels(SDL_Renderer * renderer, SDL_Rect * rect, Uint32 format, void *pixels, int pitch) nogil
    cdef int SDL_PushEvent(SDL_Event * event) nogil
    cdef int SDL_WaitEvent(SDL_Event * event) nogil

    cdef void SDL_SetClipboardText(char * text)
    cdef const char * SDL_GetClipboardText()
    cdef SDL_bool SDL_HasClipboardText()
    cdef int SDL_GetNumVideoDrivers()
    cdef const char *SDL_GetVideoDriver(int index)
    cdef int SDL_VideoInit(const char *driver_name)
    cdef void SDL_VideoQuit()
    cdef const char *SDL_GetCurrentVideoDriver()
    cdef int SDL_GetNumVideoDisplays()
    cdef const char * SDL_GetDisplayName(int displayIndex)
    cdef int SDL_GetDisplayBounds(int displayIndex, SDL_Rect * rect)
    cdef int SDL_GetNumDisplayModes(int displayIndex)
    cdef int SDL_GetDesktopDisplayMode(int displayIndex, SDL_DisplayMode * mode)
    cdef int SDL_GetCurrentDisplayMode(int displayIndex, SDL_DisplayMode * mode)
    cdef SDL_DisplayMode * SDL_GetClosestDisplayMode(int displayIndex, const SDL_DisplayMode * mode, SDL_DisplayMode * closest)
    cdef int SDL_SetWindowDisplayMode(SDL_Window * window, SDL_DisplayMode * mode)
    cdef int SDL_GetWindowDisplayMode(SDL_Window * window, SDL_DisplayMode * mode)
    cdef int SDL_GetWindowDisplayIndex(SDL_Window * window)
    cdef Uint32 SDL_GetWindowPixelFormat(SDL_Window * window)
    cdef SDL_Window * SDL_CreateWindowFrom(const void *data)
    cdef Uint32 SDL_GetWindowID(SDL_Window * window)
    cdef SDL_Window * SDL_GetWindowFromID(Uint32 id)
    cdef Uint32 SDL_GetWindowFlags(SDL_Window * window)
    cdef void SDL_SetWindowTitle(SDL_Window * window, char *title)
    cdef const char *SDL_GetWindowTitle(SDL_Window * window)
    cdef void SDL_SetWindowIcon(SDL_Window * window, SDL_Surface *icon)
    cdef void* SDL_SetWindowData(SDL_Window * window, char *name, void *data)
    cdef void *SDL_GetWindowData(SDL_Window * window, char *name)
    cdef void SDL_SetWindowPosition(SDL_Window * window, int x, int y)
    cdef void SDL_GetWindowPosition(SDL_Window * window, int *x, int *y)
    cdef void SDL_SetWindowSize(SDL_Window * window, int w, int h)
    cdef void SDL_GetWindowSize(SDL_Window * window, int *w, int *h)
    cdef void SDL_SetWindowMinimumSize(SDL_Window * window, int min_w, int min_h)
    cdef void SDL_SetWindowBordered(SDL_Window * window, SDL_bool bordered)
    cdef void SDL_ShowWindow(SDL_Window * window)
    cdef int SDL_ShowCursor(int toggle)
    cdef void SDL_SetCursor(SDL_Cursor * cursor)
    cdef SDL_Cursor* SDL_CreateSystemCursor(SDL_SystemCursor id)
    cdef void SDL_HideWindow(SDL_Window * window)
    cdef void SDL_RaiseWindow(SDL_Window * window)
    cdef void SDL_MaximizeWindow(SDL_Window * window)
    cdef void SDL_MinimizeWindow(SDL_Window * window)
    cdef void SDL_RestoreWindow(SDL_Window * window)
    cdef int SDL_SetWindowFullscreen(SDL_Window * window, SDL_bool fullscreen)
    cdef SDL_Surface * SDL_GetWindowSurface(SDL_Window * window)
    cdef int SDL_UpdateWindowSurface(SDL_Window * window)
    cdef void SDL_SetWindowGrab(SDL_Window * window, SDL_bool grabbed)
    cdef SDL_bool SDL_GetWindowGrab(SDL_Window * window)
    cdef int SDL_SetWindowBrightness(SDL_Window * window, float brightness)
    cdef float SDL_GetWindowBrightness(SDL_Window * window)
    cdef void SDL_DestroyWindow(SDL_Window * window)
    cdef SDL_bool SDL_IsScreenSaverEnabled()
    cdef void SDL_EnableScreenSaver()
    cdef void SDL_DisableScreenSaver()
    cdef int SDL_GL_LoadLibrary(const char *path)
    cdef void *SDL_GL_GetProcAddress(const char *proc)
    cdef void SDL_GL_UnloadLibrary()
    cdef int SDL_GL_SetAttribute(SDL_GLattr attr, int value)
    cdef int SDL_GL_GetAttribute(SDL_GLattr attr, int *value)
    cdef int SDL_GL_MakeCurrent(SDL_Window * window, SDL_GLContext context)
    cdef SDL_Window* SDL_GL_GetCurrentWindow()
    cdef SDL_GLContext SDL_GL_GetCurrentContext()
    cdef int SDL_GL_SetSwapInterval(int interval)
    cdef int SDL_GL_GetSwapInterval()
    cdef void SDL_GL_SwapWindow(SDL_Window * window) nogil
    cdef void SDL_GL_DeleteContext(SDL_GLContext context)

    cdef int SDL_NumJoysticks()
    cdef SDL_Joystick * SDL_JoystickOpen(int index)
    cdef SDL_Window * SDL_GetKeyboardFocus()
    cdef Uint8 *SDL_GetKeyboardState(int *numkeys)
    cdef SDL_Keymod SDL_GetModState()
    cdef void SDL_SetModState(SDL_Keymod modstate)
    cdef SDL_Keycode SDL_GetKeyFromScancode(SDL_Scancode scancode)
    cdef SDL_Scancode SDL_GetScancodeFromKey(SDL_Keycode key)
    cdef char *SDL_GetScancodeName(SDL_Scancode scancode)
    cdef SDL_Scancode SDL_GetScancodeFromName(char *name)
    cdef char *SDL_GetKeyName(SDL_Keycode key)
    cdef SDL_Keycode SDL_GetKeyFromName(char *name)
    cdef void SDL_StartTextInput()
    cdef SDL_bool SDL_IsTextInputActive()
    cdef void SDL_StopTextInput()
    cdef void SDL_SetTextInputRect(SDL_Rect *rect)
    cdef SDL_bool SDL_HasScreenKeyboardSupport()
    cdef SDL_bool SDL_IsScreenKeyboardShown(SDL_Window *window)
    cdef void SDL_GL_GetDrawableSize(SDL_Window *window, int *w, int *h)

    # Sound audio formats
    Uint16 AUDIO_U8     #0x0008  /**< Unsigned 8-bit samples */
    Uint16 AUDIO_S8     #0x8008  /**< Signed 8-bit samples */
    Uint16 AUDIO_U16LSB #0x0010  /**< Unsigned 16-bit samples */
    Uint16 AUDIO_S16LSB #0x8010  /**< Signed 16-bit samples */
    Uint16 AUDIO_U16MSB #0x1010  /**< As above, but big-endian byte order */
    Uint16 AUDIO_S16MSB #0x9010  /**< As above, but big-endian byte order */
    Uint16 AUDIO_U16    #AUDIO_U16LSB
    Uint16 AUDIO_S16    #AUDIO_S16LSB
    Uint16 AUDIO_S32LSB #0x8020  /**< 32-bit Uint16eger samples */
    Uint16 AUDIO_S32MSB #0x9020  /**< As above, but big-endian byte order */
    Uint16 AUDIO_S32    #AUDIO_S32LSB
    Uint16 AUDIO_F32LSB #0x8120  /**< 32-bit floating point samples */
    Uint16 AUDIO_F32MSB #0x9120  /**< As above, but big-endian byte order */
    Uint16 AUDIO_F32    #AUDIO_F32LSB

    # Endianness
    Uint16 SDL_BYTEORDER
    Uint16 SDL_LIL_ENDIAN
    Uint16 SDL_BIG_ENDIAN

cdef extern from "SDL_shape.h":
    cdef SDL_Window * SDL_CreateShapedWindow(
        char *title,
        unsigned int x,
        unsigned int y,
        unsigned int w,
        unsigned int h,
        Uint32 flags
    )

    # properties, flags, etc
    ctypedef enum WindowShapeMode:
        ShapeModeDefault
        ShapeModeBinarizeAlpha
        ShapeModeReverseBinarizeAlpha
        ShapeModeColorKey
    ctypedef union SDL_WindowShapeParams:
        Uint8 binarizationCutoff
        SDL_Color colorKey
    ctypedef struct SDL_WindowShapeMode:
        WindowShapeMode mode
        SDL_WindowShapeParams parameters

    int SDL_NONSHAPEABLE_WINDOW
    int SDL_INVALID_SHAPE_ARGUMENT
    int SDL_WINDOW_LACKS_SHAPE

    # set & get
    cdef SDL_bool SDL_IsShapedWindow(SDL_Window * window)
    int SDL_SetWindowShape(
        SDL_Window * window,
        SDL_Surface * shape,
        SDL_WindowShapeMode * shape_mode
    )
    int SDL_GetShapedWindowMode(
        SDL_Window * window,
        SDL_WindowShapeMode * shape_mode
    )

cdef extern from "SDL_image.h":
    ctypedef enum IMG_InitFlags:
        IMG_INIT_JPG
        IMG_INIT_PNG
        IMG_INIT_TIF
        IMG_INIT_WEBP
    cdef int IMG_Init(IMG_InitFlags flags)
    cdef char *IMG_GetError()
    cdef SDL_Surface *IMG_Load(char *file)
    cdef SDL_Surface *IMG_Load_RW(SDL_RWops *src, int freesrc)
    cdef SDL_Surface *IMG_LoadTyped_RW(SDL_RWops *src, int freesrc, char *type)
    cdef int IMG_SavePNG(SDL_Surface *src, char *file)
    cdef int IMG_SavePNG_RW(SDL_Surface *surface, SDL_RWops *dst, int freedst)
    cdef int IMG_SaveJPG(SDL_Surface *surface, const char *file, int quality)
    cdef int IMG_SaveJPG_RW(SDL_Surface *surface, SDL_RWops *dst, int freedst, int quality)


cdef extern from "SDL_ttf.h":
    ctypedef struct TTF_Font
    cdef int TTF_Init()
    cdef TTF_Font *  TTF_OpenFont( char *file, int ptsize)
    cdef TTF_Font *  TTF_OpenFontIndex( char *file, int ptsize, long index)
    cdef TTF_Font *  TTF_OpenFontRW(SDL_RWops *src, int freesrc, int ptsize)
    cdef TTF_Font *  TTF_OpenFontIndexRW(SDL_RWops *src, int freesrc, int ptsize, long index)
    #Set and retrieve the font style
    ##define TTF_STYLE_NORMAL    0x00
    ##define TTF_STYLE_BOLD      0x01
    ##define TTF_STYLE_ITALIC    0x02
    ##define TTF_STYLE_UNDERLINE 0x04
    ##define TTF_STYLE_STRIKETHROUGH 0x08
    cdef int TTF_STYLE_NORMAL
    cdef int TTF_STYLE_BOLD
    cdef int TTF_STYLE_ITALIC
    cdef int TTF_STYLE_UNDERLINE
    cdef int TTF_STYLE_STRIKETHROUGH
    cdef int  TTF_GetFontStyle( TTF_Font *font)
    cdef void  TTF_SetFontStyle(TTF_Font *font, int style)
    cdef int  TTF_GetFontOutline( TTF_Font *font)
    cdef void  TTF_SetFontOutline(TTF_Font *font, int outline)

    #Set and retrieve FreeType hinter settings */
    ##define TTF_HINTING_NORMAL    0
    ##define TTF_HINTING_LIGHT     1
    ##define TTF_HINTING_MONO      2
    ##define TTF_HINTING_NONE      3
    cdef int TTF_HINTING_NORMAL
    cdef int TTF_HINTING_LIGHT
    cdef int TTF_HINTING_MONO
    cdef int TTF_HINTING_NONE
    cdef int  TTF_GetFontHinting( TTF_Font *font)
    cdef void  TTF_SetFontHinting(TTF_Font *font, int hinting)

    #Get the total height of the font - usually equal to point size
    cdef int  TTF_FontHeight( TTF_Font *font)

    ## Get the offset from the baseline to the top of the font
    #This is a positive value, relative to the baseline.
    #*/
    cdef int  TTF_FontAscent( TTF_Font *font)

    ## Get the offset from the baseline to the bottom of the font
    #   This is a negative value, relative to the baseline.
    # */
    cdef int  TTF_FontDescent( TTF_Font *font)

    ## Get the recommended spacing between lines of text for this font */
    cdef int  TTF_FontLineSkip( TTF_Font *font)

    ## Get/Set whether or not kerning is allowed for this font */
    cdef int  TTF_GetFontKerning( TTF_Font *font)
    cdef void  TTF_SetFontKerning(TTF_Font *font, int allowed)

    ## Get the number of faces of the font */
    cdef long  TTF_FontFaces( TTF_Font *font)

    ## Get the font face attributes, if any */
    cdef int  TTF_FontFaceIsFixedWidth( TTF_Font *font)
    cdef char *  TTF_FontFaceFamilyName( TTF_Font *font)
    cdef char *  TTF_FontFaceStyleName( TTF_Font *font)

    ## Check whether a glyph is provided by the font or not */
    cdef int  TTF_GlyphIsProvided( TTF_Font *font, Uint16 ch)

    ## Get the metrics (dimensions) of a glyph
    #   To understand what these metrics mean, here is a useful link:
    #    http://freetype.sourceforge.net/freetype2/docs/tutorial/step2.html
    # */
    cdef int  TTF_GlyphMetrics(TTF_Font *font, Uint16 ch,int *minx, int *maxx, int *miny, int *maxy, int *advance)

    ## Get the dimensions of a rendered string of text */
    cdef int  TTF_SizeText(TTF_Font *font,  char *text, int *w, int *h)
    cdef int  TTF_SizeUTF8(TTF_Font *font,  char *text, int *w, int *h)
    cdef int  TTF_SizeUNICODE(TTF_Font *font,  Uint16 *text, int *w, int *h)

    # Create an 8-bit palettized surface and render the given text at
    #   fast quality with the given font and color.  The 0 pixel is the
    #   colorkey, giving a transparent background, and the 1 pixel is set
    #   to the text color.
    #   This function returns the new surface, or NULL if there was an error.
    #*/
    cdef SDL_Surface *  TTF_RenderText_Solid(TTF_Font *font, char *text, SDL_Color fg)
    cdef SDL_Surface *  TTF_RenderUTF8_Solid(TTF_Font *font, char *text, SDL_Color fg)
    cdef SDL_Surface *  TTF_RenderUNICODE_Solid(TTF_Font *font, Uint16 *text, SDL_Color fg)

    # Create an 8-bit palettized surface and render the given glyph at
    #   fast quality with the given font and color.  The 0 pixel is the
    #   colorkey, giving a transparent background, and the 1 pixel is set
    #   to the text color.  The glyph is rendered without any padding or
    #   centering in the X direction, and aligned normally in the Y direction.
    #   This function returns the new surface, or NULL if there was an error.
    #*/
    cdef SDL_Surface *  TTF_RenderGlyph_Solid(TTF_Font *font, Uint16 ch, SDL_Color fg)

    # Create an 8-bit palettized surface and render the given text at
    #   high quality with the given font and colors.  The 0 pixel is background,
    #   while other pixels have varying degrees of the foreground color.
    #  This function returns the new surface, or NULL if there was an error.
    #*/
    cdef SDL_Surface *  TTF_RenderText_Shaded(TTF_Font *font, char *text, SDL_Color fg, SDL_Color bg)
    cdef SDL_Surface *  TTF_RenderUTF8_Shaded(TTF_Font *font, char *text, SDL_Color fg, SDL_Color bg)
    cdef SDL_Surface *  TTF_RenderUNICODE_Shaded(TTF_Font *font, Uint16 *text, SDL_Color fg, SDL_Color bg)

    # Create an 8-bit palettized surface and render the given glyph at
    #   high quality with the given font and colors.  The 0 pixel is background,
    #   while other pixels have varying degrees of the foreground color.
    #   The glyph is rendered without any padding or centering in the X
    #   direction, and aligned normally in the Y direction.
    #   This function returns the new surface, or NULL if there was an error.
    #
    cdef SDL_Surface *  TTF_RenderGlyph_Shaded(TTF_Font *font,
                    Uint16 ch, SDL_Color fg, SDL_Color bg)

    # Create a 32-bit ARGB surface and render the given text at high quality,
    #   using alpha blending to dither the font with the given color.
    #   This function returns the new surface, or NULL if there was an error.
    #*/
    cdef SDL_Surface *  TTF_RenderText_Blended(TTF_Font *font,
                     char *text, SDL_Color fg)
    cdef SDL_Surface *  TTF_RenderUTF8_Blended(TTF_Font *font,
                     char *text, SDL_Color fg)
    cdef SDL_Surface *  TTF_RenderUNICODE_Blended(TTF_Font *font,
                     Uint16 *text, SDL_Color fg)

    # Create a 32-bit ARGB surface and render the given glyph at high quality,
    #   using alpha blending to dither the font with the given color.
    #   The glyph is rendered without any padding or centering in the X
    #   direction, and aligned normally in the Y direction.
    #   This function returns the new surface, or NULL if there was an error.
    #*/
    cdef SDL_Surface *  TTF_RenderGlyph_Blended(TTF_Font *font,
                            Uint16 ch, SDL_Color fg)

    # For compatibility with previous versions, here are the old functions */
    ##define TTF_RenderText(font, text, fg, bg)  \
    #    TTF_RenderText_Shaded(font, text, fg, bg)
    ##define TTF_RenderUTF8(font, text, fg, bg)  \
    #    TTF_RenderUTF8_Shaded(font, text, fg, bg)
    ##define TTF_RenderUNICODE(font, text, fg, bg)   \
    #    TTF_RenderUNICODE_Shaded(font, text, fg, bg)

    # Close an opened font file */
    cdef void  TTF_CloseFont(TTF_Font *font)

    # De-initialize the TTF engine */
    cdef void  TTF_Quit()

    # Check if the TTF engine is initialized */
    cdef int  TTF_WasInit()

    # Get the kerning size of two glyphs */
    cdef int TTF_GetFontKerningSize(TTF_Font *font, int prev_index, int index)

cdef extern from "SDL_audio.h":
    cdef int AUDIO_S16SYS
    ctypedef struct SDL_AudioFilter:
        pass
    ctypedef struct SDL_AudioCVT:
        int needed
        int src_format
        int dst_format
        double rate_incr
        Uint8 *buf
        int len
        int len_cvt
        int len_mult
        double len_ratio
        SDL_AudioFilter filters[10]
        int filter_index
    cdef int SDL_BuildAudioCVT(
        SDL_AudioCVT *cvt,
        int src_format,
        Uint8 src_channels,
        int src_rate,
        int dst_format,
        Uint8 dst_channels,
        int dst_rate
    )
    cdef int SDL_ConvertAudio(SDL_AudioCVT *cvt)

cdef extern from "SDL_mixer.h":
    cdef struct Mix_Chunk:
        int allocated
        Uint8 *abuf
        Uint32 alen
        Uint8 volume
    ctypedef struct Mix_Music:
        pass
    ctypedef enum Mix_Fading:
        MIX_NO_FADING
        MIX_FADING_OUT
        MIX_FADING_IN
    ctypedef enum Mix_MusicType:
        MUS_NONE
        MUS_CMD
        MUS_WAV
        MUS_MOD
        MUS_MID
        MUS_OGG
        MUS_MP3
        MUS_MP3_MAD
        MUS_FLAC
        MUS_MODPLUG
    ctypedef enum MIX_InitFlags:
        MIX_INIT_FLAC        = 0x00000001
        MIX_INIT_MOD         = 0x00000002
        MIX_INIT_MODPLUG     = 0x00000004 # Removed in mixer 2.0.2
        MIX_INIT_MP3         = 0x00000008
        MIX_INIT_OGG         = 0x00000010
        MIX_INIT_MID         = 0x00000020 # Previously _FLUIDSYNTH

    cdef int MIX_MAX_VOLUME


    cdef int Mix_Init(int flags)
    cdef void Mix_Quit()
    cdef int Mix_OpenAudio(int frequency, Uint16 format, int channels, int chunksize)
    cdef  int  Mix_AllocateChannels(int numchans)
    cdef  int  Mix_QuerySpec(int *frequency,Uint16 *format,int *channels)
    cdef  Mix_Chunk *  Mix_LoadWAV_RW(SDL_RWops *src, int freesrc)
    cdef  Mix_Chunk *  Mix_LoadWAV(char *file)
    cdef  Mix_Music *  Mix_LoadMUS(char *file)
    cdef  Mix_Music *  Mix_LoadMUS_RW(SDL_RWops *rw)
    cdef  Mix_Music *  Mix_LoadMUSType_RW(SDL_RWops *rw, Mix_MusicType type, int freesrc)
    cdef  Mix_Chunk *  Mix_QuickLoad_WAV(Uint8 *mem)
    cdef  Mix_Chunk *  Mix_QuickLoad_RAW(Uint8 *mem, Uint32 len)
    cdef  void  Mix_FreeChunk(Mix_Chunk *chunk)
    cdef  void  Mix_FreeMusic(Mix_Music *music)
    cdef int  Mix_GetNumChunkDecoders()
    cdef  char *  Mix_GetChunkDecoder(int index)
    cdef int  Mix_GetNumMusicDecoders()
    cdef  char *  Mix_GetMusicDecoder(int index)
    cdef Mix_MusicType  Mix_GetMusicType( Mix_Music *music)
    cdef void  Mix_SetPostMix(void (*mix_func)(void *udata, Uint8 *stream, int len), void *arg)
    cdef void  Mix_HookMusic(void (*mix_func) (void *udata, Uint8 *stream, int len), void *arg)
    cdef void  Mix_HookMusicFinished(void (*music_finished)())
    cdef void *  Mix_GetMusicHookData()
    cdef void  Mix_ChannelFinished(void (*channel_finished)(int channel))
    #    typedef void (*Mix_EffectFunc_t)(int chan, void *stream, int len, void *udata)
    #    typedef void (*Mix_EffectDone_t)(int chan, void *udata)
    #    cdef int  Mix_RegisterEffect(int chan, Mix_EffectFunc_t f,
    #    cdef int  Mix_UnregisterEffect(int channel, Mix_EffectFunc_t f)
    cdef int  Mix_UnregisterAllEffects(int channel)
    cdef int Mix_SetPanning(int channel, Uint8 left, Uint8 right)
    cdef int  Mix_SetPosition(int channel, Sint16 angle, Uint8 distance)
    cdef int  Mix_SetDistance(int channel, Uint8 distance)
    cdef int  Mix_SetReverseStereo(int channel, int flip)
    cdef int  Mix_ReserveChannels(int num)
    cdef int  Mix_GroupChannel(int which, int tag)
    cdef int  Mix_GroupChannels(int _from, int to, int tag)
    cdef int  Mix_GroupAvailable(int tag)
    cdef int  Mix_GroupCount(int tag)
    cdef int  Mix_GroupOldest(int tag)
    cdef int  Mix_GroupNewer(int tag)
    cdef int  Mix_PlayChannel(int channel, Mix_Chunk *chunk, int loops)
    cdef int  Mix_PlayChannelTimed(int channel, Mix_Chunk *chunk, int loops, int ticks)
    cdef int  Mix_PlayMusic(Mix_Music *music, int loops)
    cdef int  Mix_FadeInMusic(Mix_Music *music, int loops, int ms)
    cdef int  Mix_FadeInMusicPos(Mix_Music *music, int loops, int ms, double position)
    cdef int  Mix_FadeInChannel(int channel, Mix_Chunk *chunk, int loops, int ms)
    cdef int  Mix_FadeInChannelTimed(int channel, Mix_Chunk *chunk, int loops, int ms, int ticks)
    cdef int  Mix_Volume(int channel, int volume)
    cdef int  Mix_VolumeChunk(Mix_Chunk *chunk, int volume)
    cdef int  Mix_VolumeMusic(int volume)
    cdef int  Mix_HaltChannel(int channel)
    cdef int  Mix_HaltGroup(int tag)
    cdef int  Mix_HaltMusic()
    cdef int  Mix_ExpireChannel(int channel, int ticks)
    cdef int  Mix_FadeOutChannel(int which, int ms)
    cdef int  Mix_FadeOutGroup(int tag, int ms)
    cdef int  Mix_FadeOutMusic(int ms)
    cdef Mix_Fading  Mix_FadingMusic()
    cdef Mix_Fading  Mix_FadingChannel(int which)
    cdef void  Mix_Pause(int channel)
    cdef void  Mix_Resume(int channel)
    cdef int  Mix_Paused(int channel)
    cdef void  Mix_PauseMusic()
    cdef void  Mix_ResumeMusic()
    cdef void  Mix_RewindMusic()
    cdef int  Mix_PausedMusic()
    cdef int  Mix_SetMusicPosition(double position)
    cdef int  Mix_Playing(int channel)
    cdef int  Mix_PlayingMusic()
    cdef int  Mix_SetMusicCMD( char *command)
    cdef int  Mix_SetSynchroValue(int value)
    cdef int  Mix_GetSynchroValue()
    cdef int  Mix_SetSoundFonts( char *paths)
    cdef  char*  Mix_GetSoundFonts()
    #cdef int  Mix_EachSoundFont(int (*function)( char*, void*), void *data)
    cdef Mix_Chunk *  Mix_GetChunk(int channel)
    cdef void  Mix_CloseAudio()
    cdef char * Mix_GetError()

include '../core/window/window_attrs.pxi'
cdef extern from "SDL_syswm.h":
    cdef enum SDL_SYSWM_TYPE:
        SDL_SYSWM_UNKNOWN
        SDL_SYSWM_WINDOWS
        SDL_SYSWM_X11
        SDL_SYSWM_DIRECTFB
        SDL_SYSWM_COCOA
        SDL_SYSWM_UIKIT
        SDL_SYSWM_WAYLAND
        SDL_SYSWM_MIR
        SDL_SYSWM_WINRT
        SDL_SYSWM_ANDROID
        SDL_SYSWM_VIVANTE
        SDL_SYSWM_OS2

    IF UNAME_SYSNAME == 'Windows':
        cdef struct _wm_info_win:
            HWND window
            HDC hdc
    ELSE:
        cdef struct _wm_info_win:
            int dummy

    IF USE_WAYLAND:
        cdef struct _wm_info_wl:
            wl_display *display
            wl_surface *surface
            wl_shell_surface *shell_surface
    ELSE:
        cdef struct _wm_info_wl:
            int dummy

    IF USE_X11:
        cdef struct _wm_info_x11:
            Display *display
            Window window
    ELSE:
       cdef struct _wm_info_x11:
           int dummy

    cdef union _wm_info:
        _wm_info_win win
        _wm_info_wl wl
        _wm_info_x11 x11

    cdef struct SDL_SysWMinfo:
        SDL_version version
        SDL_SYSWM_TYPE subsystem
        _wm_info info

    cdef SDL_bool SDL_GetWindowWMInfo(SDL_Window *window, SDL_SysWMinfo *info)
