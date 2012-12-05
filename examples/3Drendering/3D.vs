#ifdef GL_ES
    precision highp float;
#endif

/* Outputs to the fragment shader */
varying vec3 normal_vec;
varying vec3 eye_vec;

/* vertex attributes */
attribute vec3     v_pos;
attribute vec3     v_normal;

/* uniform variables */
uniform mat4       modelview_mat;
uniform mat4       projection_mat;


void main (void) {
    // transform vertex to eye space and  it the fragment shader along
    // with the surface normal;
    vec4 position = modelview_mat * vec4(v_pos,1.0);
    eye_vec = position.xyz;
    normal_vec = v_normal;
    gl_Position = projection_mat * position;
}
