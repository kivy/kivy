# -*- coding: utf-8 -*-

import time
import kivy.network.curl as curl

counter = 0

def on_complete(url, status_code, data):
    global counter
    counter += 1
    print("on_complete", counter, url, status_code, data[:10])


def on_complete_image(url, image, error=None):
    global counter
    counter += 1
    print("on_complete_image", url, image, error)

curl.download("http://txzone.net", on_complete)
curl.download_image("https://dummyimage.com/600x400/000/fff", on_complete_image)

while True:
    curl.process()
    if counter == 2:
        break
    time.sleep(1)
