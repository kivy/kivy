#include <gst/gst.h>

#include "SDL2/SDL.h"

void gst_gl_init (SDL_Window *window);
void gst_gl_set_bus_cb (GstBus *bus);
void gst_gl_stop_pipeline (GstPipeline *pipeline);

unsigned int get_texture_id_from_buffer (GstBuffer *buf);
