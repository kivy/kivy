
#ifdef GL_ES
    precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord0;
varying vec2 tex_coord1;
varying vec2 tex_coord2;



/* uniform texture samplers */
uniform sampler2D texture0;

void main (void){
    float d = 1.0 -length(tex_coord2.xy);
    gl_FragColor   = frag_color.xyza * texture2D(texture0, tex_coord0);
}
