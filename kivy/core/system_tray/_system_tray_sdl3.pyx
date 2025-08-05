include "../../../kivy/lib/sdl3.pxi"

import os
import weakref
import platform
from os import environ
from kivy.config import Config
from kivy.logger import Logger
from kivy.graphics.cgl cimport *
from libc.stdint cimport uintptr_t
from kivy.logger import Logger
from kivy.resources import resource_find
from libc.stdint cimport uintptr_t



# Global dictionary to track system tray menu items
# Stores weak references to prevent memory leaks
_tray_menu_registry = weakref.WeakValueDictionary()

# Global variable to store the handler instance
cdef _TrayIconHandler _tray_icon_handler



cdef void _tray_item_callback(void *userdata, SDL_TrayEntry *entry) nogil:
    """
    C callback function invoked when a tray menu item is clicked.
    
    Args:
        userdata: Pointer containing user data (not used)
        entry: SDL_TrayEntry that was clicked
    """
    cdef uintptr_t addr = <uintptr_t>entry

    with gil:
        # Find the menu item for this entry
        menu_item = _tray_menu_registry.get(<object>addr)
        
        if menu_item is None:
            Logger.warning(f"SystemTray: No menu item found for pointer {<object>entry}")
            return
        
        # For checkbox items, toggle the checked state
        if menu_item.type == 'checkbox':
            menu_item.checked = not menu_item.checked
        
        # Call the menu item callback if it exists
        if menu_item.callback:
            try:
                menu_item.callback(menu_item)
            except Exception as e:
                Logger.error(f"SystemTray: Exception in callback: {e}")


cdef class _SDLPointerHandler:

    cdef uintptr_t __pointer

    def __cinit__(self):
        self.__pointer = 0  # Initialized as NULL

    cdef uintptr_t get_pointer(self):
        """Gets the SDL pointer associated with this item."""
        return <uintptr_t>self.__pointer

    cdef void set_pointer(self, uintptr_t value):
        """Sets the SDL pointer associated with this item."""
        if value < 0:
            raise ValueError("Invalid pointer value")
        self.__pointer = value
        self._on_pointer_set(value)

    cdef void _on_pointer_set(self, uintptr_t value):
        pass

    cdef bint has_valid_pointer(self):
        """Returns whether this object has a valid SDL pointer."""
        return self.__pointer != 0

    cpdef bint _can_update(self):
        """Returns whether this object can be updated via the tray icon handler."""
        global _tray_icon_handler
        return self.has_valid_pointer() and _tray_icon_handler is not None


cdef class TrayMenuItem(_SDLPointerHandler):
    """
    Represents a single item in a system tray menu.

    A TrayMenuItem can be one of four types:
    
    * **button**: Standard clickable menu item with callback
    * **checkbox**: Toggleable item that shows checked/unchecked state
    * **separator**: Visual divider between menu sections (no interaction)
    * **submenu**: Item that opens another menu when hovered/clicked

    Examples:
        Create a basic button item::

            def on_exit_click():
                print("Exit clicked!")
            
            exit_item = TrayMenuItem(
                label="Exit",
                type="button", 
                callback=on_exit_click
            )

        Create a checkbox item::

            def on_notifications_toggle():
                print(f"Notifications: {item.checked}")
            
            notifications_item = TrayMenuItem(
                label="Enable Notifications",
                type="checkbox",
                callback=on_notifications_toggle,
                checked=True
            )

        Create a submenu::

            sub_menu = TrayMenu()
            sub_menu.add_item(TrayMenuItem("Option 1", callback=option1_handler))
            
            submenu_item = TrayMenuItem(
                label="Settings",
                type="submenu",
                menu=sub_menu
            )

        Create a separator::

            separator = TrayMenuItem(type="separator")

    Note:
        Type-specific constraints are automatically validated:
        
        * 'separator' and 'submenu' items cannot have callbacks or be checked
        * 'submenu' items must provide a menu parameter
        * 'button' items cannot be checked
        * Only 'submenu' items can have submenus

    Attributes:
        label (str): Text displayed for this menu item
        type (str): Item type - one of 'button', 'checkbox', 'separator', 'submenu'
        callback (callable): Function called when item is clicked (None for separators/submenus)
        enabled (bool): Whether item can be interacted with
        checked (bool): Show checkmark (checkbox type only)
        sub_menu (TrayMenu): Submenu to display (submenu type only)
    """

    cdef object __weakref__

    cdef str __label
    cdef object __callback
    cdef bint __enabled
    cdef bint __checked
    cdef str __type
    cdef TrayMenu __sub_menu
    
    def __init__(self, label='', type='button', callback=None, enabled=True, checked=False, menu=None, **kwargs):
        """
        Initialize a tray menu item.
        
        Args:
            label (str, optional): Text displayed for this menu item. Defaults to ''.
            type (str, optional): Item type. Must be one of 'button', 'checkbox', 
                'separator', or 'submenu'. Defaults to 'button'.
            callback (callable, optional): Function called when item is clicked.
                Cannot be used with 'separator' or 'submenu' types. Defaults to None.
            enabled (bool, optional): Whether item can be interacted with. 
                Defaults to True.
            checked (bool, optional): Show checkmark for 'checkbox' type items only. 
                Defaults to False.
            menu (TrayMenu, optional): Submenu to display. Required for 'submenu' type,
                forbidden for other types. Defaults to None.
            **kwargs: Additional arguments passed to parent class.

        Raises:
            ValueError: If type is invalid or type-specific constraints are violated:
                
                * Invalid type (not in 'button', 'checkbox', 'separator', 'submenu')
                * 'separator' or 'submenu' items with callback or checked=True
                * 'submenu' items without a menu parameter
                * Non-'submenu' items with a menu parameter
                * 'button' items with checked=True

        Examples:
            >>> # Basic button
            >>> item = TrayMenuItem("Open", callback=lambda: print("opened"))
            
            >>> # Checkbox item
            >>> toggle = TrayMenuItem("Auto-start", type="checkbox", checked=True)
            
            >>> # Separator
            >>> sep = TrayMenuItem(type="separator")
            
            >>> # Submenu
            >>> submenu = TrayMenuItem("Options", type="submenu", menu=my_menu)
        """
        self._validate_type_constraints(type, callback, checked, menu)
        
        self.__label = label
        self.__callback = callback
        self.__enabled = enabled
        self.__checked = checked
        self.__type = type
        self.__sub_menu = menu
    
    cdef void _validate_type_constraints(self, str type, object callback, bint checked, object menu):
        """
        Validate type and type-specific parameter constraints.
        
        Args:
            type (str): The menu item type to validate
            callback (object): The callback function (if any)
            checked (bint): Whether the item should be checked
            menu (object): The submenu (if any)
            
        Raises:
            ValueError: If validation fails for any constraint
        """
        # Validate type
        valid_types = {'button', 'checkbox', 'separator', 'submenu'}
        if type not in valid_types:
            raise ValueError(f"Invalid type '{type}'. Must be one of: {valid_types}")
        
        # Type-specific validations
        if type in ('separator', 'submenu'):
            if callback is not None:
                raise ValueError(f"'{type}' items cannot have callbacks.")
            if checked:
                raise ValueError(f"'{type}' items cannot be checked.")

        if type == 'submenu' and menu is None:
            raise ValueError(f"'{type}' items must provide a menu to display.")

        if type in ('checkbox', 'button', 'separator') and menu is not None:
            raise ValueError(f"'{type}' items cannot have submenus.")

        if type == 'button' and checked:
            raise ValueError(f"'{type}' items cannot be checked")

    cpdef void _on_pointer_set(self, uintptr_t value):
        """
        Internal method called when the native pointer is set.
        
        Args:
            value (uintptr_t): The pointer value to register
        """
        if value != 0:  # If not NULL
            _tray_menu_registry[value] = self

    @property
    def label(self):
        """
        str: The text shown on the menu item.
        
        Setting this property will immediately update the visual representation
        if the menu is currently displayed.
        
        Examples:
            >>> item = TrayMenuItem("Original")
            >>> item.label = "Updated"  # Menu updates automatically
        """
        return self.__label

    @label.setter
    def label(self, value):
        if value != self.__label:
            self.__label = value
            if self._can_update():
                _tray_icon_handler.update_menu_item_label(self)

    @property
    def enabled(self):
        """
        bool: Whether the menu item is clickable or disabled.
        
        Disabled items appear grayed out (disabled) and cannot be clicked.
        Setting this property will immediately update the visual state.
        
        Examples:
            >>> item.enabled = False  # Item becomes disabled
            >>> item.enabled = True   # Item becomes clickable again
        """
        return self.__enabled

    @enabled.setter
    def enabled(self, value):
        if value != self.__enabled:
            self.__enabled = value
            if self._can_update():
                _tray_icon_handler.update_menu_item_enabled(self)

    @property
    def checked(self):
        """
        bool: Whether the menu item shows a checkmark (checkbox type only).
        
        Only meaningful for 'checkbox' type items. Setting this on other
        types has no visual effect but the value is stored.
        
        Examples:
            >>> checkbox_item = TrayMenuItem("Option", type="checkbox")
            >>> checkbox_item.checked = True   # Shows checkmark
            >>> checkbox_item.checked = False  # Removes checkmark
        """
        return self.__checked

    @checked.setter
    def checked(self, value):
        if value != self.__checked:
            self.__checked = value
            if self._can_update():
                _tray_icon_handler.update_menu_item_checked(self)

    @property
    def callback(self):
        """
        callable or None: Function to call when the item is clicked.
        
        The callback function should accept no parameters. For 'separator'
        and 'submenu' type items, this is always None.
        
        Examples:
            >>> def my_handler():
            ...     print("Item clicked!")
            >>> item.callback = my_handler
        """
        return self.__callback
    
    @callback.setter
    def callback(self, value):
        if value != self.__callback:
            self.__callback = value

    @property
    def type(self):
        """
        str: The menu item type.
        
        Read-only property that returns one of:
        
        * 'button' - Standard clickable item
        * 'checkbox' - Toggleable item with checkmark
        * 'separator' - Visual divider (no interaction)
        * 'submenu' - Opens another menu
        
        The type is set during initialization and cannot be changed.
        """
        return self.__type

    @property
    def sub_menu(self):
        """
        TrayMenu or None: The submenu displayed for 'submenu' type items.
        
        Only 'submenu' type items can have a submenu. For other types,
        this is always None.
        
        Examples:
            >>> if item.type == 'submenu':
            ...     submenu = item.sub_menu
            ...     submenu.add_item(new_item)
        """
        return self.__sub_menu


cdef class TrayMenu(_SDLPointerHandler):
    """
    Represents a system tray menu or submenu container.

    A TrayMenu is a collection of :class:`TrayMenuItem` objects that can be displayed
    as a context menu when the system tray icon is clicked, or as a submenu when
    a submenu item is hovered/clicked.

    The menu supports dynamic modification - items can be added, removed, or cleared
    at runtime, and changes will be reflected immediately in the displayed menu
    if it's currently active.

    Examples:
        Create a basic menu with different item types::

            # Create the menu
            menu = TrayMenu()
            
            # Add a button item
            menu.add_item(TrayMenuItem(
                label="Open Application",
                callback=lambda: print("Opening...")
            ))
            
            # Add a checkbox item
            menu.add_item(TrayMenuItem(
                label="Auto-start",
                type="checkbox",
                checked=True,
                callback=lambda: print("Toggled auto-start")
            ))
            
            # Add a separator
            menu.add_item(TrayMenuItem(type="separator"))
            
            # Add an exit button
            menu.add_item(TrayMenuItem(
                label="Exit",
                callback=lambda: app.quit()
            ))

        Create a menu with submenus::

            # Create main menu
            main_menu = TrayMenu()
            
            # Create submenu
            settings_menu = TrayMenu()
            settings_menu.add_item(TrayMenuItem("Preferences", callback=show_prefs))
            settings_menu.add_item(TrayMenuItem("About", callback=show_about))
            
            # Add submenu to main menu
            main_menu.add_item(TrayMenuItem(
                label="Settings",
                type="submenu",
                menu=settings_menu
            ))

    Note:
        * Menu changes are applied immediately to active menus
        * Only :class:`TrayMenuItem` objects can be added directly

    Attributes:
        items (list): Read-only list of :class:`TrayMenuItem` objects in this menu
    """

    cdef list __items

    def __init__(self) -> None:
        """
        Initialize an empty tray menu.
        
        The menu starts with no items. Use :meth:`add_item` to populate it.
        
        Examples:
            >>> menu = TrayMenu()
            >>> print(len(menu.get_items()))  # 0
        """
        self.__items = []

    cpdef list get_items(self):
        """
        Get all items in this menu.
        
        Returns:
            list: A list of :class:`TrayMenuItem` objects in display order.
            
        Note:
            The returned list is the actual internal list. Modifying it directly
            may cause inconsistencies. Use :meth:`add_item`, :meth:`remove_item`,
            and :meth:`clear` instead.
            
        Examples:
            >>> menu = TrayMenu()
            >>> menu.add_item(TrayMenuItem("Test"))
            >>> items = menu.get_items()
            >>> print(len(items))  # 1
            >>> print(items[0].label)  # "Test"
        """
        return self.__items
    
    cpdef void add_item(self, TrayMenuItem item, index=-1):
        """
        Add an item to the menu at the specified position.
        
        Args:
            item (TrayMenuItem): Item to add to the menu. Must be a
                :class:`TrayMenuItem` object.
            index (int, optional): Position where to insert the item. 
                Use -1 to append to the end. Defaults to -1.

        Raises:
            ValueError: If item is not a TrayMenuItem instance.

        Examples:
            Add TrayMenuItem objects::
            
                menu = TrayMenu()
                item = TrayMenuItem("Click me", callback=handler)
                menu.add_item(item)  # Appends to end
                menu.add_item(item2, index=0)  # Inserts at beginning

        Note:
            If the menu is currently displayed, the item is added to the
            native menu representation immediately.
        """
        if not isinstance(item, TrayMenuItem):
            raise ValueError(f"Cannot add invalid item type: {type(item)}, it should be an instance of TrayMenuItem")
        
        # If the menu already exists in SDL, add the item there too
        if self._can_update():
            _tray_icon_handler.add_menu_item(self, item, index)
        
        if index < 0 or index >= len(self.__items):
            self.__items.append(item)
        else:
            self.__items.insert(index, item)
    
    cpdef void remove_item(self, TrayMenuItem item):
        """
        Remove a specific item from the menu.
        
        Args:
            item (TrayMenuItem): The exact TrayMenuItem object to remove.
            
        Note:
            This method removes the first occurrence of the item if it exists
            in the menu. If the item is not found, no action is taken.
            
            If the menu is currently displayed, the item is also removed
            from the native menu representation immediately.
            
        Examples:
            >>> menu = TrayMenu()
            >>> item1 = TrayMenuItem("Item 1")
            >>> item2 = TrayMenuItem("Item 2")
            >>> menu.add_item(item1)
            >>> menu.add_item(item2)
            >>> menu.remove_item(item1)  # Only item2 remains
            >>> print(len(menu.get_items()))  # 1

        Warning:
            The item parameter must be the exact same TrayMenuItem object
            that was added to the menu. Creating a new TrayMenuItem with
            the same properties will not match for removal.
        """
        if item in self.__items:
            # If the menu exists in SDL, remove the item from there too
            if self.has_valid_pointer() and item.has_valid_pointer() and _tray_icon_handler:
                _tray_icon_handler.remove_menu_item(self, item)
            
            self.__items.remove(item)
    
    cpdef void clear(self):
        """
        Remove all items from the menu.
        
        This method empties the menu completely. If the menu is currently
        displayed, all items are removed from the native menu representation
        immediately.
        
        Examples:
            >>> menu = TrayMenu()
            >>> menu.add_item(TrayMenuItem("Item 1"))
            >>> menu.add_item(TrayMenuItem("Item 2"))
            >>> print(len(menu.get_items()))  # 2
            >>> menu.clear()
            >>> print(len(menu.get_items()))  # 0

        Note:
            This is more efficient than calling :meth:`remove_item` for each
            item individually when you need to empty the entire menu.
        """
        # If the menu exists in SDL, remove all items from there too
        cdef TrayMenuItem item
        if self._can_update():
            for item in list(self.__items):
                if item.has_valid_pointer():
                    _tray_icon_handler.remove_menu_item(self, item)
        
        self.__items = []


cdef class TrayIcon(_SDLPointerHandler):
    """
    Manages a system tray icon with context menu functionality.

    A TrayIcon provides integration with the operating system's notification area
    (system tray), allowing applications to display an icon that users can interact
    with via clicking. The icon supports dynamic tooltip text and a customizable
    context menu built from :class:`TrayMenu` objects.

    The tray icon remains visible in the system tray until explicitly destroyed,
    and all properties (icon image, tooltip, menu) can be updated dynamically
    while the icon is active.

    Examples:
        Create a basic tray icon::

            # Simple tray icon with default settings
            tray = TrayIcon()
            tray.create()

        Create a tray icon with custom properties::

            # Create menu first
            menu = TrayMenu()
            menu.add_item(TrayMenuItem("Show Window", callback=show_main_window))
            menu.add_item(TrayMenuItem("Exit", callback=quit_app))
            
            # Create tray icon with custom icon and menu
            tray = TrayIcon(
                icon_path="/path/to/icon.png",
                tooltip="My Application",
                menu=menu
            )
            tray.create()

        Update tray icon properties dynamically::

            # Change icon image
            tray.icon = "/path/to/new_icon.png"
            
            # Update tooltip
            tray.tooltip = "Application - Status: Connected"
            
            # Modify menu
            tray.menu.add_item(TrayMenuItem("New Option", callback=handler))

        Create tray icon with menu from list (legacy support)::

            # Using list of menu items (converted to TrayMenu automatically)
            menu_items = [
                TrayMenuItem("Option 1", callback=option1_handler),
                TrayMenuItem("Option 2", callback=option2_handler)
            ]
            tray = TrayIcon(menu=menu_items)
            tray.create()

    Note:
        * The tray icon must be created with :meth:`create` before becoming visible
        * All property updates are applied immediately to the active tray icon
        * The icon will use a default Kivy icon if no custom icon path is provided

    Attributes:
        icon_path (str): Path to the icon image file displayed in system tray
        tooltip (str): Text shown when hovering over the tray icon
        menu (TrayMenu): The context menu displayed when clicking the tray icon
        visible (bool): Read-only property indicating if the tray icon is currently active
    """
    
    cdef str __icon_path
    cdef str __tooltip
    cdef TrayMenu __menu
    cdef bint __visible
    cdef SDL_Surface* __current_icon_surface  # reference to SDL surface attached to the current icon

    def __init__(self, icon_path='', tooltip='Kivy Application', menu=None, **kwargs):
        """
        Initialize a system tray icon.
        
        Args:
            icon_path (str, optional): Path to the icon image file. If empty,
                uses the default Kivy icon. Defaults to ''.
            tooltip (str, optional): Text displayed when hovering over the 
                tray icon. Defaults to 'Kivy Application'.
            menu (TrayMenu, optional): Context menu to display when right-clicking
                the tray icon. If None, creates an empty TrayMenu that can be 
                modified later via the menu property. Defaults to None.
            **kwargs: Additional arguments passed to parent class.

        Note:
            * The tray icon is not visible until :meth:`create` is called
            * Invalid menu types will generate a warning and create empty menu
            * If no icon_path is provided, the default Kivy logo will be used

        Examples:
            >>> # Basic tray icon
            >>> tray = TrayIcon()
            
            >>> # Custom icon and tooltip
            >>> tray = TrayIcon(
            ...     icon_path="/app/icon.png", 
            ...     tooltip="My App v1.0"
            ... )
            
            >>> # With predefined menu
            >>> menu = TrayMenu()
            >>> menu.add_item(TrayMenuItem("Exit", callback=quit))
            >>> tray = TrayIcon(menu=menu)
        """
        self.__icon_path = icon_path or resource_find('data/logo/kivy-icon-32.png')
        self.tooltip = tooltip
        
        # Process the menu if provided
        if menu:
            if isinstance(menu, TrayMenu):
                self.__menu = menu
            else:
                raise ValueError(f"SystemTray: Invalid menu type: {type(menu)}")
        else:
            self.__menu = TrayMenu()
   
    cpdef bint create(self):
        """
        Create and display the tray icon in the system tray.
        
        This method makes the tray icon visible and functional in the operating
        system's notification area. The icon will respond to user interactions
        and display the configured tooltip and context menu.
        
        Returns:
            bool: True if the tray icon was created successfully, False otherwise.
            
        Note:
            * Can only be called once per TrayIcon instance
            * If already visible, logs a warning and returns False
            * Initializes the global tray handler if not already initialized
            
        Examples:
            >>> tray = TrayIcon()
            >>> success = tray.create()
            >>> if success:
            ...     print("Tray icon is now visible")
            
        Warning:
            Calling this method on an already visible tray icon will log
            a warning and return False without creating a duplicate icon.
        """
        if self.__visible:
            Logger.warning("SystemTray: The tray icon is already visible")
            return False
        
        global _tray_icon_handler
        if _tray_icon_handler is None:
            _tray_icon_handler = _TrayIconHandler()
        
        self.__visible = _tray_icon_handler.create_tray(self)
        return self.__visible
    
    def destroy(self):
        """
        Remove the tray icon from the system tray.
        
        This method hides and destroys the tray icon, making it no longer
        visible or interactive in the system notification area.
        
        Returns:
            bool: True if the tray icon was destroyed successfully, False otherwise.
            
        Note:
            * Can only destroy visible tray icons
            * Logs a warning if called on non-visible tray icon
            * After destruction, the tray icon cannot be made visible again
            
        Examples:
            >>> if tray.visible:
            ...     success = tray.destroy()
            ...     if success:
            ...         print("Tray icon removed")
            
        Warning:
            Calling this method on a non-visible tray icon will log
            a warning and return False.
        """
        if not self.__visible:
            Logger.warning("SystemTray: The tray icon is not visible")
            return False
        
        if _tray_icon_handler:
            return _tray_icon_handler.destroy_tray(self)
        return False

    @property
    def icon(self):
        """
        str: Path to the icon image file displayed in the system tray.
        
        Setting this property will immediately update the tray icon image
        if the icon is currently visible.
        
        Examples:
            >>> tray.icon = "/path/to/new_icon.png"  # Updates immediately
            >>> print(tray.icon)  # "/path/to/new_icon.png"
        """
        return self.__icon_path
        
    @icon.setter
    def icon(self, value):
        self.__icon_path = value
        if self.__visible and _tray_icon_handler:
            _tray_icon_handler.update_tray_icon_image(self, value)

    @property
    def tooltip(self):
        """
        str: Text displayed when hovering over the tray icon.
        
        Setting this property will immediately update the tooltip text
        if the tray icon is currently visible.
        
        Examples:
            >>> tray.tooltip = "Application - Status: Online"
            >>> print(tray.tooltip)  # "Application - Status: Online"
        """
        return self.__tooltip
        
    @tooltip.setter
    def tooltip(self, value):
        self.__tooltip = value
        if self.__visible and _tray_icon_handler:
            _tray_icon_handler.update_tray_tooltip(self, value)

    @property
    def visible(self):
        """
        bool: Whether the tray icon is currently visible in the system tray.
        
        Read-only property that indicates the current visibility state.
        Use :meth:`create` to make visible and :meth:`destroy` to hide.
        
        Examples:
            >>> if not tray.visible:
            ...     tray.create()
            >>> print(tray.visible)  # True
        """
        return self.__visible

    @property
    def menu(self):
        """
        TrayMenu: The context menu displayed when clicking the tray icon.
        
        This property provides access to the menu object for dynamic modification.
        Changes to the menu (adding/removing items) are reflected immediately
        if the tray icon is currently visible.
        
        Examples:
            >>> # Add new menu item
            >>> tray.menu.add_item(TrayMenuItem("New Option", callback=handler))
            
            >>> # Clear all menu items
            >>> tray.menu.clear()
            
            >>> # Get current items
            >>> items = tray.menu.get_items()
        """
        return self.__menu
        
    def clear_menu(self):
        """
        Remove all items from the tray icon's context menu.
        
        This is a convenience method that calls :meth:`TrayMenu.clear` on the
        tray icon's menu. The menu becomes empty and changes are applied
        immediately if the tray icon is visible.
        
        Returns:
            bool: True if the menu was cleared successfully, False otherwise.
            
        Note:
            * Requires the tray icon to be visible
            * Logs warnings for non-visible icons or missing menus
            
        Examples:
            >>> success = tray.clear_menu()
            >>> if success:
            ...     print("All menu items removed")
            
        Warning:
            This method will return False and log a warning if called on
            a non-visible tray icon or if no menu exists.
        """
        if not self.__visible:
            Logger.warning("SystemTray: Cannot clear menu for non-visible tray icon")
            return False
            
        if not self.__menu:
            Logger.warning("SystemTray: No menu exists to clear")
            return False
            
        self.__menu.clear()
        return True


def _get_install_command():
    """
    Detects the Linux distribution's package manager and returns the
    corresponding command to install AppIndicator libraries required
    for system tray functionality.
    
    Returns:
        str: Installation command for the detected package manager, or
             a generic message if no supported manager is found.
    
    Supported package managers:
        * APT (Debian/Ubuntu): libayatana-appindicator3-1
        * DNF (Fedora/RHEL): libayatana-appindicator-gtk3  
        * Pacman (Arch): libayatana-appindicator
        * Zypper (openSUSE): libayatana-appindicator3-1

    """
    system = platform.system().lower()
    
    if system == "linux":
        # Check common package managers
        if os.path.exists("/usr/bin/apt"):
            return "sudo apt install libayatana-appindicator3-1"
        elif os.path.exists("/usr/bin/dnf"):
            return "sudo dnf install libayatana-appindicator-gtk3"
        elif os.path.exists("/usr/bin/pacman"):
            return "sudo pacman -S libayatana-appindicator"
        elif os.path.exists("/usr/bin/zypper"):
            return "sudo zypper install libayatana-appindicator3-1"
        else:
            return "Install AppIndicator libraries for your distribution"
    
    return "System tray libraries may not be available on this platform"


def _handle_tray_error(error_message):
    """
    Generate logging messages for tray initialization errors.
    
    Args:
        error_message (str): SDL error message from tray creation failure.
    
    Returns:
        list[tuple[str, str]]: List of (log_level, message) tuples.
    
    Note:
        Detects common error types (missing libraries, display issues) 
        and provides installation commands when applicable.
    """
    error_lower = error_message.lower()
    install_cmd = _get_install_command()
    
    # Detect error type and generate appropriate message
    if any(keyword in error_lower for keyword in ["gtk", "appindicator", "load"]):
        return [
            ("ERROR", "SystemTray: System tray libraries not found"),
            ("WARNING", f"SystemTray: To enable system tray: {install_cmd}"),
            ("INFO", "SystemTray: Application will continue without tray icon")
        ]
    elif "display" in error_lower:
        return [
            ("ERROR", "SystemTray: Display system doesn't support system tray"),
            ("INFO", "SystemTray: Application will continue without tray icon")
        ]
    else:
        return [
            ("ERROR", "SystemTray: Failed to initialize system tray"),
            ("WARNING", f"SystemTray: Try installing tray support: {install_cmd}"),
            ("INFO", "SystemTray: Application will continue without tray icon")
        ]


cdef class _TrayIconHandler:
    """
    Internal handler class that manages SDL system tray resources and operations.
    
    This class provides a low-level interface to SDL's system tray functionality,
    handling the creation, destruction, and updating of system tray icons and menus.
    It serves as the bridge between Python TrayIcon objects and the native SDL
    tray implementation.
    
    The handler manages:
    - System tray icon creation and destruction
    - Icon image and tooltip updates
    - Menu population and item management
    - Dynamic menu item property updates (label, enabled state, checked state)
    
    Note:
        This is an internal class and should not be instantiated directly.
        It is automatically created when the first TrayIcon is created.
    
    """
    
    cpdef bint create_tray(self, TrayIcon tray_icon):
        """
        Creates a system tray icon using SDL.
        
        This method initializes an SDL tray icon with the specified image, tooltip,
        and menu structure. It handles the complete setup process including image
        loading, tray creation, and menu population.
        
        Args:
            tray_icon (TrayIcon): The Python TrayIcon object containing configuration
                                 data such as icon path, tooltip, and menu structure.
        
        Returns:
            bool: True if the tray icon was created successfully, False if creation
                 failed due to missing libraries, invalid icon file, or system limitations.
        
        Implementation:
            1. Loads the icon image file using SDL_Image
            2. Creates the SDL tray icon with image and tooltip
            3. Creates and populates the context menu if items exist
            4. Registers the tray pointer with the TrayIcon object
            5. Provides detailed error logging for troubleshooting
        
        Error Handling:
            * Invalid icon files result in error logs and creation failure
            * Missing system tray support triggers informative error messages
            * Memory allocation failures are properly cleaned up
        """
        # Load the icon image
        cdef bytes icon_path_bytes = tray_icon.icon.encode('utf-8')
        cdef bytes tooltip_bytes = tray_icon.tooltip.encode('utf-8')
        
        Logger.debug(f"SystemTray: Loading icon from {tray_icon.icon}")
        cdef SDL_Surface *icon_surface = IMG_Load(icon_path_bytes)
        
        if not icon_surface:
            error = <bytes>SDL_GetError()
            Logger.error(f"SystemTray: Failed to load icon: {error.decode('utf-8', 'replace')}")
            return False
        
        # Create the tray icon
        Logger.debug(f"SystemTray: Creating tray with tooltip '{tray_icon.tooltip}'")
        cdef SDL_Tray *tray = SDL_CreateTray(icon_surface, tooltip_bytes)
        
        if not tray:
            error = <bytes>SDL_GetError()
            error_message = error.decode('utf-8', 'replace')
            
            # Generate informative logs
            for level, message in _handle_tray_error(error_message):
                getattr(Logger, level.lower())(message)
            
            SDL_DestroySurface(icon_surface)
            return False
            
        # Create and populate the menu if it exists
        cdef SDL_TrayMenu *sdl_menu
        cdef TrayMenu menu = <TrayMenu>tray_icon.menu
        tray_icon_menu_items = menu.get_items()
        if menu and tray_icon_menu_items:
            sdl_menu = SDL_CreateTrayMenu(tray)
            
            if not sdl_menu:
                error = <bytes>SDL_GetError()
                Logger.error(f"SystemTray: Failed to create menu: {error.decode('utf-8', 'replace')}")
                SDL_DestroyTray(tray)
                SDL_DestroySurface(icon_surface)
                return False
            
            # Store the SDL menu pointer in the Python menu object
            menu.set_pointer(<uintptr_t>sdl_menu)
            
            # Populate the menu with items
            self._populate_menu(sdl_menu, menu)
        
        Logger.info(f"SystemTray: Successfully created tray icon")

        tray_icon.__current_icon_surface = icon_surface
        tray_icon.set_pointer(<uintptr_t>tray)
        
        return True
    
    cpdef destroy_tray(self, TrayIcon tray_icon):
        """
        Destroys the SDL tray icon and cleans up all associated resources.
        
        This method safely removes the tray icon from the system notification area
        and deallocates all SDL resources to prevent memory leaks.
        
        Args:
            tray_icon (TrayIcon): The TrayIcon object to destroy. Must have a valid
                                 SDL pointer from a previous create_tray() call.
        
        Returns:
            bool: True if destruction was successful, False if the tray icon was
                 already destroyed or invalid.
        
        Implementation:
            1. Validates that the tray icon has a valid SDL pointer
            2. Calls SDL_DestroyTray() to remove from system tray
            3. Updates the TrayIcon's visibility state
            4. Resets the SDL pointer to prevent dangling references
            5. Automatically cleans up associated menu resources
        
        Note:
            After calling this method, the TrayIcon object cannot be made visible
            again without creating a new instance.
        """
        cdef SDL_Tray *tray
        if tray_icon.has_valid_pointer():
            Logger.debug("SystemTray: Destroying tray icon")
            tray = <SDL_Tray*><uintptr_t>tray_icon.get_pointer()
            SDL_DestroyTray(tray)
            tray_icon.__visible = False
            tray_icon.set_pointer(0)
            return True
        return False
    
    cpdef update_tray_icon_image(self, TrayIcon tray_icon, str icon_path):
        """
        Updates the tray icon's image while it's displayed in the system tray.
        
        This method dynamically changes the tray icon image without requiring
        destruction and recreation of the entire tray icon.
        
        Args:
            tray_icon (TrayIcon): The active TrayIcon object to update
            icon_path (str): Path to the new icon image file. Must be a valid
                           image format supported by SDL_Image (PNG, ICO, etc.)
        
        Returns:
            bool: True if the icon was updated successfully, False if the update
                 failed due to invalid file, unsupported format, or SDL errors.
        
        Implementation:
            1. Validates that the tray icon is currently active
            2. Loads the new image file using SDL_Image
            3. Updates the tray icon using SDL_SetTrayIcon()
            4. Handles memory management (SDL takes ownership of new surface)
            5. Provides error logging for troubleshooting
        
        Supported formats: .png, .ico, .bmp, .jpg/.jpeg, .gif, .svg.

        Note:
            The old icon surface is automatically freed by SDL when the new
            icon is set. Icon size should match system expectations (typically 16x16 or 32x32) for better readability.
        """
        if not tray_icon.has_valid_pointer():
            Logger.warning("SystemTray: Cannot update icon for non-existent tray")
            return False
        
        # Load the new icon image
        cdef bytes icon_path_bytes = icon_path.encode('utf-8')
        cdef SDL_Surface *new_icon_surface = IMG_Load(icon_path_bytes)
        
        if not new_icon_surface:
            error = <bytes>SDL_GetError()
            Logger.error(f"SystemTray: Failed to load new icon: {error.decode('utf-8', 'replace')}")
            return False
        
        # Update the tray icon
        cdef SDL_Tray *tray = <SDL_Tray*><uintptr_t>tray_icon.get_pointer()
        SDL_SetTrayIcon(tray, new_icon_surface)

        # Check for errors after the call
        error = <bytes>SDL_GetError()
        if error:
            Logger.error(f"SystemTray: Failed to update icon: {error.decode('utf-8', 'replace')}")
            SDL_DestroySurface(new_icon_surface)
            return False
        
        # Free old surface and replace with new one
        SDL_DestroySurface(tray_icon.__current_icon_surface)
        tray_icon.__current_icon_surface = new_icon_surface

        return True
    
    cpdef update_tray_tooltip(self, TrayIcon tray_icon, str tooltip):
        """
        Updates the tooltip text displayed when hovering over the tray icon.
        
        This method dynamically changes the tooltip text for an active tray icon
        without requiring recreation.
        
        Args:
            tray_icon (TrayIcon): The active TrayIcon object to update
            tooltip (str): New tooltip text to display. Empty strings are allowed
                          and will show no tooltip when hovering.
        
        Returns:
            bool: True if the tooltip was updated successfully, False if the update
                 failed due to invalid tray icon or SDL errors.
        
        Implementation:
            1. Validates that the tray icon is currently active
            2. Encodes the tooltip text to UTF-8 bytes for SDL
            3. Updates the tooltip using SDL_SetTrayTooltip()
            4. Provides error handling and logging

        Note:
            Tooltip length limits are platform-dependent. Very long tooltips
            may be truncated by the operating system.
        """
        if not tray_icon.has_valid_pointer():
            Logger.warning("SystemTray: Cannot update tooltip for non-existent tray")
            return False
        
        cdef bytes tooltip_bytes = tooltip.encode('utf-8')
        cdef SDL_Tray *tray = <SDL_Tray*><uintptr_t>tray_icon.get_pointer()
        
        SDL_SetTrayTooltip(tray, tooltip_bytes)

        # Check for errors after the call
        error = <bytes>SDL_GetError()
        if error:
            Logger.error(f"SystemTray: Failed to update tooltip: {error.decode('utf-8', 'replace')}")
            return False
                    
        return True
    
    cdef add_menu_item(self, TrayMenu menu, TrayMenuItem item, index=-1):
        """
        Adds a menu item to an existing SDL tray menu at runtime.
        
        This internal method handles the SDL-level operations required to add
        a new menu item to an active tray menu, including proper type mapping,
        callback registration, and submenu creation.
        
        Args:
            menu (TrayMenu): The target menu to add the item to. Must have a valid
                           SDL menu pointer from menu creation.
            item (TrayMenuItem): The menu item to add. Will be configured with
                               appropriate SDL entry type and properties.
            index (int): Position to insert the item. Use -1 to append at the end,
                        or a specific index to insert at that position.
        
        Returns:
            bool: True if the item was added successfully, False if addition failed
                 due to invalid menu, SDL errors, or resource allocation issues.
        
        Implementation:
            1. Validates menu has valid SDL pointer
            2. Maps Python item type to SDL entry type constants
            3. Creates SDL entry using SDL_InsertTrayEntryAt()
            4. Registers callback for interactive items
            5. Sets initial state (enabled, checked) as needed
            6. Creates and populates submenus recursively
            7. Associates SDL entry pointer with Python item
        
        Type Mapping:
            * 'checkbox' -> SDL_TRAYENTRY_CHECKBOX
            * 'submenu' -> SDL_TRAYENTRY_SUBMENU  
            * 'button' -> SDL_TRAYENTRY_BUTTON
            * 'separator' -> NULL label
        """
        if not menu.has_valid_pointer():
            return False
            
        cdef SDL_TrayMenu *sdl_menu = <SDL_TrayMenu*><uintptr_t>menu.get_pointer()
        cdef SDL_TrayEntry *entry
        cdef bytes label_bytes
        cdef int entry_type
        cdef TrayMenu sub_menu = <TrayMenu>item.sub_menu
        
        # Determine entry type
        if item.type == 'checkbox':
            entry_type = SDL_TRAYENTRY_CHECKBOX
        elif item.type == 'submenu':
            entry_type = SDL_TRAYENTRY_SUBMENU
        else:  # Default to button
            entry_type = SDL_TRAYENTRY_BUTTON
            
        # Create the entry
        if item.type != 'separator':
            label_bytes = item.label.encode('utf-8')
            entry = SDL_InsertTrayEntryAt(sdl_menu, index, label_bytes, entry_type)
        else:
            entry = SDL_InsertTrayEntryAt(sdl_menu, index, NULL, entry_type)
            
        if not entry:
            error = <bytes>SDL_GetError()
            Logger.warning(f"SystemTray: Failed to add menu item: {error.decode('utf-8', 'replace')}")
            return False
            
        # Register the menu item with the entry
        item.set_pointer(<uintptr_t>entry)
            
        # Set callback for clickable items
        if item.type in ('button', 'checkbox'):
            SDL_SetTrayEntryCallback(entry, <SDL_TrayCallback>_tray_item_callback, NULL)
            
        # Set initial enabled state
        if not item.enabled:
            SDL_SetTrayEntryEnabled(entry, 0)
            
        # Set initial checked state for checkboxes
        if item.type == 'checkbox' and item.checked:
            SDL_SetTrayEntryChecked(entry, 1)
            
        # Create submenu if needed
        cdef SDL_TrayMenu *sdl_submenu
        if item.type == 'submenu' and sub_menu:
            sdl_submenu = SDL_CreateTraySubmenu(entry)
            
            if not sdl_submenu:
                error = <bytes>SDL_GetError()
                Logger.error(f"SystemTray: Failed to create submenu: {error.decode('utf-8', 'replace')}")
                return False
            
            # Store the SDL submenu pointer in the Python submenu object
            sub_menu.set_pointer(<uintptr_t>sdl_submenu)
            
            # Populate the submenu with items
            self._populate_menu(sdl_submenu, sub_menu)
            
        return True
    
    cpdef remove_menu_item(self, TrayMenu menu, TrayMenuItem item):
        """
        Removes a menu item from an existing SDL tray menu at runtime.
        
        This method handles the SDL-level operations to remove a menu item from
        an active tray menu and clean up associated resources.
        
        Args:
            menu (TrayMenu): The menu containing the item to remove. Must have
                           a valid SDL menu pointer.
            item (TrayMenuItem): The specific menu item to remove. Must have a
                               valid SDL entry pointer from previous addition.
        
        Returns:
            bool: True if the item was removed successfully, False if removal
                 failed due to invalid pointers or SDL errors.
        
        Implementation:
            1. Validates both menu and item have valid SDL pointers
            2. Retrieves SDL entry pointer from the menu item
            3. Calls SDL_RemoveTrayEntry() to remove from menu
            4. Resets the item's SDL pointer to prevent dangling references
            5. Automatically cleans up submenus if the item was a submenu type
        
        Note:
            After removal, the TrayMenuItem object is still valid but can no longer
            be used for SDL operations until re-added to a menu.
        """
        if not menu.has_valid_pointer() or not item.has_valid_pointer():
            return False
            
        cdef SDL_TrayEntry *entry = <SDL_TrayEntry*><uintptr_t>item.get_pointer()
        
        SDL_RemoveTrayEntry(entry)
        item.set_pointer(0)
            
        return True
    
    cpdef update_menu_item_label(self, TrayMenuItem item):
        """
        Updates the display label of an active menu item.
        
        This method dynamically changes the text shown for a menu item that's
        currently part of an active tray menu.
        
        Args:
            item (TrayMenuItem): The menu item to update. Must have a valid SDL
                               entry pointer and the label property should contain
                               the new text to display.
        
        Returns:
            bool: True if the label was updated successfully, False if the update
                 failed due to invalid item pointer.
        
        Implementation:
            1. Validates the item has a valid SDL entry pointer
            2. Retrieves the current label from the item's label property
            3. Encodes the label text to UTF-8 bytes for SDL
            4. Updates the entry using SDL_SetTrayEntryLabel()
        
        Note:
            The item's label property should be updated before calling this method.
            This is typically handled automatically by the TrayMenuItem's label setter.
        """
        if not item.has_valid_pointer():
            return False
            
        cdef SDL_TrayEntry *entry = <SDL_TrayEntry*><uintptr_t>item.get_pointer()
        cdef bytes label_bytes = item.label.encode('utf-8')
        
        SDL_SetTrayEntryLabel(entry, label_bytes)
            
        return True
    
    cpdef update_menu_item_enabled(self, TrayMenuItem item):
        """
        Updates the enabled/disabled state of an active menu item.
        
        This method dynamically changes whether a menu item can be clicked or
        appears grayed out in the tray menu.
        
        Args:
            item (TrayMenuItem): The menu item to update. Must have a valid SDL
                               entry pointer and the enabled property should contain
                               the new state.
        
        Returns:
            bool: True if the enabled state was updated successfully, False if
                 the update failed due to invalid item pointer.
        
        Implementation:
            1. Validates the item has a valid SDL entry pointer
            2. Retrieves the current enabled state from the item's enabled property
            3. Updates the entry using SDL_SetTrayEntryEnabled() with 1 for enabled,
               0 for disabled
        
        Visual Effect:
            * Enabled items appear normal and respond to clicks
            * Disabled items appear grayed out and ignore click events
            
        Note:
            The item's enabled property should be updated before calling this method.
            This is typically handled automatically by the TrayMenuItem's enabled setter.
        """
        if not item.has_valid_pointer():
            return False
            
        cdef SDL_TrayEntry *entry = <SDL_TrayEntry*><uintptr_t>item.get_pointer()
        
        SDL_SetTrayEntryEnabled(entry, 1 if item.enabled else 0)
            
        return True
    
    cpdef update_menu_item_checked(self, TrayMenuItem item):
        """
        Updates the checked state of an active checkbox menu item.
        
        This method dynamically changes the checkmark display for checkbox-type
        menu items in the tray menu.
        
        Args:
            item (TrayMenuItem): The checkbox menu item to update. Must have a valid
                               SDL entry pointer, be of type 'checkbox', and the
                               checked property should contain the new state.
        
        Returns:
            bool: True if the checked state was updated successfully, False if
                 the update failed due to invalid item pointer or non-checkbox type.
        
        Implementation:
            1. Validates the item has a valid SDL entry pointer
            2. Confirms the item type is 'checkbox' (only checkboxes can be checked)
            3. Retrieves the current checked state from the item's checked property
            4. Updates the entry using SDL_SetTrayEntryChecked() with 1 for checked,
               0 for unchecked
        
        Visual Effect:
            * Checked items display a checkmark or similar indicator
            * Unchecked items show no indicator
            
        Note:
            Only applies to 'checkbox' type menu items. Other item types will
            return False. The item's checked property should be updated before
            calling this method, typically handled by the TrayMenuItem's checked setter.
        """
        if not item.has_valid_pointer() or item.type != 'checkbox':
            return False
            
        cdef SDL_TrayEntry *entry = <SDL_TrayEntry*><uintptr_t>item.get_pointer()
        
        SDL_SetTrayEntryChecked(entry, 1 if item.checked else 0)
            
        return True
    
    cdef _populate_menu(self, SDL_TrayMenu *sdl_menu, TrayMenu menu):
        """
        Recursively populates an SDL menu with items from a Python TrayMenu.
        
        This internal method handles the initial population of a newly created
        SDL menu with all items from the corresponding Python TrayMenu object.
        It supports nested submenus and all menu item types.
        
        Args:
            sdl_menu (SDL_TrayMenu*): The SDL menu structure to populate
            menu (TrayMenu): The Python menu object containing items to add
        
        Implementation:
            1. Iterates through all items in the Python menu
            2. Skips items that already have SDL entries (prevents duplicates)
            3. Maps each item type to appropriate SDL entry type
            4. Creates SDL entries with proper labels and callbacks
            5. Sets initial states (enabled, checked) for each item
            6. Recursively creates and populates submenus
            7. Registers SDL pointers with Python objects for future updates
        
        Error Handling:
            * Individual item creation failures are logged but don't stop processing
            * Submenu creation failures are logged as errors
            * Memory allocation issues are handled gracefully
        
        Note:
            This method is called during initial tray creation and when adding
            submenu items. It ensures proper parent-child relationships between
            menus and handles the complete hierarchy setup.
        """
        cdef SDL_TrayEntry *entry
        cdef bytes label_bytes
        cdef int entry_type

        cdef SDL_TrayMenu *sdl_submenu
        cdef TrayMenuItem item
        cdef TrayMenu sub_menu

        menu_items = menu.get_items()

        for item in menu_items:
            # Skip items that already have entries
            if item.has_valid_pointer():
                continue
                
            sub_menu = item.sub_menu

            # Determine entry type
            if item.type == 'checkbox':
                entry_type = SDL_TRAYENTRY_CHECKBOX
            elif item.type == 'submenu':
                entry_type = SDL_TRAYENTRY_SUBMENU
            else:  # Default to button
                entry_type = SDL_TRAYENTRY_BUTTON
                
            # Create the entry
            if item.type != 'separator':
                label_bytes = item.label.encode('utf-8')
                entry = SDL_InsertTrayEntryAt(sdl_menu, -1, label_bytes, entry_type)
            else:
                entry = SDL_InsertTrayEntryAt(sdl_menu, -1, NULL, entry_type)
                
            if not entry:
                error = <bytes>SDL_GetError()
                Logger.warning(f"SystemTray: Failed to create menu item: {error.decode('utf-8', 'replace')}")
                continue
                
            # Register the menu item with the entry
            item.set_pointer(<uintptr_t>entry)
                
            # Set callback for clickable items
            if item.type in ('button', 'checkbox'):
                SDL_SetTrayEntryCallback(entry, <SDL_TrayCallback>_tray_item_callback, NULL)
                
            # Set initial enabled state
            if not item.enabled:
                SDL_SetTrayEntryEnabled(entry, 0)
                
            # Set initial checked state for checkboxes
            if item.type == 'checkbox' and item.checked:
                SDL_SetTrayEntryChecked(entry, 1)
                
            # Create submenu if needed
            if item.type == 'submenu' and sub_menu:
                sdl_submenu = SDL_CreateTraySubmenu(entry)
                
                if not sdl_submenu:
                    error = <bytes>SDL_GetError()
                    Logger.error(f"SystemTray: Failed to create submenu: {error.decode('utf-8', 'replace')}")
                    continue
                
                # Store the SDL submenu pointer in the Python submenu object
                sub_menu.set_pointer(<uintptr_t>sdl_submenu)
                
                # Populate the submenu with items
                self._populate_menu(sdl_submenu, sub_menu)
