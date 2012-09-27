from kivy.network.urlrequest import UrlRequest
from kivy.utils import MainThread
import threading
import unittest

class TestUrlFetchThreading(unittest.TestCase):


    def setUp(self):
        self.tls = threading.local()
        self.tls.x = 1
        self.url = "http://google.com"
        self.thread_result = None
        MainThread.set_main_thread()

    def _setThreadResult(self, *args, **kwargs):
            self.thread_result = hasattr(self.tls, "x") and self.tls.x == 1

    def test_thread(self):
        req = UrlRequest(self.url, on_success=self._setThreadResult)
        req.wait()

        if self.thread_result == None:
            self.fail("thread_result is None instead of true")
        elif self.thread_result == False:
            self.fail("call back was run in the wrong thread.")

        self.assertTrue(self.thread_result)

if __name__ == "__main__":
    unittest.main()
        

        
