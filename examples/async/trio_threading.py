'''Alternate version of `trio_simple.py`.
'''
import trio
import os
import threading

os.environ['KIVY_EVENTLOOP'] = 'trio'
'''trio needs to be set so that it'll be used for the event loop. '''

from kivy.app import App
from kivy.lang.builder import Builder
from kivy.utils import trio_run_in_kivy_thread

kv = '''
BoxLayout:
    orientation: 'vertical'
    Button:
        id: btn
        text: 'Press me'
    BoxLayout:
        Label:
            id: label
'''


class MyApp(App):

    def build(self):
        return Builder.load_string(kv)

    def on_start(self):
        thread = threading.Thread(target=self.thread_fn)
        thread.start()

    def thread_fn(self):
        trio.run(wait_to_finish, self)


async def watch_button_closely(app):
    '''This method is also run by trio and watches and reacts to the button
    shown in kivy.'''
    root = app.root
    print('app started')

    label = root.ids.label
    i = 0
    # watch the on_release event of the button and react to every release
    async for _ in root.ids.btn.async_bind(
            'on_release', thread_fn=trio.BlockingTrioPortal().run_sync):
        await trio_run_in_kivy_thread(
            setattr, label, 'text', 'Pressed x{}'.format(i))
        if i == 7:
            break
        i += 1

    await trio_run_in_kivy_thread(
        setattr, label, 'text', 'Goodbye :(')
    print('Done with update_label1')


async def waste_time_freely():
    try:
        while True:
            print('Sitting on the beach')
            await trio.sleep(2)
    finally:
        print('Done wasting time')


async def wait_to_finish(app):
    '''This method is also run by trio and periodically prints something.'''
    async with trio.open_nursery() as nursery:
        nursery.start_soon(watch_button_closely, app)
        nursery.start_soon(waste_time_freely)

        async for _ in app.async_bind(
                'on_stop', thread_fn=trio.BlockingTrioPortal().run_sync):
            break
        nursery.cancel_scope.cancel()
    print('completed waiting on app stop')

if __name__ == '__main__':
    MyApp().run()
