#include "_gstgl.h"

#define GST_USE_UNSTABLE_API
#include <gst/gl/gl.h>
#include <gst/gl/x11/gstgldisplay_x11.h>

#include <GL/glx.h>

#include "SDL2/SDL_syswm.h"
#include "SDL2/SDL.h"

gboolean context_created = FALSE;

static Display *x11_display;
static Window x11_window;
static GLXContext sdl_gl_context;

static GstGLDisplay *gst_gl_display;
static GstGLContext *gst_gl_context;

void gst_gl_init (SDL_Window *sdl_window) {
    if (!context_created) {
        SDL_SysWMinfo info;
        SDL_VERSION (&info.version);
        SDL_GetWindowWMInfo (sdl_window, &info);
        
        x11_display = info.info.x11.display;
        x11_window = info.info.x11.window;
        sdl_gl_context = glXGetCurrentContext();

        gst_gl_display = (GstGLDisplay *)gst_gl_display_x11_new_with_display (x11_display);
        
        glXMakeCurrent(x11_display, None, 0);
            
        gst_gl_context = gst_gl_context_new_wrapped (
            gst_gl_display, (guintptr) sdl_gl_context, gst_gl_platform_from_string ("glx"), GST_GL_API_OPENGL
        );
        
        glXMakeCurrent(x11_display, x11_window, sdl_gl_context);
        
        context_created = TRUE;
    }
}  

static gboolean gst_gl_bus_cb (GstBus *bus, GstMessage *msg, gpointer *data) {
    switch (GST_MESSAGE_TYPE (msg)) {
        case GST_MESSAGE_NEED_CONTEXT:
            {
                const gchar *context_type;

                gst_message_parse_context_type (msg, &context_type);

                if (g_strcmp0 (context_type, GST_GL_DISPLAY_CONTEXT_TYPE) == 0) {
                    GstContext *display_context = gst_context_new (GST_GL_DISPLAY_CONTEXT_TYPE, TRUE);
                    gst_context_set_gl_display (display_context, gst_gl_display);
                    gst_element_set_context (GST_ELEMENT (msg->src), display_context);
                    return TRUE;
                } else if (g_strcmp0 (context_type, "gst.gl.app_context") == 0) {
                    GstContext *app_context = gst_context_new ("gst.gl.app_context", TRUE);
                    GstStructure *s = gst_context_writable_structure (app_context);
                    gst_structure_set (s, "context", GST_GL_TYPE_CONTEXT, gst_gl_context, NULL);
                    gst_element_set_context (GST_ELEMENT (msg->src), app_context);
                    return TRUE;
                }
                break;
            }
        default:
          break;
        }
    return FALSE;
}

void gst_gl_set_bus_cb (GstBus *bus) {
    gst_bus_add_signal_watch (bus);
    g_signal_connect (bus, "sync-message", G_CALLBACK (gst_gl_bus_cb), NULL);
}

void gst_gl_stop_pipeline (GstPipeline *pipeline) {
    GST_OBJECT_LOCK(GST_OBJECT (gst_gl_display));
    glXMakeCurrent (x11_display, x11_window, sdl_gl_context);
    
    gst_element_set_state (GST_ELEMENT (pipeline), GST_STATE_NULL);
    
    glXMakeCurrent (x11_display, None, 0);
    GST_OBJECT_UNLOCK(GST_OBJECT (gst_gl_display));
}

unsigned int
get_texture_id_from_buffer (GstBuffer *buf)
{
  GstMapInfo mapinfo;
  unsigned int texture = 0;

  if (!gst_buffer_map (buf, &mapinfo, GST_MAP_READ | GST_MAP_GL)) {
    g_warning ("Failed to map the video buffer");
    return texture;
  }

  texture = (unsigned int) mapinfo.data[0];

  gst_buffer_unmap (buf, &mapinfo);

  return texture;
}
