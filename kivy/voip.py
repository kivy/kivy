from kivy.utils import platform
import threading

"""
MIT License

Copyright (c) 2024 Sanquez Heard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# Obtain client object based on platform
if platform == 'android':
    from jnius import autoclass, JavaException
    AudioRecord = autoclass("android.media.AudioRecord")
    AudioSource = autoclass("android.media.MediaRecorder$AudioSource")
    AudioFormat = autoclass("android.media.AudioFormat")
    AudioTrack = autoclass("android.media.AudioTrack")
    AudioManager = autoclass("android.media.AudioManager")
    Socket = autoclass("java.net.Socket")
    SocketTimer = autoclass("java.net.InetSocketAddress")
    SSLContext = autoclass("javax.net.ssl.SSLContext")
    SecureRandom = autoclass("java.security.SecureRandom")

    class Client:
        # Variables to be configured per client
        client_id = ""  # Used to identify/auth client's connection
        dst_address = "127.0.0.1"  # Use root domain for ssl connection
        dst_port = 8080
        timeout = 5  # Sets WAN timeout. LAN connection max is 2 secs.
        ssl = False
        tls_version = "TLSv1.3"  # Enforces TLSv1.3 by default if using SSL
        debug = False
        # Variables to adjust sound quality. Default settings recommended
        SAMPLE_RATE = 16000
        CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO
        AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT
        # Variables to be assigned dynamic values for VOIP services
        socket = None
        data_output_stream = None
        data_input_stream = None
        audio_record = None
        hasPermission = False
        connected = False
        active_call = False
        buffer_size = 640

        def __init__(self):
            min_buffer_size = AudioRecord.getMinBufferSize(
                self.SAMPLE_RATE, self.CHANNEL_CONFIG, self.AUDIO_FORMAT
            )
            if min_buffer_size > self.buffer_size:
                self.buffer_size = min_buffer_size
        
        def send_client_id(self):
            try:
                self.data_output_stream.write(self.client_id.encode())
                self.data_output_stream.flush()
                if self.debug:
                    print("Client ID sent")
            except JavaException as e:
                if self.debug:
                    print("Client ID delivery failed")
                    print(e)

        def start_call(self):
            if self.debug:
                print("Starting call")
            self.verifyPermission()  # Includes debug statements
            if self.hasPermission:  # If permission is granted, attempt server connection
                self.connected = False
                if self.debug:
                    print(f"{self.timeout} sec(s) wait for connection")
                try:
                    if self.ssl:
                        ssl_context = SSLContext.getInstance(self.tls_version)
                        ssl_context.init(None, None, SecureRandom())
                        ssl_socket_factory = ssl_context.getSocketFactory()
                        self.socket = ssl_socket_factory.createSocket()
                        self.socket.connect(
                            SocketTimer(self.dst_address, self.dst_port),
                            self.timeout * 1000
                        )
                        self.data_input_stream = self.socket.getInputStream()
                        self.data_output_stream = self.socket.getOutputStream()
                    else:
                        self.socket = Socket()
                        self.socket.connect(
                            SocketTimer(self.dst_address, self.dst_port),
                            self.timeout * 1000
                        )
                        self.data_input_stream = self.socket.getInputStream()
                        self.data_output_stream = self.socket.getOutputStream()
                    self.connected = True
                    if self.debug:
                        print(f"Connected to {self.dst_address}:{self.dst_port}")
                except JavaException as e:
                    if self.debug:
                        print(e)
                if self.connected:
                    # Establish VOIP session
                    self.active_call = True
                    if self.client_id != "":
                        self.send_client_id() 
                    self.record_thread = threading.Thread(target=self.send_audio, daemon=True)
                    self.record_thread.start()
                    self.listening_thread = threading.Thread(target=self.receive_audio, daemon=True)
                    self.listening_thread.start()
                else:
                    if self.debug:
                        print(
                            "Ensure INTERNET and ACCESS_NETWORK_STATE permissions are in buildozer.spec "
                            "and server is available."
                        )

        def end_call(self):
            if self.debug:
                print("Ending call")
            # Ensure threads are closed before closing socket
            self.active_call = False
            if hasattr(self, "record_thread") and self.record_thread.is_alive():
                self.record_thread.join()
            if hasattr(self, "listening_thread") and self.listening_thread.is_alive():
                self.listening_thread.join()
            if self.socket != None:
                self.socket.close()
                self.socket = None
            if self.debug:
                print("Call ended")

        def verifyPermission(self):
            self.hasPermission = False
            self.audio_record = AudioRecord(
                AudioSource.VOICE_COMMUNICATION,
                self.SAMPLE_RATE,
                self.CHANNEL_CONFIG,
                self.AUDIO_FORMAT,
                self.buffer_size,
            )
            # If the microphone state is initiatialized, allow VOIP call
            if self.audio_record.getState() != AudioRecord.STATE_UNINITIALIZED:
                self.hasPermission = True
                if self.debug:
                    print("Microphone permission granted")
            else:
                if self.debug:
                    print(
                        "Permission Error: "
                        "Ensure RECORD_AUDIO (Mic) permission is enabled in app settings"
                    )

        # Establish microphone stream
        def send_audio(self):
            audio_data = bytearray(self.buffer_size)
            self.audio_record.startRecording()
            if self.debug:
                print("Microphone live stream started")
            while self.active_call == True:
                try:
                    bytes_read = self.audio_record.read(
                        audio_data, 0, self.buffer_size
                    )
                    if (
                        bytes_read != AudioRecord.ERROR_INVALID_OPERATION
                        and bytes_read != AudioRecord.ERROR_BAD_VALUE
                    ):
                        self.data_output_stream.write(audio_data, 0, bytes_read)
                    elif bytes_read == AudioRecord.ERROR_INVALID_OPERATION:
                        if self.debug:
                            print("ERROR_INVALID_OPERATION on microphone")
                    else:
                        if self.debug:
                            print("ERROR_BAD_VALUE on microphone")
                except JavaException as e:
                    self.active_call = False
                    if self.debug:
                        print(f"Microphone Stream Error")
                        print(e)

            self.audio_record.stop()
            if self.debug:
                print("Microphone live stream ended")
        
        # Establish speaker stream
        def receive_audio(self):
            audio_track = AudioTrack(
                AudioManager.STREAM_VOICE_CALL,
                self.SAMPLE_RATE,
                AudioFormat.CHANNEL_OUT_MONO,
                self.AUDIO_FORMAT,
                self.buffer_size,
                AudioTrack.MODE_STREAM,
            )
            buffer = bytearray(self.buffer_size)
            audio_track.play()
            if self.debug:
                print("Speaker live stream started")
            try:
                while self.active_call == True:
                    bytes_received = self.data_input_stream.read(buffer)
                    if bytes_received > 0:
                        audio_track.write(buffer, 0, bytes_received)
            except JavaException as e:
                self.active_call = False
                if self.debug:
                    print("Speaker Stream Error")
                    print(e)

            audio_track.stop()
            if self.debug:
                print("Speaker live stream ended")
else:
    print("VOIP features are currently exclusive to Android devices")
