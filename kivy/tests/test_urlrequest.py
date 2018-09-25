'''
UrlRequest tests
================
'''

import unittest

try:
    # py3k
    import _thread
except ImportError:
    # py27
    import thread as _thread

from kivy.network.urlrequest import UrlRequest
from time import sleep
from base64 import b64encode
from kivy.clock import Clock
import os


class UrlRequestTest(unittest.TestCase):

    def _on_success(self, req, *args):
        self.queue.append((_thread.get_ident(), 'success', args))

    def _on_redirect(self, req, *args):
        self.queue.append((_thread.get_ident(), 'redirect', args))

    def _on_error(self, req, *args):
        self.queue.append((_thread.get_ident(), 'error', args))

    def _on_progress(self, req, *args):
        self.queue.append((_thread.get_ident(), 'progress', args))

    def test_callbacks(self):
        if os.environ.get('NONETWORK'):
            return
        self.queue = []
        req = UrlRequest('http://google.com',
                         on_success=self._on_success,
                         on_progress=self._on_progress,
                         on_error=self._on_error,
                         on_redirect=self._on_redirect,
                         debug=True)

        # don't use wait, but maximum 10s timeout
        for i in range(50):
            Clock.tick()
            sleep(.5)
            if req.is_finished:
                break

        self.assertTrue(req.is_finished)

        # we should have 2 progress minimum and one success
        self.assertTrue(len(self.queue) >= 3)

        # ensure the callback is called from this thread (main).
        tid = _thread.get_ident()
        self.assertEqual(self.queue[0][0], tid)
        self.assertEqual(self.queue[-2][0], tid)
        self.assertEqual(self.queue[-1][0], tid)

        self.assertEqual(self.queue[0][1], 'progress')
        self.assertEqual(self.queue[-2][1], 'progress')
        self.assertIn(self.queue[-1][1], ('success', 'redirect'))

        self.assertEqual(self.queue[0][2][0], 0)
        self.assertEqual(self.queue[-2][2][0], self.queue[-2][2][1])

    def test_auth_header(self):
        if os.environ.get('NONETWORK'):
            return
        self.queue = []
        head = {
            "Authorization": "Basic {}".format(b64encode(
                "{}:{}".format('user', 'passwd').encode('utf-8')
            ).decode('utf-8'))
        }
        req = UrlRequest(
            'http://httpbin.org/basic-auth/user/passwd',
            on_success=self._on_success,
            on_progress=self._on_progress,
            on_error=self._on_error,
            on_redirect=self._on_redirect,
            req_headers=head,
            debug=True
        )

        # don't use wait, but maximum 10s timeout
        for i in range(50):
            Clock.tick()
            sleep(.5)
            if req.is_finished:
                break

        self.assertTrue(req.is_finished)

        # we should have 2 progress minimum and one success
        self.assertTrue(len(self.queue) >= 3)

        # ensure the callback is called from this thread (main).
        tid = _thread.get_ident()
        self.assertEqual(self.queue[0][0], tid)
        self.assertEqual(self.queue[-2][0], tid)
        self.assertEqual(self.queue[-1][0], tid)

        self.assertEqual(self.queue[0][1], 'progress')
        self.assertEqual(self.queue[-2][1], 'progress')
        self.assertIn(self.queue[-1][1], ('success', 'redirect'))
        self.assertEqual(
            self.queue[-1][2],
            ({'authenticated': True, 'user': 'user'}, )
        )

        self.assertEqual(self.queue[0][2][0], 0)
        self.assertEqual(self.queue[-2][2][0], self.queue[-2][2][1])

    def test_auth_auto(self):
        if os.environ.get('NONETWORK'):
            return
        self.queue = []
        req = UrlRequest(
            'http://user:passwd@httpbin.org/basic-auth/user/passwd',
            on_success=self._on_success,
            on_progress=self._on_progress,
            on_error=self._on_error,
            on_redirect=self._on_redirect,
            debug=True
        )

        # don't use wait, but maximum 10s timeout
        for i in range(50):
            Clock.tick()
            sleep(.5)
            if req.is_finished:
                break

        self.assertTrue(req.is_finished)

        # we should have 2 progress minimum and one success
        self.assertTrue(len(self.queue) >= 3)

        # ensure the callback is called from this thread (main).
        tid = _thread.get_ident()
        self.assertEqual(self.queue[0][0], tid)
        self.assertEqual(self.queue[-2][0], tid)
        self.assertEqual(self.queue[-1][0], tid)

        self.assertEqual(self.queue[0][1], 'progress')
        self.assertEqual(self.queue[-2][1], 'progress')
        self.assertIn(self.queue[-1][1], ('success', 'redirect'))
        self.assertEqual(
            self.queue[-1][2],
            ({'authenticated': True, 'user': 'user'}, )
        )

        self.assertEqual(self.queue[0][2][0], 0)
        self.assertEqual(self.queue[-2][2][0], self.queue[-2][2][1])


if __name__ == '__main__':
    unittest.main()
