# -*- coding: utf-8 -*-

import time
import kivy.network.curl as curl

counter = 0

def on_complete(result):
    global counter
    counter += 1
    print("on_complete", result.url, result.error)


def on_complete_image(result):
    global counter
    counter += 1
    print("on_complete_image", result.url, result.error, result.image)

curl.request("http://txzone.net", on_complete)
curl.download_image("https://dummyimage.com/600x400/000/fff", on_complete_image)

while True:
    curl.process()
    if counter == 2:
        break
    time.sleep(1)
