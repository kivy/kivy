'''Example shows the recommended way of how to run Kivy with the Python built
in asyncio event loop as just another async coroutine.
'''
import asyncio

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

    other_task = None

    def build(self):
        return Builder.load_string(kv)

    def app_func(self):
        '''This will run both methods asynchronously and then block until they
        are finished
        '''
        self.other_task = asyncio.ensure_future(self.waste_time_freely())

        async def run_wrapper():
            # we don't actually need to set asyncio as the lib because it is
            # the default, but it doesn't hurt to be explicit
            await self.async_run(async_lib='asyncio')
            print('App done')
            self.other_task.cancel()

        return asyncio.gather(run_wrapper(), self.other_task)

    async def waste_time_freely(self):
        '''This method is also run by the asyncio loop and periodically prints
        something.
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
                await asyncio.sleep(2)
        except asyncio.CancelledError as e:
            print('Wasting time was canceled', e)
        finally:
            # when canceled, print that it finished
            print('Done wasting time')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(AsyncApp().app_func())
    loop.close()
