'''Example shows the recommended way of how to run Kivy with a trio
event loop as just another async coroutine.
'''
import trio
import os

os.environ['KIVY_EVENTLOOP'] = 'trio'
'''trio needs to be set so that it'll be used for the event loop. '''

from kivy.app import async_runTouchApp
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


async def watch_button_closely(root):
    '''This is run side by side with the app and it watches and reacts to the
    button shown in kivy.'''
    label = root.ids.label
    i = 0

    # we watch for 7 button presses and then exit this task. if the app is
    # closed before that, run_app_happily will cancel all the tasks, so we
    # should catch it first and print it and then re-raise
    try:
        # watch the on_release event of the button and react to every release
        async for _ in root.ids.btn.async_bind('on_release'):
            label.text = 'Pressed x{}'.format(i)
            if i == 7:
                break
            i += 1

        label.text = 'Goodbye :('
    except trio.Cancelled:
        print('update_label1 canceled early')
        raise  # we MUST re-raise this exception
    finally:
        print('Done with update_label1')


async def run_app_happily(root, nursery):
    '''This method, which runs Kivy, is run by trio as one of the coroutines.
    '''
    await async_runTouchApp(root)  # run Kivy
    print('App done')
    # now cancel all the other tasks that may be running
    nursery.cancel_scope.cancel()


async def waste_time_freely():
    '''This method is also run by trio and periodically prints something.'''
    try:
        while True:
            print('Sitting on the beach')
            await trio.sleep(2)
    finally:
        # when canceled, print that it finished
        print('Done wasting time')

if __name__ == '__main__':
    async def root_func():
        '''trio needs to run a function, so this is it. '''

        root = Builder.load_string(kv)  # root widget
        async with trio.open_nursery() as nursery:
            '''In trio you create a nursery, in which you schedule async
            functions to be run by the nursery simultaneously as tasks.
            
            This will run all three methods starting in random order
            asynchronously and then block until they are finished or canceled
            at the `with` level. '''
            nursery.start_soon(run_app_happily, root, nursery)
            nursery.start_soon(watch_button_closely, root)
            nursery.start_soon(waste_time_freely)

    trio.run(root_func)
