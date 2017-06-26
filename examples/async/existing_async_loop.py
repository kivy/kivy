import asyncio

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


async def update_label1(root):
    label = root.ids.label

    i = 0
    async for _ in root.ids.btn.async_bind('on_release'):
        label.text = 'Pressed x{}'.format(i)
        if i == 7:
            break
        i += 1
    print('Done with update_label1')


class MyApp(App):

    def build(self):
        return Builder.load_string(kv)

    def on_start(self):
        loop = asyncio.get_event_loop()
        loop.create_task(update_label1(self.root))


app_done = False
async def run_app():
    global app_done
    await MyApp().async_run()
    print('App done')
    app_done = True


async def waste_time():
    while not app_done:
        print('Sitting on the beach')
        await asyncio.sleep(2)
    print('Done wasting time')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([waste_time(), run_app()]))
    loop.close()
