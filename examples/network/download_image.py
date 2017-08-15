# -*- coding: utf-8 -*-

import sys
import time
import kivy.network.curl as curl


counter = 0

def on_complete(url, status_code, data):
    global counter
    counter += 1
    print("on_complete", counter, url, status_code, data[:10])

curl.download("http://txzone.net", on_complete)


while True:
    curl.process()
    if counter == 1:
        break
    time.sleep(1)
