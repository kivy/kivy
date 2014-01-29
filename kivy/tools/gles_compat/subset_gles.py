'''
    Common GLES Subset Extraction Script
    ====================================

    In Kivy, our goal is to use OpenGL ES 2.0 (GLES2) for all drawing on all
    platforms. The problem is that GLES2 is not a proper subset of any OpenGL
    Desktop (GL) version prior to version 4.1.
    However, to keep all our drawing cross-platform compatible, we're
    restricting the Kivy drawing core to a real subset of GLES2 that is
    available on all platforms.

    This script therefore parses the GL and GL Extension (GLEXT) headers and
    compares them with the GLES2 header. It then generates a header that only
    contains symbols that are common to GLES2 and at least either GL or GLEXT.
    However, since GLES2 doesn't support double values, we also need to do some
    renaming, because functions in GL that took doubles as arguments now take
    floats in GLES2, with their function name being suffixed with 'f'.

    Furthermore, sometimes the pure symbol name doesn't match because there
    might be an _EXT or _ARB or something akin to that at the end of a symbol
    name. In that case, we take the symbol from the original header and add
    a #define directive to redirect to that symbol from the symbol name without
    extension.
'''

from __future__ import print_function

gl = open("/Developer/SDKs/MacOSX10.6.sdk/System/Library/Frameworks/" +
          "OpenGL.framework/Versions/A/Headers/gl.h", 'r')
glext = open("/Developer/SDKs/MacOSX10.6.sdk/System/Library/Frameworks/" +
             "OpenGL.framework/Versions/A/Headers/glext.h", 'r')
gles = open("gl2.h", 'r')


def add_defines_to_set(header):
    symbols = []
    lineno = 0
    for line in header:
        symbol = None
        hexcode = None
        lineno += 1
        line = line.strip()
        try:
            elements = line.split()
            if line.startswith("#define"):
                symbol = elements[1]
                for element in elements:
                    if element.startswith("0x"):
                        hexcode = element
            elif line.startswith("typedef"):
                symbol = elements[-1]
            else:
                for element in elements:
                    if element.startswith("gl"):
                        symbol = element
            if symbol:
                symbols.append((symbol, lineno, line, hexcode))
        except Exception as e:
            print('error:', lineno, ':', line)
            print(e)

    return symbols


def extract_common_symbols(symbols1, symbols2, already_extracted):
    for symbol1, lineno1, line1, hexcode1 in symbols1:
        for symbol2, lineno2, line2, hexcode2 in symbols2:
            if symbol1 in already_extracted or symbol2 in already_extracted:
                continue
            if symbol1 == symbol2 + 'f':
                # There is no `double` type in GLES; Functions that were using
                # a double were renamed with the suffix 'f'.
                print("// Different Name; Redefine")
                print(line2)
                print("#define %s %s" % (symbol1, symbol2))
            elif symbol1 == symbol2:
                already_extracted.append(symbol1)
                print(line1)
                if symbol1 == 'GLclampf;':
                    # See explanation about doubles on GLES above.
                    print('typedef GLclampf GLclampd;')
            elif hexcode1 and hexcode2 and hexcode1 == hexcode2:
                already_extracted.append(symbol1)
                already_extracted.append(symbol2)
                print("// Different Name; Redefine")
                print(line2)
                print("#define %s %s" % (symbol1, symbol2))

# Generate ------------------------------------------------
# pipe to kivy/kivy/graphics/common_subset.h

gl_symbols = add_defines_to_set(gl)
glext_symbols = add_defines_to_set(glext)
gles_symbols = add_defines_to_set(gles)

print('// GLES 2.0 Header file, generated for Kivy')
print('// Check kivy/kivy/tools/gles_compat/subset_gles.py')
print('#pragma once')
print('#include "gl2platform.h"')
print('#ifdef __cplusplus')
print('extern "C" {')
print('#endif')

# Don't add the same symbol more than once
already_extracted = []

print('\n// Subset common to GLES and GL: ====================================')
extract_common_symbols(gles_symbols, gl_symbols, already_extracted)

print('\n// Subset common to GLES and GLEXT: =================================')
extract_common_symbols(gles_symbols, glext_symbols, already_extracted)

print()
print('// What follows was manually extracted from the GLES2 headers because')
print('// it was not present in any other header.', end=' ')
print('''
#define GL_SHADER_BINARY_FORMATS          0x8DF8
#define GL_RGB565                         0x8D62
''')

print('#ifdef __cplusplus')
print('}')
print('#endif')
print()

