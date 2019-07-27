'''Example shows the recommended way of how to run Kivy with a trio
event loop as just another async coroutine.
'''
import trio
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
            text: 'Button is "{}"'.format(btn.state)
'''


async def run_app_happily(root, nursery):
    '''This method, which runs Kivy, is run by trio as one of the coroutines.
    '''
    # trio needs to be set so that it'll be used for the event loop
    await async_runTouchApp(root, async_lib='trio')  # run Kivy
    print('App done')
    # now cancel all the other tasks that may be running
    nursery.cancel_scope.cancel()


async def waste_time_freely():
    '''This method is also run by trio and periodically prints something.'''
    try:
        while True:
            print('Sitting on the beach')
            await trio.sleep(2)
    except trio.Cancelled as e:
        print('Wasting time was canceled', e)
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

            This will run all two methods starting in random order
            asynchronously and then block until they are finished or canceled
            at the `with` level. '''
            nursery.start_soon(run_app_happily, root, nursery)
            nursery.start_soon(waste_time_freely)

    trio.run(root_func)
