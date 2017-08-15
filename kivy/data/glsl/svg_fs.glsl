// #version 130
#ifdef GL_ES
    precision highp float;
#endif

varying vec4 vertex_color;
varying vec2 texcoord;
varying vec2 coord;
varying float gradient;
varying float gradient_param1;
varying float gradient_param2;
varying float gradient_param3;
varying float gradient_param4;
varying float gradient_param5;


uniform sampler2D texture0;
uniform sampler2D gradients;
uniform vec2 gradients_size;
uniform float time;

#define LINEAR 0
#define RADIAL 1

#define PAD 1
#define REPEAT 2
#define REFLECT 3

#define USER_SPACE 1
#define OBJECT_BBOX 2

float linear_gradient(vec2 pos) {
    // w = 1. / (texcoord.x / pos.x);
    // h = 1. / (texcoord.y / pos.y);

    float x1 = gradient_param1;
    float x2 = gradient_param2;
    float y1 = gradient_param3;
    float y2 = gradient_param4;

    // return pos.x;
    return (
        (pos.x - x1) * (x2 - x1) +
        (pos.y - y1) * (y2 - y1)
    ) / (
        (x1 - x2) * (x2 - x1) +
        (y1 - y2) * (y2 - y1)
    );
}

float radial_gradient(vec2 pos) {
    float cx = gradient_param1;
    float cy = gradient_param2;
    float r = gradient_param3;
    float fx = gradient_param4;
    float fy = gradient_param5;

    vec2 d = vec2(fx, fy) - pos;
    vec2 center = vec2(cx, cy);
    vec2 radius = vec2(r, r);

    float l = length(d);
    center /= l;
    radius /= l;

    d /= l;

    float cd = dot(center, vec2(-d.y, d.x)),
          cl = sqrt(radius.x * radius.x - cd * cd) + dot(center, d);

    float a_cl = 1. / cl;

    // special case for when focale point is outside of radius
    if (a_cl < 0.)
        a_cl = 1.;

    return a_cl;
}

float g(int index){
    return texture2D(
        gradients, // coord / gradients_size
        vec2(
            float(index),
            gradient
        ) / gradients_size
    ).r;
}

int ig(int index) {
    return int(g(index) * 255.);
}

vec4 interp() {
    mat3 transform;
    vec4 col1, col2;
    float t;
    vec2 p;

    int i = 0;
    int type = ig(i++);
    // return texture2D(gradients, texcoord);
    // return vec4(0., 0., float(type), 1.);

    int spread = ig(i++);
    int units = ig(i++);

    // return vec4(float(spread), float(units), 0., 1.);
    // initiate transformation matrix
    for (int m=0; m < 2; m++)
        for (int n=0; n < 3; n++)
            transform[n][m] = g(i++);

    // 3rd line of the matrix is zeroed
    for (int n=0; n < 3; n++)
        transform[n][2] = 0.;

    // TODO apply transform and unit conversion if needed

    // return vec4(coord.x, 0., 0., 1.);
    if (type == LINEAR) {
        t = linear_gradient(coord);
        // return vec4(1., 1., 0., 1.);
    }

    else if (type == RADIAL) {
        t = radial_gradient(coord);
        // return vec4(0., 1., 0., 1.);
    } else {
        // show that something is wrong
        return vec4(1., 0., 0., 1.);
    }

    return vec4(t, 0., 0., 1);

    int stops = int(g(i++) * 255.);
    float first_stop = g(i);
    float last_stop = g(i + 5 * stops);

    // now we have first and last stop value, and spread, we can fix it if needed
    if (!(first_stop < t && t < last_stop)) {
        if (spread == PAD)
            t = min(1., t);
        else if (spread == REPEAT)
            t = fract(t);
        else if (spread ==  REFLECT) {
            float n = floor(t);
            float r = fract(t);
            if (mod(n, 2.) >= 1.)
                t = 1. - r;
            else
                t = r;
        }
     }

    // repeat the search process with a corrected t
    for (int i_s=0; i_s < stops; i_s++) {
        float s = g(i++);

        col2 = col1;
        col1.r = g(i++);
        col1.g = g(i++);
        col1.b = g(i++);
        col1.a = g(i++);

        if (0. < last_stop && last_stop < t && t < s)
            return mix(col1, col2, (t - last_stop) / (s - last_stop));

        else if (t < s)
            return col1;

        last_stop = s;
    }
    // we didn't find a last stop superior to t, so we must be in padding mode
    return col1;
}

void main (void) {
    if (gradient >= 1.) {
        // debug gradient ids, only good up to 4 ids, requires #version 130
        // int gid = int(gradient - 1.);
        // float xxr, xxg, xxb;
        // xxr = float(gid & 4);
        // xxg = float(gid & 2);
        // xxb = float(gid & 1);
        // gl_FragColor = vec4(xxr, xxg, xxb, 1.);

        // check that the texture is correctly uploaded
        // gl_FragColor = texture2D(gradients, coord / (gradients_size);
        gl_FragColor = interp();
    } else
        gl_FragColor = texture2D(texture0, texcoord) * (vertex_color / 255.);
}

