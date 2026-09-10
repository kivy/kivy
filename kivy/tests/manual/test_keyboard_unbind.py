from kivy.core.window import Window

print("Requesting keyboard...")
keyboard = Window.request_keyboard(lambda: None, None)

print("🔹 Unbinding keyboard once...")
keyboard.unbind(on_key_down=None)

print("🔹 Unbinding keyboard twice (should not crash)...")
try:
    keyboard.unbind(on_key_down=None)
    print("No crash! Keyboard unbinding is safe.")
except Exception as e:
    print(f"Crash detected: {e}")

print("Test completed successfully.")
