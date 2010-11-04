
#ifdef GL_ES
    precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord;

/* uniform texture samplers */
uniform sampler2D texture0;

void main (void){
    gl_FragColor   = frag_color * texture2D(texture0, tex_coord);
}
