#ifdef GL_ES
    precision highp float;
#endif

attribute vec2 v_pos;
attribute vec2 v_tex;
attribute vec4 v_color;
attribute float v_gradient;
uniform mat4 modelview_mat;
uniform mat4 projection_mat;
varying vec4 vertex_color;
varying vec2 texcoord;
varying float gradient;

void main (void) {
    vertex_color = v_color;
    gradient = v_gradient;
    gl_Position = projection_mat * modelview_mat * vec4(v_pos, 0.0, 1.0);
    texcoord = v_tex;
}

