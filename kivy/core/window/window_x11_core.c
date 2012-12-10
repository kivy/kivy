
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

#include <GL/gl.h>
#include <GL/glx.h>
#include <GL/glxext.h>
#include <X11/Xatom.h>
#include <X11/extensions/Xrender.h>
#include <X11/Xutil.h>
#include <X11/XKBlib.h>


typedef int (*event_cb_t)(XEvent *event);
event_cb_t g_event_callback = NULL;

static int Xscreen;
static Atom del_atom;
static Colormap cmap;
static Display *Xdisplay;
static XVisualInfo *visual;
static XRenderPictFormat *pict_format;
static GLXFBConfig *fbconfigs, fbconfig;
static int numfbconfigs;
static GLXContext render_context;
static Window Xroot, window_handle;
static GLXWindow glX_window_handle;
static int g_width, g_height;

static int VisData[] = {
	GLX_RENDER_TYPE, GLX_RGBA_BIT,
	GLX_DRAWABLE_TYPE, GLX_WINDOW_BIT,
	GLX_DOUBLEBUFFER, True,
	GLX_RED_SIZE, 8,
	GLX_GREEN_SIZE, 8,
	GLX_BLUE_SIZE, 8,
	GLX_ALPHA_SIZE, 8,
	GLX_DEPTH_SIZE, 16,
	None
};

static void fatalError(const char *why)
{
	fprintf(stderr, "%s", why);
	exit(0x666);
}

static Bool WaitForMapNotify(Display *d, XEvent *e, char *arg)
{
	return d && e && arg && (e->type == MapNotify) && (e->xmap.window == *(Window*)arg);
}

static void describe_fbconfig(GLXFBConfig fbconfig)
{
	int doublebuffer;
	int red_bits, green_bits, blue_bits, alpha_bits, depth_bits;

	glXGetFBConfigAttrib(Xdisplay, fbconfig, GLX_DOUBLEBUFFER, &doublebuffer);
	glXGetFBConfigAttrib(Xdisplay, fbconfig, GLX_RED_SIZE, &red_bits);
	glXGetFBConfigAttrib(Xdisplay, fbconfig, GLX_GREEN_SIZE, &green_bits);
	glXGetFBConfigAttrib(Xdisplay, fbconfig, GLX_BLUE_SIZE, &blue_bits);
	glXGetFBConfigAttrib(Xdisplay, fbconfig, GLX_ALPHA_SIZE, &alpha_bits);
	glXGetFBConfigAttrib(Xdisplay, fbconfig, GLX_DEPTH_SIZE, &depth_bits);

	fprintf(stderr, "FBConfig selected:\n"
			"Doublebuffer: %s\n"
			"Red Bits: %d, Green Bits: %d, Blue Bits: %d, Alpha Bits: %d, Depth Bits: %d\n",
			doublebuffer == True ? "Yes" : "No",
			red_bits, green_bits, blue_bits, alpha_bits, depth_bits);
}

static void createTheWindow(int width, int height, int x, int y, int resizable, int fullscreen, int border, char *title)
{
	XEvent event;
	int attr_mask;
	XSizeHints hints;
	XWMHints *startup_state;
	XTextProperty textprop;
	XSetWindowAttributes attr = {0,};

	Xdisplay = XOpenDisplay(NULL);
	if (!Xdisplay) {
		fatalError("Couldn't connect to X server\n");
	}
	Xscreen = DefaultScreen(Xdisplay);
	Xroot = RootWindow(Xdisplay, Xscreen);

	fbconfigs = glXChooseFBConfig(Xdisplay, Xscreen, VisData, &numfbconfigs);
	fbconfig = 0;
	int i;
	for(i = 0; i<numfbconfigs; i++) {
		visual = (XVisualInfo*) glXGetVisualFromFBConfig(Xdisplay, fbconfigs[i]);
		if(!visual)
			continue;

		pict_format = XRenderFindVisualFormat(Xdisplay, visual->visual);
		if(!pict_format)
			continue;

		fbconfig = fbconfigs[i];
		if(pict_format->direct.alphaMask > 0) {
			break;
		}
	}

	if(!fbconfig) {
		fatalError("No matching FB config found");
	}

	describe_fbconfig(fbconfig);

	/* Create a colormap - only needed on some X clients, eg. IRIX */
	cmap = XCreateColormap(Xdisplay, Xroot, visual->visual, AllocNone);

	attr.colormap = cmap;
	attr.background_pixmap = None;
	attr.border_pixmap = None;
	attr.border_pixel = 0;
	attr.override_redirect = True;

	attr.event_mask =
		StructureNotifyMask |
		EnterWindowMask |
		LeaveWindowMask |
		ExposureMask |
		ButtonPressMask |
		ButtonReleaseMask |
		OwnerGrabButtonMask |
		KeyPressMask |
		PointerMotionMask |
		KeyReleaseMask;

	attr_mask =
		CWBackPixmap|
		CWBorderPixel|
		CWColormap|
		CWEventMask;

	if ( fullscreen ) {
		if ( width == -1 ) {
			width = DisplayWidth(Xdisplay, DefaultScreen(Xdisplay));
			height = DisplayHeight(Xdisplay, DefaultScreen(Xdisplay));
		}
		border = 0;
	}

	if ( !border )
		attr_mask |= CWOverrideRedirect;

	window_handle = XCreateWindow(  Xdisplay,
			Xroot,
			x, y, width, height,
			0,
			visual->depth,
			InputOutput,
			visual->visual,
			attr_mask, &attr);

	g_width = width;
	g_height = height;

	if( !window_handle ) {
		fatalError("Couldn't create the window\n");
	}

#if USE_GLX_CREATE_WINDOW
	int glXattr[] = { None };
	glX_window_handle = glXCreateWindow(Xdisplay, fbconfig, window_handle, glXattr);
	if( !glX_window_handle ) {
		fatalError("Couldn't create the GLX window\n");
	}
#else
	glX_window_handle = window_handle;
#endif

	textprop.value = (unsigned char*)title;
	textprop.encoding = XA_STRING;
	textprop.format = 8;
	textprop.nitems = strlen(title);

	hints.x = x;
	hints.y = y;
	hints.width = width;
	hints.height = height;
	hints.flags = USPosition|USSize;

	startup_state = XAllocWMHints();
	startup_state->initial_state = NormalState;
	startup_state->flags = StateHint;

	XSetWMProperties(Xdisplay, window_handle,&textprop, &textprop,
			NULL, 0,
			&hints,
			startup_state,
			NULL);


	XFree(startup_state);

	XMapWindow(Xdisplay, window_handle);
	XIfEvent(Xdisplay, &event, WaitForMapNotify, (char*)&window_handle);

	if ((del_atom = XInternAtom(Xdisplay, "WM_DELETE_WINDOW", 0)) != None) {
		XSetWMProtocols(Xdisplay, window_handle, &del_atom, 1);
	}
}

static void createTheRenderContext()
{
	int dummy;
	if (!glXQueryExtension(Xdisplay, &dummy, &dummy)) {
		fatalError("OpenGL not supported by X server\n");
	}

	{
		render_context = glXCreateNewContext(Xdisplay, fbconfig, GLX_RGBA_TYPE, 0, True);
		if (!render_context) {
			fatalError("Failed to create a GL context\n");
		}
	}

	if (!glXMakeContextCurrent(Xdisplay, glX_window_handle, glX_window_handle, render_context)) {
		fatalError("glXMakeCurrent failed for window\n");
	}
}

static int updateTheMessageQueue()
{
	XEvent event;
	XConfigureEvent *xc;

	while (XPending(Xdisplay))
	{
		XNextEvent(Xdisplay, &event);

		switch (event.type)
		{
			case ClientMessage:
				if (event.xclient.data.l[0] == del_atom)
				{
					return 0;
				}
				break;

			default:
				if ( g_event_callback ) {
					if ( g_event_callback(&event) < 0 )
						return 0;
				}
				break;

			/**
			case ConfigureNotify:
				xc = &(event.xconfigure);
				g_width = xc->width;
				g_height = xc->height;
				break;
			 **/
		}
	}
	return 1;
}

//-----------------------------------------------------------------------------
//
// Minimal API to be used from cython
//

void x11_set_event_callback(event_cb_t callback) {
	g_event_callback = callback;
}

int x11_create_window(int width, int height, int x, int y,
		int resizable, int fullscreen, int border, char *title) {
	createTheWindow(width, height, x, y, resizable, fullscreen, border, title);
	createTheRenderContext();
	return 1;
}

void x11_gl_swap() {
	glXSwapBuffers(Xdisplay, glX_window_handle);
}

int x11_get_width() {
	return g_width;
}

int x11_get_height() {
	return g_height;
}

int x11_idle() {
	return updateTheMessageQueue();
}

#include "window_x11_keytab.c"

long x11_keycode_to_keysym(unsigned int keycode, int shiftDown) {
    KeySym keysym;
	long ucs;

    keysym = XkbKeycodeToKeysym(Xdisplay, keycode, 0, shiftDown);
	if ( keysym == NoSymbol )
		return 0;

	if ( keysym == XK_Escape )
		return 27;
	else if ( keysym == XK_Return )
		return 13;
	else if ( keysym == XK_BackSpace )
		return 8;
	else if ( keysym == XK_Delete )
		return 127;
	else if ( keysym == XK_Up )
		return 273;
	else if ( keysym == XK_Down )
		return 274;
	else if ( keysym == XK_Left )
		return 276;
	else if ( keysym == XK_Right )
		return 275;
	else if ( keysym == XK_space )
		return 32;
	else if ( keysym == XK_Home )
		return 278;
	else if ( keysym == XK_End )
		return 279;
	else if ( keysym == XK_Page_Up )
		return 280;
	else if ( keysym == XK_Page_Down )
		return 281;

	ucs = keysym2ucs(keysym);

	//printf("%d -> %d (ucs %ld)\n", keycode, keysym, ucs);

	return ucs;
}
