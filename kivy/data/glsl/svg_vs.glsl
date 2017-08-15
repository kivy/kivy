#ifdef GL_ES
    precision highp float;
#endif

attribute vec2 v_pos;
attribute vec2 v_tex;
attribute vec4 v_color;
attribute float v_gradient;
attribute float v_gradient_param1;
attribute float v_gradient_param2;
attribute float v_gradient_param3;
attribute float v_gradient_param4;
attribute float v_gradient_param5;

uniform mat4 modelview_mat;
uniform mat4 projection_mat;
varying vec4 vertex_color;
varying vec2 texcoord;
varying vec2 coord;
varying float gradient;
varying float gradient_param1;
varying float gradient_param2;
varying float gradient_param3;
varying float gradient_param4;
varying float gradient_param5;


void main (void) {
    vertex_color = v_color;
    gl_Position = projection_mat * modelview_mat * vec4(v_pos, 0.0, 1.0);
    texcoord = v_tex;
    coord = v_pos;
    gradient = floor(v_gradient * 255.);
    gradient_param1 = v_gradient_param1;
    gradient_param2 = v_gradient_param2;
    gradient_param3 = v_gradient_param3;
    gradient_param4 = v_gradient_param4;
    gradient_param5 = v_gradient_param5;
}

