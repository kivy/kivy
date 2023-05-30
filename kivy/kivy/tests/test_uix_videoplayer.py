import pytest

from kivy.tests import async_run, UnitKivyApp, GraphicUnitTest
from unittest.mock import patch


def videoplayer_app():
    from kivy.app import App
    from kivy.uix.videoplayer import VideoPlayer

    class TestApp(UnitKivyApp, App):
        def build(self):
            root = VideoPlayer()
            return root

    return TestApp()


@async_run(app_cls_func=videoplayer_app)
async def test_default_thumbnail(
    kivy_app,
):
    with patch(
        "kivy.uix.videoplayer.VideoPlayer._load_thumbnail"
    ) as mock__load_thumbnail, patch(
        "kivy.uix.videoplayer.VideoPlayer._load_annotations"
    ) as mock__load_annotations, patch(
        "kivy.uix.videoplayer.exists"
    ) as mock_exists:
        mock_exists.return_value = True
        kivy_app.root.source = "data/video.mp4"
        await kivy_app.wait_clock_frames(2)
        mock__load_thumbnail.assert_called_once_with("data/video.png")


@async_run(app_cls_func=videoplayer_app)
async def test_default_annotation(
    kivy_app,
):
    with patch(
        "kivy.uix.videoplayer.VideoPlayer._load_annotations"
    ) as mock__load_annotations, patch(
        "kivy.uix.videoplayer.exists"
    ) as mock_exists:
        mock_exists.return_value = True
        kivy_app.root.source = "data/video.mp4"
        await kivy_app.wait_clock_frames(2)
        mock__load_annotations.assert_called_once_with("data/video.jsa")


@async_run(app_cls_func=videoplayer_app)
async def test_custom_thumbnail(
    kivy_app,
):
    with patch(
        "kivy.uix.videoplayer.VideoPlayer._load_thumbnail"
    ) as mock__load_thumbnail, patch(
        "kivy.uix.videoplayer.VideoPlayer._load_annotations"
    ) as mock__load_annotations, patch(
        "kivy.uix.videoplayer.exists"
    ) as mock_exists:
        mock_exists.return_value = True
        kivy_app.root.source = "data/video.mp4"
        kivy_app.root.thumbnail = "data/custom.jpg"
        await kivy_app.wait_clock_frames(2)
        mock__load_thumbnail.assert_called_once_with("data/custom.jpg")


@async_run(app_cls_func=videoplayer_app)
async def test_custom_annotation(
    kivy_app,
):
    with patch(
        "kivy.uix.videoplayer.VideoPlayer._load_annotations"
    ) as mock__load_annotations, patch(
        "kivy.uix.videoplayer.exists"
    ) as mock_exists:
        mock_exists.return_value = True
        kivy_app.root.source = "data/video.mp4"
        kivy_app.root.annotations = "data/custom.jsa"
        await kivy_app.wait_clock_frames(2)
        mock__load_annotations.assert_called_once_with("data/custom.jsa")


@async_run(app_cls_func=videoplayer_app)
async def test_custom_thumbnail_reset(
    kivy_app,
):
    kivy_app.root.thumbnail = "data/custom.jpg"
    assert len(kivy_app.root.container.children) != 0

    kivy_app.root.thumbnail = ""
    assert len(kivy_app.root.container.children) == 0


@async_run(app_cls_func=videoplayer_app)
async def test_custom_annotations_reset_no_fail(
    kivy_app,
):
    with patch(
        "kivy.uix.videoplayer.VideoPlayer._load_annotations"
    ) as mock__load_annotations:
        kivy_app.root.annotations = "data/annotations.jsa"

    kivy_app.root.annotations = ""

if __name__ == "__main__":
    pytest.main(
        args=[
            __file__,
        ]
    )
