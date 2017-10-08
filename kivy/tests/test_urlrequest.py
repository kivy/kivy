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

    def test_parse(self):
        cases = [
            ('git+ssh://kivy.org/one/two/Three/', (
                'git+ssh',          # schema
                'kivy.org',         # hostname
                '/one/two/Three/',  # path
                None,               # username
                None,               # password
                '',                 # query
                '',                 # fragment
            )),
            ('git+ssh://kivy.org:99/one/two/Three/', (
                'git+ssh',
                'kivy.org',
                '/one/two/Three/',
                None,
                None,
                '',
                '',
            )),
            ('git+ssh://git@github.com/user/project.git', (
                'git+ssh',
                'github.com',
                '/user/project.git',
                'git',
                None,
                '',
                '',
            )),
            ('git+ssh://git@github.com:99/user/project.git', (
                'git+ssh',
                'github.com',
                '/user/project.git',
                'git',
                None,
                '',
                '',
            )),
            ('http://User:Pass@www.kivy.org/a/?query=yes#frag', (
                'http',
                'www.kivy.org',
                '/a/',
                'User',
                'Pass',
                'query=yes',
                'frag',
            )),
            ('http://User:Pass@www.kivy.org:80/a/?query=yes#frag', (
                'http',
                'www.kivy.org',
                '/a/',
                'User',
                'Pass',
                'query=yes',
                'frag',
            )),
            ('http://User@kivy.org:Pass@www.kivy.org/a/?query=yes#frag', (
                'http',
                'www.kivy.org',
                '/a/',
                'User@kivy.org',
                'Pass',
                'query=yes',
                'frag',
            )),
            ('http://User@kivy.org:Pass@www.kivy.org:80/a/?query=yes#frag', (
                'http',
                'www.kivy.org',
                '/a/',
                'User@kivy.org',
                'Pass',
                'query=yes',
                'frag',
            )),
        ]

        for case in cases:
            url, expected = case
            host, port, parse = UrlRequest._parse_url(None, url)
            self.assertEqual(parse.scheme, expected[0])
            self.assertEqual(parse.hostname, expected[1])
            self.assertEqual(parse.path, expected[2])

            # host + port for UrlRequest
            # password provided
            if expected[4]:
                self.assertEqual(
                    host,
                    '@'.join([
                        ':'.join([
                            expected[3],
                            expected[4]
                        ]),
                        expected[1]
                    ])
                )
                self.assertEqual(
                    parse.netloc,
                    '@'.join([
                        ':'.join([
                            expected[3],
                            expected[4]
                        ]),
                        expected[1] + ':' + str(port)
                        if port else expected[1]
                    ])
                )

            # only username
            elif not expected[4] and expected[3]:
                self.assertEqual(
                    host,
                    expected[3] + '@' + expected[1]
                )
                self.assertEqual(
                    parse.netloc,
                    expected[3] + '@' + expected[1] + ':' + str(port)
                    if port else expected[3] + '@' + expected[1]
                )

            # no user, no pass
            else:
                self.assertEqual(host, expected[1])
                self.assertEqual(
                    parse.netloc,
                    expected[1] + ':' + str(port)
                    if port else expected[1]
                )

            self.assertEqual(parse.username, expected[3])
            self.assertEqual(parse.password, expected[4])
            self.assertEqual(parse.query, expected[5])
            self.assertEqual(parse.fragment, expected[6])
            self.assertEqual(parse.geturl(), url)


if __name__ == '__main__':
    unittest.main()
