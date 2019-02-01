from os import getcwd
from kivy.config import Config


__theme_path = Config.get("kivy", "theme_path")
if __theme_path == "/":
    __path__ = [getcwd() + "/uix"]
else:
    __path__ = [__theme_path]
