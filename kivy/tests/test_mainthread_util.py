import threading
import unittest
from kivy.utils import MainThread


class TestMainThread(unittest.TestCase):

    def setUp(self):
        pass

    def test_thread_main(self):

        class MyTestThread(threading.Thread):

            def test1(self):
                success = MainThread.is_main_thread()
                return success

            def test2(self):
                MainThread.set_main_thread()
                success = MainThread.is_main_thread()
                return success

            def run(self):
                #This thread is *NOT* the main thread
                #test1() and test2() should both be False
                self.success = not self.test1() and not self.test2()

        #This thread is the main thread
        self.assertFalse(MainThread.is_main_thread())
        MainThread.set_main_thread()
        self.assertTrue(MainThread.is_main_thread())

        test_thread = MyTestThread()
        test_thread.start()
        test_thread.join()
        self.assertTrue(MainThread.is_main_thread())
        self.assertTrue(test_thread.success)

if __name__ == "__main__":
    unittest.main()
