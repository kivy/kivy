import trio
import os

os.environ['KIVY_EVENTLOOP'] = 'trio'

from kivy.app import App
from kivy.lang.builder import Builder

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


app_done = False


async def run_app_happily():
    global app_done
    await MyApp().async_run()
    print('App done')
    app_done = True


async def watch_button_closely():
    while App.get_running_app() is None or App.get_running_app().root is None:
        await trio.sleep(.1)
    root = App.get_running_app().root
    print('app started')

    label = root.ids.label
    i = 0
    async for _ in root.ids.btn.async_bind('on_release'):
        label.text = 'Pressed x{}'.format(i)
        if i == 7:
            break
        i += 1

    label.text = 'Goodbye :('
    print('Done with update_label1')


async def waste_time_freely():
    while not app_done:
        print('Sitting on the beach')
        await trio.sleep(2)
    print('Done wasting time')

if __name__ == '__main__':
    async def root_func():
        async with trio.open_nursery() as nursery:
            nursery.start_soon(run_app_happily)
            nursery.start_soon(waste_time_freely)
            nursery.start_soon(watch_button_closely)

    trio.run(root_func)
