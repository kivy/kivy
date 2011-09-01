.. _other_frameworks

Integrating with other Frameworks
=================================

Using Twisted inside Kivy
-------------------------
You can use the `kivy.support.install_twisted_reactor` function to
install a twisted reactor that will run inside the kivy event loop.

Any arguments or keyword arguments passed to this function will be
passed on the the threadedselect reactors interleave function, these
are the arguments one would usually pass to twisted's reactor.startRunning

.. warning::
    Unlike the default twisted reactor, the installed reactor will not handle
    any signals unnless you set the 'installSignalHandlers' keyword argument
    to 1 explicitly.  This is done to allow kivy to handle teh signals as
    usual, unless you specifically want the twisted reactor to handle the
    signals (e.g. SIGINT).

Here is a brief example kivy application that has a twisted server running
inside it.  It based mostly on simple Echo example from the twisted docs, 
which you can find here:
    http://twistedmatrix.com/documents/current/core/examples/simpleserv.py
    http://twistedmatrix.com/documents/current/core/examples/simpleclient.py
    

echo_server_app.py::

    #install_twisted_rector must be called before importing  and using the reactor
    from kivy.support import install_twisted_reactor
    install_twisted_reactor()


    from twisted.internet import reactor
    from twisted.internet import protocol

    class EchoProtocol(protocol.Protocol):
        def dataReceived(self, data):
            response = self.factory.app.handle_message(data)
            self.transport.write(response)

    class EchoFactory(protocol.Factory):
        protocol = EchoProtocol
        def __init__(self, app):
            self.app = app


    from kivy.app import App
    from kivy.uix.label import Label

    class TwistedServerApp(App):
        def build(self):
            self.label = Label(text="server started\n")
            reactor.listenTCP(8000, EchoFactory(self))
            return self.label

        def handle_message(self, msg):
            response  = "echo: <%s>" % msg
            if msg == "ping":  response =  "pong"
            if msg == "plop":  response = "kivy rocks"

            self.label.text  = "received:  %s\n" % msg
            self.label.text += "responded: %s\n" % response
            return response


    if __name__ == '__main__':
        TwistedServerApp().run()


echo_client_app.py::

    #install_twisted_rector must be called before importing the reactor
    from kivy.support import install_twisted_reactor
    install_twisted_reactor()


    #A simple Client that send messages to the echo server
    from twisted.internet import reactor, protocol

    class EchoClient(protocol.Protocol):
        def connectionMade(self):
            self.factory.app.print_message("connected successfully")
            self.factory.app.echo_transport = self.transport
        
        def dataReceived(self, data):
            self.factory.app.print_message(data)

    class EchoFactory(protocol.ClientFactory):
        protocol = EchoClient
        def __init__(self, app):
            self.app = app

        def clientConnectionLost(self, conn, reason):
            self.app.print_message("connection lost")
        
        def clientConnectionFailed(self, conn, reason):
            self.app.print_message("connection failed")


    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.textinput import TextInput
    from kivy.uix.boxlayout import BoxLayout

    #A simple kivy App, with a textbox to enter messages, and 
    #a large label to display all the messages received from 
    #the server
    class TwistedClientApp(App):
        echo_transport = None

        def build(self):
            root = self.setup_gui()
            self.connect_to_server()
            return root

        def setup_gui(self):
            self.textbox = TextInput(size_hint_y=.1, multiline=False)
            self.textbox.bind(on_text_validate=self.send_message)
            self.label = Label(text='connecting...\n')
            self.layout = BoxLayout(orientation='vertical')
            self.layout.add_widget(self.label)
            self.layout.add_widget(self.textbox)
            return self.layout
            
        def connect_to_server(self):
            reactor.connectTCP('localhost', 8000, EchoFactory(self))

        def send_message(self, *args):
            msg = self.textbox.text
            if msg and self.echo_transport:
                self.echo_transport.write(str(self.textbox.text))
                self.textbox.text = ""

        def print_message(self, msg):
            self.label.text += msg + "\n"


    if __name__ == '__main__':
        TwistedClientApp().run()


Run echo_server_app.py first, and then launch echo_client_app.py.  The server
will, reply with simple echo messages to anything the client app sends, when
you hit enter after typing something in teh textbox.

