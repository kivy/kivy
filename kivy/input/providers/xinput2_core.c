/*
 * xinput2_core.c - Connect to x and fetch touch events
 *
 * Heavily inspired from https://github.com/esjeon/xinput2-touch
 * => 2013 Eon S. Jeon <esjeon@live.com>
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <X11/Xlib.h>
#include <X11/extensions/XInput2.h>

#define TOUCH_DOWN 0
#define TOUCH_MOVE 1
#define TOUCH_UP 2

static Display *dpy;
static int xi_opcode;

// Cython API
typedef struct TouchStruct{
    int t_id;
    int state;
	float  x;
	float  y;
} TouchStruct;

typedef int (*touch_cb_type)(TouchStruct *touch);
touch_cb_type touch_cb = NULL;

void x11_set_touch_callback(touch_cb_type callback) {
	touch_cb = callback;
}


int init (int windowID){
	dpy = XOpenDisplay(NULL);

	int devid = 0;
	Window win = windowID;

	/* check XInput extension */
	{
		int ev;
		int err;

		if (!XQueryExtension(dpy, "XInputExtension", &xi_opcode, &ev, &err)) {
			printf("X Input extension not available.\n");
			return 1;
		}
	}

	/* check the version of XInput */
	{
		int rc;
		int major = 2;
		int minor = 3;

		rc = XIQueryVersion(dpy, &major, &minor);
		if (rc != Success)
		{
			printf("No XI2 support. (%d.%d only)\n", major, minor);
			exit(1);
		}
	}

	/* create window */
	{
		XMapWindow(dpy, win);
		XSync(dpy, False);
	}

	/* select device */
	{
		XIDeviceInfo *di;
		XIDeviceInfo *dev;
		XITouchClassInfo *class;
		int cnt;
		int i, j;

		di = XIQueryDevice(dpy, XIAllDevices, &cnt);
		for (i = 0; i < cnt; i ++)
		{
			dev = &di[i];
			for (j = 0; j < dev->num_classes; j ++)
			{
				class = (XITouchClassInfo*)(dev->classes[j]);
				if (class->type != XITouchClass)
				{
					devid = dev->deviceid;
					goto STOP_SEARCH_DEVICE;
				}
			}
		}
STOP_SEARCH_DEVICE:
		XIFreeDeviceInfo(di);
	}

	/* select events to listen */
	{
		XIEventMask mask = {
			.deviceid = devid, //XIAllDevices,
			.mask_len = XIMaskLen(XI_TouchEnd)
		};
		mask.mask = (unsigned char*)calloc(3, sizeof(char));
		XISetMask(mask.mask, XI_TouchBegin);
		XISetMask(mask.mask, XI_TouchUpdate);
		XISetMask(mask.mask, XI_TouchEnd);
        XISetMask(mask.mask, XI_Motion); // Only for testing without overlay

		XISelectEvents(dpy, win, &mask, 1);

		free(mask.mask);
	}
	XFlush(dpy);
	return 0;
}

int idle(void){
    TouchStruct touch;
	XEvent ev;
	XGenericEventCookie *cookie = &ev.xcookie; // hacks!
	XIDeviceEvent *devev;

	while (XPending(dpy)){
		XNextEvent(dpy, &ev);
		if (XGetEventData(dpy, cookie)) // extended event
		{
			// check if this belongs to XInput
			if(cookie->type == GenericEvent && cookie->extension == xi_opcode)
			{
				devev = cookie->data;
				switch(devev->evtype) {
				case XI_TouchBegin:
                    touch.t_id = devev->detail;
                    touch.state = TOUCH_DOWN;
                    touch.x = devev->event_x;
                    touch.y = devev->event_y;
                    touch_cb(&touch);
					break;
				case XI_TouchUpdate:
                    touch.t_id = devev->detail;
                    touch.state = TOUCH_MOVE;
                    touch.x = devev->event_x;
                    touch.y = devev->event_y;
                    touch_cb(&touch);
					break;
				case XI_TouchEnd:
                    touch.t_id = devev->detail;
                    touch.state = TOUCH_UP;
                    touch.x = devev->event_x;
                    touch.y = devev->event_y;
                    touch_cb(&touch);
					break;
				}
			}
		}
		else // normal event
		{
			if (ev.type == KeyPress)
				break;
		}
	}
	return 0;
}