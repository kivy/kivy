#include <glib.h>
#include <gst/gst.h>

static void g_object_set_void(GstElement *element, char *name, void *value)
{
	g_object_set(G_OBJECT(element), name, value, NULL);
}

static void g_object_set_double(GstElement *element, char *name, double value)
{
	g_object_set(G_OBJECT(element), name, value, NULL);
}

static void g_object_set_caps(GstElement *element, char *value)
{
	GstCaps *caps = gst_caps_from_string(value);
	g_object_set(G_OBJECT(element), "caps", caps, NULL);
}

static void g_object_set_int(GstElement *element, char *name, int value)
{
	g_object_set(G_OBJECT(element), name, value, NULL);
}

typedef void (*appcallback_t)(void *, int, int, char *, int);
typedef struct {
	appcallback_t callback;
	PyObject *userdata;
} appcallback_data_t;

static GstFlowReturn c_on_appsink_sample(GstElement *appsink, appcallback_data_t *data)
{
	GstSample *sample = NULL;
	GstBuffer *buffer = NULL;
	GstMapInfo mapinfo;
	GstCaps *caps = NULL;
	GstStructure *structure = NULL;
	gint width, height;

	g_signal_emit_by_name (appsink, "pull-sample", &sample);
	if ( sample == NULL ) {
		g_warning("Could not get sample");
		goto done;
	}

	caps = gst_sample_get_caps(sample);
	if ( caps == NULL ) {
		g_warning("Could not get snapshot format");
		goto done;
	}

	structure = gst_caps_get_structure(caps, 0);
	gst_structure_get_int(structure, "width", &width);
	gst_structure_get_int(structure, "height", &height);


	buffer = gst_sample_get_buffer(sample);

	if ( gst_buffer_map(buffer, &mapinfo, GST_MAP_READ) != TRUE ) {
		g_debug("Unable to map buffer");
		goto done;
	}

	data->callback(data->userdata, width, height, (char *)mapinfo.data, mapinfo.size);

	gst_buffer_unmap(buffer, &mapinfo);

done:
	//gst_caps_unref(caps);
	if ( sample != NULL )
		gst_sample_unref(sample);
	return GST_FLOW_OK;
}

static void c_appsink_free_data(gpointer data, GClosure *closure)
{
	appcallback_data_t *cdata = data;
	Py_DECREF(cdata->userdata);
	free(cdata);
}

static gulong c_appsink_set_sample_callback(GstElement *appsink, appcallback_t callback, PyObject *userdata)
{
	appcallback_data_t *data = (appcallback_data_t *)malloc(sizeof(appcallback_data_t));
	if ( data == NULL )
		return 0;
	data->callback = callback;
	data->userdata = userdata;

	Py_INCREF(data->userdata);

    g_object_set(G_OBJECT(appsink), "emit-signals", TRUE, NULL);

	return g_signal_connect_data(
			appsink, "new-sample",
			G_CALLBACK(c_on_appsink_sample), data,
			c_appsink_free_data, 0);
}

static void c_appsink_disconnect(GstElement *appsink, gulong handler_id)
{
	g_signal_handler_disconnect(appsink, handler_id);
}

