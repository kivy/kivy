# save an image into bytesio

from kivy.core.image import Image
from io import BytesIO

img = Image.load("data/logo/kivy-icon-512.png")

bio = BytesIO()
ret = img.save(bio, fmt="png")
print("len=", len(bio.read()))

bio = BytesIO()
ret = img.save(bio, fmt="jpg")
print("len=", len(bio.read()))
