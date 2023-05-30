/*
  Simple DirectMedia Layer
  Copyright (C) 1997-2018 Sam Lantinga <slouken@libsdl.org>

  This software is provided 'as-is', without any express or implied
  warranty.  In no event will the authors be held liable for any damages
  arising from the use of this software.

  Permission is granted to anyone to use this software for any purpose,
  including commercial applications, and to alter it and redistribute it
  freely, subject to the following restrictions:

  1. The origin of this software must not be misrepresented; you must not
     claim that you wrote the original software. If you use this software
     in a product, an acknowledgment in the product documentation would be
     appreciated but is not required.
  2. Altered source versions must be plainly marked as such, and must not be
     misrepresented as being the original software.
  3. This notice may not be removed or altered from any source distribution.

  --

  This is the endian-detection code from include/SDL_endian.h, reproduced
  here for compile-time endian check in Cython (it relies on the C compiler
  to fold resulting code, Cython will wrap it in some boilerplate)
*/
#ifndef KIVY_ENDIAN_HEADER
#define KIVY_ENDIAN_HEADER

#define KIVY_LIL_ENDIAN  1234
#define KIVY_BIG_ENDIAN  4321

#ifndef KIVY_BYTEORDER
#ifdef __linux__
#include <endian.h>
#define KIVY_BYTEORDER  __BYTE_ORDER
#else /* __linux__ */
#if defined(__hppa__) || \
    defined(__m68k__) || defined(mc68000) || defined(_M_M68K) || \
    (defined(__MIPS__) && defined(__MISPEB__)) || \
    defined(__ppc__) || defined(__POWERPC__) || defined(_M_PPC) || \
    defined(__sparc__)
#define KIVY_BYTEORDER   KIVY_BIG_ENDIAN
#else
#define KIVY_BYTEORDER   KIVY_LIL_ENDIAN
#endif
#endif /* __linux__ */
#endif /* !KIVY_BYTEORDER */
#endif /* !KIVY_ENDIAN_HEADER */
