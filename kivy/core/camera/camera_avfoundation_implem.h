typedef void *camera_t;

camera_t avf_camera_init(int index, int width, int height);
void avf_camera_deinit(camera_t camera);
bool avf_camera_update(camera_t camera);
void avf_camera_start(camera_t camera);
void avf_camera_stop(camera_t camera);
void avf_camera_get_image(camera_t camera, int *width, int *height, int *rowsize, char **data);
bool avf_camera_attempt_framerate_selection(camera_t camera, int fps);
bool avf_camera_attempt_capture_preset(camera_t camera, char* preset);
bool avf_camera_attempt_start_metadata_analysis(camera_t camera);
void avf_camera_get_metadata(camera_t camera, char **metatype, char **data);
bool avf_camera_have_new_metadata(camera_t camera);
bool avf_camera_set_video_orientation(camera_t camera, int orientation);
