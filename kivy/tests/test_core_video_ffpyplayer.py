from kivy.core.video.video_ffpyplayer import VideoFFPy


def test_video_ffpyplayer__is_stream():
    """Test that the VideoFFPy _is_stream property works as expected."""
    player = VideoFFPy(filename='test.mp4')
    assert player._is_stream is False

    player = VideoFFPy(filename='rtsp://test.mp4')
    assert player._is_stream is True

    # The default, when no filename is given
    player = VideoFFPy(filename=None)
    assert player._is_stream is False
