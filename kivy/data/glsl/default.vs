#ifdef GL_ES
    precision highp float;
#endif

/* Outputs to the fragment shader */
varying vec4 frag_color;
varying vec2 tex_coord0;
varying vec2 tex_coord1;
varying vec2 tex_coord2;


/* vertex attributes */
attribute vec2     vPosition;
attribute vec2     vTexCoords0;
attribute vec2     vTexCoords1;
attribute vec2     vTexCoords2;

/* uniform variables */
uniform float      linewidth;
uniform mat4       modelview_mat;
uniform mat4       projection_mat;
uniform vec4       color;

void main (void){
  vec2 pos    = vPosition.xy;
  gl_Position = vec4(pos.xy, 0.0, 1.0);
  frag_color  = vec4(1.0,1.0,color.x, 1.0);
  tex_coord0   = vTexCoords0;
  tex_coord1   = vTexCoords1;
  tex_coord2   = vTexCoords2;
}
