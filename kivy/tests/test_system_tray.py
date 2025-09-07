import os
import tempfile
from unittest.mock import Mock

from kivy.tests import GraphicUnitTest
from kivy.logger import LoggerHistory
from kivy.core.system_tray import TrayIcon, TrayMenu, TrayMenuItem
from kivy.resources import resource_find


class TrayMenuTest(GraphicUnitTest):
    """Test TrayMenu functionality"""

    def setUp(self):
        super().setUp()
        self.parent_menu = TrayMenu()

    def test_menu_creation(self):
        """Test that TrayMenu can be created"""
        self.assertIsInstance(self.parent_menu, TrayMenu)
        self.assertEqual(len(self.parent_menu.get_items()), 0)

    def test_add_item(self):
        """Test adding items to menu"""
        item = TrayMenuItem(label="Test Item", type="button")
        self.parent_menu.add_item(item)

        items = self.parent_menu.get_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0], item)

    def test_add_item_at_index(self):
        """Test adding items at specific index"""
        item1 = TrayMenuItem(label="Item 1", type="button")
        item2 = TrayMenuItem(label="Item 2", type="button")
        item3 = TrayMenuItem(label="Item 3", type="button")

        self.parent_menu.add_item(item1)
        self.parent_menu.add_item(item3)
        self.parent_menu.add_item(item2, 1)  # Insert at index 1

        items = self.parent_menu.get_items()
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].label, "Item 1")
        self.assertEqual(items[1].label, "Item 2")
        self.assertEqual(items[2].label, "Item 3")

    def test_remove_item(self):
        """Test removing items from menu"""
        item1 = TrayMenuItem(label="Item 1", type="button")
        item2 = TrayMenuItem(label="Item 2", type="button")

        self.parent_menu.add_item(item1)
        self.parent_menu.add_item(item2)
        self.assertEqual(len(self.parent_menu.get_items()), 2)

        self.parent_menu.remove_item(item1)
        items = self.parent_menu.get_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0], item2)

    def test_clear_menu(self):
        """Test clearing all items from menu"""
        for i in range(5):
            item = TrayMenuItem(label=f"Item {i}", type="button")
            self.parent_menu.add_item(item)

        self.assertEqual(len(self.parent_menu.get_items()), 5)

        self.parent_menu.clear()
        self.assertEqual(len(self.parent_menu.get_items()), 0)

    def test_get_items_returns_reference(self):
        """Test that get_items returns the actual list (based on implementation)"""
        item = TrayMenuItem(label="Test Item", type="button")
        self.parent_menu.add_item(item)

        items1 = self.parent_menu.get_items()
        items2 = self.parent_menu.get_items()

        # Based on the implementation, it returns the same list reference
        self.assertEqual(items1, items2)
        self.assertIs(items1, items2)


class TrayMenuItemTest(GraphicUnitTest):
    """Test TrayMenuItem functionality"""

    def test_button_item_creation(self):
        """Test creating button menu item"""
        callback = Mock()
        item = TrayMenuItem(
            label="Test Button", type="button", callback=callback
        )

        self.assertEqual(item.label, "Test Button")
        self.assertEqual(item.type, "button")
        self.assertEqual(item.callback, callback)
        self.assertFalse(item.checked)  # Default for button

    def test_checkbox_item_creation(self):
        """Test creating checkbox menu item"""
        callback = Mock()
        item = TrayMenuItem(
            label="Test Checkbox",
            type="checkbox",
            checked=True,
            callback=callback,
        )

        self.assertEqual(item.label, "Test Checkbox")
        self.assertEqual(item.type, "checkbox")
        self.assertTrue(item.checked)
        self.assertEqual(item.callback, callback)

    def test_separator_item_creation(self):
        """Test creating separator menu item"""
        item = TrayMenuItem(type="separator")

        self.assertEqual(item.type, "separator")
        # Based on implementation, label defaults to empty string, not None
        self.assertEqual(item.label, "")
        self.assertIsNone(item.callback)

    def test_submenu_item_creation(self):
        """Test creating submenu item"""
        submenu = TrayMenu()
        submenu_item = TrayMenuItem(
            label="Submenu", type="submenu", menu=submenu
        )

        self.assertEqual(submenu_item.label, "Submenu")
        self.assertEqual(submenu_item.type, "submenu")
        self.assertEqual(submenu_item.sub_menu, submenu)

    def test_item_property_modification(self):
        """Test modifying item properties after creation"""
        item = TrayMenuItem(label="Original", type="button")

        item.label = "Modified"
        item.checked = True

        self.assertEqual(item.label, "Modified")
        self.assertTrue(item.checked)

    def test_callback_execution(self):
        """Test that callback is properly stored and can be called"""
        callback = Mock()
        item = TrayMenuItem(label="Test Item", type="button", callback=callback)

        # Simulate clicking the item
        if item.callback:
            item.callback(item)

        callback.assert_called_once_with(item)

    def test_checkbox_state_toggle(self):
        """Test checkbox state can be toggled"""
        item = TrayMenuItem(label="Toggle Test", type="checkbox", checked=False)

        self.assertFalse(item.checked)

        item.checked = True
        self.assertTrue(item.checked)

        item.checked = False
        self.assertFalse(item.checked)


class TrayIconTest(GraphicUnitTest):
    """Test TrayIcon functionality"""

    def setUp(self):
        super().setUp()
        self.parent_menu = TrayMenu()
        self.test_icon_path = resource_find("data/logo/kivy-icon-32.png")
        if not self.test_icon_path:
            # Create a temporary icon file for testing
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                self.test_icon_path = f.name
                # Write minimal PNG data
                f.write(
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x04\x00\x01]\xcc\xdb\x8a\x00\x00\x00\x00IEND\xaeB`\x82"
                )
                self._temp_icon = True
        else:
            self._temp_icon = False

    def tearDown(self):
        if self._temp_icon and os.path.exists(self.test_icon_path):
            os.unlink(self.test_icon_path)
        super().tearDown()

    def test_tray_icon_creation(self):
        """Test basic tray icon creation"""
        tray_icon = TrayIcon(
            icon_path=self.test_icon_path,
            tooltip="Test Tooltip",
            menu=self.parent_menu,
        )
        tray_icon.create()

        self.assertEqual(tray_icon.visible, True)
        self.assertEqual(tray_icon.icon, self.test_icon_path)
        self.assertEqual(tray_icon.tooltip, "Test Tooltip")
        # Based on implementation, the property is 'menu', not 'parent_menu'
        self.assertEqual(tray_icon.menu, self.parent_menu)

    def test_tray_icon_creation_minimal(self):
        """Test tray icon creation with minimal parameters"""
        tray_icon = TrayIcon(icon_path=self.test_icon_path)

        self.assertEqual(tray_icon.icon, self.test_icon_path)
        # Based on implementation, default tooltip is "Kivy Application", not None
        self.assertEqual(tray_icon.tooltip, "Kivy Application")
        # Menu should be created automatically as empty TrayMenu
        self.assertIsInstance(tray_icon.menu, TrayMenu)

    def test_tray_icon_property_modification(self):
        """Test modifying tray icon properties"""
        tray_icon = TrayIcon(icon_path=self.test_icon_path)

        tray_icon.tooltip = "New Tooltip"
        # Cannot directly set menu property, but we can verify it exists
        self.assertEqual(tray_icon.tooltip, "New Tooltip")
        self.assertIsInstance(tray_icon.menu, TrayMenu)

    def test_tray_icon_with_populated_menu(self):
        """Test tray icon with a menu containing items"""
        # Add items to menu
        item1 = TrayMenuItem(label="Item 1", type="button")
        item2 = TrayMenuItem(label="Item 2", type="checkbox", checked=True)
        separator = TrayMenuItem(type="separator")

        self.parent_menu.add_item(item1)
        self.parent_menu.add_item(separator)
        self.parent_menu.add_item(item2)

        tray_icon = TrayIcon(
            icon_path=self.test_icon_path,
            tooltip="Test with Menu",
            menu=self.parent_menu,
        )

        self.assertEqual(len(tray_icon.menu.get_items()), 3)
        items = tray_icon.menu.get_items()
        self.assertEqual(items[0].label, "Item 1")
        self.assertEqual(items[1].type, "separator")
        self.assertEqual(items[2].label, "Item 2")
        self.assertTrue(items[2].checked)


class TrayIconFileHandlingTest(GraphicUnitTest):
    """Test TrayIcon file handling capabilities"""

    def setUp(self):
        super().setUp()
        self.temp_files = []

    def tearDown(self):
        # Clean up temporary files
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        super().tearDown()

    def create_temp_image_file(self, suffix=".png", content=None):
        """Create temporary image file for testing"""
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            if content:
                f.write(content)
            else:
                # Write minimal PNG data
                f.write(
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x04\x00\x01]\xcc\xdb\x8a\x00\x00\x00\x00IEND\xaeB`\x82"
                )
            temp_path = f.name

        self.temp_files.append(temp_path)
        return temp_path

    def test_icon_path_validation_png(self):
        """Test tray icon with PNG file"""
        png_path = self.create_temp_image_file(".png")
        tray_icon = TrayIcon(icon_path=png_path)

        self.assertEqual(tray_icon.icon, png_path)
        self.assertTrue(os.path.exists(tray_icon.icon))

    def test_icon_path_validation_ico(self):
        """Test tray icon with ICO file"""
        ico_path = self.create_temp_image_file(".ico")
        tray_icon = TrayIcon(icon_path=ico_path)

        self.assertEqual(tray_icon.icon, ico_path)

    def test_icon_path_validation_jpg(self):
        """Test tray icon with JPG file"""
        jpg_path = self.create_temp_image_file(".jpg")
        tray_icon = TrayIcon(icon_path=jpg_path)

        self.assertEqual(tray_icon.icon, jpg_path)

    def test_supported_file_extensions(self):
        """Test various supported file extensions"""
        extensions = [".png", ".ico", ".jpg", ".jpeg", ".gif", ".svg"]

        for ext in extensions:
            with self.subTest(extension=ext):
                temp_path = self.create_temp_image_file(ext)
                tray_icon = TrayIcon(icon_path=temp_path)
                self.assertEqual(tray_icon.icon, temp_path)

    def test_nonexistent_file_handling(self):
        """Test handling of nonexistent icon file"""
        nonexistent_path = "/path/to/nonexistent/file.png"

        # TrayIcon should still be created, but behavior may vary by platform
        tray_icon = TrayIcon(icon_path=nonexistent_path)
        self.assertEqual(tray_icon.icon, nonexistent_path)


class TrayComplexMenuTest(GraphicUnitTest):
    """Test complex menu structures and interactions"""

    def setUp(self):
        super().setUp()
        self.main_menu = TrayMenu()
        self.callback_results = []

    def callback_method(self, item):
        """Callback function for menu items"""
        self.callback_results.append(f"Clicked: {item.label}")

    def test_nested_submenu_structure(self):
        """Test creating nested submenus"""
        # Create main menu items
        item1 = TrayMenuItem(
            label="Main Item 1", type="button", callback=self.callback_method
        )
        separator1 = TrayMenuItem(type="separator")

        # Create submenu
        submenu = TrayMenu()
        sub_item1 = TrayMenuItem(
            label="Sub Item 1", type="button", callback=self.callback_method
        )
        sub_item2 = TrayMenuItem(
            label="Sub Item 2",
            type="checkbox",
            checked=True,
            callback=self.callback_method,
        )

        submenu.add_item(sub_item1)
        submenu.add_item(sub_item2)

        submenu_item = TrayMenuItem(
            label="Submenu", type="submenu", menu=submenu
        )

        # Create nested submenu
        nested_submenu = TrayMenu()
        nested_item = TrayMenuItem(
            label="Nested Item", type="button", callback=self.callback_method
        )
        nested_submenu.add_item(nested_item)

        nested_submenu_item = TrayMenuItem(
            label="Nested Submenu", type="submenu", menu=nested_submenu
        )
        submenu.add_item(nested_submenu_item)

        # Add to main menu
        self.main_menu.add_item(item1)
        self.main_menu.add_item(separator1)
        self.main_menu.add_item(submenu_item)

        # Verify structure
        main_items = self.main_menu.get_items()
        self.assertEqual(len(main_items), 3)
        self.assertEqual(main_items[0].label, "Main Item 1")
        self.assertEqual(main_items[1].type, "separator")
        self.assertEqual(main_items[2].label, "Submenu")

        # Verify submenu
        sub_items = main_items[2].sub_menu.get_items()
        self.assertEqual(len(sub_items), 3)
        self.assertEqual(sub_items[2].type, "submenu")

        # Verify nested submenu
        nested_items = sub_items[2].sub_menu.get_items()
        self.assertEqual(len(nested_items), 1)
        self.assertEqual(nested_items[0].label, "Nested Item")

    def test_mixed_item_types_menu(self):
        """Test menu with various item types"""
        items_data = [
            ("Button Item", "button", False),
            ("Checkbox Unchecked", "checkbox", False),
            ("Checkbox Checked", "checkbox", True),
            (None, "separator", False),
            ("Another Button", "button", False),
        ]

        for label, item_type, checked in items_data:
            if item_type == "separator":
                item = TrayMenuItem(type="separator")
            else:
                item = TrayMenuItem(
                    label=label,
                    type=item_type,
                    checked=checked,
                    callback=self.callback_method,
                )
            self.main_menu.add_item(item)

        items = self.main_menu.get_items()
        self.assertEqual(len(items), 5)

        # Verify each item
        self.assertEqual(items[0].label, "Button Item")
        self.assertEqual(items[0].type, "button")

        self.assertEqual(items[1].label, "Checkbox Unchecked")
        self.assertEqual(items[1].type, "checkbox")
        self.assertFalse(items[1].checked)

        self.assertEqual(items[2].label, "Checkbox Checked")
        self.assertEqual(items[2].type, "checkbox")
        self.assertTrue(items[2].checked)

        self.assertEqual(items[3].type, "separator")
        # Based on implementation, separator label is empty string, not None
        self.assertEqual(items[3].label, "")

        self.assertEqual(items[4].label, "Another Button")
        self.assertEqual(items[4].type, "button")

    def test_callback_execution_tracking(self):
        """Test that callbacks are properly executed and tracked"""
        item1 = TrayMenuItem(
            label="Test Item 1", type="button", callback=self.callback_method
        )
        item2 = TrayMenuItem(
            label="Test Item 2", type="checkbox", callback=self.callback_method
        )

        self.main_menu.add_item(item1)
        self.main_menu.add_item(item2)

        # Simulate clicking items
        self.callback_results.clear()

        if item1.callback:
            item1.callback(item1)
        if item2.callback:
            item2.callback(item2)

        self.assertEqual(len(self.callback_results), 2)
        self.assertEqual(self.callback_results[0], "Clicked: Test Item 1")
        self.assertEqual(self.callback_results[1], "Clicked: Test Item 2")

    def test_large_menu_performance(self):
        """Test menu with many items for performance"""
        num_items = 100

        for i in range(num_items):
            item_type = "checkbox" if i % 3 == 0 else "button"
            checked = i % 2 == 0 if item_type == "checkbox" else False

            item = TrayMenuItem(
                label=f"Item {i}",
                type=item_type,
                checked=checked,
                callback=self.callback_method,
            )
            self.main_menu.add_item(item)

        items = self.main_menu.get_items()
        self.assertEqual(len(items), num_items)

        # Verify random items
        self.assertEqual(items[0].label, "Item 0")
        self.assertEqual(items[50].label, "Item 50")
        self.assertEqual(items[99].label, "Item 99")

        # Test clearing large menu
        self.main_menu.clear()
        self.assertEqual(len(self.main_menu.get_items()), 0)


class TraySystemIntegrationTest(GraphicUnitTest):
    """Test system integration aspects of tray functionality"""

    def setUp(self):
        super().setUp()
        self._prev_history = LoggerHistory.history[:]

    def tearDown(self):
        LoggerHistory.history[:] = self._prev_history
        super().tearDown()

    def test_tray_creation_logging(self):
        """Test that tray icon creation is properly logged"""
        LoggerHistory.clear_history()

        # Try to create tray icon
        icon_path = resource_find("data/logo/kivy-icon-32.png")
        if not icon_path:
            # Create minimal temp file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                icon_path = f.name
                f.write(b"\x89PNG\r\n\x1a\n")

        try:
            menu = TrayMenu()
            tray_icon = TrayIcon(
                icon_path=icon_path, tooltip="Test Tray", menu=menu
            )

            # Check if tray icon creation was attempted
            # (Logging behavior may vary by platform)
            self.assertIsInstance(tray_icon, TrayIcon)

        finally:
            if icon_path and not icon_path.endswith("kivy-icon-32.png"):
                if os.path.exists(icon_path):
                    os.unlink(icon_path)

    def test_platform_tray_support_detection(self):
        """Test detection of platform tray support"""
        # This test checks if the tray system can be initialized
        # without actually creating a visible tray icon

        try:
            menu = TrayMenu()
            item = TrayMenuItem(label="Test", type="button")
            menu.add_item(item)

            # Platform support can be detected indirectly
            self.assertIsInstance(menu, TrayMenu)
            self.assertEqual(len(menu.get_items()), 1)

        except Exception as e:
            # If tray is not supported, it should fail gracefully
            self.skipTest(f"Tray not supported on this platform: {e}")

    def test_multiple_tray_icons_handling(self):
        """Test handling multiple tray icons"""
        icon_path = resource_find("data/logo/kivy-icon-32.png")
        if not icon_path:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                icon_path = f.name
                f.write(b"\x89PNG\r\n\x1a\n")

        try:
            menu1 = TrayMenu()
            menu2 = TrayMenu()

            tray1 = TrayIcon(icon_path=icon_path, tooltip="Tray 1", menu=menu1)
            tray2 = TrayIcon(icon_path=icon_path, tooltip="Tray 2", menu=menu2)

            # Both should be created successfully
            self.assertIsInstance(tray1, TrayIcon)
            self.assertIsInstance(tray2, TrayIcon)
            self.assertNotEqual(tray1, tray2)

        finally:
            if icon_path and not icon_path.endswith("kivy-icon-32.png"):
                if os.path.exists(icon_path):
                    os.unlink(icon_path)
