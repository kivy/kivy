#ifdef GL_ES
    precision highp float;
#endif

varying vec4 vertex_color;
varying vec2 texcoord;
varying float gradient;
uniform sampler2D texture0;
uniform sampler2D gradients;
uniform vec2 gradients_size;

#define LINEAR 1.
#define RADIAL 2.

#define PAD 1.
#define REPEAT 2.
#define REFLECT 3.

float linear_gradient(vec2 pos, vec2 a, vec2 b) {
    return (
        (pos.x - a.x) * (b.x - a.x) +
        (pos.y - a.y) * (b.y - a.y)
    ) / (
        (a.x - b.x) * (a.x - b.x) +
        (a.y - b.y) * (a.y - b.y)
    );
}

float radial_gradient(vec2 pos, vec2 radius, vec2 center, vec2 focale) {
    vec2 d = focale - pos;
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
    return texture2D(gradients, vec2(gradient, float(index)) / gradients_size).r;
}

vec4 interp(vec2 pos) {
    int i = 0;
    float type = g(i++);
    mat3 transform;
    vec4 col1, col2;
    float t;
    float spread = g(i++);
    float units = g(i++);

    for (int n=0; n < 3; n++)
        for (int m=0; m < 3; m++)
            transform[n][m] = g(i++);


    if (type == LINEAR) {
        float x1 = g(i++);
        float y1 = g(i++);
        float x2 = g(i++);
        float y2 = g(i++);

        // XXX apply transform and unit conversion if needed
        t = linear_gradient(pos, vec2(x1, y1), vec2(x2, y2));
    }

    else if (type == RADIAL) {
        float cx = g(i++);
        float cy = g(i++);
        float r = g(i++);
        float fx = g(i++);
        float fy = g(i++);

        // XXX apply transform and unit conversion if needed
        t = radial_gradient(pos, vec2(r, r), vec2(cx, cy), vec2(fx, fy));
    }

    float first_stop = g(i);
    float last_stop = -1.;

    int saved_i = i;
    col2 = vec4(
        g(i),
        g(i + 1),
        g(i + 2),
        g(i + 3)
    );

    while (true) {
        float s = g(i++);

        // negative value mark the end of the stops, since it's
        // illegal to have a negative stop value
        if (s < 0.)
            break;

        col1.r = g(i++);
        col1.g = g(i++);
        col1.b = g(i++);
        col1.a = g(i++);

        if (0. <= last_stop && last_stop <= t && t <= s)
            return mix(col1, col2, (t - last_stop) / (s - last_stop));

        last_stop = s;
    }

    // now we have first and last stop value, and spread, we can fix t if needed
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
    i = saved_i;
    while (true) {
        float s = g(i++);

        // negative value mark the end of the stops, since it's
        // illegal to have a negative stop value
        if (s < 0.)
            break;

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
/*
    if (gradient != 0.)
        gl_FragColor = texture2D(texture0, texcoord) * interp(texcoord);

    else
*/
        gl_FragColor = texture2D(texture0, texcoord) * (vertex_color / 255.);
}

