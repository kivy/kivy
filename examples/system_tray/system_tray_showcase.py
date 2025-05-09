import os
from kivy.app import App
from kivy.core.tray import TrayIcon, TrayMenu, TrayMenuItem
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import ObjectProperty
from kivy.resources import resource_add_path, resource_find
from kivy.uix.boxlayout import BoxLayout

Builder.load_string("""
<MainUI>:
    orientation: 'vertical'
    padding: 10
    spacing: 10
    Label:
        id: status_label
        text: "Status: Ready"
        size_hint: 1, 0.4
        font_size: dp(18)
    BoxLayout:
        orientation: 'horizontal'
        size_hint: 1, 0.1
        spacing: 5
        TextInput:
            id: item_label_input
            hint_text: "Item name"
            multiline: False
            size_hint: 0.5, 1
        TextInput:
            id: item_index_input
            hint_text: "Index (optional)"
            multiline: False
            input_filter: 'int'
            size_hint: 0.2, 1
        Button:
            text: "Add"
            size_hint: 0.3, 1
            on_press: root.add_item_from_input()
    BoxLayout:
        orientation: 'horizontal'
        size_hint: 1, 0.1
        spacing: 5
        TextInput:
            id: remove_label_input
            hint_text: "Name to remove"
            multiline: False
            size_hint: 0.7, 1
        Button:
            text: "Remove"
            size_hint: 0.3, 1
            on_press: root.remove_item_from_input()
    BoxLayout:
        orientation: 'horizontal'
        size_hint: 1, 0.1
        spacing: 5
        TextInput:
            id: tooltip_input
            hint_text: "Enter new tooltip text"
            multiline: False
            size_hint: 0.7, 1
        Button:
            text: "Update Tooltip"
            size_hint: 0.3, 1
            on_press: root.update_tooltip()
    BoxLayout:
        orientation: 'horizontal'
        size_hint: 1, 0.1
        spacing: 5
        TextInput:
            id: icon_path_input
            hint_text: "Path to icon file (png, ico, jpg, jpeg, gif, svg)"
            multiline: False
            size_hint: 0.7, 1
        Button:
            text: "Change Icon"
            size_hint: 0.3, 1
            on_press: root.change_icon_from_path()
    Button:
        text: "Add Dynamic Item"
        size_hint: 1, 0.1
        on_press: root.add_dynamic_item()
    Button:
        text: "Create Submenu"
        size_hint: 1, 0.1
        on_press: root.add_submenu()
    Button:
        text: "Clear Menu"
        size_hint: 1, 0.1
        on_press: root.clear_menu()
    Button:
        text: "Rebuild Default Menu"
        size_hint: 1, 0.1
        on_press: root.rebuild_default_menu()
""")


class TrayManagerApp(App):
    def build(self):
        main_ui = MainUI()
        main_ui.app = self
        main_ui.build_default_menu()
        return main_ui

    def on_stop(self):
        """Removes the system tray icon when the application is closed"""
        if hasattr(self.root, "tray_icon") and self.root.tray_icon:
            self.root.tray_icon.destroy()


class MainUI(BoxLayout):
    """Main interface for managing the system tray menu"""

    app = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dynamic_items = []
        self.current_icon_path = resource_find("data/logo/kivy-icon-32.png")

    def build_default_menu(self):
        """Builds the default initial system tray menu"""
        self.tray_menu = TrayMenu()

        # Checkbox item to demonstrate states
        self.notifications_item = TrayMenuItem(
            label="Notifications",
            type="checkbox",
            checked=True,
            callback=self.on_menu_item_clicked,
        )
        self.tray_menu.add_item(self.notifications_item)

        # Separator to visually organize the menu
        self.tray_menu.add_item(TrayMenuItem(type="separator"))

        # Simple button item
        self.about_item = TrayMenuItem(
            label="About", type="button", callback=self.on_menu_item_clicked
        )
        self.tray_menu.add_item(self.about_item)

        self.tray_menu.add_item(TrayMenuItem(type="separator"))

        # Exit application item
        self.exit_item = TrayMenuItem(
            label="Exit", type="button", callback=lambda x: self.app.stop()
        )
        self.tray_menu.add_item(self.exit_item)

        # Create the system tray icon if it doesn't exist
        if not hasattr(self, "tray_icon") or not self.tray_icon:
            self.tray_icon = TrayIcon(
                icon_path=self.current_icon_path,
                tooltip="Tray Menu Manager",
                menu=self.tray_menu,
            )
            if not self.tray_icon.create():
                Logger.error("MainUI: Failed to create tray icon")

    def on_menu_item_clicked(self, item):
        """Callback for menu items when clicked"""
        Logger.info(f"MainUI: Item '{item.label}' clicked")

        if item.type == "checkbox":
            state = "enabled" if item.checked else "disabled"
            self.ids.status_label.text = f"{item.label}: {state}"
        else:
            self.ids.status_label.text = f"Clicked: {item.label}"

    def add_item_from_input(self):
        """Adds an item based on input text, with option to specify an index"""
        label_text = self.ids.item_label_input.text.strip()
        if not label_text:
            self.ids.status_label.text = "Enter a name for the item"
            return

        # Check the index (optional)
        index_text = self.ids.item_index_input.text.strip()
        index = -1  # add to end as default
        menu_items = self.tray_menu.get_items()
        if index_text:
            try:
                index = int(index_text)
                if index < 0 or index > len(menu_items):
                    self.ids.status_label.text = (
                        f"Invalid index. Use 0-{len(menu_items)}"
                    )
                    return
            except ValueError:
                self.ids.status_label.text = "Index must be an integer"
                return

        # Create and add the new item
        new_item = TrayMenuItem(
            label=label_text,
            type="button",
            callback=self.on_menu_item_clicked,
        )
        self.tray_menu.add_item(new_item, index)

        # Update status and clear inputs
        status_msg = (
            f"Item added at {index}: {label_text}"
            if index >= 0
            else f"Item added: {label_text}"
        )
        self.ids.status_label.text = status_msg
        self.ids.item_label_input.text = ""
        self.ids.item_index_input.text = ""

    def remove_item_from_input(self):
        """Removes an item based on input text"""
        label_text = self.ids.remove_label_input.text.strip()
        if not label_text:
            self.ids.status_label.text = "Enter the name of the item to remove"
            return

        # Find and remove the item
        menu_items = self.tray_menu.get_items()
        for item in list(menu_items):
            if item.label == label_text:
                self.tray_menu.remove_item(item)
                self.ids.status_label.text = f"Item removed: {label_text}"
                self.ids.remove_label_input.text = ""
                return

        self.ids.status_label.text = f"Item not found: {label_text}"

    def add_dynamic_item(self):
        """Adds a new dynamic item to the menu"""
        menu_items = self.tray_menu.get_items()
        counter = len(
            [i for i in menu_items if i.label and i.label.startswith("Dynamic")]
        )

        new_item = TrayMenuItem(
            label=f"Dynamic {counter + 1}",
            type="button",
            callback=self.on_menu_item_clicked,
        )
        self.tray_menu.add_item(new_item)
        self.dynamic_items.append(new_item)
        self.ids.status_label.text = f"Added: {new_item.label}"

    def add_submenu(self):
        """Adds a submenu with multiple items to demonstrate submenu functionality"""
        submenu = TrayMenu()

        # Create submenu items of different types
        option1 = TrayMenuItem(
            label="Option 1",
            type="button",
            callback=self.on_menu_item_clicked,
        )
        option2 = TrayMenuItem(
            label="Option 2",
            type="checkbox",
            checked=True,
            callback=self.on_menu_item_clicked,
        )
        submenu.add_item(option1)
        submenu.add_item(option2)
        self.tray_menu.add_item(TrayMenuItem(type="separator"))

        option3 = TrayMenuItem(
            label="Option 3",
            type="button",
            callback=self.on_menu_item_clicked,
        )
        submenu.add_item(option3)

        # Name the submenu dynamically
        menu_items = self.tray_menu.get_items()
        counter = len(
            [i for i in menu_items if i.label and i.label.startswith("Submenu")]
        )
        submenu_item = TrayMenuItem(
            label=f"Submenu {counter + 1}", type="submenu", menu=submenu
        )
        self.tray_menu.add_item(submenu_item)
        self.ids.status_label.text = f"Submenu added: {submenu_item.label}"

    def clear_menu(self):
        """Clears all items from the menu"""
        self.tray_menu.clear()
        self.dynamic_items = []
        self.ids.status_label.text = "Menu cleared"

    def rebuild_default_menu(self):
        """Rebuilds the original default menu"""
        self.tray_menu.clear()
        self.dynamic_items = []

        # Recreate the essential menu items
        self.notifications_item = TrayMenuItem(
            label="Notifications",
            type="checkbox",
            checked=True,
            callback=self.on_menu_item_clicked,
        )
        self.tray_menu.add_item(self.notifications_item)
        self.tray_menu.add_item(TrayMenuItem(type="separator"))
        self.about_item = TrayMenuItem(
            label="About", type="button", callback=self.on_menu_item_clicked
        )
        self.tray_menu.add_item(self.about_item)
        self.tray_menu.add_item(TrayMenuItem(type="separator"))
        self.exit_item = TrayMenuItem(
            label="Exit", type="button", callback=lambda x: self.app.stop()
        )
        self.tray_menu.add_item(self.exit_item)
        self.ids.status_label.text = "Default menu rebuilt"

    def update_tooltip(self):
        """Updates the tooltip text of the system tray icon"""
        new_tooltip = self.ids.tooltip_input.text.strip()
        if not new_tooltip:
            self.ids.status_label.text = "Please enter tooltip text"
            return
        self.tray_icon.tooltip = new_tooltip
        self.ids.status_label.text = f"Tooltip updated: {new_tooltip}"
        self.ids.tooltip_input.text = ""

    def change_icon_from_path(self):
        """Changes the tray icon using a provided path"""
        icon_path = self.ids.icon_path_input.text.strip()
        if not icon_path:
            self.ids.status_label.text = (
                "Please enter a valid path to an icon file"
            )
            return

        # Check if the file exists
        if not os.path.exists(icon_path):
            self.ids.status_label.text = f"File not found: {icon_path}"
            return

        # Check if it's a valid image file
        valid_extensions = [".png", ".ico", ".jpg", ".jpeg", ".gif", ".svg"]
        file_ext = os.path.splitext(icon_path)[1].lower()
        if file_ext not in valid_extensions:
            self.ids.status_label.text = f"Not a valid image file: {file_ext}"
            return

        try:
            # Destroy and recreate the tray icon with the new icon
            if hasattr(self, "tray_icon") and self.tray_icon:
                self.tray_icon.destroy()
            self.current_icon_path = icon_path
            self.tray_icon = TrayIcon(
                icon_path=self.current_icon_path,
                tooltip="Tray Menu Manager",
                menu=self.tray_menu,
            )
            if not self.tray_icon.create():
                Logger.error("MainUI: Failed to create tray icon with new icon")
                self.ids.status_label.text = "Failed to apply new icon"
                return
            self.ids.status_label.text = (
                f"Icon changed: {os.path.basename(icon_path)}"
            )
        except Exception as e:
            Logger.error(f"MainUI: Error changing icon: {e}")
            self.ids.status_label.text = f"Error changing icon: {str(e)}"


if __name__ == "__main__":
    TrayManagerApp().run()
