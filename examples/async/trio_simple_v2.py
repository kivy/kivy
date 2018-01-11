'''Alternate version of `trio_simple.py`.
'''
import trio
import os

os.environ['KIVY_EVENTLOOP'] = 'trio'
'''trio needs to be set so that it'll be used for the event loop. '''

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


async def watch_button_closely(app, task_status=trio.TASK_STATUS_IGNORED):
    '''This method is also run by trio and watches and reacts to the button
    shown in kivy.'''
    task_status.started()
    # wait for the app to be created and widgets displayed
    # we could also have created the app object first and then listened
    # for start and stop events
    async for _ in app.async_bind('on_start'):
        break
    root = App.get_running_app().root
    print('app started')

    label = root.ids.label
    i = 0
    # watch the on_release event of the button and react to every release
    async for _ in root.ids.btn.async_bind('on_release'):
        label.text = 'Pressed x{}'.format(i)
        if i == 7:
            break
        i += 1

    label.text = 'Goodbye :('
    print('Done with update_label1')


async def waste_time_freely():
    try:
        while True:
            print('Sitting on the beach')
            await trio.sleep(2)
    finally:
        print('Done wasting time')


async def wait_to_finish(app, task_status=trio.TASK_STATUS_IGNORED):
    '''This method is also run by trio and periodically prints something.'''
    async with trio.open_nursery() as nursery:
        await nursery.start(watch_button_closely, app)

        task_status.started()
        nursery.start_soon(waste_time_freely)

        async for _ in app.async_bind('on_stop'):
            break
        nursery.cancel_scope.cancel()
    print('completed waiting on app stop')

if __name__ == '__main__':
    async def root_func():
        '''trio needs to run a function, so this is it. '''
        app = MyApp()
        async with trio.open_nursery() as nursery:
            '''In trio you create a nursery, in which you schedule async
            functions to be run by the nursery simultaneously.
            
            nursery.start waits until `task_status.started()` is called, it 
            then continues. This allows us to ensure that we're waiting for
            the app start and stop events 
            '''
            await nursery.start(wait_to_finish, app)
            nursery.start_soon(app.async_run)

    trio.run(root_func)
