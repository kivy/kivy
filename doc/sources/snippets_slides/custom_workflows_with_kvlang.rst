App-level workflow using custom events and kvlang
------------

KV code::

    ScreenManager:
        id: screenmanager

        IdleScreen:
            name: 'idle'
            on_press: screenmanager.current = 'date_selection'

        DateSelectionScreen:
            name: 'date_selection'
            catalog: app.catalog
            on_submit:
                app.departure_datetime = self.departure_datetime
                app.cart.filter_by_deadline(self.departure_datetime)
                screenmanager.current = 'browse'

        BrowseScreen:
            name: 'browse'
            catalog: app.catalog
            cart: app.cart
            departure_datetime: app.departure_datetime
            on_date_edit: screenmanager.current = 'date_selection'
            on_back: screenmanager.current = 'date_selection'
            on_order_submit:
                app.create_order()
                screenmanager.current = 'order'

        OrderScreen:
            id: order_screen
            name: 'order'
            cart: app.cart
            order: app.order
            on_back: screenmanager.current = 'browse'

**NOTICE** the ``on_submit``, ``on_date_edit``, ``on_back``, ``on_order_submit``, etc - these are all custom events.
Declaring them is trivial: set the event names in ``__events__`` class property, then make sure to implement empty handlers for them.

Python code::

    from kivy.uix.screenmanager import Screen


    class OrderScreen(Screen):
        __events__ = ('on_reset', 'on_back')

        def on_reset(self):
            pass

        def on_back(self):
            pass



Created by `Cheaterman <https://discord.com/channels/423249981340778496/1311789012339527772>`_ - November 28, 2024
