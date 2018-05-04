from asyncio import SelectorEventLoop


class GuiEventLoop(SelectorEventLoop):

    def call_soon(self, callback, *args):
        return self.call_later(0, callback, *args)

    def call_soon_threadsafe(self, callback, *args):
        return self.call_soon(callback, *args)
