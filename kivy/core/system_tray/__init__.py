"""
System Tray
===========

.. image:: images/system_tray.png
    :align: center
    :scale: 80%


This module provides system tray functionality for Kivy applications using
the core.system_tray components.

Classes Overview
----------------

The system tray implementation consists of three main classes:

* :class:`TrayIcon`: Main system tray icon management
* :class:`TrayMenu`: Container for menu items
* :class:`TrayMenuItem`: Individual menu entries

Basic Usage
-----------

Creating a Simple System Tray
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from kivy.core.system_tray import TrayIcon, TrayMenu, TrayMenuItem
    
    # Approach 1: Using internal menu
    system_tray = TrayIcon()
    system_tray.create()
    
    main_menu = system_tray.menu
    main_menu.add_item(TrayMenuItem(label="File"))
    main_menu.add_item(TrayMenuItem(label="Exit"))

.. code-block:: python

    # Approach 2: External menu creation
    main_menu = TrayMenu()
    main_menu.add_item(TrayMenuItem(label="File"))
    main_menu.add_item(TrayMenuItem(label="Exit"))
    
    system_tray = TrayIcon(menu=main_menu).create()

Advanced Features
-----------------

Creating Submenus
~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Create submenu
    options_submenu = TrayMenu()
    options_submenu.add_item(TrayMenuItem(label="General"))
    options_submenu.add_item(TrayMenuItem(label="Security"))
    
    # Add to main menu
    main_menu.add_item(
        TrayMenuItem(
            label="Options",
            type="submenu",
            menu=options_submenu
        )
    )

Menu Separators
~~~~~~~~~~~~~~~

.. code-block:: python

    main_menu.add_item(TrayMenuItem(type="separator"))

Inline Menu Creation
~~~~~~~~~~~~~~~~~~~~

For complex menus, you can use inline creation:

.. code-block:: python

    system_tray = TrayIcon(
        menu=TrayMenu(
            items=[
                TrayMenuItem(label="File"),
                TrayMenuItem(type="separator"),
                TrayMenuItem(
                    label="Options",
                    type="submenu",
                    menu=TrayMenu(
                        items=[
                            TrayMenuItem(label="General"),
                            TrayMenuItem(label="Security"),
                        ]
                    )
                ),
            ]
        )
    ).create()

Classes Reference
-----------------

TrayIcon
~~~~~~~~

.. class:: TrayIcon(menu=None)

    Main system tray icon manager.
    
    :param menu: Optional TrayMenu instance
    :type menu: TrayMenu or None
    
    .. method:: create()
    
        Initialize and display the system tray icon.
        
        :returns: TrayIcon instance for method chaining
        :rtype: TrayIcon
    
    .. attribute:: menu
    
        Internal menu reference. Available after create() is called.
        
        :type: TrayMenu

TrayMenu
~~~~~~~~

.. class:: TrayMenu(items=None)

    Container for menu items.
    
    :param items: List of TrayMenuItem instances
    :type items: list or None
    
    .. method:: add_item(item)
    
        Add a menu item to the menu.
        
        :param item: Menu item to add
        :type item: TrayMenuItem

TrayMenuItem
~~~~~~~~~~~~

.. class:: TrayMenuItem(label=None, type="item", menu=None)

    Individual menu entry.
    
    :param label: Display text for the menu item
    :type label: str or None
    :param type: Item type ("item", "separator", "submenu")
    :type type: str
    :param menu: Submenu for submenu items
    :type menu: TrayMenu or None

Best Practices
--------------

1. **Menu Structure**: Keep menus simple and intuitive
2. **Separators**: Use separators to group related items
3. **Method Chaining**: TrayIcon.create() returns self for chaining
4. **Memory Management**: Store tray reference to prevent garbage collection

Examples
--------

Complete Application Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.core.system_tray import TrayIcon, TrayMenu, TrayMenuItem
    
    class MyApp(App):
        def build(self):
            # Create system tray
            self.setup_tray()
            return Label(text="App with System Tray")
        
        def setup_tray(self):
            main_menu = TrayMenu()
            main_menu.add_item(TrayMenuItem(label="Show App"))
            main_menu.add_item(TrayMenuItem(type="separator"))
            main_menu.add_item(TrayMenuItem(label="Exit"))
            
            self.system_tray = TrayIcon(menu=main_menu).create()
    
    MyApp().run()

See Also
--------

* Kivy Documentation: https://kivy.org/doc/stable/
* System Tray Guidelines: Platform-specific implementation notes
"""

from ._system_tray_sdl3 import (  # pyre-ignore # noqa: F401
    TrayIcon,
    TrayMenu,
    TrayMenuItem,
)
