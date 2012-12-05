#ifdef GL_ES
    precision highp float;
#endif

/* uniforms */
uniform mat4 modelview_mat;
uniform vec3 diffuse_light;
uniform vec3 ambient_light;
uniform vec4 color;

/* Outputs from the vertex shader */
varying vec3 normal_vec;
varying vec3 eye_vec;


void main (void){
    //if non unioform scale transform is used, you need transpose inverse:
    //mat4  nmat = transpose(inverse(modelview_mat));
    //vec3 v_normal = normalize(vec3( nmat* vec4(v_normal.xyz, 0.0)));
    vec3 v_normal = normalize( vec3(modelview_mat * vec4(normal_vec, 0.0)) );
    vec3 v_light = normalize(-eye_vec);

    //diffuse and ambient light 
    //reflectance based on lamberts law of cosine
    float theta = clamp(dot(v_normal, v_light), 0.0, 1.0);
    vec3 reflectance = diffuse_light * theta;

    //compute final fragment color
    vec3 fc = clamp(color.xyz * reflectance + ambient_light, 0.0, 1.0);
    gl_FragColor = vec4(fc, color.a);
}

