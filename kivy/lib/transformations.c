/* transformations.c

A Python/Numpy C extension module for homogeneous transformation matrices
and quaternions.

Refer to the transformations.py module for documentation and tests.

Tested on Python 2.6 and 3.1, 32-bit and 64-bit.

Authors:
  Christoph Gohlke <http://www.lfd.uci.edu/~gohlke/>,
  Laboratory for Fluorescence Dynamics. University of California, Irvine.

Copyright (c) 2007-2010, The Regents of the University of California
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.
* Neither the name of the copyright holders nor the names of any
  contributors may be used to endorse or promote products derived
  from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
*/

/*****************************************************************************/
/* setup.py

"""A Python script to build the _transformations extension module.

Usage:: ``python setup.py build_ext --inplace``

"""

from distutils.core import setup, Extension
import numpy

setup(name='_transformations', ext_modules=[
      Extension('_transformations', ['transformations.c'],
      include_dirs=[numpy.get_include()], extra_compile_args=[])],)

******************************************************************************/

#define _VERSION_ "2010.04.10"

#define WIN32_LEAN_AND_MEAN
#ifdef _WIN32
#include <windows.h>
#include <wincrypt.h>
#endif

#include "Python.h"
#include "structmember.h"
#include "math.h"
#include "float.h"
#include "string.h"
#include "numpy/arrayobject.h"

#define EPSILON 8.8817841970012523e-016 /* 4.0 * DBL_EPSILON */
#define PIVOT_TOLERANCE 1.0e-14
#define DEG2RAD 0.017453292519943295769236907684886
#define TWOPI 6.283185307179586476925286766559
#ifndef M_PI
#define M_PI 3.1415926535897932384626433832795
#endif

#ifndef MAX
#define MAX(a, b) (((a) > (b)) ? (a) : (b))
#define MIN(a, b) (((a) < (b)) ? (a) : (b))
#endif

#define ISZERO(x) (((x) < EPSILON) && ((x) > -EPSILON))
#define NOTZERO(x) (((x) > EPSILON) || ((x) < -EPSILON))

/*****************************************************************************/
/* C helper functions */

/*
Return random doubles in half-open interval [0.0, 1.0).
Uses /dev/urandom or CryptoAPI. Not very fast but random.
Assumes sizeof(double) == 2*sizeof(int).
*/
int random_doubles(
    double *buffer,
    Py_ssize_t size)
{
#ifndef _WIN32
    int done;
    FILE *rfile;
    if (size < 1)
        return 0;
    rfile = fopen("/dev/urandom", "rb");
    if (rfile == NULL)
        return -1;
    done = fread(buffer, size*sizeof(double), 1, rfile);
    fclose(rfile);
#else
#pragma comment(lib,"advapi32")
    BOOL done;
    HCRYPTPROV hcryptprov;
    if (size < 1)
        return 0;
    if (!CryptAcquireContext(&hcryptprov, NULL, NULL, PROV_RSA_FULL,
                             CRYPT_VERIFYCONTEXT) || !hcryptprov)
        return -1;
    done = CryptGenRandom(hcryptprov, (DWORD)(size*sizeof(double)),
                          (unsigned char *)buffer);
    CryptReleaseContext(hcryptprov, 0);
#endif
    if (done) {
        unsigned int a, b;
        unsigned int *p = (unsigned int *)buffer;
        while (size--) {
            a = (*p++) >> 5;
            b = (*p++) >> 6;
            *buffer++ = (a * 67108864.0 + b) / 9007199254740992.0;
        }
        return 0;
    }
    return -1;
}

/*
Tridiagonal matrix from symmetric 4x4 matrix using Housholder reduction.
The input matrix is altered.
*/
int tridiagonalize_symmetric_44(
    double *matrix,      /* double[16] */
    double *diagonal,    /* double[4] */
    double *subdiagonal) /* double[3] */
{
    double t, n, g, h;
    double v0, v1, v2;
    double *M = matrix;
    double *u;

    u = &M[1];
    t = u[1]*u[1] + u[2]*u[2];
    n = sqrt(u[0]*u[0] + t);
    if (n > EPSILON) {
        if (u[0] < 0.0)
            n = -n;
        u[0] += n;
        h = (u[0]*u[0] + t) / 2.0;
        v0 = M[5]*u[0] + M[6]*u[1]  + M[7]*u[2];
        v1 = M[6]*u[0] + M[10]*u[1] + M[11]*u[2];
        v2 = M[7]*u[0] + M[11]*u[1] + M[15]*u[2];
        v0 /= h;
        v1 /= h;
        v2 /= h;
        g = (u[0]*v0 + u[1]*v1 + u[2]*v2) / (2.0 * h);
        v0 -= g * u[0];
        v1 -= g * u[1];
        v2 -= g * u[2];
        M[5] -=  2.0*v0*u[0];
        M[10] -= 2.0*v1*u[1];
        M[15] -= 2.0*v2*u[2];
        M[6]  -= v1*u[0] + v0*u[1];
        M[7]  -= v2*u[0] + v0*u[2];
        M[11] -= v2*u[1] + v1*u[2];
        M[1] = -n;
    }

    u = &M[6];
    t = u[1]*u[1];
    n = sqrt(u[0]*u[0] + t);
    if (n > EPSILON) {
        if (u[0] < 0.0)
            n = -n;
        u[0] += n;
        h = (u[0]*u[0] + t) / 2.0;
        v0 = M[10]*u[0] + M[11]*u[1];
        v1 = M[11]*u[0] + M[15]*u[1];
        v0 /= h;
        v1 /= h;
        g = (u[0]*v0 + u[1]*v1) / (2.0 * h);
        v0 -= g * u[0];
        v1 -= g * u[1];
        M[10] -= 2.0*v0*u[0];
        M[15] -= 2.0*v1*u[1];
        M[11] -= v1*u[0] + v0*u[1];
        M[6] = -n;
    }

    diagonal[0] = M[0];
    diagonal[1] = M[5];
    diagonal[2] = M[10];
    diagonal[3] = M[15];
    subdiagonal[0] = M[1];
    subdiagonal[1] = M[6];
    subdiagonal[2] = M[11];

    return 0;
}

/*
Return largest eigenvalue of symmetric tridiagonal matrix.
Matrix Algorithms: Basic decompositions. By GW Stewart. Chapter 3.
*/
double max_eigenvalue_of_tridiag_44(
    double *diagonal,    /* double[4] */
    double *subdiagonal) /* double[3] */
{
    int count;
    double lower, upper, t0, t1, d, eps, eigenv;
    double *a = diagonal;
    double *b = subdiagonal;

    /* upper and lower bounds using Gerschgorin's theorem */
    t0 = fabs(b[0]);
    t1 = fabs(b[1]);
    lower = a[0] - t0;
    upper = a[0] + t0;
    d = a[1] - t0 - t1;
    lower = MIN(lower, d);
    d = a[1] + t0 + t1;
    upper = MAX(upper, d);
    t0 = fabs(b[2]);
    d = a[2] - t0 - t1;
    lower = MIN(lower, d);
    d = a[2] + t0 + t1;
    upper = MAX(upper, d);
    d = a[3] - t0;
    lower = MIN(lower, d);
    d = a[3] + t0;
    upper = MAX(upper, d);

    /* precision */
    eps = (4.0 * (fabs(lower) + fabs(upper))) * DBL_EPSILON;

    /* interval bisection until width is less than tolerance */
    while (fabs(upper - lower) > eps) {

        eigenv = (upper + lower) / 2.0;
        if ((eigenv == upper) || (eigenv == lower))
            return eigenv;

        /* counting pivots < 0 */
        d = a[0] - eigenv;
        count = (d < 0.0) ? 1 : 0;
        if (fabs(d) < eps)
            d = eps;
        d = a[1] - eigenv - b[0]*b[0] / d;
        if (d < 0.0)
            count++;
        if (fabs(d) < eps)
            d = eps;
        d = a[2] - eigenv - b[1]*b[1] / d;
        if (d < 0.0)
            count++;
        if (fabs(d) < eps)
            d = eps;
        d = a[3] - eigenv - b[2]*b[2] / d;
        if (d < 0.0)
            count++;

        if (count < 4)
            lower = eigenv;
        else
            upper = eigenv;
    }

    return (upper + lower) / 2.0;
}

/*
Eigenvector of symmetric tridiagonal 4x4 matrix using Cramer's rule.
*/
int eigenvector_of_symmetric_44(
    double *matrix, /* double[16] */
    double *vector, /* double[4]  */
    double *buffer) /* double[12] */
{
    double n, eps;
    double *M = matrix;
    double *v = vector;
    double *t = buffer;

    /* eps: minimum length of eigenvector to use */
    eps = (M[0]*M[5]*M[10]*M[15] - M[1]*M[1]*M[11]*M[11]) * 1e-6;
    eps *= eps;
    if (eps < EPSILON)
        eps = EPSILON;

    t[0] = M[10] * M[15];
    t[1] = M[11] * M[11];
    t[2] = M[6] *  M[15];
    t[3] = M[11] * M[7];
    t[4] = M[6] *  M[11];
    t[5] = M[10] * M[7];
    t[6] = M[2] *  M[15];
    t[7] = M[11] * M[3];
    t[8] = M[2] *  M[11];
    t[9] = M[10] * M[3];
    t[10] = M[2] * M[7];
    t[11] = M[6] * M[3];

    v[0] =  t[1]*M[1] + t[6]*M[6] + t[9]*M[7];
    v[0] -= t[0]*M[1] + t[7]*M[6] + t[8]*M[7];
    v[1] =  t[2]*M[1] + t[7]*M[5] + t[10]*M[7];
    v[1] -= t[3]*M[1] + t[6]*M[5] + t[11]*M[7];
    v[2] =  t[5]*M[1] + t[8]*M[5] + t[11]*M[6];
    v[2] -= t[4]*M[1] + t[9]*M[5] + t[10]*M[6];
    v[3] =  t[0]*M[5] + t[3]*M[6] + t[4]*M[7];
    v[3] -= t[1]*M[5] + t[2]*M[6] + t[5]*M[7];
    n = v[0]*v[0] + v[1]*v[1] + v[2]*v[2] + v[3]*v[3];

    if (n < eps) {
        v[0] =  t[0]*M[0] + t[7]*M[2] + t[8]*M[3];
        v[0] -= t[1]*M[0] + t[6]*M[2] + t[9]*M[3];
        v[1] =  t[3]*M[0] + t[6]*M[1] + t[11]*M[3];
        v[1] -= t[2]*M[0] + t[7]*M[1] + t[10]*M[3];
        v[2] =  t[4]*M[0] + t[9]*M[1] + t[10]*M[2];
        v[2] -= t[5]*M[0] + t[8]*M[1] + t[11]*M[2];
        v[3] =  t[1]*M[1] + t[2]*M[2] + t[5]*M[3];
        v[3] -= t[0]*M[1] + t[3]*M[2] + t[4]*M[3];
        n = v[0]*v[0] + v[1]*v[1] + v[2]*v[2] + v[3]*v[3];
    }

    if (n < eps) {
        t[0]  = M[2] * M[7];
        t[1]  = M[3] * M[6];
        t[2]  = M[1] * M[7];
        t[3]  = M[3] * M[5];
        t[4]  = M[1] * M[6];
        t[5]  = M[2] * M[5];
        t[6]  = M[0] * M[7];
        t[7]  = M[3] * M[1];
        t[8]  = M[0] * M[6];
        t[9]  = M[2] * M[1];
        t[10] = M[0] * M[5];
        t[11] = M[1] * M[1];

        v[0] =  t[1]*M[3] + t[6]*M[11] + t[9]*M[15];
        v[0] -= t[0]*M[3] + t[7]*M[11] + t[8]*M[15];
        v[1] =  t[2]*M[3] + t[7]*M[7] + t[10]*M[15];
        v[1] -= t[3]*M[3] + t[6]*M[7] + t[11]*M[15];
        v[2] =  t[5]*M[3] + t[8]*M[7] + t[11]*M[11];
        v[2] -= t[4]*M[3] + t[9]*M[7] + t[10]*M[11];
        v[3] =  t[0]*M[7] + t[3]*M[11] + t[4]*M[15];
        v[3] -= t[1]*M[7] + t[2]*M[11] + t[5]*M[15];
        n = v[0]*v[0] + v[1]*v[1] + v[2]*v[2] + v[3]*v[3];
    }

    if (n < eps) {
        v[0] =  t[8]*M[11] + t[0]*M[2] + t[7]*M[10];
        v[0] -= t[6]*M[10] + t[9]*M[11] + t[1]*M[2];
        v[1] =  t[6]*M[6] + t[11]*M[11] + t[3]*M[2];
        v[1] -= t[10]*M[11] + t[2]*M[2] + t[7]*M[6];
        v[2] =  t[10]*M[10] + t[4]*M[2] + t[9]*M[6];
        v[2] -= t[8]*M[6] + t[11]*M[10] + t[5]*M[2];
        v[3] =  t[2]*M[10] + t[5]*M[11] + t[1]*M[6];
        v[3] -= t[4]*M[11] + t[0]*M[6] + t[3]*M[10];
        n = v[0]*v[0] + v[1]*v[1] + v[2]*v[2] + v[3]*v[3];
    }

    if (n < eps)
        return -1;

    n = sqrt(n);
    v[0] /= n;
    v[1] /= n;
    v[2] /= n;
    v[3] /= n;

    return 0;
}

/*
Matrix 2x2 inversion.
*/
int invert_matrix22(
    double *matrix, /* double[4] */
    double *result) /* double[4] */
{
    double det = matrix[0]*matrix[3] - matrix[1]*matrix[2];

    if (ISZERO(det))
        return -1;

    result[0] = matrix[3] / det;
    result[1] = -matrix[1] / det;
    result[2] = -matrix[2] / det;
    result[3] = matrix[0] / det;

    return 0;
}

/*
Matrix 3x3 inversion.
*/
int invert_matrix33(
    double *matrix, /* double[9] */
    double *result) /* double[9] */
{
    double *M = matrix;
    double det;
    int i;

    result[0] = M[8]*M[4] - M[7]*M[5];
    result[1] = M[7]*M[2] - M[8]*M[1];
    result[2] = M[5]*M[1] - M[4]*M[2];
    result[3] = M[6]*M[5] - M[8]*M[3];
    result[4] = M[8]*M[0] - M[6]*M[2];
    result[5] = M[3]*M[2] - M[5]*M[0];
    result[6] = M[7]*M[3] - M[6]*M[4];
    result[7] = M[6]*M[1] - M[7]*M[0];
    result[8] = M[4]*M[0] - M[3]*M[1];

    det = M[0]*result[0] + M[3]*result[1] + M[6]*result[2];

    if (ISZERO(det))
        return -1;

    det = 1.0 / det;
    for (i = 0; i < 9; i++)
        result[i] *= det;

    return 0;
}

/*
Matrix 4x4 inversion.
*/
int invert_matrix44(
    double *matrix, /* double[16] */
    double *result) /* double[16] */
{
    double *M = matrix;
    double t[12];
    double det;
    int i;

    t[0] = M[10] * M[15];
    t[1] = M[14] * M[11];
    t[2] = M[6] * M[15];
    t[3] = M[14] * M[7];
    t[4] = M[6] * M[11];
    t[5] = M[10] * M[7];
    t[6] = M[2] * M[15];
    t[7] = M[14] * M[3];
    t[8] = M[2] * M[11];
    t[9] = M[10] * M[3];
    t[10] = M[2] * M[7];
    t[11] = M[6] * M[3];

    result[0] = t[0]*M[5] + t[3]*M[9] + t[4]*M[13];
    result[0] -= t[1]*M[5] + t[2]*M[9] + t[5]*M[13];
    result[1] = t[1]*M[1] + t[6]*M[9] + t[9]*M[13];
    result[1] -= t[0]*M[1] + t[7]*M[9] + t[8]*M[13];
    result[2] = t[2]*M[1] + t[7]*M[5] + t[10]*M[13];
    result[2] -= t[3]*M[1] + t[6]*M[5] + t[11]*M[13];
    result[3] = t[5]*M[1] + t[8]*M[5] + t[11]*M[9];
    result[3] -= t[4]*M[1] + t[9]*M[5] + t[10]*M[9];
    result[4] = t[1]*M[4] + t[2]*M[8] + t[5]*M[12];
    result[4] -= t[0]*M[4] + t[3]*M[8] + t[4]*M[12];
    result[5] = t[0]*M[0] + t[7]*M[8] + t[8]*M[12];
    result[5] -= t[1]*M[0] + t[6]*M[8] + t[9]*M[12];
    result[6] = t[3]*M[0] + t[6]*M[4] + t[11]*M[12];
    result[6] -= t[2]*M[0] + t[7]*M[4] + t[10]*M[12];
    result[7] = t[4]*M[0] + t[9]*M[4] + t[10]*M[8];
    result[7] -= t[5]*M[0] + t[8]*M[4] + t[11]*M[8];

    t[0] = M[8]*M[13];
    t[1] = M[12]*M[9];
    t[2] = M[4]*M[13];
    t[3] = M[12]*M[5];
    t[4] = M[4]*M[9];
    t[5] = M[8]*M[5];
    t[6] = M[0]*M[13];
    t[7] = M[12]*M[1];
    t[8] = M[0]*M[9];
    t[9] = M[8]*M[1];
    t[10] = M[0]*M[5];
    t[11] = M[4]*M[1];

    result[8] = t[0]*M[7] + t[3]*M[11] + t[4]*M[15];
    result[8] -= t[1]*M[7] + t[2]*M[11] + t[5]*M[15];
    result[9] = t[1]*M[3] + t[6]*M[11] + t[9]*M[15];
    result[9] -= t[0]*M[3] + t[7]*M[11] + t[8]*M[15];
    result[10] = t[2]*M[3] + t[7]*M[7] + t[10]*M[15];
    result[10]-= t[3]*M[3] + t[6]*M[7] + t[11]*M[15];
    result[11] = t[5]*M[3] + t[8]*M[7] + t[11]*M[11];
    result[11]-= t[4]*M[3] + t[9]*M[7] + t[10]*M[11];
    result[12] = t[2]*M[10] + t[5]*M[14] + t[1]*M[6];
    result[12]-= t[4]*M[14] + t[0]*M[6] + t[3]*M[10];
    result[13] = t[8]*M[14] + t[0]*M[2] + t[7]*M[10];
    result[13]-= t[6]*M[10] + t[9]*M[14] + t[1]*M[2];
    result[14] = t[6]*M[6] + t[11]*M[14] + t[3]*M[2];
    result[14]-= t[10]*M[14] + t[2]*M[2] + t[7]*M[6];
    result[15] = t[10]*M[10] + t[4]*M[2] + t[9]*M[6];
    result[15]-= t[8]*M[6] + t[11]*M[10] + t[5]*M[2];

    det = M[0]*result[0] + M[4]*result[1] + M[8]*result[2] + M[12]*result[3];

    if (ISZERO(det))
        return -1;

    det = 1.0 / det;
    for (i = 0; i < 16; i++)
        result[i] *= det;

    return 0;
}

/*
Invert square matrix using LU factorization with pivoting.
The input matrix is altered.
*/
int invert_matrix(
    Py_ssize_t size,
    double *matrix,     /* [size*size] */
    double *result,     /* [size*size] */
    Py_ssize_t *buffer) /* [2*size] */
{
    double temp, temp1;
    double *M = matrix;
    Py_ssize_t *seq = buffer;
    Py_ssize_t *iseq = buffer + size;
    Py_ssize_t i, j, k, ks, ps, ksk, js, p, is;

    /* sequence of pivots */
    for (k = 0; k < size; k++)
        seq[k] = k;

    /* forward solution */
    for (k = 0; k < size-1; k++) {
        ks = k*size;
        ksk = ks + k;

        /* pivoting: find maximum coefficient in column */
        p = k;
        temp = fabs(M[ksk]);
        for (i = k+1; i < size; i++) {
            temp1 = fabs(M[i*size + k]);
            if (temp < temp1) {
                temp = temp1;
                p = i;
            }
        }
        /* permutate lines with index k and p */
        if (p != k) {
            ps = p*size;
            for (i = 0; i < size; i++) {
                temp = M[ks + i];
                M[ks + i] = M[ps + i];
                M[ps + i] = temp;
            }
            i = seq[k];
            seq[k] = seq[p];
            seq[p] = i;
        }

        /* test for singular matrix */
        if (fabs(M[ksk]) < PIVOT_TOLERANCE)
            return -1;

        /* elimination */
        temp = M[ksk];
        for (j = k+1; j < size; j++) {
            M[j*size + k] /= temp;
        }
        for (j = k+1; j < size; j++) {
            js = j * size;
            temp = M[js + k];
            for(i = k+1; i < size; i++) {
                M[js + i] -= temp * M[ks + i];
            }
            M[js + k] = temp;
        }
    }

    /* Backward substitution with identity matrix */
    memset(result, 0, size*size*sizeof(double));
    for (i = 0; i < size; i++) {
        result[i*size + seq[i]] = 1.0;
        iseq[seq[i]] = i;
    }

    for (i = 0; i < size; i++) {
        is = iseq[i];
        for (k = 1; k < size; k++) {
            ks = k*size;
            temp = 0.0;
            for (j = is; j < k; j++)
                temp += M[ks + j] * result[j*size + i];
            result[ks + i] -= temp;
        }
        for (k = size-1; k >= 0; k--) {
            ks = k*size;
            temp = result[ks + i];
            for (j = k+1; j < size; j++)
                temp -= M[ks + j] * result[j*size + i];
            result[ks + i] = temp / M[ks + k];
        }
    }
    return 0;
}

/*
Quaternion from matrix.
*/
int quaternion_from_matrix(
    double *matrix,     /* double[16] */
    double *quaternion) /* double[4] */
{
    double *M = matrix;
    double *q = quaternion;
    double s;

    if (ISZERO(M[15]))
        return -1;

    if ((M[0] + M[5] + M[10]) > 0.0) {
        s = 0.5 / sqrt(M[0] + M[5] + M[10] + M[15]);
        q[0] = 0.25 / s;
        q[3] = (M[4] - M[1]) * s;
        q[2] = (M[2] - M[8]) * s;
        q[1] = (M[9] - M[6]) * s;
    } else if ((M[0] > M[5]) && (M[0] > M[10])) {
        s = 0.5 / sqrt(M[0] - (M[5] + M[10]) + M[15]);
        q[1] = 0.25 / s;
        q[2] = (M[4] + M[1]) * s;
        q[3] = (M[2] + M[8]) * s;
        q[0] = (M[9] - M[6]) * s;
    } else if (M[5] > M[10]) {
        s = 0.5 / sqrt(M[5] - (M[0] + M[10]) + M[15]);
        q[2] = 0.25 / s;
        q[1] = (M[4] + M[1]) * s;
        q[0] = (M[2] - M[8]) * s;
        q[3] = (M[9] + M[6]) * s;
    } else {
        s = 0.5 / sqrt(M[10] - (M[0] + M[5]) + M[15]);
        q[3] = 0.25 / s;
        q[0] = (M[4] - M[1]) * s;
        q[1] = (M[2] + M[8]) * s;
        q[2] = (M[9] + M[6]) * s;
    }

    if (M[15] != 1.0) {
        s = 1.0 / sqrt(M[15]);
        q[0] *= s;
        q[1] *= s;
        q[2] *= s;
        q[3] *= s;
    }
    return 0;
}

/*
Quaternion to rotation matrix.
*/
int quaternion_matrix(
    double *quat,    /* double[4]  */
    double *matrix)  /* double[16] */
{
    double *M = matrix;
    double *q = quat;
    double n = sqrt(q[0]*q[0] + q[1]*q[1] + q[2]*q[2] + q[3]*q[3]);

    if (n < EPSILON) {
        /* return identity matrix */
        memset(M, 0, 16*sizeof(double));
        M[0] = M[5] = M[10] = M[15] = 1.0;
    } else {
        q[0] /= n;
        q[1] /= n;
        q[2] /= n;
        q[3] /= n;
        {
            double x2 = q[1]+q[1];
            double y2 = q[2]+q[2];
            double z2 = q[3]+q[3];
            {
                double xx2 = q[1]*x2;
                double yy2 = q[2]*y2;
                double zz2 = q[3]*z2;
                M[0]  = 1.0 - yy2 - zz2;
                M[5]  = 1.0 - xx2 - zz2;
                M[10] = 1.0 - xx2 - yy2;
            }{
                double yz2 = q[2]*z2;
                double wx2 = q[0]*x2;
                M[6] = yz2 - wx2;
                M[9] = yz2 + wx2;
            }{
                double xy2 = q[1]*y2;
                double wz2 = q[0]*z2;
                M[1] = xy2 - wz2;
                M[4] = xy2 + wz2;
            }{
                double xz2 = q[1]*z2;
                double wy2 = q[0]*y2;
                M[8] = xz2 - wy2;
                M[2] = xz2 + wy2;
            }
            M[3] = M[7] = M[11] = M[12] = M[13] = M[14] = 0.0;
            M[15] = 1.0;
        }
    }
    return 0;
}

/*
Unit quaternion from unit sphere points.
*/
int quaternion_from_sphere_points(
    double *point0, /* double[3] */
    double *point1, /* double[3] */
    double *quat)   /* double[4] */
{
    quat[0] = point0[0]*point1[0] + point0[1]*point1[1] + point0[2]*point1[2];
    quat[1] = point0[1]*point1[2] - point0[2]*point1[1];
    quat[2] = point0[2]*point1[0] - point0[0]*point1[2];
    quat[3] = point0[0]*point1[1] - point0[1]*point1[0];
    return 0;
}

/*
Unit quaternion to unit sphere points.
*/
int quaternion_to_sphere_points(
    double *quat,   /* double[4] */
    double *point0, /* double[3] */
    double *point1) /* double[3] */
{
    double n = sqrt(quat[0]*quat[0] + quat[1]*quat[1]);

    if (n < EPSILON) {
        point0[0] = 0.0;
        point0[1] = 1.0;
        point0[2] = 0.0;
    } else {
        point0[0] = -quat[2] / n;
        point0[1] = quat[1] / n;
        point0[2] = 0.0;
    }

    point1[0] = quat[0]*point0[0] - quat[3]*point0[1];
    point1[1] = quat[0]*point0[1] + quat[3]*point0[0];
    point1[2] = quat[1]*point0[1] - quat[2]*point0[0];

    if (quat[0] < 0.0) {
        point0[0] = -point0[0];
        point0[1] = -point0[1];
    }

    return 0;
}

/*****************************************************************************/
/* Python functions */

/*
Numpy array converters for use with PyArg_Parse functions.
*/
static int
PyConverter_DoubleArray(
    PyObject *object,
    PyObject **address)
{
    *address = PyArray_FROM_OTF(object, NPY_DOUBLE, NPY_IN_ARRAY);
     if (*address == NULL) return NPY_FAIL;
     return NPY_SUCCEED;
}

static int
PyConverter_AnyDoubleArray(
    PyObject *object,
    PyObject **address)
{
    PyArrayObject *obj = (PyArrayObject *)object;
    if (PyArray_Check(object) && obj->descr->type_num == PyArray_DOUBLE) {
        *address = object;
        Py_INCREF(object);
        return NPY_SUCCEED;
    } else {
        *address = PyArray_FROM_OTF(object, NPY_DOUBLE, NPY_ALIGNED);
        if (*address == NULL) {
            PyErr_Format(PyExc_ValueError, "can not convert to array");
            return NPY_FAIL;
        }
        return NPY_SUCCEED;
    }
}

static int
PyConverter_DoubleArrayOrNone(
    PyObject *object,
    PyObject **address)
{
    if ((object == NULL) || (object == Py_None)) {
        *address = NULL;
    } else {
        *address = PyArray_FROM_OTF(object, NPY_DOUBLE, NPY_IN_ARRAY);
        if (*address == NULL) {
            PyErr_Format(PyExc_ValueError, "can not convert to array");
            return NPY_FAIL;
        }
    }
    return NPY_SUCCEED;
}

static int
PyConverter_DoubleMatrix44(
    PyObject *object,
    PyObject **address)
{
    PyArrayObject *obj;
    *address = PyArray_FROM_OTF(object, NPY_DOUBLE, NPY_IN_ARRAY);
    if (*address == NULL) {
        PyErr_Format(PyExc_ValueError, "can not convert to array");
        return NPY_FAIL;
    }
    obj = (PyArrayObject *) *address;
    if ((PyArray_NDIM(obj) != 2) || (PyArray_DIM(obj, 0) != 4)
        || (PyArray_DIM(obj, 1) != 4) || PyArray_ISCOMPLEX(obj)) {
        PyErr_Format(PyExc_ValueError, "not a 4x4 matrix");
        Py_DECREF(*address);
        *address = NULL;
        return NPY_FAIL;
    }
    return NPY_SUCCEED;
}

static int
PyConverter_DoubleMatrix44Copy(
    PyObject *object,
    PyObject **address)
{
    PyArrayObject *obj;
    *address = PyArray_FROM_OTF(object, NPY_DOUBLE,
                                NPY_ENSURECOPY|NPY_IN_ARRAY);
    if (*address == NULL) {
        PyErr_Format(PyExc_ValueError, "can not convert to array");
        return NPY_FAIL;
    }
    obj = (PyArrayObject *) *address;
    if ((PyArray_NDIM(obj) != 2) || (PyArray_DIM(obj, 0) != 4)
        || (PyArray_DIM(obj, 1) != 4) || PyArray_ISCOMPLEX(obj)) {
        PyErr_Format(PyExc_ValueError, "not a 4x4 matrix");
        Py_DECREF(*address);
        *address = NULL;
        return NPY_FAIL;
    }
    return NPY_SUCCEED;
}

static int
PyConverter_DoubleVector3(
    PyObject *object,
    PyObject **address)
{
    PyArrayObject *obj;
    *address = PyArray_FROM_OTF(object, NPY_DOUBLE, NPY_IN_ARRAY);
    if (*address == NULL) {
        PyErr_Format(PyExc_ValueError, "can not convert to array");
        return NPY_FAIL;
    }
    obj = (PyArrayObject *) *address;
    if ((PyArray_NDIM(obj) != 1) || (PyArray_DIM(obj, 0) < 3)
        || PyArray_ISCOMPLEX(obj)) {
        PyErr_Format(PyExc_ValueError, "not a vector3");
        Py_DECREF(*address);
        *address = NULL;
        return NPY_FAIL;
    }
    return NPY_SUCCEED;
}

static int
PyConverter_DoubleVector4(
    PyObject *object,
    PyObject **address)
{
    PyArrayObject *obj;
    *address = PyArray_FROM_OTF(object, NPY_DOUBLE, NPY_IN_ARRAY);
    if (*address == NULL) {
        PyErr_Format(PyExc_ValueError, "can not convert to array");
        return NPY_FAIL;
    }
    obj = (PyArrayObject *) *address;
    if ((PyArray_NDIM(obj) != 1) || (PyArray_DIM(obj, 0) < 4)
        || PyArray_ISCOMPLEX(obj)) {
        PyErr_Format(PyExc_ValueError, "not a vector4");
        Py_DECREF(*address);
        *address = NULL;
        return NPY_FAIL;
    }
    return NPY_SUCCEED;
}

static int
PyConverter_DoubleVector4Copy(
    PyObject *object,
    PyObject **address)
{
    PyArrayObject *obj;
    *address = PyArray_FROM_OTF(object, NPY_DOUBLE,
                                NPY_ENSURECOPY|NPY_IN_ARRAY);
    if (*address == NULL) {
        PyErr_Format(PyExc_ValueError, "can not convert to array");
        return NPY_FAIL;
    }
    obj = (PyArrayObject *) *address;
    if ((PyArray_NDIM(obj) != 1) || (PyArray_DIM(obj, 0) < 4)
        || PyArray_ISCOMPLEX(obj)) {
        PyErr_Format(PyExc_ValueError, "not a vector4");
        Py_DECREF(*address);
        *address = NULL;
        return NPY_FAIL;
    }
    return NPY_SUCCEED;
}

static int
PyConverter_DoubleVector3OrNone(
    PyObject *object,
    PyObject **address)
{
    if ((object == NULL) || (object == Py_None)) {
        *address = NULL;
    } else {
        PyArrayObject *obj;
        *address = PyArray_FROM_OTF(object, NPY_DOUBLE, NPY_IN_ARRAY);
        if (*address == NULL) {
            PyErr_Format(PyExc_ValueError, "can not convert to array");
            return NPY_FAIL;
        }
        obj = (PyArrayObject *) *address;
        if ((PyArray_NDIM(obj) != 1) || (PyArray_DIM(obj, 0) < 3)
            || PyArray_ISCOMPLEX(obj)) {
            PyErr_Format(PyExc_ValueError, "not a vector3");
            Py_DECREF(*address);
            *address = NULL;
            return NPY_FAIL;
        }
    }
    return NPY_SUCCEED;
}

static int
PyOutputConverter_AnyDoubleArrayOrNone(
    PyObject *object,
    PyArrayObject **address)
{
    PyArrayObject *obj = (PyArrayObject *)object;
    if ((object == NULL) || (object == Py_None)) {
        *address = NULL;
        return NPY_SUCCEED;
    }
    if (PyArray_Check(object) && (obj->descr->type_num == PyArray_DOUBLE)) {
        Py_INCREF(object);
        *address = (PyArrayObject *)object;
        return NPY_SUCCEED;
    } else {
        PyErr_Format(PyExc_TypeError, "output must be array of type double");
        *address = NULL;
        return NPY_FAIL;
    }
}

/*
Return i-th element of Python sequence as long, or -1 on failure.
*/
long PySequence_GetInteger(PyObject *obj, Py_ssize_t i)
{
    long value;
    PyObject *item = PySequence_GetItem(obj, i);
    if (item == NULL ||
#if PY_MAJOR_VERSION < 3
        !PyInt_Check(item)
#else
        !PyLong_Check(item)
#endif
        ) {
        PyErr_Format(PyExc_ValueError, "expected integer number");
        Py_XDECREF(item);
        return -1;
    }

#if PY_MAJOR_VERSION < 3
    value = PyInt_AsLong(item);
#else
    value = PyLong_AsLong(item);
#endif
    Py_XDECREF(item);
    return value;
}

/*
Equivalence of transformations.
*/
char py_is_same_transform_doc[] =
    "Return True if two matrices perform same transformation.";

static PyObject *
py_is_same_transform(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *matrix0 = NULL;
    PyArrayObject *matrix1 = NULL;
    int result;
    static char *kwlist[] = {"matrix0", "matrix1", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&O&", kwlist,
        PyConverter_DoubleMatrix44, &matrix0,
        PyConverter_DoubleMatrix44, &matrix1)) goto _fail;

    {
        double *M0 = (double *)PyArray_DATA(matrix0);
        double *M1 = (double *)PyArray_DATA(matrix1);
        double t0 = M0[15];
        double t1 = M1[15];
        double t;
        int i;
        if (ISZERO(t0) || ISZERO(t1)) {
            result = 0;
        } else {
            result = 1;
            for (i = 0; i < 16; i++) {
                t = M1[i] / t1;
                if (fabs(M0[i]/t0 - t) > (1e-8 + 1e-5*fabs(t))) {
                    result = 0;
                    break;
                }
            }
        }
    }

    Py_DECREF(matrix0);
    Py_DECREF(matrix1);
    if (result)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;

  _fail:
    Py_XDECREF(matrix0);
    Py_XDECREF(matrix1);
    return NULL;
}

/*
Identity matrix.
*/
char py_identity_matrix_doc[] = "Return identity/unit matrix.";

static PyObject *
py_identity_matrix(
    PyObject *obj,
    PyObject *args)
{
    PyArrayObject *result = NULL;
    PyArray_Descr *type = NULL;
    Py_ssize_t dims[] = {4, 4};

    type = PyArray_DescrFromType(NPY_DOUBLE);
    result = (PyArrayObject*)PyArray_Zeros(2, dims, type, 0);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate matrix");
        goto _fail;
    }
    {
        double *M = (double *)PyArray_DATA(result);
        M[0] = M[5] = M[10] = M[15] = 1.0;
    }

    return PyArray_Return(result);

  _fail:
    Py_XDECREF(result);
    return NULL;
}

/*
Translation matrix.
*/
char py_translation_matrix_doc[] =
    "Return matrix to translate by direction vector.";

static PyObject *
py_translation_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *result = NULL;
    PyArrayObject *direction = NULL;
    PyArray_Descr *type = NULL;
    Py_ssize_t dims[] = {4, 4};
    static char *kwlist[] = {"direction", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&", kwlist,
        PyConverter_DoubleVector3, &direction)) goto _fail;

    type = PyArray_DescrFromType(NPY_DOUBLE);
    result = (PyArrayObject*)PyArray_Zeros(2, dims, type, 0);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate matrix");
        goto _fail;
    }
    {
        double *M = (double *)PyArray_DATA(result);
        double *d = (double *)PyArray_DATA(direction);
        M[0] = M[5] = M[10] = M[15] = 1.0;
        M[3] = d[0];
        M[7] = d[1];
        M[11] = d[2];
    }

    Py_DECREF(direction);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(direction);
    Py_XDECREF(result);
    return NULL;
}

/*
Reflection matrix.
*/
char py_reflection_matrix_doc[] =
    "Return matrix to mirror at plane defined by point and normal vector.";

static PyObject *
py_reflection_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *result = NULL;
    PyArrayObject *point = NULL;
    PyArrayObject *normal = NULL;
    Py_ssize_t dims[] = {4, 4};
    static char *kwlist[] = {"point", "normal", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&O&", kwlist,
        PyConverter_DoubleVector3, &point,
        PyConverter_DoubleVector3, &normal)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate matrix");
        goto _fail;
    }
    {
        double *M = (double *)PyArray_DATA(result);
        double *p = (double *)PyArray_DATA(point);
        double *n = (double *)PyArray_DATA(normal);
        double nx = n[0];
        double ny = n[1];
        double nz = n[2];
        double t = sqrt(nx*nx + ny*ny + nz*nz);
        if (t < EPSILON) {
            PyErr_Format(PyExc_ValueError, "invalid normal vector");
            goto _fail;
        }
        nx /= t;
        ny /= t;
        nz /= t;
        M[12] = M[13] = M[14] = 0.0;
        M[15] = 1.0;
        M[0] = 1.0 - 2.0 * nx *nx;
        M[5] = 1.0 - 2.0 * ny *ny;
        M[10] = 1.0 - 2.0 * nz *nz;
        M[1] = M[4] = -2.0 * nx *ny;
        M[2] = M[8] = -2.0 * nx *nz;
        M[6] = M[9] = -2.0 * ny *nz;
        t = 2.0 * (p[0]*nx + p[1]*ny + p[2]*nz);
        M[3] = nx * t;
        M[7] = ny * t;
        M[11] = nz * t;
    }

    Py_DECREF(point);
    Py_DECREF(normal);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(point);
    Py_XDECREF(normal);
    Py_XDECREF(result);
    return NULL;
}

/*
Rotation matrix.
*/
char py_rotation_matrix_doc[] =
    "Return matrix to rotate about axis defined by point and direction.";

static PyObject *
py_rotation_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *result = NULL;
    PyArrayObject *point = NULL;
    PyArrayObject *direction = NULL;
    Py_ssize_t dims[] = {4, 4};
    double angle;
    static char *kwlist[] = {"angle", "direction", "point", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "dO&|O&", kwlist,
        &angle,
        PyConverter_DoubleVector3, &direction,
        PyConverter_DoubleVector3OrNone, &point)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate matrix");
        goto _fail;
    }
    {
        double *M = (double *)PyArray_DATA(result);
        double *d = (double *)PyArray_DATA(direction);
        double dx = d[0];
        double dy = d[1];
        double dz = d[2];
        double sa = sin(angle);
        double ca = cos(angle);
        double ca1 = 1 - ca;
        double s, t;

        t = sqrt(dx*dx + dy*dy + dz*dz);
        if (t < EPSILON) {
            PyErr_Format(PyExc_ValueError, "invalid direction vector");
            goto _fail;
        }
        dx /= t;
        dy /= t;
        dz /= t;

        M[0] =  ca + dx*dx * ca1;
        M[5] =  ca + dy*dy * ca1;
        M[10] = ca + dz*dz * ca1;

        s = dz * sa;
        t = dx*dy * ca1;
        M[1] = t - s;
        M[4] = t + s;

        s = dy * sa;
        t = dx*dz * ca1;
        M[2] = t + s;
        M[8] = t - s;

        s = dx * sa;
        t = dy*dz * ca1;
        M[6] = t - s;
        M[9] = t + s;

        M[12] = M[13] = M[14] = 0.0;
        M[15] = 1.0;

        if (point != NULL) {
            double *p = (double *)PyArray_DATA(point);
            M[3]  = p[0] - (M[0]*p[0] + M[1]*p[1] + M[2]*p[2]);
            M[7]  = p[1] - (M[4]*p[0] + M[5]*p[1] + M[6]*p[2]);
            M[11] = p[2] - (M[8]*p[0] + M[9]*p[1] + M[10]*p[2]);
        } else {
            M[3] = M[7] = M[11] = 0.0;
        }
    }

    Py_XDECREF(point);
    Py_DECREF(direction);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(point);
    Py_XDECREF(direction);
    Py_XDECREF(result);
    return NULL;
}

/*
Projection matrix.
*/
char py_projection_matrix_doc[] =
    "Return matrix to project onto plane defined by point and normal.";

static PyObject *
py_projection_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *result = NULL;
    PyArrayObject *point = NULL;
    PyArrayObject *normal = NULL;
    PyArrayObject *direction = NULL;
    PyArrayObject *perspective = NULL;
    PyObject *pseudobj = NULL;
    Py_ssize_t dims[] = {4, 4};
    int pseudo = 0;
    static char *kwlist[] = {"point", "normal", "direction",
                             "perspective", "pseudo", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&O&|O&O&O", kwlist,
        PyConverter_DoubleVector3, &point,
        PyConverter_DoubleVector3, &normal,
        PyConverter_DoubleVector3OrNone, &direction,
        PyConverter_DoubleVector3OrNone, &perspective,
        &pseudobj)) goto _fail;

    if (pseudobj != NULL)
        pseudo = PyObject_IsTrue(pseudobj);

    result = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate matrix");
        goto _fail;
    }
    {
        double *M = (double *)PyArray_DATA(result);
        double *p = (double *)PyArray_DATA(point);
        double px = p[0];
        double py = p[1];
        double pz = p[2];
        double *n = (double *)PyArray_DATA(normal);
        double nx = n[0];
        double ny = n[1];
        double nz = n[2];
        double t = sqrt(nx*nx + ny*ny + nz*nz);
        if (t < EPSILON) {
            PyErr_Format(PyExc_ValueError, "invalid normal vector");
            goto _fail;
        }
        nx /= t;
        ny /= t;
        nz /= t;

        if (perspective) {
            /* perspective projection */
            double *d = (double *)PyArray_DATA(perspective);
            double dx = d[0];
            double dy = d[1];
            double dz = d[2];

            t = (dx-px)*nx + (dy-py)*ny + (dz-pz)*nz;
            M[0]  = t - dx*nx;
            M[5]  = t - dy*ny;
            M[10] = t - dz*nz;
            M[1] = - dx*ny;
            M[2] = - dx*nz;
            M[4] = - dy*nx;
            M[6] = - dy*nz;
            M[8] = - dz*nx;
            M[9] = - dz*ny;

            if (pseudo) {
                /* preserve relative depth */
                M[0]  -= nx*nx;
                M[5]  -= ny*ny;
                M[10] -= nz*nz;
                t = nx*ny;
                M[1] -= t;
                M[4] -= t;
                t = nx*nz;
                M[2] -= t;
                M[8] -= t;
                t = ny*nz;
                M[6] -= t;
                M[9] -= t;
                t = px*nx + py*ny + pz*nz;
                M[3]  = t * (dx+nx);
                M[7]  = t * (dy+ny);
                M[11] = t * (dz+nz);
            } else {
                t = px*nx + py*ny + pz*nz;
                M[3]  = t * dx;
                M[7]  = t * dy;
                M[11] = t * dz;
            }
            M[12] = -nx;
            M[13] = -ny;
            M[14] = -nz;
            M[15] = dx*nx + dy*ny + dz*nz;
        } else if (direction) {
            /* parallel projection */
            double *d = (double *)PyArray_DATA(direction);
            double dx = d[0];
            double dy = d[1];
            double dz = d[2];
            double scale = dx*nx + dy*ny + dz*nz;

            if (ISZERO(scale)) {
                PyErr_Format(PyExc_ValueError,
                    "normal and direction vectors are orthogonal");
                goto _fail;
            }
            scale = -1.0 / scale;
            M[0]  = 1.0 + scale * dx*nx;
            M[5]  = 1.0 + scale * dy*ny;
            M[10] = 1.0 + scale * dz*nz;
            M[1] = scale * dx*ny;
            M[2] = scale * dx*nz;
            M[4] = scale * dy*nx;
            M[6] = scale * dy*nz;
            M[8] = scale * dz*nx;
            M[9] = scale * dz*ny;
            t = (px*nx + py*ny + pz*nz) * -scale;
            M[3]  = t * dx;
            M[7]  = t * dy;
            M[11] = t * dz;
            M[12] = M[13] = M[14] = 0.0;
            M[15] = 1.0;
        } else {
            /* orthogonal projection */
            M[0]  = 1.0 - nx*nx;
            M[5]  = 1.0 - ny*ny;
            M[10] = 1.0 - nz*nz;
            M[1] = M[4] = - nx*ny;
            M[2] = M[8] = - nx*nz;
            M[6] = M[9] = - ny*nz;
            t = px*nx + py*ny + pz*nz;
            M[3]  = t * nx;
            M[7]  = t * ny;
            M[11] = t * nz;
            M[12] = M[13] = M[14] = 0.0;
            M[15] = 1.0;
        }
    }

    Py_DECREF(point);
    Py_DECREF(normal);
    Py_XDECREF(direction);
    Py_XDECREF(perspective);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(point);
    Py_XDECREF(normal);
    Py_XDECREF(direction);
    Py_XDECREF(perspective);
    Py_XDECREF(result);
    return NULL;
}

/*
Clipping matrix.
*/
char py_clip_matrix_doc[] =
    "Return matrix to obtain normalized device coordinates from frustrum.";

static PyObject *
py_clip_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *result = NULL;
    PyObject *boolobj = NULL;
    Py_ssize_t dims[] = {4, 4};
    double *M;
    double left, right, bottom, top, hither, yon;
    int perspective = 0;
    static char *kwlist[] = {"left", "right", "bottom",
                             "top", "near", "far", "perspective", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "dddddd|O", kwlist,
        &left, &right, &bottom, &top, &hither, &yon, &boolobj))
        goto _fail;

    if (boolobj != NULL)
        perspective = PyObject_IsTrue(boolobj);

    if ((left >= right) || (bottom >= top) || (hither >= yon)) {
        PyErr_Format(PyExc_ValueError, "invalid frustrum");
        goto _fail;
    }

    result = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate matrix");
        goto _fail;
    }

    M = (double *)PyArray_DATA(result);

    if (perspective) {
        double t = 2.0 * hither;
        if (hither < EPSILON) {
            PyErr_Format(PyExc_ValueError, "invalid frustrum: near <= 0");
            goto _fail;
        }
        M[1] = M[3] = M[4] = M[7] = M[8] = M[9] = M[12] = M[13] = M[15] = 0.0;
        M[14] = -1.0;
        M[0] = t / (left-right);
        M[2] = (right+left) / (right-left);
        M[5] = t / (bottom-top);
        M[6] = (top+bottom) / (top-bottom);
        M[10] = (yon+hither) / (hither-yon);
        M[11] = t*yon / (yon-hither);
    } else {
        M[1] = M[2] = M[4] = M[6] = M[8] = M[9] = M[12] = M[13] = M[14] = 0.0;
        M[15] = 1.0;
        M[0] = 2.0 / (right-left);
        M[3] = (right+left) / (left-right);
        M[5] = 2.0 / (top-bottom);
        M[7] = (top+bottom) / (bottom-top);
        M[10] = 2.0 / (yon-hither);
        M[11] = (yon+hither) / (hither-yon);
    }

    return PyArray_Return(result);

  _fail:
    Py_XDECREF(result);
    return NULL;
}

/*
Scale matrix.
*/
char py_scale_matrix_doc[] =
    "Return matrix to scale by factor around origin in direction.";

static PyObject *
py_scale_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *result = NULL;
    PyArrayObject *origin = NULL;
    PyArrayObject *direction = NULL;
    Py_ssize_t dims[] = {4, 4};
    double factor;
    static char *kwlist[] = {"factor", "origin", "direction", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "d|O&O&", kwlist,
        &factor,
        PyConverter_DoubleVector3OrNone, &origin,
        PyConverter_DoubleVector3OrNone, &direction)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate matrix");
        goto _fail;
    }
    {
        double *M = (double *)PyArray_DATA(result);
        if (direction == NULL) {
            memset(M, 0, 16*sizeof(double));
            M[0] = M[5] = M[10] = factor;
            M[15] = 1.0;
            if (origin != NULL) {
                double *p = (double *)PyArray_DATA(origin);
                factor = 1.0 - factor;
                M[3]  = factor * p[0];
                M[7]  = factor * p[1];
                M[11] = factor * p[2];
            }
        } else {
            double *d = (double *)PyArray_DATA(direction);
            double dx = d[0];
            double dy = d[1];
            double dz = d[2];
            factor = 1.0 - factor;
            M[0]  = 1.0 - factor * dx*dx;
            M[5]  = 1.0 - factor * dy*dy;
            M[10] = 1.0 - factor * dz*dz;
            factor *= -1.0;
            M[1] = M[4] = factor * dx*dy;
            M[2] = M[8] = factor * dx*dz;
            M[6] = M[9] = factor * dy*dz;
            M[12] = M[13] = M[14] = 0.0;
            M[15] = 1.0;
            if (origin != NULL) {
                double *p = (double *)PyArray_DATA(origin);
                factor *= - (p[0]*dx + p[1]*dy + p[2]*dz);
                M[3]  = factor * dx;
                M[7]  = factor * dy;
                M[11] = factor * dz;
            } else {
                M[3] = M[7] = M[11] = 0.0;
            }
        }
    }

    Py_XDECREF(origin);
    Py_XDECREF(direction);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(origin);
    Py_XDECREF(direction);
    Py_XDECREF(result);
    return NULL;
}

/*
Shearing matrix.
*/
char py_shear_matrix_doc[] =
    "Return matrix to shear by angle along direction vector on shear plane.";

static PyObject *
py_shear_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *result = NULL;
    PyArrayObject *direction = NULL;
    PyArrayObject *point = NULL;
    PyArrayObject *normal = NULL;
    Py_ssize_t dims[] = {4, 4};
    double angle;
    static char *kwlist[] = {"angle", "direction", "point", "normal", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "dO&O&O&", kwlist,
        &angle,
        PyConverter_DoubleVector3, &direction,
        PyConverter_DoubleVector3, &point,
        PyConverter_DoubleVector3, &normal)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate matrix");
        goto _fail;
    }
    {
        double *M = (double *)PyArray_DATA(result);
        double *p = (double *)PyArray_DATA(point);
        double *d = (double *)PyArray_DATA(direction);
        double dx = d[0];
        double dy = d[1];
        double dz = d[2];
        double *n = (double *)PyArray_DATA(normal);
        double nx = n[0];
        double ny = n[1];
        double nz = n[2];
        double t;

        t = sqrt(dx*dx + dy*dy + dz*dz);
        if (t < EPSILON) {
            PyErr_Format(PyExc_ValueError, "invalid direction vector");
            goto _fail;
        }
        dx /= t;
        dy /= t;
        dz /= t;

        t = sqrt(nx*nx + ny*ny + nz*nz);
        if (t < EPSILON) {
            PyErr_Format(PyExc_ValueError, "invalid normal vector");
            goto _fail;
        }
        nx /= t;
        ny /= t;
        nz /= t;

        if (fabs(nx*dx + ny*dy + nz*dz) > 1e-6) {
            PyErr_Format(PyExc_ValueError,
                "direction and normal vectors are not orthogonal");
            goto _fail;
        }

        angle = tan(angle);

        M[0]  = 1.0 + angle * dx*nx;
        M[5]  = 1.0 + angle * dy*ny;
        M[10] = 1.0 + angle * dz*nz;
        M[1] = angle * dx*ny;
        M[2] = angle * dx*nz;
        M[4] = angle * dy*nx;
        M[6] = angle * dy*nz;
        M[8] = angle * dz*nx;
        M[9] = angle * dz*ny;
        M[12] = M[13] = M[14] = 0.0;
        M[15] = 1.0;

        t = -angle * (p[0]*nx + p[1]*ny + p[2]*nz);
        M[3]  = t * dx;
        M[7]  = t * dy;
        M[11] = t * dz;
    }

    Py_DECREF(direction);
    Py_DECREF(point);
    Py_DECREF(normal);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(direction);
    Py_XDECREF(point);
    Py_XDECREF(normal);
    Py_XDECREF(result);
    return NULL;
}

/*
Superimposition matrix.
*/
char py_superimposition_matrix_doc[] =
    "Return matrix to transform given vector set into second vector set.";

static PyObject *
py_superimposition_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyThreadState *_save = NULL;
    PyArrayObject *result = NULL;
    PyArrayObject *v0 = NULL;
    PyArrayObject *v1 = NULL;
    PyObject *usesvdobj = NULL;
    PyObject *scalingobj = NULL;
    double *buffer = NULL;
    Py_ssize_t dims[] = {4, 4};
    int scaling = 0;

    static char *kwlist[] = {"v0", "v1", "scaling", "usesvd", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&O&|OO", kwlist,
        PyConverter_AnyDoubleArray, &v0,
        PyConverter_AnyDoubleArray, &v1,
        &scalingobj, &usesvdobj)) goto _fail;

    if (scalingobj != NULL)
        scaling = PyObject_IsTrue(scalingobj);

    if (!PyArray_SAMESHAPE(v0, v1)) {
        PyErr_Format(PyExc_ValueError, "shape of vector sets must match");
        goto _fail;
    }

    if ((PyArray_NDIM(v0) != 2) || PyArray_DIM(v0, 0) < 3) {
        PyErr_Format(PyExc_ValueError,
            "vector sets are of wrong shape or type");
        goto _fail;
    }

    result = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate matrix");
        goto _fail;
    }

    buffer = (double *)PyMem_Malloc(42 * sizeof(double));
    if (!buffer) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate buffer");
        goto _fail;
    }
    {
        Py_ssize_t i, j;
        double v0t[3], v1t[3];
        double *q = buffer;
        double *N = (buffer + 4);
        double *M = (double *)PyArray_DATA(result);

        Py_ssize_t size = PyArray_DIM(v0, 1);
        Py_ssize_t v0s0 = PyArray_STRIDE(v0, 0);
        Py_ssize_t v0s1 = PyArray_STRIDE(v0, 1);
        Py_ssize_t v1s0 = PyArray_STRIDE(v1, 0);
        Py_ssize_t v1s1 = PyArray_STRIDE(v1, 1);

        /* displacements of v0 & v1 centroids from origin */
        {
            double t;
            if (v0s1 == sizeof(double)) {
                double *p;
                for (j = 0; j < 3; j++) {
                    t = 0.0;
                    p = (double*)((char *)PyArray_DATA(v0) + j*v0s0);
                    for (i = 0; i < size; i++) {
                        t += p[i];
                    }
                    v0t[j] = t / (double)size;
                }
            } else {
                char *p;
                for (j = 0; j < 3; j++) {
                    t = 0.0;
                    p = (char *)PyArray_DATA(v0) + j*v0s0;
                    for (i = 0; i < size; i++) {
                        t += *(double*)p;
                        p += v0s1;
                    }
                    v0t[j] = t / (double)size;
                }
            }
            if (v1s1 == sizeof(double)) {
                double *p;
                for (j = 0; j < 3; j++) {
                    t = 0.0;
                    p = (double*)((char *)PyArray_DATA(v1) + j*v1s0);
                    for (i = 0; i < size; i++) {
                        t += p[i];
                    }
                    v1t[j] = t / (double)size;
                }
            } else {
                char *p;
                for (j = 0; j < 3; j++) {
                    t = 0.0;
                    p = (char *)PyArray_DATA(v1) + j*v1s0;
                    for (i = 0; i < size; i++) {
                        t += *(double*)p;
                        p += v1s1;
                    }
                    v1t[j] = t / (double)size;
                }
            }
        }
        /* symmetric matrix N */
        {
            double xx, yy, zz, xy, yz, zx, xz, yx, zy;
            xx = yy = zz = xy = yz = zx = xz = yx = zy = 0.0;

            if ((v0s1 == sizeof(double)) && (v1s1 == sizeof(double))) {
                double t, v0x, v0y, v0z;
                double *v0px = (double *)PyArray_DATA(v0);
                double *v0py = (double *)((char *)PyArray_DATA(v0) + v0s0);
                double *v0pz = (double *)((char *)PyArray_DATA(v0) + v0s0*2);
                double *v1px = (double *)PyArray_DATA(v1);
                double *v1py = (double *)((char *)PyArray_DATA(v1) + v1s0);
                double *v1pz = (double *)((char *)PyArray_DATA(v1) + v1s0*2);

                #pragma vector always
                for (i = 0; i < size; i++) {
                    v0x = v0px[i] - v0t[0];
                    v0y = v0py[i] - v0t[1];
                    v0z = v0pz[i] - v0t[2];

                    t = v1px[i] - v1t[0];
                    xx += v0x * t;
                    yx += v0y * t;
                    zx += v0z * t;
                    t = v1py[i] - v1t[1];
                    xy += v0x * t;
                    yy += v0y * t;
                    zy += v0z * t;
                    t = v1pz[i] - v1t[2];
                    xz += v0x * t;
                    yz += v0y * t;
                    zz += v0z * t;
                }
            } else {
                double t, v1x, v1y, v1z;
                char *v0p = PyArray_DATA(v0);
                char *v1p = PyArray_DATA(v1);

                for (i = 0; i < size; i++) {
                    v1x = (*(double*)(v1p)) - v1t[0];
                    v1y = (*(double*)(v1p + v1s0)) - v1t[1];
                    v1z = (*(double*)(v1p + v1s0 + v1s0)) - v1t[2];

                    t = (*(double*)(v0p)) - v0t[0];
                    xx += t * v1x;
                    xy += t * v1y;
                    xz += t * v1z;
                    t = (*(double*)(v0p + v0s0)) - v0t[1];
                    yx += t * v1x;
                    yy += t * v1y;
                    yz += t * v1z;
                    t = (*(double*)(v0p + v0s0 + v0s0)) - v0t[2];
                    zx += t * v1x;
                    zy += t * v1y;
                    zz += t * v1z;

                    v0p += v0s1;
                    v1p += v1s1;
                }
            }

            _save = PyEval_SaveThread();

            N[0]  =  xx + yy + zz;
            N[5]  =  xx - yy - zz;
            N[10] = -xx + yy - zz;
            N[15] = -xx - yy + zz;
            N[1]  = N[4]  = yz - zy;
            N[2]  = N[8]  = zx - xz;
            N[3]  = N[12] = xy - yx;
            N[6]  = N[9]  = xy + yx;
            N[7]  = N[13] = zx + xz;
            N[11] = N[14] = yz + zy;
        }
        /* quaternion q: eigenvector corresponding to most positive */
        /* eigenvalue of N. */
        {
            double l;
            double *a = (buffer + 20);
            double *b = (buffer + 24);
            double *t = (buffer + 27);

            for (i = 0; i < 16; i++)
                M[i] = N[i];

            if (tridiagonalize_symmetric_44(M, a, b) != 0) {
                PyEval_RestoreThread(_save);
                PyErr_Format(PyExc_ValueError,
                    "tridiagonalize_symmetric_44() failed");
                goto _fail;
            }

            l = max_eigenvalue_of_tridiag_44(a, b);
            N[0] -= l;
            N[5] -= l;
            N[10] -= l;
            N[15] -= l;

            if (eigenvector_of_symmetric_44(N, q, t) != 0) {
                PyEval_RestoreThread(_save);
                PyErr_Format(PyExc_ValueError,
                    "eigenvector_of_symmetric_44() failed");
                goto _fail;
            }

            l = q[3];
            q[3] = q[2];
            q[2] = q[1];
            q[1] = q[0];
            q[0] = l;
        }

        if (quaternion_matrix(q, M) != 0) {
            PyEval_RestoreThread(_save);
            PyErr_Format(PyExc_ValueError, "quaternion_matrix() failed");
            goto _fail;
        }

        PyEval_RestoreThread(_save);

        if (scaling) {
            /* scaling factor = sqrt(sum(v1) / sum(v0) */
            double t, dt;
            double v0s = 0.0;
            double v1s = 0.0;

            if (v0s1 == sizeof(double)) {
                double *p;
                for (j = 0; j < 3; j++) {
                    p = (double*)((char *)PyArray_DATA(v0) + j*v0s0);
                    dt = v0t[j];
                    #pragma vector always
                    for (i = 0; i < size; i++) {
                        t = p[i] - dt;
                        v0s += t*t;
                    }
                }
            } else {
                char *p;
                for (j = 0; j < 3; j++) {
                    p = (char *)PyArray_DATA(v0) + j*v0s0;
                    dt = v0t[j];
                    for (i = 0; i < size; i++) {
                        t = (*(double*)p) - dt;
                        v0s += t*t;
                        p += v0s1;
                    }
                }
            }

            if (v1s1 == sizeof(double)) {
                double *p;
                for (j = 0; j < 3; j++) {
                    p = (double*)((char *)PyArray_DATA(v1) + j*v1s0);
                    dt = v1t[j];
                    #pragma vector always
                    for (i = 0; i < size; i++) {
                        t = p[i] - dt;
                        v1s += t*t;
                    }
                }
            } else {
                char *p;
                for (j = 0; j < 3; j++) {
                    p = (char *)PyArray_DATA(v1) + j*v1s0;
                    dt = v1t[j];
                    for (i = 0; i < size; i++) {
                        t = (*(double*)p) - dt;
                        v1s += t*t;
                        p += v1s1;
                    }
                }
            }

            t = sqrt(v1s / v0s);
            M[0] *= t;
            M[1] *= t;
            M[2] *= t;
            M[4] *= t;
            M[5] *= t;
            M[6] *= t;
            M[8] *= t;
            M[9] *= t;
            M[10] *= t;
        }

        /* translation */
        M[3]  = v1t[0] - M[0]*v0t[0] - M[1]*v0t[1] - M[2]*v0t[2];
        M[7]  = v1t[1] - M[4]*v0t[0] - M[5]*v0t[1] - M[6]*v0t[2];
        M[11] = v1t[2] - M[8]*v0t[0] - M[9]*v0t[1] - M[10]*v0t[2];
    }

    PyMem_Free(buffer);
    Py_DECREF(v0);
    Py_DECREF(v1);
    return PyArray_Return(result);

  _fail:
    PyMem_Free(buffer);
    Py_XDECREF(v0);
    Py_XDECREF(v1);
    Py_XDECREF(result);
    return NULL;
}

/*
Orthogonalization matrix.
*/
char py_orthogonalization_matrix_doc[] =
    "Return orthogonalization matrix for crystallographic cell coordinates.";

static PyObject *
py_orthogonalization_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *result = NULL;
    PyArrayObject *lengths = NULL;
    PyArrayObject *angles = NULL;
    Py_ssize_t dims[] = {4, 4};
    static char *kwlist[] = {"lengths", "angles", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&O&", kwlist,
        PyConverter_DoubleVector3, &lengths,
        PyConverter_DoubleVector3, &angles)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate matrix");
        goto _fail;
    }
    {
        double *M = (double *)PyArray_DATA(result);
        double *a = (double *)PyArray_DATA(angles);
        double *l = (double *)PyArray_DATA(lengths);
        double la = l[0];
        double lb = l[1];
        double sa = sin(a[0] * DEG2RAD);
        double ca = cos(a[0] * DEG2RAD);
        double sb = sin(a[1] * DEG2RAD);
        double cb = cos(a[1] * DEG2RAD);
        double cg = cos(a[2] * DEG2RAD);
        double t = ca * cb - cg;

        if ((fabs(sa*sb) < EPSILON) || (fabs(t-sa*sb) < EPSILON)) {
            PyErr_Format(PyExc_ValueError, "invalid cell geometry");
            goto _fail;
        }
        t /= (sa * sb);
        M[15] = 1.0;
        M[1] = M[2] = M[3] = M[6] = M[7] = M[11] = M[12] = M[13] = M[14] = 0.0;
        M[0] = la * sb * sqrt(1.0-t*t);
        M[4] = -la * sb * t;
        M[5] = lb * sa;
        M[8] = la * cb;
        M[9] = lb * ca;
        M[10] = l[2];
    }

    Py_DECREF(lengths);
    Py_DECREF(angles);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(lengths);
    Py_XDECREF(angles);
    Py_XDECREF(result);
    return NULL;
}

/*
Map Euler axes strings and tuples to inner axis, parity, repetition, and frame.
*/
static int axis2tuple(
    PyObject *axes,
    int *firstaxis,
    int *parity,
    int *repetition,
    int *frame
)
{
    *firstaxis = 0; *parity = 0; *repetition = 0; *frame = 0;
    if (axes == NULL)
        return 0;

    /* axes strings */
#if PY_MAJOR_VERSION < 3
    if (PyString_Check(axes) && (PyString_Size(axes) == 4)) {
        char *s = PyString_AS_STRING(axes);
#else
    if (PyUnicode_Check(axes) && (PyUnicode_GetSize(axes) == 4)) {
        char *s = PyBytes_AsString(PyUnicode_AsASCIIString(axes));
#endif
        int hash = *((int *)s);
        switch (hash)
        {
        case 2054781043:
        case 1937275258: /* sxyz */
            *firstaxis = 0; *parity = 0; *repetition = 0; *frame = 0; break;
        case 2054781042:
        case 1920498042: /* rxyz */
            *firstaxis = 2; *parity = 1; *repetition = 0; *frame = 1; break;
        case 2037938802:
        case 1920628857: /* rzxy */
            *firstaxis = 1; *parity = 1; *repetition = 0; *frame = 1; break;
        case 2054716018:
        case 1920628858: /* rzxz */
            *firstaxis = 2; *parity = 0; *repetition = 1; *frame = 1; break;
        case 2054716019:
        case 1937406074: /* szxz */
            *firstaxis = 2; *parity = 0; *repetition = 1; *frame = 0; break;
        case 2037938803:
        case 1937406073: /* szxy */
            *firstaxis = 2; *parity = 0; *repetition = 0; *frame = 0; break;
        case 2038069618:
        case 1920563833: /* ryzy */
            *firstaxis = 1; *parity = 0; *repetition = 1; *frame = 1; break;
        case 2021292402:
        case 1920563832: /* ryzx */
            *firstaxis = 0; *parity = 1; *repetition = 0; *frame = 1; break;
        case 2054715762:
        case 1920563322: /* ryxz */
            *firstaxis = 2; *parity = 0; *repetition = 0; *frame = 1; break;
        case 2037938546:
        case 1920563321: /* ryxy */
            *firstaxis = 1; *parity = 1; *repetition = 1; *frame = 1; break;
        case 2021292146:
        case 1920498296: /* rxzx */
            *firstaxis = 0; *parity = 1; *repetition = 1; *frame = 1; break;
        case 2038069362:
        case 1920498297: /* rxzy */
            *firstaxis = 1; *parity = 0; *repetition = 0; *frame = 1; break;
        case 2021226611:
        case 1937275256: /* sxyx */
            *firstaxis = 0; *parity = 0; *repetition = 1; *frame = 0; break;
        case 2038069363:
        case 1937275513: /* sxzy */
            *firstaxis = 0; *parity = 1; *repetition = 0; *frame = 0; break;
        case 2054781554:
        case 1920629114: /* rzyz */
            *firstaxis = 2; *parity = 1; *repetition = 1; *frame = 1; break;
        case 2021227122:
        case 1920629112: /* rzyx */
            *firstaxis = 0; *parity = 0; *repetition = 0; *frame = 1; break;
        case 2021227123:
        case 1937406328: /* szyx */
            *firstaxis = 2; *parity = 1; *repetition = 0; *frame = 0; break;
        case 2054781555:
        case 1937406330: /* szyz */
            *firstaxis = 2; *parity = 1; *repetition = 1; *frame = 0; break;
        case 2021226610:
        case 1920498040: /* rxyx */
            *firstaxis = 0; *parity = 0; *repetition = 1; *frame = 1; break;
        case 2021292403:
        case 1937341048: /* syzx */
            *firstaxis = 1; *parity = 0; *repetition = 0; *frame = 0; break;
        case 2038069619:
        case 1937341049: /* syzy */
            *firstaxis = 1; *parity = 0; *repetition = 1; *frame = 0; break;
        case 2037938547:
        case 1937340537: /* syxy */
            *firstaxis = 1; *parity = 1; *repetition = 1; *frame = 0; break;
        case 2054715763:
        case 1937340538: /* syxz */
            *firstaxis = 1; *parity = 1; *repetition = 0; *frame = 0; break;
        case 2021292147:
        case 1937275512: /* sxzx */
            *firstaxis = 0; *parity = 1; *repetition = 1; *frame = 0; break;
        default:
            PyErr_Format(PyExc_ValueError, "invalid axes string");
            return -1;
        }
        return 0;
    }

    if (PySequence_Check(axes) && (PySequence_Size(axes) == 4)) {
        /* axes tuples */
        *firstaxis = (int)PySequence_GetInteger(axes, 0);
        *parity = (int)PySequence_GetInteger(axes, 1);
        *repetition = (int)PySequence_GetInteger(axes, 2);
        *frame = (int)PySequence_GetInteger(axes, 3);
        if (((*firstaxis != 0) && (*firstaxis != 1) && (*firstaxis != 2)) ||
            ((*parity != 0) && (*parity != 1)) ||
            ((*repetition != 0) && (*repetition != 1)) ||
            ((*frame != 0) && (*frame != 1))) {
            PyErr_Format(PyExc_ValueError, "invalid axes sequence");
            return -1;
        }
        return 0;
    }

    PyErr_Format(PyExc_ValueError, "invalid axes type or shape");
    return -1;
}

/*
Matrix from Euler angles.
*/
char py_euler_matrix_doc[] =
    "Return homogeneous rotation matrix from Euler angles and axis sequence.";

static PyObject *
py_euler_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *result = NULL;
    PyObject *axes = NULL;
    Py_ssize_t dims[] = {4, 4};
    int next_axis[] = {1, 2, 0, 1};
    double ai, aj, ak;
    int firstaxis = 0;
    int parity = 0;
    int repetition = 0;
    int frame = 0;
    static char *kwlist[] = {"ai", "aj", "ak", "axes", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ddd|O", kwlist,
        &ai, &aj, &ak, &axes)) goto _fail;

    if (axes != NULL) Py_INCREF(axes);

    result = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate matrix");
        goto _fail;
    }

    if (axis2tuple(axes, &firstaxis, &parity, &repetition, &frame) != 0)
        goto _fail;
    Py_XDECREF(axes);

    {
        double *M = (double *)PyArray_DATA(result);
        int i = firstaxis;
        int j = next_axis[i+parity];
        int k = next_axis[i-parity+1];
        double t;
        double si, sj, sk, ci, cj, ck, cc, cs, sc, ss;

        if (frame) {
            t = ai;
            ai = ak;
            ak = t;
        }

        if (parity) {
            ai = -ai;
            aj = -aj;
            ak = -ak;
        }

        si = sin(ai);
        sj = sin(aj);
        sk = sin(ak);
        ci = cos(ai);
        cj = cos(aj);
        ck = cos(ak);
        cc = ci*ck;
        cs = ci*sk;
        sc = si*ck;
        ss = si*sk;

        if (repetition) {
            M[4*i+i] = cj;
            M[4*i+j] = sj*si;
            M[4*i+k] = sj*ci;
            M[4*j+i] = sj*sk;
            M[4*j+j] = -cj*ss+cc;
            M[4*j+k] = -cj*cs-sc;
            M[4*k+i] = -sj*ck;
            M[4*k+j] = cj*sc+cs;
            M[4*k+k] = cj*cc-ss;
        } else {
            M[4*i+i] = cj*ck;
            M[4*i+j] = sj*sc-cs;
            M[4*i+k] = sj*cc+ss;
            M[4*j+i] = cj*sk;
            M[4*j+j] = sj*ss+cc;
            M[4*j+k] = sj*cs-sc;
            M[4*k+i] = -sj;
            M[4*k+j] = cj*si;
            M[4*k+k] = cj*ci;
        }

        M[3] = M[7] = M[11] = M[12] = M[13] = M[14] = 0.0;
        M[15] = 1.0;
    }

    return PyArray_Return(result);

  _fail:
    Py_XDECREF(axes);
    Py_XDECREF(result);
    return NULL;
}

/*
Euler angles from matrix.
*/
char py_euler_from_matrix_doc[] =
    "Return Euler angles from rotation matrix for specified axis sequence.";

static PyObject *
py_euler_from_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *matrix = NULL;
    PyObject *axes = NULL;
    int next_axis[] = {1, 2, 0, 1};
    double ai = 0.0;
    double aj = 0.0;
    double ak = 0.0;
    int firstaxis = 0;
    int parity = 0;
    int repetition = 0;
    int frame = 0;
    static char *kwlist[] = {"matrix", "axes", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&|O", kwlist,
        PyConverter_DoubleMatrix44, &matrix, &axes)) goto _fail;

    if (axes != NULL)
        Py_INCREF(axes);

    if (axis2tuple(axes, &firstaxis, &parity, &repetition, &frame) != 0)
        goto _fail;

    {
        double *M = (double *)PyArray_DATA(matrix);
        int i = firstaxis;
        int j = next_axis[i+parity];
        int k = next_axis[i-parity+1];
        double x, y, t;

        if (repetition) {
            x = M[4*i+j];
            y = M[4*i+k];
            t = sqrt(x*x + y*y);
            if (t > EPSILON) {
                ai = atan2( M[4*i+j],  M[4*i+k]);
                aj = atan2( t,         M[4*i+i]);
                ak = atan2( M[4*j+i], -M[4*k+i]);
            } else {
                ai = atan2(-M[4*j+k],  M[4*j+j]);
                ai = atan2( t,         M[4*i+i]);
            }
        } else {
            x = M[4*i+i];
            y = M[4*j+i];
            t = sqrt(x*x + y*y);
            if (t > EPSILON) {
                ai = atan2( M[4*k+j],  M[4*k+k]);
                aj = atan2(-M[4*k+i],  t);
                ak = atan2( M[4*j+i],  M[4*i+i]);
            } else {
                ai = atan2(-M[4*j+k],  M[4*j+j]);
                ai = atan2(-M[4*k+i],  t);
            }
        }
        if (parity) {
            ai = -ai;
            aj = -aj;
            ak = -ak;
        }
        if (frame) {
            t = ai;
            ai = ak;
            ak = t;
        }
    }

    Py_XDECREF(axes);
    Py_DECREF(matrix);
    return Py_BuildValue("(d,d,d)", ai, aj, ak);

  _fail:
    Py_XDECREF(axes);
    Py_XDECREF(matrix);
    return NULL;
}

/*
Quaternion from Euler angles.
*/
char py_quaternion_from_euler_doc[] =
    "Return quaternion from Euler angles and axis sequence.";

static PyObject *
py_quaternion_from_euler(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *result = NULL;
    PyObject *axes = NULL;
    Py_ssize_t dims = 4;
    int next_axis[] = {1, 2, 0, 1};
    double ai, aj, ak;
    int firstaxis = 0;
    int parity = 0;
    int repetition = 0;
    int frame = 0;
    static char *kwlist[] = {"ai", "aj", "ak", "axes", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ddd|O", kwlist,
        &ai, &aj, &ak, &axes)) goto _fail;

    if (axes != NULL)
        Py_INCREF(axes);

    result = (PyArrayObject*)PyArray_SimpleNew(1, &dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate quaternion");
        goto _fail;
    }

    if (axis2tuple(axes, &firstaxis, &parity, &repetition, &frame) != 0)
        goto _fail;

    {
        double *q = (double *)PyArray_DATA(result);
        int i = firstaxis + 1;
        int j = next_axis[i+parity-1] + 1;
        int k = next_axis[i-parity] + 1;
        double t;
        double si, sj, sk, ci, cj, ck, cc, cs, sc, ss;

        if (frame) {
            t = ai;
            ai = ak;
            ak = t;
        }

        if (parity) {
            aj = -aj;
        }

        ai /= 2.0;
        aj /= 2.0;
        ak /= 2.0;

        si = sin(ai);
        sj = sin(aj);
        sk = sin(ak);
        ci = cos(ai);
        cj = cos(aj);
        ck = cos(ak);
        cc = ci*ck;
        cs = ci*sk;
        sc = si*ck;
        ss = si*sk;

        if (repetition) {
            q[i] = cj*(cs + sc);
            q[k] = sj*(cs - sc);
            q[j] = sj*(cc + ss);
            q[0] = cj*(cc - ss);
        } else {
            q[i] = cj*sc - sj*cs;
            q[k] = cj*cs - sj*sc;
            q[j] = cj*ss + sj*cc;
            q[0] = cj*cc + sj*ss;
        }

        if (parity) {
            q[j] *= -1.0;
        }
    }

    Py_XDECREF(axes);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(axes);
    Py_XDECREF(result);
    return NULL;
}

/*
Quaternion about axis.
*/
char py_quaternion_about_axis_doc[] =
    "Return quaternion for rotation about axis.";

static PyObject *
py_quaternion_about_axis(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *axis = NULL;
    PyArrayObject *result = NULL;
    double angle;
    Py_ssize_t dims = 4;
    static char *kwlist[] = {"angle", "axis", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "dO&", kwlist,
        &angle,
        PyConverter_DoubleVector3, &axis)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(1, &dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate quaternion");
        goto _fail;
    }
    {
        double *q = (double *)PyArray_DATA(result);
        double *a = (double *)PyArray_DATA(axis);
        double t = sqrt(a[0]*a[0] + a[1]*a[1] + a[2]*a[2]);

        if (t > EPSILON) {
            t = sin(angle / 2.0) / t;
            q[1] = a[0] * t;
            q[2] = a[1] * t;
            q[3] = a[2] * t;
        } else {
            q[1] = a[0];
            q[2] = a[1];
            q[3] = a[2];
        }
        q[0] = cos(angle / 2.0);
    }

    Py_DECREF(axis);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(result);
    Py_XDECREF(axis);
    return NULL;
}

/*
Quaternion from rotation matrix.
*/
char py_quaternion_from_matrix_doc[] =
    "Return quaternion from rotation matrix.";

static PyObject *
py_quaternion_from_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyThreadState *_save = NULL;
    PyArrayObject *matrix = NULL;
    PyArrayObject *result = NULL;
    PyObject *boolobj = NULL;
    Py_ssize_t dims = 4;
    static char *kwlist[] = {"matrix", "isprecise", NULL};
    double *buffer = NULL;
    int isprecise = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&|O", kwlist,
        PyConverter_DoubleMatrix44, &matrix, &boolobj)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(1, &dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate quaternion");
        goto _fail;
    }

    if (boolobj != NULL)
        isprecise = PyObject_IsTrue(boolobj);

    if (isprecise) {
        /* precise rotation matrix */
        double *q = (double *)PyArray_DATA(result);
        double *M = (double *)PyArray_DATA(matrix);
        if (quaternion_from_matrix(M, q) != 0) {
            PyEval_RestoreThread(_save);
            PyErr_Format(PyExc_ValueError,
                "quaternion_from_matrix() failed");
            goto _fail;
        }
    } else {
        double *q = (double *)PyArray_DATA(result);
        double *M = (double *)PyArray_DATA(matrix);
        double *K, *N, *a, *b, *t;
        double l;
        int i;

        buffer = (double *)PyMem_Malloc(52 * sizeof(double));
        if (!buffer) {
            PyErr_Format(PyExc_MemoryError, "unable to allocate buffer");
            goto _fail;
        }
        K = buffer;
        N = (buffer + 16);
        a = (buffer + 32);
        b = (buffer + 36);
        t = (buffer + 40);

        /* symmetric matrix K */
        K[0] = (M[0] - M[5] - M[10]) / 3.0;
        K[5] = (M[5] - M[0] - M[10]) / 3.0;
        K[10] = (M[10] - M[0] - M[5]) / 3.0;
        K[15] = (M[0] + M[5] + M[10]) / 3.0;
        K[1] = K[4] = (M[4] + M[1]) / 3.0;
        K[2] = K[8] = (M[8] + M[2]) / 3.0;
        K[3] = K[12] = (M[9] - M[6]) / 3.0;
        K[6] = K[9] = (M[9] + M[6]) / 3.0;
        K[7] = K[13] = (M[2] - M[8]) / 3.0;
        K[11] = K[14] = (M[4] - M[1]) / 3.0;

        _save = PyEval_SaveThread();

        /* quaternion q: eigenvector corresponding to most positive */
        /* eigenvalue of K. */
        for (i = 0; i < 16; i++) {
            N[i] = K[i];
        }

        if (tridiagonalize_symmetric_44(N, a, b) != 0) {
            PyEval_RestoreThread(_save);
            PyErr_Format(PyExc_ValueError,
                "tridiagonalize_symmetric_44() failed");
            goto _fail;
        }

        l = max_eigenvalue_of_tridiag_44(a, b);
        K[0] -= l;
        K[5] -= l;
        K[10] -= l;
        K[15] -= l;

        if (eigenvector_of_symmetric_44(K, q, t) != 0) {
            PyEval_RestoreThread(_save);
            PyErr_Format(PyExc_ValueError,
                "eigenvector_of_symmetric_44() failed");
            goto _fail;
        }

        l = q[0];
        q[0] = q[2];
        q[2] = l;
        l = q[1];
        q[1] = q[3];
        q[3] = l;

        if (q[0] < 0.0) {
            q[0] = -q[0];
            q[1] = -q[1];
            q[2] = -q[2];
            q[3] = -q[3];
        }
        PyEval_RestoreThread(_save);
    }

    PyMem_Free(buffer);
    Py_DECREF(matrix);
    return PyArray_Return(result);

  _fail:
    PyMem_Free(buffer);
    Py_XDECREF(result);
    Py_XDECREF(matrix);
    return NULL;
}

/*
Rotation matrix from quaternion.
*/
char py_quaternion_matrix_doc[] =
    "Return rotation matrix from quaternion.";

static PyObject *
py_quaternion_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *quaternion = NULL;
    PyArrayObject *result = NULL;
    Py_ssize_t dims[] = {4, 4};
    static char *kwlist[] = {"quaternion" , NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&", kwlist,
        PyConverter_DoubleVector4, &quaternion)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate matrix");
        goto _fail;
    }

    if (quaternion_matrix((double *)PyArray_DATA(quaternion),
                          (double *)PyArray_DATA(result)) != 0) {
        PyErr_Format(PyExc_ValueError, "quaternion_matrix failed");
        goto _fail;
    }

    Py_DECREF(quaternion);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(result);
    Py_XDECREF(quaternion);
    return NULL;
}

/*
Multiply two quaternions.
*/
char py_quaternion_multiply_doc[] = "Multiply two quaternions.";

static PyObject *
py_quaternion_multiply(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *quaternion0 = NULL;
    PyArrayObject *quaternion1 = NULL;
    PyArrayObject *result = NULL;
    Py_ssize_t dims = 4;
    static char *kwlist[] = {"quaternion1", "quaternion0", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&O&", kwlist,
        PyConverter_DoubleVector4, &quaternion1,
        PyConverter_DoubleVector4, &quaternion0)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(1, &dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate quaternion");
        goto _fail;
    }
    {
        double *q0 = (double *)PyArray_DATA(quaternion0);
        double *q1 = (double *)PyArray_DATA(quaternion1);
        double *qq = (double *)PyArray_DATA(result);
        qq[0] = -q1[1]*q0[1] - q1[2]*q0[2] - q1[3]*q0[3] + q1[0]*q0[0];
        qq[1] =  q1[1]*q0[0] + q1[2]*q0[3] - q1[3]*q0[2] + q1[0]*q0[1];
        qq[2] = -q1[1]*q0[3] + q1[2]*q0[0] + q1[3]*q0[1] + q1[0]*q0[2];
        qq[3] =  q1[1]*q0[2] - q1[2]*q0[1] + q1[3]*q0[0] + q1[0]*q0[3];
    }

    Py_DECREF(quaternion0);
    Py_DECREF(quaternion1);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(result);
    Py_XDECREF(quaternion0);
    Py_XDECREF(quaternion1);
    return NULL;
}

/*
Quaternion conjugate.
*/
char py_quaternion_conjugate_doc[] = "Return conjugate of quaternion.";

static PyObject *
py_quaternion_conjugate(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *quaternion = NULL;
    PyArrayObject *result = NULL;
    Py_ssize_t dims = 4;
    static char *kwlist[] = {"quaternion", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&", kwlist,
        PyConverter_DoubleVector4, &quaternion)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(1, &dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate quaternion");
        goto _fail;
    }
    {
        double *q0 = (double *)PyArray_DATA(quaternion);
        double *q1 = (double *)PyArray_DATA(result);
        q1[0] =  q0[0];
        q1[1] = -q0[1];
        q1[2] = -q0[2];
        q1[3] = -q0[3];
    }

    Py_DECREF(quaternion);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(result);
    Py_XDECREF(quaternion);
    return NULL;
}

/*
Quaternion inverse.
*/
char py_quaternion_inverse_doc[] = "Return inverse of quaternion.";

static PyObject *
py_quaternion_inverse(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *quaternion = NULL;
    PyArrayObject *result = NULL;
    Py_ssize_t dims = 4;
    static char *kwlist[] = {"quaternion", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&", kwlist,
        PyConverter_DoubleVector4, &quaternion)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(1, &dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate quaternion");
        goto _fail;
    }
    {
        double *r = (double *)PyArray_DATA(result);
        double *q = (double *)PyArray_DATA(quaternion);
        double n = q[0]*q[0] + q[1]*q[1] + q[2]*q[2] + q[3]*q[3];

        if (n < EPSILON) {
            PyErr_Format(PyExc_ValueError, "not a valid quaternion");
            goto _fail;
        }

        r[0] =  q[0] / n;
        r[1] = -q[1] / n;
        r[2] = -q[2] / n;
        r[3] = -q[3] / n;
    }

    Py_DECREF(quaternion);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(result);
    Py_XDECREF(quaternion);
    return NULL;
}

/*
Quaternion spherical linear interpolation.
*/
char py_quaternion_slerp_doc[] =
    "Return spherical linear interpolation between two quaternions.";

static PyObject *
py_quaternion_slerp(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyObject *boolobj = NULL;
    PyArrayObject *quaternion0 = NULL;
    PyArrayObject *quaternion1 = NULL;
    PyArrayObject *result = NULL;
    Py_ssize_t dims = 4;
    int shortestpath = 1;
    int spin = 0;
    double fraction = 0.0;
    static char *kwlist[] = {"quat0", "quat1", "fraction",
                             "spin", "shortestpath", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&O&d|iO", kwlist,
        PyConverter_DoubleVector4, &quaternion0,
        PyConverter_DoubleVector4, &quaternion1,
        &fraction, &spin, &boolobj)) goto _fail;

    if (boolobj != NULL)
        shortestpath = PyObject_IsTrue(boolobj);

    result = (PyArrayObject*)PyArray_SimpleNew(1, &dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate quaternion");
        goto _fail;
    }
    {
        double *q = (double *)PyArray_DATA(result);
        double *q0 = (double *)PyArray_DATA(quaternion0);
        double *q1 = (double *)PyArray_DATA(quaternion1);
        double n;

        n = sqrt(q0[0]*q0[0] + q0[1]*q0[1] + q0[2]*q0[2] + q0[3]*q0[3]);
        if (n < EPSILON) {
            PyErr_Format(PyExc_ValueError, "quaternion0 not valid");
            goto _fail;
        }
        q[0] = q0[0] / n;
        q[1] = q0[1] / n;
        q[2] = q0[2] / n;
        q[3] = q0[3] / n;

        n = sqrt(q1[0]*q1[0] + q1[1]*q1[1] + q1[2]*q1[2] + q1[3]*q1[3]);
        if (n < EPSILON) {
            PyErr_Format(PyExc_ValueError, "quaternion1 not valid");
            goto _fail;
        }

        if (fabs(fabs(fraction) - 1.0) < EPSILON) {
            q[0] = q1[0] / n;
            q[1] = q1[1] / n;
            q[2] = q1[2] / n;
            q[3] = q1[3] / n;
        } else if (NOTZERO(fraction)) {
            int flip = 0;
            double a = (q[0]*q1[0] + q[1]*q1[1] + q[2]*q1[2] + q[3]*q1[3]) / n;
            if (fabs(fabs(a) - 1.0) > EPSILON) {
                if (shortestpath && (a < 0.0)) {
                    a = -a;
                    flip = 1;
                }
                a = acos(a) + spin * M_PI;
                if (NOTZERO(a)) {
                    double s = 1.0 / sin(a);
                    double f0 = sin((1.0 - fraction) * a) * s;
                    double f1 = sin(fraction * a) * s / n;
                    if (flip) f1 = -f1;
                    q[0] = q[0] * f0 + q1[0] * f1;
                    q[1] = q[1] * f0 + q1[1] * f1;
                    q[2] = q[2] * f0 + q1[2] * f1;
                    q[3] = q[3] * f0 + q1[3] * f1;
                }
            }
        }
    }

    Py_DECREF(quaternion0);
    Py_DECREF(quaternion1);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(result);
    Py_DECREF(quaternion0);
    Py_DECREF(quaternion1);
    return NULL;
}

/*
Random quaternion.
*/
char py_random_quaternion_doc[] =
    "Return uniform random unit quaternion.";

static PyObject *
py_random_quaternion(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *result = NULL;
    PyArrayObject *arand = NULL;
    Py_ssize_t dims = 4;
    static char *kwlist[] = {"rand", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O&", kwlist,
        PyConverter_DoubleVector3OrNone, &arand)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(1, &dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate quaternion");
        goto _fail;
    }
    {
        double *q = (double *)PyArray_DATA(result);
        double r0, r1, r2, t;

        if (arand == NULL) {
            double r[3];
            if (random_doubles(&r[0], 3) != 0) {
                PyErr_Format(PyExc_ValueError, "random_numbers() failed");
                goto _fail;
            }
            r0 = r[0];
            r1 = r[1];
            r2 = r[2];
        } else {
            double *r = (double *)PyArray_DATA(arand);
            r0 = r[0];
            r1 = r[1];
            r2 = r[2];
        }
        t = TWOPI * r1;
        r1 = sqrt(1.0 - r0);
        q[1] = sin(t) * r1;
        q[2] = cos(t) * r1;
        t = TWOPI * r2;
        r2 = sqrt(r0);
        q[3] = sin(t) * r2;
        q[0] = cos(t) * r2;
    }

    Py_XDECREF(arand);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(arand);
    Py_XDECREF(result);
    return NULL;
}

/*
Random rotation matrix.
*/
char py_random_rotation_matrix_doc[] =
    "Return uniform random rotation matrix.";

static PyObject *
py_random_rotation_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *result = NULL;
    PyArrayObject *arand = NULL;
    Py_ssize_t dims[] = {4, 4};
    static char *kwlist[] = {"rand", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O&", kwlist,
        PyConverter_DoubleVector3OrNone, &arand)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate matrix");
        goto _fail;
    }
    {
        double *M = (double *)PyArray_DATA(result);
        double r0, r1, r2, t, qx, qy, qz, qw;

        if (arand == NULL) {
            double r[3];
            if (random_doubles(&r[0], 3) != 0) {
                PyErr_Format(PyExc_ValueError, "random_numbers() failed");
                goto _fail;
            }
            r0 = r[0];
            r1 = r[1];
            r2 = r[2];
        } else {
            double *r = (double *)PyArray_DATA(arand);
            r0 = r[0];
            r1 = r[1];
            r2 = r[2];
        }
        t = TWOPI * r1;
        r1 = sqrt(1.0 - r0);
        qx = sin(t) * r1;
        qy = cos(t) * r1;
        t = TWOPI * r2;
        r2 = sqrt(r0);
        qz = sin(t) * r2;
        qw = cos(t) * r2;

        {
            double x2 = qx+qx;
            double y2 = qy+qy;
            double z2 = qz+qz;
            {
                double xx2 = qx*x2;
                double yy2 = qy*y2;
                double zz2 = qz*z2;
                M[0]  = 1.0 - yy2 - zz2;
                M[5]  = 1.0 - xx2 - zz2;
                M[10] = 1.0 - xx2 - yy2;
            }{
                double yz2 = qy*z2;
                double wx2 = qw*x2;
                M[6] = yz2 - wx2;
                M[9] = yz2 + wx2;
            }{
                double xy2 = qx*y2;
                double wz2 = qw*z2;
                M[1] = xy2 - wz2;
                M[4] = xy2 + wz2;
            }{
                double xz2 = qx*z2;
                double wy2 = qw*y2;
                M[8] = xz2 - wy2;
                M[2] = xz2 + wy2;
            }
            M[3] = M[7] = M[11] = M[12] = M[13] = M[14] = 0.0;
            M[15] = 1.0;
        }
    }

    Py_XDECREF(arand);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(arand);
    Py_XDECREF(result);
    return NULL;
}

/*
Matrix inversion.
Significantly faster than numpy.linalg.inv() for small sizes.
*/
char py_inverse_matrix_doc[] = "Return inverse of symmetric matrix.";

static PyObject *
py_inverse_matrix(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyObject *object;
    PyArrayObject *result = NULL;
    PyArrayObject *matrix = NULL;
    Py_ssize_t dims[2];
    Py_ssize_t size = 0;
    static char *kwlist[] = {"matrix", NULL};
    int iscopy = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", kwlist, &object))
        goto _fail;

    matrix = (PyArrayObject *)PyArray_FROM_OTF(object, NPY_DOUBLE,
                                               NPY_IN_ARRAY);
    if (matrix == NULL) {
        PyErr_Format(PyExc_ValueError, "not an array");
        goto _fail;
    }
    iscopy = ((PyObject *)matrix != object);

    size = PyArray_DIM(matrix, 0);
    if ((size != PyArray_DIM(matrix, 1)) || (size < 1)) {
        PyErr_Format(PyExc_ValueError, "not a symmetric matrix");
        goto _fail;
    }

    dims[0] = dims[1] = size;
    result = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate matrix");
        goto _fail;
    }
    {
        int error = 1;
        double *M = (double *)PyArray_DATA(matrix);
        double *Minv = (double *)PyArray_DATA(result);

        switch (size) {
            case 4:
                error = invert_matrix44(M, Minv);
                break;
            case 3:
                error = invert_matrix33(M, Minv);
                break;
            case 2:
                error = invert_matrix22(M, Minv);
                break;
            case 1:
                error = ISZERO(M[0]);
                if (error == 0)
                    Minv[0] = 1.0 / M[0];
                break;
            default: {
                void *buffer;
                if (iscopy)
                    buffer = PyMem_Malloc(size*2*sizeof(Py_ssize_t));
                else
                    buffer = PyMem_Malloc(size*2*sizeof(Py_ssize_t) +
                                          size*size*sizeof(double));
                if (buffer == NULL) {
                    PyErr_Format(PyExc_MemoryError,
                        "unable to allocate buffer");
                    goto _fail;
                }
                if (!iscopy) {
                    M = (double *)((Py_ssize_t *)buffer + 2*size);
                    memcpy(M, (double *)PyArray_DATA(matrix),
                           size*size*sizeof(double));
                }
                Py_BEGIN_ALLOW_THREADS
                error = invert_matrix(size, M, Minv, (Py_ssize_t *)buffer);
                Py_END_ALLOW_THREADS
                PyMem_Free(buffer);
            }
        }

        if (error != 0) {
            PyErr_Format(PyExc_ValueError, "non-singular matrix");
            goto _fail;
        }
    }

    Py_XDECREF(matrix);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(matrix);
    Py_XDECREF(result);
    return NULL;
}

/*
Arcball: map window to sphere coordinates.
*/
char py_arcball_map_to_sphere_doc[] =
    "Return unit sphere coordinates from window coordinates.";

static PyObject *
py_arcball_map_to_sphere(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyObject *point = NULL;
    PyObject *center = NULL;
    PyArrayObject *result = NULL;
    Py_ssize_t dims = 3;
    double p[] = {0.0, 0.0};
    double c[] = {0.0, 0.0};
    double radius;
    static char *kwlist[] = {"point", "center", "radius", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOd", kwlist,
        &point, &center, &radius)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(1, &dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate vector");
        goto _fail;
    }

    if (PySequence_Check(point) && (PySequence_Size(point) > 1)) {
        PyObject* o;
        o = PySequence_GetItem(point, 0);
        if (o != NULL) {
            p[0] = PyFloat_AsDouble(o);
        }
        Py_XDECREF(o);
        o = PySequence_GetItem(point, 1);
        if (o != NULL) {
            p[1] = PyFloat_AsDouble(o);
        }
        Py_XDECREF(o);
    } else {
        PyErr_Format(PyExc_ValueError, "invalid point");
        goto _fail;
    }

    if (PySequence_Check(center) && (PySequence_Size(center) > 1)) {
        PyObject* o;
        o = PySequence_GetItem(center, 0);
        if (o != NULL) {
            c[0] = PyFloat_AsDouble(o);
        }
        Py_XDECREF(o);
        o = PySequence_GetItem(center, 1);
        if (o != NULL) {
            c[1] = PyFloat_AsDouble(o);
        }
        Py_XDECREF(o);
    } else {
        PyErr_Format(PyExc_ValueError, "invalid center");
        goto _fail;
    }
    {
        double *v = (double *)PyArray_DATA(result);
        double n;

        v[0] = (p[0] - c[0]) / radius;
        v[1] = (c[1] - p[1]) / radius;

        n = v[0]*v[0] + v[1]*v[1];

        if (n > 1.0) {
            n = sqrt(n);
            v[0] /= n;
            v[1] /= n;
            v[2] = 0.0;
        } else {
            v[2] = sqrt(1.0 - n);
        }
    }

    return PyArray_Return(result);

  _fail:
    Py_XDECREF(result);
    return NULL;
}

/*
Arcball: constrain point to axis.
*/
char py_arcball_constrain_to_axis_doc[] =
    "Return sphere point perpendicular to axis.";

static PyObject *
py_arcball_constrain_to_axis(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *point = NULL;
    PyArrayObject *axis = NULL;
    PyArrayObject *result = NULL;
    Py_ssize_t dims = 3;
    static char *kwlist[] = {"point", "axis", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&O&", kwlist,
        PyConverter_DoubleVector3, &point,
        PyConverter_DoubleVector3, &axis)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(1, &dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate vector");
        goto _fail;
    }
    {
        double *v = (double *)PyArray_DATA(result);
        double *a = (double *)PyArray_DATA(axis);
        double *p = (double *)PyArray_DATA(point);
        double n = p[0]*a[0] + p[1]*a[1] + p[2]*a[2];

        v[0] = p[0] - a[0]*n;
        v[1] = p[1] - a[1]*n;
        v[2] = p[2] - a[2]*n;

        n = sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]);

        if (n > EPSILON) {
            v[0] /= n;
            v[1] /= n;
            v[2] /= n;
        } else if (a[2] == 1.0) {
            v[0] = 1.0;
            v[1] = 0.0;
            v[2] = 0.0;
        } else {
            n = sqrt(a[0]*a[0] + a[1]*a[1]);
            v[0] = -a[1] / n;
            v[1] = a[0] / n;
            v[2] = 0.0;
        }
    }

    Py_DECREF(axis);
    Py_DECREF(point);
    return PyArray_Return(result);

  _fail:
    Py_XDECREF(axis);
    Py_XDECREF(point);
    Py_XDECREF(result);
    return NULL;
}

/*
Vector length along axis of ndarray.
*/
char py_vector_norm_doc[] =
    "Return length, i.e. eucledian norm, of ndarray along axis.";

static PyObject *
py_vector_norm(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *data = NULL;
    PyArrayObject *out = NULL;
    PyArrayObject *oout = NULL;
    PyArrayIterObject *dit = NULL;
    PyArrayIterObject *oit = NULL;
    Py_ssize_t newshape[NPY_MAXDIMS];
    int axis = NPY_MAXDIMS;

    static char *kwlist[] = {"data", "axis", "out", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&|O&O&", kwlist,
        PyConverter_AnyDoubleArray, &data,
        PyArray_AxisConverter, &axis,
        PyOutputConverter_AnyDoubleArrayOrNone, &oout)) goto _fail;

    if (axis == NPY_MAXDIMS ) {
        /* iterate over all elements */
        double len = 0.0;

        if (oout != NULL) {
            PyErr_Format(PyExc_ValueError,
                "axis needs to be specified when output array is given");
            goto _fail;
        }

        if ((PyArray_NDIM(data) == 1) &&
            (PyArray_STRIDE(data, 0) == sizeof(double))) {
            Py_ssize_t i;
            double* dptr = PyArray_DATA(data);
            #pragma vector always
            for (i = 0; i < PyArray_DIM(data, 0); i++) {
                len += dptr[i] * dptr[i];
            }
        } else {
            double t;
            dit = (PyArrayIterObject *) PyArray_IterNew((PyObject *)data);
            if (dit == NULL) {
                PyErr_Format(PyExc_ValueError, "failed to create iterator");
                goto _fail;
            }
            while (dit->index < dit->size) {
                t = *((double *)dit->dataptr);
                len += t*t;
                PyArray_ITER_NEXT(dit);
            }
            Py_DECREF(dit);
        }
        len = sqrt(len);

        Py_DECREF(data);
        return PyFloat_FromDouble(len);

    } else { /* iterate over elements of specified axis */
        Py_ssize_t dstride, s, size;
        Py_ssize_t i, j;
        int n = PyArray_NDIM(data);

        /* calculate shape of output array */
        if (axis < 0) {
            axis += n;
        }
        if ((axis < 0) || (axis >= n)) {
            PyErr_Format(PyExc_ValueError, "invalid axis");
            goto _fail;
        }

        j = 0;
        for (i = 0; i < n; i++) {
            if (i != axis)
                newshape[j++] = PyArray_DIM(data, i);
        }

        if (oout == NULL) {
            /* create a new output array */
            out = (PyArrayObject*)PyArray_SimpleNew(n-1, newshape,
                                                    NPY_DOUBLE);
            if (out == NULL) {
                PyErr_Format(PyExc_MemoryError, "failed to allocate array");
                goto _fail;
            }
        } else {
            /* validate given output array */
            if (PyArray_NDIM(data) != (PyArray_NDIM(oout)+1)) {
                PyErr_Format(PyExc_ValueError,
                    "size of output must match data");
                goto _fail;
            }
            j = 0;
            for (i = 0; i < n; i++) {
                if ((i != axis) && (PyArray_DIM(data, i) != newshape[j++])) {
                    PyErr_Format(PyExc_ValueError, "incorrect output size");
                    goto _fail;
                }
            }
            out = oout;
        }

        /* iterate data over all but specified axis */
        dit = (PyArrayIterObject *) PyArray_IterAllButAxis((PyObject *)data,
                                                           &axis);
        oit = (PyArrayIterObject *) PyArray_IterNew((PyObject *)out);
        dstride = PyArray_STRIDE(data, axis);
        size = PyArray_DIM(data, axis);

        if (dstride == sizeof(double)) {
            double *dptr;
            double len;
            while (dit->index < dit->size) {
                dptr = (double *)dit->dataptr;
                len = 0.0;
                #pragma vector always
                for (s = 0; s < size; s++) {
                    len += dptr[s]*dptr[s];
                }
                *((double *)oit->dataptr) = sqrt(len);
                PyArray_ITER_NEXT(oit);
                PyArray_ITER_NEXT(dit);
            }
        } else {
            char *dptr;
            double t, len;
            while (dit->index < dit->size) {
                dptr = dit->dataptr;
                len = 0.0;
                s = size;
                while (s--) {
                    t = *((double*) dptr);
                    len +=  t*t;
                    dptr += dstride;
                }
                *((double *)oit->dataptr) = sqrt(len);
                PyArray_ITER_NEXT(oit);
                PyArray_ITER_NEXT(dit);
            }
        }
        Py_DECREF(oit);
        Py_DECREF(dit);
        Py_DECREF(data);

        /* Return output vector if not provided as argument */
        if (oout == NULL) {
            return PyArray_Return(out);
        } else {
            Py_DECREF(oout);
            Py_INCREF(Py_None);
            return Py_None;
        }
    }

  _fail:
    Py_XDECREF(oit);
    Py_XDECREF(dit);
    Py_XDECREF(data);
    Py_XDECREF((oout == NULL) ? out : oout);
    return NULL;
}

/*
Normalize ndarray by vector length along axis.
*/
char py_unit_vector_doc[] =
    "Return ndarray normalized by length, i.e. eucledian norm, along axis.";

static PyObject *
py_unit_vector(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *data = NULL;
    PyArrayObject *out = NULL;
    PyArrayObject *oout = NULL;
    PyArrayIterObject *dit = NULL;
    PyArrayIterObject *oit = NULL;
    Py_ssize_t dstride, ostride;
    int axis = NPY_MAXDIMS;

    static char *kwlist[] = {"data", "axis", "out", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&|O&O&", kwlist,
        PyConverter_AnyDoubleArray, &data,
        PyArray_AxisConverter, &axis,
        PyOutputConverter_AnyDoubleArrayOrNone, &oout)) goto _fail;

    if (oout == NULL) {
        /* create a new output array */
        out = (PyArrayObject*)PyArray_SimpleNew(PyArray_NDIM(data),
                                              PyArray_DIMS(data), NPY_DOUBLE);
        if (out == NULL) {
            PyErr_Format(PyExc_ValueError, "failed to create output array");
            goto _fail;
        }
    } else {
        /* check shape of provided output array */
        if (!PyArray_SAMESHAPE(data, oout)) {
            PyErr_Format(PyExc_ValueError, "shape of output must match data");
            goto _fail;
        }
        out = oout;
    }

    if (axis == NPY_MAXDIMS) {
        /* iterate over all elements */
        if ((PyArray_NDIM(data) == 1) &&
            (PyArray_STRIDE(data, 0) == sizeof(double)) &&
            (PyArray_STRIDE(out, 0) == sizeof(double))) {

            Py_ssize_t i, size = PyArray_DIM(data, 0);
            double *dptr = (double *)PyArray_DATA(data);
            double *optr = (double *)PyArray_DATA(out);
            double len = 0.0;

            #pragma vector always
            for (i = 0; i < size; i++) {
                len += dptr[i]*dptr[i];
            }
            len = 1.0 / sqrt(len);
            #pragma vector always
            for (i = 0; i < size; i++) {
                optr[i] = dptr[i] * len;
            }
        } else {
            double t, len = 0.0;
            dit = (PyArrayIterObject *)PyArray_IterNew((PyObject *)data);
            oit = (PyArrayIterObject *)PyArray_IterNew((PyObject *)out);
            if (dit == NULL || oit == NULL) {
                PyErr_Format(PyExc_ValueError,
                    "failed to create iterator(s)");
                goto _fail;
            }
            while (dit->index < dit->size) {
                t = *((double *)dit->dataptr);
                len += t*t;
                PyArray_ITER_NEXT(dit);
            }
            Py_DECREF(dit);
            len = 1.0 / sqrt(len);
            dit = (PyArrayIterObject *) PyArray_IterNew((PyObject *)data);
            if (dit == NULL) {
                PyErr_Format(PyExc_ValueError, "failed to create iterator");
                goto _fail;
            }
            while (dit->index < dit->size) {
                *((double *)oit->dataptr) = *((double *)dit->dataptr) * len;
                PyArray_ITER_NEXT(dit);
                PyArray_ITER_NEXT(oit);
            }
        }
    }
    else {
        /* iterate over elements of specified axis */
        Py_ssize_t size, s;

        if (axis < 0) {
            axis += PyArray_NDIM(data);
        }
        if ((axis < 0) || (axis >= PyArray_NDIM(data))) {
            PyErr_Format(PyExc_ValueError, "invalid axis");
            goto _fail;
        }

        dit = (PyArrayIterObject *) PyArray_IterAllButAxis((PyObject *)data,
                                                           &axis);
        oit = (PyArrayIterObject *) PyArray_IterAllButAxis((PyObject *)out,
                                                           &axis);
        if (dit == NULL || oit == NULL) {
            PyErr_Format(PyExc_ValueError, "failed to create iterator(s)");
            goto _fail;
        }
        dstride = PyArray_STRIDE(data, axis);
        ostride = PyArray_STRIDE(out, axis);
        size = PyArray_DIM(data, axis);

        if ((dstride == sizeof(double)) && (ostride == sizeof(double))) {
            Py_ssize_t i;
            double len;
            double *optr, *dptr;
            while (dit->index < dit->size) {
                len = 0.0;
                optr = (double *)oit->dataptr;
                dptr = (double *)dit->dataptr;
                #pragma vector always
                for (i = 0; i < size; i++) {
                    len += dptr[i]*dptr[i];
                }
                len = 1.0 / sqrt(len);
                #pragma vector always
                for (i = 0; i < size; i++) {
                    optr[i] = dptr[i] * len;
                }
                PyArray_ITER_NEXT(oit);
                PyArray_ITER_NEXT(dit);
            }
        } else {
            double t, len;
            char *optr, *dptr;

            while (dit->index < dit->size) {
                len = 0.0;
                dptr = dit->dataptr;
                s = size;
                while (s--) {
                    t = *((double*) dptr);
                    len += t*t;
                    dptr += dstride;
                }
                len = 1.0 / sqrt(len);
                dptr = dit->dataptr;
                optr = oit->dataptr;
                s = size;
                while (s--) {
                    *((double*) optr) = *((double*) dptr) * len;
                    optr += ostride;
                    dptr += dstride;
                }
                PyArray_ITER_NEXT(oit);
                PyArray_ITER_NEXT(dit);
            }
        }
    }

    Py_XDECREF(oit);
    Py_XDECREF(dit);
    Py_DECREF(data);

    /* Return output vector if not provided as argument */
    if (oout == NULL) {
        return PyArray_Return(out);
    } else {
        Py_DECREF(oout);
        Py_INCREF(Py_None);
        return Py_None;
    }

  _fail:
    Py_XDECREF(oit);
    Py_XDECREF(dit);
    Py_XDECREF(data);
    Py_XDECREF((oout == NULL) ? out : oout);
    return NULL;
}

/*
Random vector.
*/
char py_random_vector_doc[] =
    "Return array of random doubles in half-open interval [0.0, 1.0).";

static PyObject *
py_random_vector(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *result = NULL;
    Py_ssize_t size = 0;
    int error ;
    static char *kwlist[] = {"size", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "n", kwlist, &size))
        goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(1, &size, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate array");
        goto _fail;
    }

    Py_BEGIN_ALLOW_THREADS
    error = random_doubles((double *)PyArray_DATA(result), size);
    Py_END_ALLOW_THREADS

    if (error != 0) {
        PyErr_Format(PyExc_ValueError, "random_doubles() failed");
        goto _fail;
    }

    return PyArray_Return(result);

  _fail:
    Py_XDECREF(result);
    return NULL;
}

/*
Tridiagonal matrix.
*/
char py_tridiagonalize_symmetric_44_doc[] =
    "Turn symmetric 4x4 matrix into tridiagonal matrix.";

static PyObject *
py_tridiagonalize_symmetric_44(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *matrix = NULL;
    PyArrayObject *diagonal = NULL;
    PyArrayObject *subdiagonal = NULL;
    Py_ssize_t dims = 4;
    int error;
    static char *kwlist[] = {"matrix", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&", kwlist,
        PyConverter_DoubleMatrix44Copy, &matrix)) goto _fail;

    diagonal = (PyArrayObject*)PyArray_SimpleNew(1, &dims, NPY_DOUBLE);
    if (diagonal == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate diagonal");
        goto _fail;
    }

    dims = 3;
    subdiagonal = (PyArrayObject*)PyArray_SimpleNew(1, &dims, NPY_DOUBLE);
    if (subdiagonal == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate subdiagonal");
        goto _fail;
    }

    Py_BEGIN_ALLOW_THREADS
    error = tridiagonalize_symmetric_44(
        (double *)PyArray_DATA(matrix),
        (double *)PyArray_DATA(diagonal),
        (double *)PyArray_DATA(subdiagonal));
    Py_END_ALLOW_THREADS

    if (error != 0) {
        PyErr_Format(PyExc_ValueError,
            "tridiagonalize_symmetric_44() failed");
        goto _fail;
    }

    Py_DECREF(matrix);
    return Py_BuildValue("(N,N)", diagonal, subdiagonal);

  _fail:
    Py_XDECREF(matrix);
    Py_XDECREF(diagonal);
    Py_XDECREF(subdiagonal);
    return NULL;
}

/*
Eigenvalue of tridiagonal matrix.
*/
char py_max_eigenvalue_of_tridiag_44_doc[] =
    "Return largest eigenvalue of symmetric tridiagonal 4x4 matrix.";

static PyObject *
py_max_eigenvalue_of_tridiag_44(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *diagonal = NULL;
    PyArrayObject *subdiagonal = NULL;
    double result;
    static char *kwlist[] = {"diagonal", "subdiagonal", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&O&", kwlist,
        PyConverter_DoubleVector4, &diagonal,
        PyConverter_DoubleVector3, &subdiagonal)) goto _fail;

    result = max_eigenvalue_of_tridiag_44(
        (double *)PyArray_DATA(diagonal),
        (double *)PyArray_DATA(subdiagonal));

    Py_DECREF(diagonal);
    Py_DECREF(subdiagonal);
    return PyFloat_FromDouble(result);

  _fail:
    Py_XDECREF(diagonal);
    Py_XDECREF(subdiagonal);
    return NULL;
}

/*
Eigenvector of symmetric matrix.
*/
char py_eigenvector_of_symmetric_44_doc[] =
    "Return eigenvector of eigenvalue of symmetric tridiagonal 4x4 matrix.";

static PyObject *
py_eigenvector_of_symmetric_44(
    PyObject *obj,
    PyObject *args,
    PyObject *kwds)
{
    PyArrayObject *matrix = NULL;
    PyArrayObject *result = NULL;
    Py_ssize_t dims = 4;
    int error;
    double *M;
    double *buffer = NULL;
    double eigenvalue;
    static char *kwlist[] = {"matrix", "eigenvalue", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O&d", kwlist,
        PyConverter_DoubleMatrix44Copy, &matrix, &eigenvalue)) goto _fail;

    result = (PyArrayObject*)PyArray_SimpleNew(1, &dims, NPY_DOUBLE);
    if (result == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate eigenvector");
        goto _fail;
    }

    buffer = PyMem_Malloc(12 * sizeof(double));
    if (buffer == NULL) {
        PyErr_Format(PyExc_MemoryError, "unable to allocate buffer");
        goto _fail;
    }

    M = (double *)PyArray_DATA(matrix);
    M[0] -= eigenvalue;
    M[5] -= eigenvalue;
    M[10] -= eigenvalue;
    M[15] -= eigenvalue;

    Py_BEGIN_ALLOW_THREADS
    error = eigenvector_of_symmetric_44(
                M, (double *)PyArray_DATA(result), buffer);
    Py_END_ALLOW_THREADS

    if (error != 0) {
        PyErr_Format(PyExc_ValueError, "no eigenvector found");
        goto _fail;
    }

    PyMem_Free(buffer);
    Py_DECREF(matrix);
    return PyArray_Return(result);

  _fail:
    PyMem_Free(buffer);
    Py_XDECREF(matrix);
    Py_XDECREF(result);
    return NULL;
}

/*****************************************************************************/
/* Create Python module */

char module_doc[] =
    "Homogeneous Transformation Matrices and Quaternions.\n\n"
    "Refer to the transformations.py module for documentation and tests.\n\n"
    "Authors:\n  Christoph Gohlke <http://www.lfd.uci.edu/~gohlke/>\n"
    "  Laboratory for Fluorescence Dynamics, University of California, Irvine."
    "\n\nVersion: %s\n";

static PyMethodDef module_methods[] = {
    {"is_same_transform",
        (PyCFunction)py_is_same_transform,
        METH_VARARGS|METH_KEYWORDS, py_is_same_transform_doc},
    {"identity_matrix",
        (PyCFunction)py_identity_matrix, METH_NOARGS,
        py_identity_matrix_doc},
    {"translation_matrix",
        (PyCFunction)py_translation_matrix,
        METH_VARARGS|METH_KEYWORDS, py_translation_matrix_doc},
    {"reflection_matrix",
        (PyCFunction)py_reflection_matrix,
        METH_VARARGS|METH_KEYWORDS, py_reflection_matrix_doc},
    {"rotation_matrix",
        (PyCFunction)py_rotation_matrix,
        METH_VARARGS|METH_KEYWORDS, py_rotation_matrix_doc},
    {"scale_matrix",
        (PyCFunction)py_scale_matrix,
        METH_VARARGS|METH_KEYWORDS, py_scale_matrix_doc},
    {"projection_matrix",
        (PyCFunction)py_projection_matrix,
        METH_VARARGS|METH_KEYWORDS, py_projection_matrix_doc},
    {"clip_matrix",
        (PyCFunction)py_clip_matrix,
        METH_VARARGS|METH_KEYWORDS, py_clip_matrix_doc},
    {"shear_matrix",
        (PyCFunction)py_shear_matrix,
        METH_VARARGS|METH_KEYWORDS, py_shear_matrix_doc},
    {"superimposition_matrix",
        (PyCFunction)py_superimposition_matrix,
        METH_VARARGS|METH_KEYWORDS, py_superimposition_matrix_doc},
    {"orthogonalization_matrix",
        (PyCFunction)py_orthogonalization_matrix,
        METH_VARARGS|METH_KEYWORDS, py_orthogonalization_matrix_doc},
    {"euler_matrix",
        (PyCFunction)py_euler_matrix,
        METH_VARARGS|METH_KEYWORDS, py_euler_matrix_doc},
    {"euler_from_matrix",
        (PyCFunction)py_euler_from_matrix,
        METH_VARARGS|METH_KEYWORDS, py_euler_from_matrix_doc},
    {"quaternion_from_euler",
        (PyCFunction)py_quaternion_from_euler,
        METH_VARARGS|METH_KEYWORDS, py_quaternion_from_euler_doc},
    {"quaternion_about_axis",
        (PyCFunction)py_quaternion_about_axis,
        METH_VARARGS|METH_KEYWORDS, py_quaternion_about_axis_doc},
    {"quaternion_multiply",
        (PyCFunction)py_quaternion_multiply,
        METH_VARARGS|METH_KEYWORDS, py_quaternion_multiply_doc},
    {"quaternion_matrix",
        (PyCFunction)py_quaternion_matrix,
        METH_VARARGS|METH_KEYWORDS, py_quaternion_matrix_doc},
    {"quaternion_from_matrix",
        (PyCFunction)py_quaternion_from_matrix,
        METH_VARARGS|METH_KEYWORDS, py_quaternion_from_matrix_doc},
    {"quaternion_conjugate",
        (PyCFunction)py_quaternion_conjugate,
        METH_VARARGS|METH_KEYWORDS, py_quaternion_conjugate_doc},
    {"quaternion_inverse",
        (PyCFunction)py_quaternion_inverse,
        METH_VARARGS|METH_KEYWORDS, py_quaternion_inverse_doc},
    {"quaternion_slerp",
        (PyCFunction)py_quaternion_slerp,
        METH_VARARGS|METH_KEYWORDS, py_quaternion_slerp_doc},
    {"random_quaternion",
        (PyCFunction)py_random_quaternion,
        METH_VARARGS|METH_KEYWORDS, py_random_quaternion_doc},
    {"random_rotation_matrix",
        (PyCFunction)py_random_rotation_matrix,
        METH_VARARGS|METH_KEYWORDS, py_random_rotation_matrix_doc},
    {"arcball_map_to_sphere",
        (PyCFunction)py_arcball_map_to_sphere,
        METH_VARARGS|METH_KEYWORDS, py_arcball_map_to_sphere_doc},
    {"arcball_constrain_to_axis",
        (PyCFunction)py_arcball_constrain_to_axis,
        METH_VARARGS|METH_KEYWORDS, py_arcball_constrain_to_axis_doc},
    {"vector_norm",
        (PyCFunction)py_vector_norm,
        METH_VARARGS|METH_KEYWORDS, py_vector_norm_doc},
    {"unit_vector",
        (PyCFunction)py_unit_vector,
        METH_VARARGS|METH_KEYWORDS, py_unit_vector_doc},
    {"random_vector",
        (PyCFunction)py_random_vector,
        METH_VARARGS|METH_KEYWORDS, py_random_vector_doc},
    {"inverse_matrix",
        (PyCFunction)py_inverse_matrix,
        METH_VARARGS|METH_KEYWORDS, py_inverse_matrix_doc},
    {"_tridiagonalize_symmetric_44",
        (PyCFunction)py_tridiagonalize_symmetric_44,
        METH_VARARGS|METH_KEYWORDS, py_tridiagonalize_symmetric_44_doc},
    {"_max_eigenvalue_of_tridiag_44",
        (PyCFunction)py_max_eigenvalue_of_tridiag_44,
        METH_VARARGS|METH_KEYWORDS, py_max_eigenvalue_of_tridiag_44_doc},
    {"_eigenvector_of_symmetric_44",
        (PyCFunction)py_eigenvector_of_symmetric_44,
        METH_VARARGS|METH_KEYWORDS, py_eigenvector_of_symmetric_44_doc},
    {NULL, NULL, 0, NULL} /* Sentinel */
};

#if PY_MAJOR_VERSION >= 3

struct module_state {
    PyObject *error;
};

#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))

static int module_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int module_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}

static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "_transformations",
        NULL,
        sizeof(struct module_state),
        module_methods,
        NULL,
        module_traverse,
        module_clear,
        NULL
};

#define INITERROR return NULL

PyMODINIT_FUNC
PyInit__transformations(void)

#else

#define INITERROR return

PyMODINIT_FUNC
init_transformations(void)
#endif
{
    PyObject *module;

    char *doc = (char *)PyMem_Malloc(sizeof(module_doc) + sizeof(_VERSION_));
    sprintf(doc, module_doc, _VERSION_);

#if PY_MAJOR_VERSION >= 3
    moduledef.m_doc = doc;
    module = PyModule_Create(&moduledef);
#else
    module = Py_InitModule3("_transformations", module_methods, doc);
#endif

    PyMem_Free(doc);

    if (module == NULL)
        INITERROR;

    if (_import_array() < 0) {
        Py_DECREF(module);
        INITERROR;
    }

    {
#if PY_MAJOR_VERSION < 3
    PyObject *s = PyString_FromString(_VERSION_);
#else
    PyObject *s = PyUnicode_FromString(_VERSION_);
#endif
    PyObject *dict = PyModule_GetDict(module);
    PyDict_SetItemString(dict, "__version__", s);
    Py_DECREF(s);
    }

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}