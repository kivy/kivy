'''
from kivy.graphics.carray import FloatArray, ByteArray

a = FloatArray(10)
a[:] = range(10)
a[2:5] = [0] * 4
print a.tolist()

a = ByteArray(16 * 16 * 4)
a[:] = map(ord, '\x00\x00\x00\xff' * 16 * 16)
#a[:] = '\x00\x00\x00\xff' * 16 * 16
print a.tolist()
'''

from time import time
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.graphics.carray import ByteArray

# initialize
texsize = 64
tex = Texture.create(size=(texsize, texsize), colorfmt='rgb')
sdata = '\x00\xff\x00' * texsize * texsize
cdata = ByteArray(texsize * texsize * 3)
cdata[:] = '\x00\xff\x00' * texsize


# blit with string
def teststr():
    global sdata
    for idx in xrange(texsize * texsize * 3):
        sdata = sdata[:idx] + '\xdd' + sdata[idx + 1:]
        tex.blit_buffer(sdata, colorfmt='rgb')


# blit with bytebuffer
def testbytearray():
    for idx in xrange(texsize * texsize * 3):
        cdata[idx] = '\xdd'
        tex.blit_buffer(cdata, colorfmt='rgb')

count = 10
for func in (teststr, testbytearray):
    print 'Testing', count, 'times with', func
    start = time()
    for x in xrange(count):
        func()
    print 'Duration: {:.3f}s'.format(time() - start)


