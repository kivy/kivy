from functools import partial
from contextlib import contextmanager, ExitStack
from dataclasses import dataclass
from random import uniform, choice

from kivy.config import Config
Config.set('graphics', 'resizable', False)
from kivy.utils import get_random_color
from kivy.graphics import Color, Ellipse, Scale
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.relativelayout import RelativeLayout


RECORD_SCREEN = True  # Whether to record the screen or not.


@contextmanager
def draw_upside_down():
    '''
    OpenGL's glRead(n)Pixels reads screen pixels from bottom to top, whereas FFmpeg
    expects pixel data from top to bottom. To fill this gap, we simply draw everything
    upside down.
    '''
    s = Scale(1, -1, 1, origin=(0, Window.height / 2, 0))
    Window.canvas.insert(0, s)
    try:
        yield
    finally:
        Window.canvas.remove(s)


@contextmanager
def fixed_timestep(timestep, *, auto_start=False):
    '''
    To stabilize a video file's framerate, we need a clock that advances in fixed
    increments. However, this destabilizes the runtime framerate.
    '''
    from kivy.context import Context
    from kivy.clock import ClockBase

    with ExitStack() as stack:
        defer = stack.callback

        context = Context(init=False)
        context['Clock'] = clock = ClockBase()
        context.push()
        defer(context.pop)

        # The reason for unlimiting the framerate is that, otherwise, the loop inside
        # `ClockBaseBehavior.idle()` never ends, causing the application to freeze.
        clock._max_fps = 0
        current_time = clock.time()
        clock.time = lambda: current_time

        def _advance_time(__, timestep=timestep):
            nonlocal current_time
            current_time += timestep
        defer(clock.schedule_interval(_advance_time, 0).cancel)

        if auto_start:
            clock.start_clock()
            defer(clock.stop_clock)
        yield clock


@contextmanager
def record_screen(
    outfile, *, fps=30, overwrite=False, drop_first_frame=False,
    outfile_options=('-codec:v', 'libx265', '-qscale:v', '0', ),
):
    '''
    Records the screen to a video file using FFmpeg.
    '''
    import subprocess
    from kivy.graphics import opengl as gl

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

        pixels = bytearray(height * width * 3)
        process = stack.enter_context(
            subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, bufsize=0))

        def feed_pixels_into_ffmpeg(dt, write=process.stdin.write, pixels=pixels):
            write(pixels)
        defer(Clock.schedule_interval(feed_pixels_into_ffmpeg, 0).cancel)

        read_pixels_inplace = partial(gl.glReadPixels_inplace, 0, 0, width, height,
                                      gl.GL_RGB, gl.GL_UNSIGNED_BYTE, pixels)
        defer(Window.unbind_uid, 'on_flip',
              Window.fbind('on_flip', lambda __: read_pixels_inplace()))

        yield


random_sign = partial(choice, (-1.0, 1.0))


@dataclass
class Ball:
    color: Color
    ellipse: Ellipse
    velocity_x: float
    velocity_y: float


KV = '''
RelativeLayout:
    Label:
        text: "top"
        font_size: 50
        pos_hint: {'center_x': .5, 'top': 1, }
        size_hint: None, None
        size: self.texture_size
    Label:
        text: "bottom"
        font_size: 50
        pos_hint: {'center_x': .5, 'y': 0, }
        size_hint: None, None
        size: self.texture_size
'''


class BouncingBallsApp(App):
    def build(self):
        return Builder.load_string(KV)

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
                velocity_x=uniform(10, 200) * random_sign(),
                velocity_y=uniform(10, 200) * random_sign(),
            ))


if __name__ == '__main__':
    if RECORD_SCREEN:
        with (
            draw_upside_down(),
            fixed_timestep(1 / 60),
            record_screen(fps=60, outfile='./bouncing_balls.mkv', overwrite=True,
                          drop_first_frame=True),
        ):
            BouncingBallsApp(title="Recording...").run()
    else:
        BouncingBallsApp(title="Not Recording").run()
