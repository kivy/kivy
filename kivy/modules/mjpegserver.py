'''
Stream the Kivy video inside MJPEG HTTP server

:Configuration:
    `ip` : str, default to ''
        By default, server will listen on all ips availables
    `port` : int, default to 8000
        TCP Port to listen
    `fps` : int, default to 20
        Fix a FPS to try to have the same FPS on the whole video
    `size` : str, default to ''
        If the image must be resized, set size to "320x240" for example

'''
#
# Developper note
#
# Double lock is needed if we don't want the sensation about laggy video
# The deal is, if we don't lock the screen, you got more FPS on OpenGL than
# streaming (and that would be good.) Except that since it's not synced,
# video look laggy.
# Double-lock was just the faster solution to do right now :)
#

import os
import kivy
import threading
import time
import StringIO
import random
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from kivy.core.gl import glReadBuffer, glReadPixels, GL_RGB, GL_UNSIGNED_BYTE, GL_FRONT
from kivy.utils import curry

if 'KIVY_DOC' not in os.environ:
    from PIL import Image

lock_current = threading.Lock()
sem_current = threading.Semaphore(0)
sem_next = threading.Semaphore(1)
img_current = None
connected = False


def keep_running():
    return True


class MjpegHttpRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        global connected, sem_next
        try:
            connected = True
            self._stream_video()
        finally:
            connected = False
            # to prevent that app hang
            sem_next.release()
            Logger.info(
                'MjpegServer: Client %s:%d disconnect' % self.client_address)

    def _stream_video(self):
        global img_current

        lfps = []
        dt = 0
        frames = 0
        fps_wanted = self.server.config.get('fps')
        if fps_wanted == '':
            fps_wanted = 0
        fps_wanted = float(fps_wanted)
        if fps_wanted <= 1:
            fps_wanted = 0
        else:
            fps_wanted = 1 / fps_wanted
        size = self.server.config.get('size')
        if size == '':
            size = None
        else:
            size = map(int, size.split('x'))

        Logger.info(
            'MjpegServer: Client %s:%d connected' % self.client_address)

        self.send_response(200, 'OK')
        self.boundary = 'kivy-mjpegserver-boundary-%d' % (random.randint(1, 9999999))
        self.send_header('Server', 'Kivy MjpegServer')
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=%s' % self.boundary)
        self.end_headers()

        # don't accept connection until the window is created
        # XXX really needed ?
        while not kivy.getWindow():
            time.sleep(0.1)
        win = kivy.getWindow()

        dt = dt_current = dt_old = time.time()
        while keep_running():

            # SYNC START
            sem_current.acquire()

            with lock_current:
                im = Image.fromstring('RGB', win.size, img_current)
                img_current = None

            sem_next.release()
            # SYNC END

            buf = StringIO.StringIO()
            if size:
                im = im.resize(size)
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
            im.save(buf, format='JPEG')
            jpeg = buf.getvalue()

            self.wfile.write('--%s\r\n' % self.boundary)
            self.wfile.write('Content-Type: image/jpeg\r\n')
            self.wfile.write('Content-Length: %d\r\n\r\n' % len(jpeg))
            self.wfile.write(jpeg)

            dt_old = dt_current
            dt_current = time.time()

            d = dt_current - dt_old
            if d < fps_wanted:
                time.sleep(d)

            frames += 1
            if dt_current - dt > 2.:
                fps = frames / (dt_current - dt)
                lfps.append(fps)
                x = sum(lfps) / len(lfps)
                Logger.debug('MjpegServer: current FPS is %.1f, average is %.1f' % (fps, x))
                dt = dt_current
                frames = 0


class MjpegServerThread(threading.Thread):

    def __init__(self, config):
        super(MjpegServerThread, self).__init__()
        self.config = config

    def run(self):
        server_address = (self.config.get('ip'), int(self.config.get('port')))
        httpd = HTTPServer(server_address, MjpegHttpRequestHandler)
        httpd.config = self.config
        Logger.info('MjpegServer: Listen to %s:%d' % server_address)
        while keep_running():
            httpd.handle_request()


def window_flip_and_save():
    global img_current
    win = kivy.getWindow()

    with lock_current:
        if not connected:
            return

    sem_next.acquire()

    with lock_current:
        glReadBuffer(GL_FRONT)
        data = glReadPixels(0, 0, win.width, win.height, GL_RGB, GL_UNSIGNED_BYTE)
        img_current = str(buffer(data))

    sem_current.release()


def start(win, ctx):
    win.push_handlers(on_flip=window_flip_and_save)

    ctx.config.setdefault('ip', '')
    ctx.config.setdefault('port', '8000')
    ctx.config.setdefault('fps', '')
    ctx.config.setdefault('size', '')

    ctx.server = MjpegServerThread(ctx.config)
    ctx.server.daemon = True
    ctx.server.start()


def stop(win, ctx):
    win.remove_handlers(on_flip=window_flip_and_save)
