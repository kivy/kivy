Async with Trio
------------

Python code::

    import trio
    from kivy.app import App
    from kivy.uix.label import Label


    class AsyncApp(App):
        def build(self):
            return Label(text='Hello Kivy')

        async def async_run(self):
            async with trio.open_nursery() as nursery:
                self.nursery = nursery
                await super().async_run(async_lib='trio')
                nursery.cancel_scope.cancel()


    if __name__ == '__main__':
        trio.run(AsyncApp().async_run)



Created by `Cheaterman <https://discord.com/channels/423249981340778496/1311789935577010188>`_ - November 28, 2024
