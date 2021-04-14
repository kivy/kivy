'''Example shows the recommended way of how to run Kivy with a trio
event loop as just another async coroutine.
'''
import trio

from kivy.app import App
from kivy.lang.builder import Builder

kv = '''
BoxLayout:
    orientation: 'vertical'
    BoxLayout:
        ToggleButton:
            id: btn1
            group: 'a'
            text: 'Sleeping'
            allow_no_selection: False
            on_state: if self.state == 'down': label.status = self.text
        ToggleButton:
            id: btn2
            group: 'a'
            text: 'Swimming'
            allow_no_selection: False
            on_state: if self.state == 'down': label.status = self.text
        ToggleButton:
            id: btn3
            group: 'a'
            text: 'Reading'
            allow_no_selection: False
            state: 'down'
            on_state: if self.state == 'down': label.status = self.text
    Label:
        id: label
        status: 'Reading'
        text: 'Beach status is "{}"'.format(self.status)
'''


class AsyncApp(App):

    nursery = None

    def build(self):
        return Builder.load_string(kv)

    async def app_func(self):
        '''trio needs to run a function, so this is it. '''

        async with trio.open_nursery() as nursery:
            '''In trio you create a nursery, in which you schedule async
            functions to be run by the nursery simultaneously as tasks.

            This will run all two methods starting in random order
            asynchronously and then block until they are finished or canceled
            at the `with` level. '''
            self.nursery = nursery

            async def run_wrapper():
                # trio needs to be set so that it'll be used for the event loop
                await self.async_run(async_lib='trio')
                print('App done')
                nursery.cancel_scope.cancel()

            nursery.start_soon(run_wrapper)
            nursery.start_soon(self.waste_time_freely)

    async def waste_time_freely(self):
        '''This method is also run by trio and periodically prints something.
        '''
        try:
            i = 0
            while True:
                if self.root is not None:
                    status = self.root.ids.label.status
                    print('{} on the beach'.format(status))

                    # get some sleep
                    if self.root.ids.btn1.state != 'down' and i >= 2:
                        i = 0
                        print('Yawn, getting tired. Going to sleep')
                        self.root.ids.btn1.trigger_action()

                i += 1
                await trio.sleep(2)
        except trio.Cancelled as e:
            print('Wasting time was canceled', e)
        finally:
            # when canceled, print that it finished
            print('Done wasting time')


if __name__ == '__main__':
    trio.run(AsyncApp().app_func)
