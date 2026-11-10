'''CoreImage frame sequencing independently of a graphics context.'''

import pytest

from kivy.core.image import Image, ImageData, ImageLoaderBase


class FrameLoader(ImageLoaderBase):
    def load(self, filename):
        return [ImageData(1, 1, 'rgba', bytes((i, 0, 0, 255)))
                for i in range(3)]

    def populate(self):
        # Only texture upload needs a GPU. CoreImage selects these references
        # and publishes on_texture through its real dispatcher and Clock.
        self._textures = [object() for _ in self._data]


@pytest.fixture
def animated_image(kivy_clock):
    loader = FrameLoader('frames')
    image = Image(loader, anim_delay=1)
    assert image.texture is loader.textures[0]
    try:
        yield image, loader.textures
    finally:
        image.anim_reset(False)


@pytest.mark.parametrize('current_frame', [0, 1, 2])
def test_image_animation_restart_from_first_frame(animated_image, current_frame):
    image, frames = animated_image
    for _ in range(current_frame):
        image._anim()
    assert image.texture is frames[current_frame]
    published = []
    image.bind(on_texture=lambda image: published.append(image.texture))
    old_event = image._anim_ev

    image.anim_reset(True)

    assert image.texture is frames[0]
    assert published == [frames[0]]
    assert image._anim_ev is not old_event
    assert not old_event.is_triggered
    # The reporter resets and immediately stops: that must leave frame zero.
    image.anim_reset(False)
    assert image.texture is frames[0]
    assert image._anim_ev is None


@pytest.mark.parametrize('current_frame', [0, 1, 2])
def test_image_animation_stop_preserves_frame(animated_image, current_frame):
    image, frames = animated_image
    for _ in range(current_frame):
        image._anim()
    old_event = image._anim_ev

    image.anim_reset(False)

    assert image.texture is frames[current_frame]
    assert image._anim_ev is None
    assert not old_event.is_triggered


def test_image_animation_disabled_delay_preserves_frame(animated_image):
    image, frames = animated_image
    image._anim()
    image.anim_delay = -1

    image.anim_reset(True)

    assert image.texture is frames[1]
    assert image._anim_ev is None


def test_image_animation_reset_loaded_gif(tmp_path, monkeypatch, kivy_clock):
    pil = pytest.importorskip('PIL.Image')
    from kivy.core.image.img_pil import ImageLoaderPIL

    source = tmp_path / 'animated.gif'
    images = [pil.new('RGBA', (1, 1), (i * 80, 0, 0, 255))
              for i in range(3)]
    images[0].save(source, save_all=True, append_images=images[1:],
                   duration=100, loop=0, disposal=2)
    loader = ImageLoaderPIL(str(source), keep_data=True)
    assert len(loader._data) == 3
    frames = [object() for _ in loader._data]
    monkeypatch.setattr(loader, 'populate',
                        lambda: setattr(loader, '_textures', frames))
    image = Image(loader, anim_delay=1)
    try:
        assert image.texture is frames[0]
        image._anim()
        assert image.texture is frames[1]

        image.anim_reset(True)
        image.anim_reset(False)

        assert image.texture is frames[0]
    finally:
        image.anim_reset(False)
