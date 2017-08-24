# -*- coding: utf-8 -*-
"""
Demonstration about having a Asynchronous Image viewer
======================================================

The demo use an image source from Pebblo / PBA Lille.
It is separated in 2 steps:
1. load the json containing the informations about medias
2. load each media on the fly when displayed, and save it into a cache for
   a later usage.
"""

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.properties import StringProperty
import kivy.network.curl as curl
import os
from os.path import join, exists, dirname
from kivy.animation import Animation

URL_POI = "https://pebblo.herokuapp.com/apps/2/poi/"
CACHE_DIR = join(dirname(__file__), "cache")
if not exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

Builder.load_string("""
<AsyncCurlImage>:
    allow_stretch: True

<ImageList>:
    RecycleView:
        id: rv
        viewclass: "AsyncCurlImage"
        RecycleGridLayout:
            cols: 3
            padding: dp(10)
            spacing: dp(10)
            default_size: None, root.width / self.cols
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
""")


class AsyncCurlImage(Image):
    url = StringProperty()
    _anim = None
    CACHE = {}

    def on_url(self, instance, url):
        cache_fn = join(CACHE_DIR, url.rsplit("/", 1)[-1])
        if url in self.CACHE:
            self.texture = self.CACHE[url]
            self.animate()
            return
        self.opacity = 0
        curl.download_image(
            url, self.on_url_downloaded, cache_fn=cache_fn, preload_image=True)

    def on_url_downloaded(self, result):
        result.raise_for_status()
        if result.url != self.url:
            return
        self.texture = result.image.texture
        self.CACHE[result.url] = self.texture
        self.animate()

    def animate(self):
        if self._anim is not None:
            self._anim.stop_all(self)
        self._anim = Animation(opacity=1., d=.1)
        self._anim.start(self)


class ImageList(RelativeLayout):
    def load(self):
        self.images = []
        curl.request(URL_POI, self._on_poi_callback)

    def _on_poi_callback(self, result):
        result.raise_for_status()
        data = result.json()
        # if data["next"] is not None:
        #     curl.download(data["next"], self._on_poi_callback)
        self.process_result(data["results"])

    def process_result(self, results):
        for result in results:
            try:
                title = result["translated_fields"]["title"]["fr"]
                image_url = result["media"][0]["image_url"]
            except:
                continue

            filename = image_url.rsplit("/", 1)[-1]
            url = "https://media.pebblo.io/unsafe/fit-in/512x512/{}".format(
                filename)

            self.ids.rv.data.append({"title": title, "url": url})


class ImageBrowser(App):
    def build(self):
        curl.install()
        root = ImageList()
        root.load()
        return root


ImageBrowser().run()
