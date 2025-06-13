include "../../../kivy/lib/sdl3.pxi"
include "../../include/config.pxi"

from os import environ
from kivy.config import Config
from kivy.logger import Logger
from kivy.graphics.cgl cimport *
from libc.stdint cimport uintptr_t
from kivy.logger import Logger
from kivy.resources import resource_find
from libc.stdint cimport uintptr_t
import weakref
# from kivy.core.window import WindowBase


if not environ.get('KIVY_DOC_INCLUDE'):
    is_desktop = Config.get('kivy', 'desktop') == '1'


# Global dictionary to track system tray menu items
# Stores weak references to prevent memory leaks
_tray_menu_registry = weakref.WeakValueDictionary()


cdef void _tray_item_callback(void *userdata, SDL_TrayEntry *entry) nogil:
    """
    C callback function invoked when a tray menu item is clicked.
    
    Args:
        userdata: Pointer containing user data (not used)
        entry: SDL_TrayEntry that was clicked
    """
    with gil:
        # Find the menu item for this entry
        addr = <uintptr_t>entry
        py_addr = <object>addr
        menu_item = _tray_menu_registry.get(py_addr)
        
        if menu_item is None:
            Logger.warning(f"TrayIcon: No menu item found for pointer {<object>entry}")
            return
        
        # For checkbox items, toggle the checked state
        if menu_item.type == 'checkbox':
            menu_item.checked = not menu_item.checked
        
        # Call the menu item callback if it exists
        if menu_item.callback:
            try:
                menu_item.callback(menu_item)
            except Exception as e:
                Logger.error(f"TrayIcon: Exception in callback: {e}")


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
    
    Properties:
        label (str): The text shown on the menu item
        enabled (bool): Whether the menu item is clickable or disabled
        checked (bool): Whether the menu item shows a checkmark (for checkbox items)
        type (str): The menu item type ('button', 'checkbox', 'separator', 'submenu')
        menu (TrayMenu): For submenu type items, contains the submenu items
    """

    cdef object __weakref__

    cdef str __label
    cdef object __callback
    cdef bint __enabled
    cdef bint __checked
    cdef str __type
    cdef TrayMenu __parent_menu
    
    def __init__(self, label='', callback=None, enabled=True, checked=False, 
                type='button', menu=None, **kwargs):
        """
        Initializes a tray menu item.
        
        Args:
            label (str): The text shown for this menu item
            callback (callable): Function to call when the item is clicked
            enabled (bool): Whether the item is enabled (can be clicked)
            checked (bool): Whether the item shows a checkmark
            type (str): The menu item type ('button', 'checkbox', 'separator', 'submenu')
            menu (TrayMenu): For submenu types, contains submenu items
        """
        self.__label = label
        self.__callback = callback
        self.__enabled = enabled
        self.__checked = checked
        self.__type = type
        self.__parent_menu = menu

    cpdef void _on_pointer_set(self, uintptr_t value):
        if value != 0:  # If not NULL
            _tray_menu_registry[value] = self

    @property
    def label(self):
        """The text shown on the menu item."""
        return self.__label

    @label.setter
    def label(self, value):
        if value != self.__label:
            self.__label = value
            if self._can_update():
                _tray_icon_handler.update_menu_item_label(self)

    @property
    def enabled(self):
        """Whether the menu item is clickable or disabled."""
        return self.__enabled

    @enabled.setter
    def enabled(self, value):
        if value != self.__enabled:
            self.__enabled = value
            if self._can_update():
                _tray_icon_handler.update_menu_item_enabled(self)

    @property
    def checked(self):
        """Whether the menu item shows a checkmark (for checkbox items)."""
        return self.__checked

    @checked.setter
    def checked(self, value):
        if value != self.__checked:
            self.__checked = value
            if self._can_update():
                _tray_icon_handler.update_menu_item_checked(self)

    @property
    def callback(self):
        """Function to call when the item is clicked."""
        return self.__callback
    
    @callback.setter
    def callback(self, value):
        if value != self.__callback:
            self.__callback = value

    @property
    def type(self):
        """The menu item type ('button', 'checkbox', 'separator', 'submenu')."""
        return self.__type

    @property
    def parent_menu(self):
        """For submenu type items, contains the submenu items."""
        return self.__parent_menu


cdef class TrayMenu(_SDLPointerHandler):
    """Represents a system tray menu or submenu."""

    cdef list __items

    def __init__(self) -> None:
        self.__items = []

    cpdef list get_items(self):
        return self.__items
    
    cpdef void add_item(self, TrayMenuItem item, index=-1):
        """
        Add an item to the menu.
        
        Args:
            item: TrayMenuItem or dict to add to the menu
            index: Index where to insert the item (-1 to append to the end)
        """
        if isinstance(item, dict):
            # Handle submenu case
            if 'submenu' in item:
                submenu = TrayMenu(items=item.pop('submenu'))
                item['menu'] = submenu
                item['type'] = 'submenu'
            item = TrayMenuItem(**item)
        elif item == 'separator':
            item = TrayMenuItem(type='separator')
        
        if not isinstance(item, TrayMenuItem):
            Logger.warning(f"SystemTray: Cannot add invalid item type: {type(item)}")
            return
        
        # If the menu already exists in SDL, add the item there too
        if self._can_update():
            _tray_icon_handler.add_menu_item(self, item, index)
        
        if index < 0 or index >= len(self.__items):
            self.__items.append(item)
        else:
            self.__items.insert(index, item)
    
    cpdef void remove_item(self, TrayMenuItem item):
        """
        Remove an item from the menu.
        
        Args:
            item: TrayMenuItem to remove
        """
        if item in self.__items:
            # If the menu exists in SDL, remove the item from there too
            if self.has_valid_pointer() and item.has_valid_pointer() and _tray_icon_handler:
                _tray_icon_handler.remove_menu_item(self, item)
            
            self.__items.remove(item)
    
    cpdef void clear(self):
        """Remove all items from the menu."""
        # If the menu exists in SDL, remove all items from there too
        cdef TrayMenuItem item
        if self._can_update():
            for item in list(self.__items):
                if item.has_valid_pointer():
                    _tray_icon_handler.remove_menu_item(self, item)
        
        self.__items = []


cdef class TrayIcon(_SDLPointerHandler):
    """
    Manages a system tray icon with menu functionality.
    
    Properties:
        icon_path (str): Path to the icon image
        tooltip (str): Tooltip text shown when hovering over the tray icon
        menu (TrayMenu): The menu displayed when clicking on the tray icon
        visible (bool): Whether the tray icon is currently visible
    """
    
    cdef str __icon_path
    cdef str __tooltip
    cdef TrayMenu __menu
    cdef bint __visible

    def __init__(self, icon_path='', tooltip='Kivy Application', menu=None, **kwargs):
        """
        Initializes a system tray icon.
        
        Args:
            icon_path (str): Path to the icon image file
            tooltip (str): Text to be displayed when hovering over the icon
            menu (TrayMenu or list): Menu to be displayed when clicking on the icon
        """
        self.__icon_path = icon_path or resource_find('data/logo/kivy-icon-32.png')
        self.tooltip = tooltip
        
        # Process the menu if provided
        if menu:
            if isinstance(menu, list):
                self.__menu = TrayMenu(items=menu)
            elif isinstance(menu, TrayMenu):
                self.__menu = menu
            else:
                Logger.warning(f"TrayIcon: Invalid menu type: {type(menu)}")
                self.__menu = TrayMenu()
        else:
            self.__menu = TrayMenu()
   
    cpdef bint create(self):
        """Creates and displays the tray icon."""
        if self.__visible:
            Logger.warning("TrayIcon: The tray icon is already visible")
            return False
        
        global _tray_icon_handler
        if _tray_icon_handler is None:
            _tray_icon_handler = _TrayIconHandler()
        
        self.__visible = _tray_icon_handler.create_tray(self)
        return self.__visible
    
    def destroy(self):
        """Removes the tray icon from the system tray."""
        if not self.__visible:
            Logger.warning("TrayIcon: The tray icon is not visible")
            return False
        
        if _tray_icon_handler:
            return _tray_icon_handler.destroy_tray(self)
        return False

    @property
    def icon(self):
        return self.__icon_path
        
    @icon.setter
    def icon(self, value):
        """
        Updates the tray icon image.
        
        Args:
            value (str): Path to the new icon image file
        """
        self.__icon_path = value
        if self.__visible and _tray_icon_handler:
            _tray_icon_handler.update_tray(self, value)

    @property
    def tooltip(self):
        return self.__tooltip
        
    @tooltip.setter
    def tooltip(self, value):
        """
        Updates the tray icon tooltip.
        
        Args:
            value (str): New tooltip text
        """
        self.__tooltip = value
        if self.__visible and _tray_icon_handler:
            _tray_icon_handler.update_tray_tooltip(self, value)

    @property
    def visible(self):
        return self.__visible

    @visible.setter
    def visible(self, value):
        self.__visible = value

    @property
    def menu(self):
        return self.__menu
        
    def clear_menu(self):
        """
        Removes all items from the tray icon's menu.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.__visible:
            Logger.warning("TrayIcon: Cannot clear menu for non-visible tray icon")
            return False
            
        if not self.__menu:
            Logger.warning("TrayIcon: No menu exists to clear")
            return False
            
        self.__menu.clear()
        return True


# Global variable to store the handler instance
cdef _TrayIconHandler _tray_icon_handler


cdef class _TrayIconHandler:
    """Internal class for managing SDL tray icon resources."""
    
    cpdef bint create_tray(self, TrayIcon tray_icon):
        """
        Creates a system tray icon.
        
        Args:
            tray_icon: Python TrayIcon object
        """
        # Load the icon image
        cdef bytes icon_path_bytes = tray_icon.icon.encode('utf-8')
        cdef bytes tooltip_bytes = tray_icon.tooltip.encode('utf-8')
        
        Logger.debug(f"TrayIcon: Loading icon from {tray_icon.icon}")
        cdef SDL_Surface *icon_surface = IMG_Load(icon_path_bytes)
        
        if not icon_surface:
            error = <bytes>SDL_GetError()
            Logger.error(f"TrayIcon: Failed to load icon: {error.decode('utf-8', 'replace')}")
            return False
        
        # Create the tray icon
        Logger.debug(f"TrayIcon: Creating tray with tooltip '{tray_icon.tooltip}'")
        cdef SDL_Tray *tray = SDL_CreateTray(icon_surface, tooltip_bytes)
        
        if not tray:
            error = <bytes>SDL_GetError()
            Logger.error(f"TrayIcon: Failed to create tray: {error.decode('utf-8', 'replace')}")
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
                Logger.error(f"TrayIcon: Failed to create menu: {error.decode('utf-8', 'replace')}")
                SDL_DestroyTray(tray)
                SDL_DestroySurface(icon_surface)
                return False
            
            # Store the SDL menu pointer in the Python menu object
            menu.set_pointer(<uintptr_t>sdl_menu)
            
            # Populate the menu with items
            self._populate_menu(sdl_menu, menu)
        
        Logger.info(f"TrayIcon: Successfully created tray icon")

        tray_icon.set_pointer(<uintptr_t>tray)
        
        return True
    
    cpdef destroy_tray(self, TrayIcon tray_icon):
        """
        Destroys the tray icon and cleans up resources.
        
        Args:
            tray_icon: Python TrayIcon object
        """
        cdef SDL_Tray *tray
        if tray_icon.has_valid_pointer():
            Logger.debug("TrayIcon: Destroying tray icon")
            tray = <SDL_Tray*><uintptr_t>tray_icon.get_pointer()
            SDL_DestroyTray(tray)
            tray_icon.visible = False
            tray_icon.set_pointer(0)
            return True
        return False
    
    cpdef update_tray(self, TrayIcon tray_icon, str icon_path):
        """
        Updates the tray icon image.
        
        Args:
            tray_icon: Python TrayIcon object
            icon_path: Path to the new icon image file
        """
        if not tray_icon.has_valid_pointer():
            Logger.warning("TrayIcon: Cannot update icon for non-existent tray")
            return False
        
        # Load the new icon image
        cdef bytes icon_path_bytes = icon_path.encode('utf-8')
        cdef SDL_Surface *new_icon_surface = IMG_Load(icon_path_bytes)
        
        if not new_icon_surface:
            error = <bytes>SDL_GetError()
            Logger.error(f"TrayIcon: Failed to load new icon: {error.decode('utf-8', 'replace')}")
            return False
        
        # Update the tray icon
        cdef SDL_Tray *tray = <SDL_Tray*><uintptr_t>tray_icon.get_pointer()
        SDL_SetTrayIcon(tray, new_icon_surface)

        # Check for errors after the call
        error = <bytes>SDL_GetError()
        if error:
            Logger.error(f"TrayIcon: Failed to update icon: {error.decode('utf-8', 'replace')}")
            SDL_DestroySurface(new_icon_surface)
            return False
        
        # SDL_SetTrayIcon takes ownership of the surface, we don't need to destroy it
        return True
    
    cpdef update_tray_tooltip(self, TrayIcon tray_icon, str tooltip):
        """
        Updates the tray icon tooltip.
        
        Args:
            tray_icon: Python TrayIcon object
            tooltip: New tooltip text
        """
        if not tray_icon.has_valid_pointer():
            Logger.warning("TrayIcon: Cannot update tooltip for non-existent tray")
            return False
        
        cdef bytes tooltip_bytes = tooltip.encode('utf-8')
        cdef SDL_Tray *tray = <SDL_Tray*><uintptr_t>tray_icon.get_pointer()
        
        SDL_SetTrayTooltip(tray, tooltip_bytes)

        # Check for errors after the call
        error = <bytes>SDL_GetError()
        if error:
            Logger.error(f"TrayIcon: Failed to update tooltip: {error.decode('utf-8', 'replace')}")
            return False
                    
        return True
    
    cdef add_menu_item(self, TrayMenu menu, TrayMenuItem item, index=-1):
        """
        Adds a menu item to an existing menu.
        
        Args:
            menu: Python TrayMenu object
            item: Python TrayMenuItem object
            index: Index where to insert the item (-1 to append at the end)
        """
        if not menu.has_valid_pointer():
            return False
            
        cdef SDL_TrayMenu *sdl_menu = <SDL_TrayMenu*><uintptr_t>menu.get_pointer()
        cdef SDL_TrayEntry *entry
        cdef bytes label_bytes
        cdef int entry_type
        cdef TrayMenu parent_menu = <TrayMenu>item.parent_menu
        
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
            Logger.warning(f"TrayIcon: Failed to add menu item: {error.decode('utf-8', 'replace')}")
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
        if item.type == 'submenu' and parent_menu:
            sdl_submenu = SDL_CreateTraySubmenu(entry)
            
            if not sdl_submenu:
                error = <bytes>SDL_GetError()
                Logger.error(f"TrayIcon: Failed to create submenu: {error.decode('utf-8', 'replace')}")
                return False
            
            # Store the SDL submenu pointer in the Python submenu object
            parent_menu.set_pointer(<uintptr_t>sdl_submenu)
            
            # Populate the submenu with items
            self._populate_menu(sdl_submenu, parent_menu)
            
        return True
    
    cpdef remove_menu_item(self, TrayMenu menu, TrayMenuItem item):
        """
        Removes a menu item from an existing menu.
        
        Args:
            menu: Python TrayMenu object
            item: Python TrayMenuItem object
        """
        if not menu.has_valid_pointer() or not item.has_valid_pointer():
            return False
            
        cdef SDL_TrayEntry *entry = <SDL_TrayEntry*><uintptr_t>item.get_pointer()
        
        SDL_RemoveTrayEntry(entry)
        item.set_pointer(0)
            
        return True
    
    cpdef update_menu_item_label(self, TrayMenuItem item):
        """
        Updates a menu item's label.
        
        Args:
            item: Python TrayMenuItem object
        """
        if not item.has_valid_pointer():
            return False
            
        cdef SDL_TrayEntry *entry = <SDL_TrayEntry*><uintptr_t>item.get_pointer()
        cdef bytes label_bytes = item.label.encode('utf-8')
        
        SDL_SetTrayEntryLabel(entry, label_bytes)
            
        return True
    
    cpdef update_menu_item_enabled(self, TrayMenuItem item):
        """
        Updates a menu item's enabled state.
        
        Args:
            item: Python TrayMenuItem object
        """
        if not item.has_valid_pointer():
            return False
            
        cdef SDL_TrayEntry *entry = <SDL_TrayEntry*><uintptr_t>item.get_pointer()
        
        SDL_SetTrayEntryEnabled(entry, 1 if item.enabled else 0)
            
        return True
    
    cpdef update_menu_item_checked(self, TrayMenuItem item):
        """
        Updates a menu item's checked state.
        
        Args:
            item: Python TrayMenuItem object
        """
        if not item.has_valid_pointer() or item.type != 'checkbox':
            return False
            
        cdef SDL_TrayEntry *entry = <SDL_TrayEntry*><uintptr_t>item.get_pointer()
        
        SDL_SetTrayEntryChecked(entry, 1 if item.checked else 0)
            
        return True
    
    cdef _populate_menu(self, SDL_TrayMenu *sdl_menu, TrayMenu menu):
        """
        Populates a menu with items.
        
        Args:
            sdl_menu: SDL_TrayMenu pointer
            menu: Python TrayMenu object
        """
        cdef SDL_TrayEntry *entry
        cdef bytes label_bytes
        cdef int entry_type

        cdef SDL_TrayMenu *sdl_submenu
        cdef TrayMenuItem item
        cdef TrayMenu parent_menu

        menu_items = menu.get_items()

        for item in menu_items:
            # Skip items that already have entries
            if item.has_valid_pointer():
                continue
                
            parent_menu = item.parent_menu

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
                Logger.warning(f"TrayIcon: Failed to create menu item: {error.decode('utf-8', 'replace')}")
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
            if item.type == 'submenu' and parent_menu:
                sdl_submenu = SDL_CreateTraySubmenu(entry)
                
                if not sdl_submenu:
                    error = <bytes>SDL_GetError()
                    Logger.error(f"TrayIcon: Failed to create submenu: {error.decode('utf-8', 'replace')}")
                    continue
                
                # Store the SDL submenu pointer in the Python submenu object
                parent_menu.set_pointer(<uintptr_t>sdl_submenu)
                
                # Populate the submenu with items
                self._populate_menu(sdl_submenu, parent_menu)
