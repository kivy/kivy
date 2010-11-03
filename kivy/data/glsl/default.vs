#ifdef GL_ES
    precision highp float;
#endif

/* Outputs to the fragment shader */
varying vec4 frag_color;
varying vec2 tex_coord;

/* vertex attributes */
attribute vec2     vPosition;
attribute vec4     vColor;
attribute vec2     vTexCoords0;

/* uniform variables */
uniform mat4       modelview_mat;
uniform mat4       projection_mat;
    
void main (void){
  gl_Position = projection_mat * modelview_mat * vec4(vPosition, 0.0,1.0);
  frag_color  = vColor;
  tex_coord   = vTexCoords0;
}
