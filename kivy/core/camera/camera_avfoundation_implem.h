typedef void *camera_t;

camera_t avf_camera_init(int index, int width, int height);
void avf_camera_deinit(camera_t camera);
void avf_camera_update(camera_t camera);
void avf_camera_start(camera_t camera);
void avf_camera_stop(camera_t camera);
void avf_camera_get_image(camera_t camera, int *width, int *height, int *rowsize, char **data);
