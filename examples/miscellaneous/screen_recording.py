'''
TODO: This program uses NumPy to flip an image vertically before sending it to ffmpeg,
      but it might be more efficient to do this with shaders instead.
'''

from functools import partial
from contextlib import contextmanager, ExitStack
from dataclasses import dataclass
from random import uniform, choice

from kivy.config import Config
Config.set('graphics', 'resizable', False)
from kivy.utils import get_random_color
from kivy.graphics import Color, Ellipse
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.relativelayout import RelativeLayout


@contextmanager
def fixed_timestep(timestep):
    '''
    To stabilize a video file's framerate, we need a clock that advances in fixed
    increments. However, this destabilizes the runtime framerate.
    '''
    from kivy.context import Context
    from kivy.clock import ClockBase

    context = Context(init=False)
    context['Clock'] = clock = ClockBase()
    context.push()

    try:
        clock._max_fps = 0
        current_time = clock.time()
        clock.time = lambda: current_time

        def _advance_time(__, timestep=timestep):
            nonlocal current_time
            current_time += timestep
        clock.schedule_interval(_advance_time, 0)
        clock.start_clock()
        yield clock
    finally:
        clock.stop_clock()
        context.pop()


@contextmanager
def record_screen(
    outfile, *, fps=30, overwrite=False, drop_first_frame=False,
    outfile_options=tuple(r"-codec:v libx265 -qscale:v 0".split()),
):
    '''
    Records the screen to a video file using ffmpeg.
    '''
    import subprocess
    from kivy.graphics.opengl import glReadPixels_inplace, GL_RGB, GL_UNSIGNED_BYTE
    from kivy.clock import Clock
    import numpy as np

    # size, system_size or unrotated_size. I don't know which one is correct.
    width, height = Window.system_size

    ffmpeg_cmd = (
        'ffmpeg',
        '-y' if overwrite else '-n',
        '-f', 'rawvideo',
        '-codec:v', 'rawvideo',
        '-pixel_format', 'rgb24',
        '-video_size', f'{width}x{height}',
        '-framerate', str(fps),
        '-i', '-',  # stdin as the input source
        *(('-filter:v', 'trim=start_frame=1') if drop_first_frame else ''),
        '-an',  # no audio
        *outfile_options,
        outfile,
    )

    with ExitStack() as stack:
        defer = stack.callback

        original = np.ndarray((height, width, 3), dtype=np.uint8)
        flipped = np.empty_like(original)
        read_pixels_inplace = partial(glReadPixels_inplace, 0, 0, width, height,
                                      GL_RGB, GL_UNSIGNED_BYTE, original.ravel())

        process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, bufsize=0)
        defer(process.wait)
        defer(process.stdin.close)

        def feed_pixels_into_ffmpeg(dt, write=process.stdin.write, pixels=flipped):
            write(pixels)
        defer(Clock.schedule_interval(feed_pixels_into_ffmpeg, 0).cancel)

        def capture_current_frame(__):
            read_pixels_inplace()
            flipped[:] = original[::-1]  # flip vertically
        defer(Window.unbind_uid, 'on_flip',
              Window.fbind('on_flip', capture_current_frame))

        yield


@dataclass
class Ball:
    color: Color
    ellipse: Ellipse
    velocity_x: float
    velocity_y: float


class BouncingBallsApp(App):
    def build(self):
        return RelativeLayout()

    def on_start(self):
        space = self.root
        balls = []
        Clock.schedule_interval(partial(self.generate_ball, space, balls), 1)
        Clock.schedule_interval(partial(self.update_ball_positions, space, balls), 0)

    @staticmethod
    def update_ball_positions(space: RelativeLayout, balls: list[Ball], dt):
        abs_ = abs
        space_width, space_height = space.size
        for ball in balls:
            elps = ball.ellipse
            pos = elps.pos
            size = elps.size
            elps.pos = pos = (
                pos[0] + ball.velocity_x * dt,
                pos[1] + ball.velocity_y * dt,
            )
            if pos[0] < 0:
                ball.velocity_x = abs_(ball.velocity_x)
            elif pos[0] + size[0] > space_width:
                ball.velocity_x = -abs_(ball.velocity_x)
            if pos[1] < 0:
                ball.velocity_y = abs_(ball.velocity_y)
            elif pos[1] + size[1] > space_height:
                ball.velocity_y = -abs_(ball.velocity_y)

    @staticmethod
    def generate_ball(space: RelativeLayout, balls: list[Ball], dt):
        with space.canvas:
            ball_width = ball_height = uniform(10, 200)
            balls.append(Ball(
                color=Color(*get_random_color(alpha=.5)),
                ellipse=Ellipse(
                    pos=((space.width - ball_width) / 2,
                         (space.height - ball_height) / 2),
                    size=(ball_width, ball_height)
                ),
                velocity_x=uniform(10, 200) * choice((-1, 1)),
                velocity_y=uniform(10, 200) * choice((-1, 1)),
            ))


if __name__ == '__main__':
    FPS = 60
    with (
        fixed_timestep(1 / FPS),
        record_screen(fps=FPS, outfile='./bouncing_balls.mkv', overwrite=True,
                      drop_first_frame=True),
    ):
        BouncingBallsApp(title="Running Kivy while recording the screen").run()
