'''    simpleOSC 0.2
    ixi software - July, 2006
    www.ixi-software.net

    simple API  for the Open SoundControl for Python (by Daniel Holth, Clinton
    McChesney --> pyKit.tar.gz file at http://wiretap.stetson.edu)
    Documentation at http://wiretap.stetson.edu/docs/pyKit/

    The main aim of this implementation is to provide with a simple way to deal
    with the OSC implementation that makes life easier to those who don't have
    understanding of sockets or programming. This would not be on your screen without the help
    of Daniel Holth.

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

    Thanks for the support to Buchsenhausen, Innsbruck, Austria.
'''

import OSC
import socket, os, time, errno, sys
from threading import Lock
from kivy.logger import Logger
try:
    # multiprocessing support is not good on window
    if sys.platform in ('win32', 'cygwin'):
        raise
    use_multiprocessing = True
    from multiprocessing import Process, Queue, Value
    __import__('multiprocessing.synchronize')
    Logger.info('OSC: using <multiprocessing> for socket')
except:
    use_multiprocessing = False
    from threading import Thread
    Logger.info('OSC: using <thread> for socket')

# globals
outSocket      = 0
oscThreads     = {}
oscLock        = Lock()

if use_multiprocessing:
    def _readQueue(thread_id=None):
        global oscThreads
        for id in oscThreads:
            if thread_id is not None:
                if id != thread_id:
                    continue
            thread = oscThreads[id]
            try:
                while True:
                    message = thread.queue.get_nowait()
                    thread.addressManager.handle(message)
            except:
                pass

    class _OSCServer(Process):
        def __init__(self, **kwargs):
            self.addressManager = OSC.CallbackManager()
            self.queue = Queue()
            Process.__init__(self, args=(self.queue,))
            self.daemon     = True
            self._isRunning = Value('b', True)
            self._haveSocket= Value('b', False)

        def _queue_message(self, message):
            self.queue.put(message)

        def _get_isRunning(self):
            return self._isRunning.value
        def _set_isRunning(self, value):
            self._isRunning.value = value
        isRunning = property(_get_isRunning, _set_isRunning)

        def _get_haveSocket(self):
            return self._haveSocket.value
        def _set_haveSocket(self, value):
            self._haveSocket.value = value
        haveSocket = property(_get_haveSocket, _set_haveSocket)
else:
    def _readQueue(thread_id=None):
        pass

    class _OSCServer(Thread):
        def __init__(self, **kwargs):
            Thread.__init__(self)
            self.addressManager = OSC.CallbackManager()
            self.daemon     = True
            self.isRunning  = True
            self.haveSocket = False

        def _queue_message(self, message):
            self.addressManager.handle(message)


def init() :
    '''instantiates address manager and outsocket as globals
    '''
    assert('Not used anymore')


def bind(oscid, func, oscaddress):
    '''bind given oscaddresses with given functions in address manager
    '''
    global oscThreads
    thread = oscThreads.get(oscid, None)
    if thread is None:
        assert('Unknown thread')
    thread.addressManager.add(func, oscaddress)


def sendMsg(oscAddress, dataArray=[], ipAddr='127.0.0.1', port=9000) :
    '''create and send normal OSC msgs
        defaults to '127.0.0.1', port 9000
    '''
    oscLock.acquire()
    outSocket.sendto( createBinaryMsg(oscAddress, dataArray),  (ipAddr, port))
    oscLock.release()


def createBundle():
    '''create bundled type of OSC messages
    '''
    b = OSC.OSCMessage()
    b.address = ""
    b.append("#bundle")
    b.append(0)
    b.append(0)
    return b


def appendToBundle(bundle, oscAddress, dataArray):
    '''create OSC mesage and append it to a given bundle
    '''
    bundle.append( createBinaryMsg(oscAddress, dataArray),  'b')


def sendBundle(bundle, ipAddr='127.0.0.1', port=9000) :
    '''convert bundle to a binary and send it
    '''
    oscLock.acquire()
    outSocket.sendto(bundle.message, (ipAddr, port))
    oscLock.release()


def createBinaryMsg(oscAddress, dataArray):
    '''create and return general type binary OSC msg
    '''
    m = OSC.OSCMessage()
    m.address = oscAddress

    for x in dataArray:
        m.append(x)

    return m.getBinary()

def readQueue(thread_id=None):
    '''Read queues from all threads, and dispatch message.
    This must be call in the main thread.

    You can pass the thread id to deque message from a specific thread.
    This id is returned from the listen() function'''
    return _readQueue(thread_id)


################################ receive osc from The Other.

class OSCServer(_OSCServer):
    def __init__(self, **kwargs):
        kwargs.setdefault('ipAddr', '127.0.0.1')
        kwargs.setdefault('port', 9001)
        super(OSCServer, self).__init__()
        self.ipAddr     = kwargs.get('ipAddr')
        self.port       = kwargs.get('port')

    def run(self):
        self.haveSocket = False
        # create socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # fix trouble if python leave without cleaning well the socket
        # not needed under windows, he can reuse addr even if the socket
        # are in fin2 or wait state.
        if os.name in ['posix', 'mac'] and hasattr(socket, 'SO_REUSEADDR'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # try to bind the socket, retry if necessary
        while not self.haveSocket and self.isRunning:
            try :
                self.socket.bind((self.ipAddr, self.port))
                self.socket.settimeout(0.5)
                self.haveSocket = True

            except socket.error, e:
                error, message = e.args

                # special handle for EADDRINUSE
                if error == errno.EADDRINUSE:
                    Logger.error('OSC: Address %s:%i already in use, retry in 2 second' % (self.ipAddr, self.port))
                else:
                    Logger.exception(e)
                self.haveSocket = False

                # sleep 2 second before retry
                time.sleep(2)

        Logger.info('OSC: listening for Tuio on %s:%i' % (self.ipAddr, self.port))

        while self.isRunning:
            try:
                message = self.socket.recv(65535)
                self._queue_message(message)
            except Exception, e:
                if type(e) == socket.timeout:
                    continue
                Logger.error('OSC: Error in Tuio recv()')
                Logger.exception(e)
                return 'no data arrived'

def listen(ipAddr='127.0.0.1', port=9001):
    '''Creates a new thread listening to that port
    defaults to ipAddr='127.0.0.1', port 9001
    '''
    global oscThreads
    id = '%s:%d' % (ipAddr, port)
    if id in oscThreads:
        return
    Logger.debug('OSC: Start thread <%s>' % id)
    oscThreads[id] = OSCServer(ipAddr=ipAddr, port=port)
    oscThreads[id].start()
    return id


def dontListen(id = None):
    '''closes the socket and kills the thread
    '''
    global oscThreads
    if id and id in oscThreads:
        ids = [id]
    else:
        ids = oscThreads.keys()
    for id in ids:
        #oscThreads[id].socket.close()
        Logger.debug('OSC: Stop thread <%s>' % id)
        oscThreads[id].isRunning = False
        oscThreads[id].join()
        Logger.debug('OSC: Stop thread <%s> finished' % id)
        del oscThreads[id]

if __name__ == '__main__':
    # example of how to use oscAPI
    init()
    listen() # defaults to "127.0.0.1", 9001
    time.sleep(5)

    # add addresses to callback manager
    def printStuff(msg):
        '''deals with "print" tagged OSC addresses
        '''
        print "printing in the printStuff function ", msg
        print "the oscaddress is ", msg[0]
        print "the value is ", msg[2]

    bind(printStuff, "/test")

    #send normal msg, two ways
    sendMsg("/test", [1, 2, 3], "127.0.0.1", 9000)
    sendMsg("/test2", [1, 2, 3]) # defaults to "127.0.0.1", 9000
    sendMsg("/hello") # defaults to [], "127.0.0.1", 9000

    # create and send bundle, to ways to send
    bundle = createBundle()
    appendToBundle(bundle, "/testing/bundles", [1, 2, 3])
    appendToBundle(bundle, "/testing/bundles", [4, 5, 6])
    sendBundle(bundle, "127.0.0.1", 9000)
    sendBundle(bundle) # defaults to "127.0.0.1", 9000

    dontListen()  # finally close the connection bfore exiting or program

