
'''
VideoNull: empty implementation of VideoBase for the no provider case
'''

from kivy.core.video import VideoBase


class VideoNull(VideoBase):
    '''VideoBase implementation when there is no provider.
    '''
    pass
