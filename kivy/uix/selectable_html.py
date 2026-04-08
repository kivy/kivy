"""
Selectable HTML widgets
=======================

This module provides selectable readonly text widgets that can render
HTML-like content as Kivy markup, detect links, and optionally open links
externally.
"""

from __future__ import annotations

import html as html_lib
import re
import webbrowser
from urllib.parse import urljoin

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

__all__ = [
    "SelectableBodyTextInput",
    "SelectableMarkupLabel",
    "SelectableHtmlLabel",
    "normalized_sender_html",
    "html_to_text",
    "html_to_kivy_markup",
    "html_to_kivy_markup_with_links",
    "resolve_link_url",
    "open_external_link",
]


def normalized_sender_html(raw_html: str) -> str:
    html_text = str(raw_html or "").strip()
    if not html_text:
        return ""

    srcdoc_match = re.search(
        r'(?is)<iframe\b[^>]*\bsrcdoc=(["\'])(?P<srcdoc>.*?)\1',
        html_text,
    )
    if not srcdoc_match:
        return html_text

    candidate = str(srcdoc_match.group("srcdoc") or "")
    if not candidate:
        return html_text

    decoded = candidate
    for _ in range(3):
        next_value = html_lib.unescape(decoded)
        if next_value == decoded:
            break
        decoded = next_value

    normalized = decoded.strip()
    return normalized or html_text


def html_to_text(raw_html: str) -> str:
    html_text = normalized_sender_html(raw_html)
    if not html_text:
        return ""

    text = re.sub(r"(?is)<(script|style|head).*?>.*?</\1>", "", html_text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)<li\b[^>]*>", "• ", text)
    text = re.sub(r"(?i)</(p|div|section|article|header|footer|tr|table|ul|ol|li|h[1-6])\s*>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text)
    text = text.replace("\xa0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+\n", "\n", text)
    text = re.sub(r"\n[ \t\f\v]+", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def html_to_kivy_markup(raw_html: str) -> str:
    markup, _ = html_to_kivy_markup_with_links(raw_html)
    return markup


def html_to_kivy_markup_with_links(raw_html: str) -> tuple[str, dict[str, str]]:
    html_text = normalized_sender_html(raw_html)
    if not html_text:
        return "", {}

    text = re.sub(r"(?is)<(script|style|head).*?>.*?</\1>", "", html_text)
    link_targets: dict[str, str] = {}
    link_counter = 0

    def _anchor_repl(match: re.Match[str]) -> str:
        nonlocal link_counter
        href = html_lib.unescape(str(match.group("href") or "").strip())
        label_html = str(match.group("label") or "")
        label_text = re.sub(r"(?is)<[^>]+>", " ", label_html)
        label_text = " ".join(html_lib.unescape(label_text).split()) or href or "link"
        if not href:
            return label_text
        link_counter += 1
        ref_uid = f"link_{link_counter}"
        link_targets[ref_uid] = href
        return f"__LINK_REF_OPEN_{ref_uid}__{label_text}__LINK_CLOSE__"

    text = re.sub(
        r'(?is)<a\b[^>]*href=(["\'])(?P<href>.*?)\1[^>]*>(?P<label>.*?)</a>',
        _anchor_repl,
        text,
    )

    tag_replacements: tuple[tuple[str, str], ...] = (
        (r"(?is)<(strong|b)\b[^>]*>", "__B_OPEN__"),
        (r"(?is)</(strong|b)\s*>", "__B_CLOSE__"),
        (r"(?is)<(em|i)\b[^>]*>", "__I_OPEN__"),
        (r"(?is)</(em|i)\s*>", "__I_CLOSE__"),
        (r"(?is)<u\b[^>]*>", "__U_OPEN__"),
        (r"(?is)</u\s*>", "__U_CLOSE__"),
        (r"(?is)<br\s*/?>", "\n"),
        (r"(?is)<li\b[^>]*>", "\n• "),
        (r"(?is)</(p|div|section|article|header|footer|tr|table|ul|ol|li|h[1-6])\s*>", "\n"),
        (r"(?is)<(p|div|section|article|header|footer|tr|table|ul|ol|h[1-6])\b[^>]*>", "\n"),
    )
    for pattern, replacement in tag_replacements:
        text = re.sub(pattern, replacement, text)

    text = re.sub(r"(?is)<[^>]+>", "", text)
    text = html_lib.unescape(text).replace("\xa0", " ")
    text = text.replace("[", "&bl;").replace("]", "&br;")

    markup_tokens = {
        "__B_OPEN__": "[b]",
        "__B_CLOSE__": "[/b]",
        "__I_OPEN__": "[i]",
        "__I_CLOSE__": "[/i]",
        "__U_OPEN__": "[u]",
        "__U_CLOSE__": "[/u]",
    }
    for token, markup in markup_tokens.items():
        text = text.replace(token, markup)
    text = re.sub(
        r"__LINK_REF_OPEN_(?P<ref>[A-Za-z0-9_]+)__",
        lambda m: f"[ref={m.group('ref')}][u][color=#8fb9ff]",
        text,
    )
    text = text.replace("__LINK_CLOSE__", "[/color][/u][/ref]")

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+\n", "\n", text)
    text = re.sub(r"\n[ \t\f\v]+", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip(), link_targets


def resolve_link_url(raw_url: str, *, base_url: str = "") -> str:
    candidate = html_lib.unescape(str(raw_url or "").strip())
    if not candidate:
        return ""
    if re.match(r"(?i)^(https?|mailto|tel):", candidate):
        return candidate
    if candidate.startswith("//"):
        return f"https:{candidate}"
    normalized_base = str(base_url or "").strip()
    if normalized_base:
        return urljoin(normalized_base, candidate)
    return candidate


def open_external_link(
    raw_url: str,
    *,
    base_url: str = "",
    copy_on_failure: bool = True,
    browser_window: int = 2,
) -> tuple[bool, bool, str]:
    resolved_url = resolve_link_url(raw_url, base_url=base_url)
    if not resolved_url:
        return False, False, ""

    opened = False
    try:
        opened = bool(webbrowser.open(resolved_url, new=int(browser_window)))
    except Exception:  # noqa: BLE001
        opened = False

    copied = False
    if not opened and copy_on_failure:
        try:
            Clipboard.copy(resolved_url)
            copied = True
        except Exception:  # noqa: BLE001
            copied = False

    return opened, copied, resolved_url


class SelectableBodyTextInput(TextInput):
    """Readonly text area with mobile-friendly long-press word selection."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._long_press_event = None
        self._touch_uid = None
        self._touch_pos: tuple[float, float] = (0.0, 0.0)
        self._touch_moved = False
        self._handle_drag_active = False
        self._restore_bubble_after_handle = False
        self._default_use_bubble = bool(getattr(self, "use_bubble", True))
        self._default_use_handles = bool(getattr(self, "use_handles", True))
        self.on_copy_complete = None

    def on_touch_down(self, touch):  # noqa: ANN001
        handled = super().on_touch_down(touch)
        if not self.collide_point(*touch.pos):
            return handled
        self._touch_uid = touch.uid
        self._touch_pos = (touch.x, touch.y)
        self._touch_moved = False
        self._cancel_long_press()
        self._long_press_event = Clock.schedule_once(self._on_long_press, 0.35)
        return handled

    def on_touch_move(self, touch):  # noqa: ANN001
        if touch.uid == self._touch_uid:
            dx = abs(touch.x - self._touch_pos[0])
            dy = abs(touch.y - self._touch_pos[1])
            if dx > 12 or dy > 12:
                self._touch_moved = True
                self._cancel_long_press()
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):  # noqa: ANN001
        if touch.uid == self._touch_uid:
            self._touch_uid = None
            self._cancel_long_press()
        return super().on_touch_up(touch)

    def _cancel_long_press(self):
        if self._long_press_event is not None:
            self._long_press_event.cancel()
            self._long_press_event = None

    def _on_long_press(self, *_args):
        self._long_press_event = None
        if self._touch_moved:
            return
        x, y = self._touch_pos
        if not self.collide_point(x, y):
            return
        try:
            self.focus = True
            cursor = self.get_cursor_from_xy(x, y)
            if isinstance(cursor, tuple):
                self.cursor = cursor
            self.select_word()
        except Exception:  # noqa: BLE001
            return

    def reset_interaction_state(self):
        self._cancel_long_press()
        self._touch_uid = None
        self._touch_pos = (0.0, 0.0)
        self._touch_moved = False
        self._handle_drag_active = False
        self._restore_bubble_after_handle = False
        try:
            self.use_bubble = bool(self._default_use_bubble)
        except Exception:  # noqa: BLE001
            pass
        try:
            self.use_handles = bool(self._default_use_handles)
        except Exception:  # noqa: BLE001
            pass
        self._set_handle_widgets_enabled(True)
        self._force_hide_bubble_immediate()
        self.clear_selection_handles()

    def clear_selection_handles(self):
        self._cancel_long_press()
        self._touch_uid = None
        self._touch_pos = (0.0, 0.0)
        self._touch_moved = False
        self._handle_drag_active = False
        self._restore_bubble_after_handle = False
        try:
            self.cancel_selection()
        except Exception:  # noqa: BLE001
            pass

        for attr_name, attr_value in (
            ("_touch_count", 0),
            ("_handle_moved", False),
            ("_selection_touch", None),
        ):
            if hasattr(self, attr_name):
                try:
                    setattr(self, attr_name, attr_value)
                except Exception:  # noqa: BLE001
                    pass

        for method_name in ("_hide_handles", "_hide_cut_copy_paste"):
            method = getattr(self, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception:  # noqa: BLE001
                    pass
        for handle_name in ("_handle_left", "_handle_right", "_handle_middle"):
            handle_widget = getattr(self, handle_name, None)
            if handle_widget is None:
                continue
            try:
                handle_widget.opacity = 0
            except Exception:  # noqa: BLE001
                pass
            try:
                handle_widget.disabled = False
            except Exception:  # noqa: BLE001
                pass

        try:
            target_use_handles = bool(getattr(self, "use_handles", True))
            self.use_handles = False
            if target_use_handles:
                Clock.schedule_once(lambda *_: setattr(self, "use_handles", True), 0)
        except Exception:  # noqa: BLE001
            pass

        self._force_hide_bubble_immediate()
        self.focus = False

    def copy(self, data=""):
        copied_text = str(data or getattr(self, "selection_text", "") or "")
        if not copied_text:
            return
        try:
            Clipboard.copy(copied_text)
        except Exception:  # noqa: BLE001
            return
        self.clear_selection_handles()
        Clock.schedule_once(lambda *_: self.clear_selection_handles(), 0)
        callback = getattr(self, "on_copy_complete", None)
        if callable(callback):
            callback(copied_text.strip())

    def _handle_pressed(self, instance):  # noqa: ANN001
        self._set_handle_widgets_enabled(True)
        self._handle_drag_active = True
        self._restore_bubble_after_handle = bool(self.use_bubble)
        self.use_bubble = False
        self._force_hide_bubble_immediate()
        return super()._handle_pressed(instance)

    def _handle_released(self, instance):  # noqa: ANN001
        self._handle_drag_active = False
        self.use_bubble = bool(self._restore_bubble_after_handle)
        self._restore_bubble_after_handle = False
        return super()._handle_released(instance)

    def _show_cut_copy_paste(
        self,
        pos,  # noqa: ANN001
        win,  # noqa: ANN001
        parent_changed=False,
        mode="",
        pos_in_window=False,
        *args,  # noqa: ANN002
    ):
        if self._handle_drag_active:
            return None
        result = super()._show_cut_copy_paste(
            pos,
            win,
            parent_changed=parent_changed,
            mode=mode,
            pos_in_window=pos_in_window,
            *args,
        )
        self._patch_readonly_bubble_actions()
        return result

    def _patch_readonly_bubble_actions(self):
        if not self.readonly or not self.use_bubble:
            return
        bubble = getattr(self, "_bubble", None)
        if bubble is None:
            return
        if getattr(bubble, "parent", None) is None:
            return

        content = getattr(bubble, "content", None)
        copy_button = getattr(bubble, "but_copy", None)
        select_all_button = getattr(bubble, "but_selectall", None)
        if content is None or copy_button is None or select_all_button is None:
            return

        try:
            select_all_button.opacity = 1
            select_all_button.disabled = False
            content.clear_widgets()
            content.add_widget(copy_button)
            content.add_widget(select_all_button)
        except Exception:  # noqa: BLE001
            return

    def _force_hide_bubble_immediate(self):
        bubble = getattr(self, "_bubble", None)
        if bubble is None:
            return
        parent = getattr(bubble, "parent", None)
        if parent is None:
            return
        try:
            bubble.opacity = 0
        except Exception:  # noqa: BLE001
            pass
        try:
            parent.remove_widget(bubble)
        except Exception:  # noqa: BLE001
            pass

    def _set_handle_widgets_enabled(self, enabled: bool):
        for handle_name in ("_handle_left", "_handle_right", "_handle_middle"):
            handle_widget = getattr(self, handle_name, None)
            if handle_widget is None:
                continue
            try:
                handle_widget.disabled = not bool(enabled)
            except Exception:  # noqa: BLE001
                continue


class SelectableMarkupLabel(FloatLayout):
    """Render rich label markup while keeping selection/copy via hidden TextInput."""

    __events__ = ("on_selection", "on_link_press")

    allow_selection = BooleanProperty(True)
    markup_text = StringProperty("")
    plain_text = StringProperty("")
    font_size = NumericProperty(16.0)
    text_color = ListProperty([0.94, 0.95, 0.97, 1.0])
    selection_color = ListProperty([0.84, 0.50, 0.36, 0.35])
    padding = ListProperty([2.0, 6.0, 2.0, 6.0])
    content_height = NumericProperty(0.0)
    on_copy_complete = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._link_targets: dict[str, str] = {}
        self._hovering_link = False
        self._cursor_bound = False
        self._label = Label(
            text="",
            markup=True,
            halign="left",
            valign="top",
            size_hint=(None, None),
        )
        self._label.bind(on_ref_press=self._on_label_ref_press)
        self._plain_measure = Label(
            text="",
            markup=False,
            halign="left",
            valign="top",
            size_hint=(None, None),
        )
        self._selector = SelectableBodyTextInput(
            text="",
            readonly=True,
            multiline=True,
            use_handles=True,
            use_bubble=True,
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),
            foreground_color=(0, 0, 0, 0),
            cursor_color=(0, 0, 0, 0),
            cursor_width=0,
            size_hint=(None, None),
        )
        self._selector.on_copy_complete = self._on_selector_copy_complete
        self._selector.bind(selection_text=self._on_selector_selection_text)

        self.add_widget(self._label)
        self.add_widget(self._selector)

        self.bind(
            pos=self._refresh_layout,
            size=self._refresh_layout,
            markup_text=self._refresh_layout,
            plain_text=self._refresh_layout,
            font_size=self._refresh_layout,
            text_color=self._refresh_layout,
            selection_color=self._refresh_layout,
            padding=self._refresh_layout,
            allow_selection=self._apply_selection_state,
        )
        self.bind(parent=self._on_parent_changed)
        Clock.schedule_once(self._refresh_layout, 0)
        Clock.schedule_once(self._apply_selection_state, 0)
        Clock.schedule_once(self._ensure_cursor_binding, 0)

    def on_selection(self, _selected_text: str):
        return

    def on_link_press(self, _url: str):
        return

    def on_touch_down(self, touch):  # noqa: ANN001
        if self.collide_point(*touch.pos):
            try:
                if self._label.on_touch_down(touch):
                    return True
            except Exception:  # noqa: BLE001
                pass
        return super().on_touch_down(touch)

    @property
    def selection_text(self) -> str:
        return str(getattr(self._selector, "selection_text", "") or "")

    def _on_selector_copy_complete(self, copied_text: str):
        callback = getattr(self, "on_copy_complete", None)
        if callable(callback):
            callback(str(copied_text or ""))

    def _on_selector_selection_text(self, _selector, value):
        selected_text = str(value or "").strip()
        if not selected_text:
            return
        self.dispatch("on_selection", selected_text)

    def _apply_selection_state(self, *_args):
        enabled = bool(self.allow_selection)
        self._selector.disabled = not enabled
        self._selector.use_handles = enabled
        self._selector.use_bubble = enabled
        if not enabled:
            self.clear_selection_handles()

    def clear_selection_handles(self):
        clear_fn = getattr(self._selector, "clear_selection_handles", None)
        if callable(clear_fn):
            clear_fn()

    def reset_interaction_state(self):
        reset_fn = getattr(self._selector, "reset_interaction_state", None)
        if callable(reset_fn):
            reset_fn()
        else:
            self.clear_selection_handles()

    def copy(self, data=""):
        copy_fn = getattr(self._selector, "copy", None)
        if callable(copy_fn):
            copy_fn(data)

    def set_link_targets(self, targets: dict[str, str]):
        normalized: dict[str, str] = {}
        if isinstance(targets, dict):
            for ref_uid, url in targets.items():
                key = str(ref_uid or "").strip()
                value = str(url or "").strip()
                if key and value:
                    normalized[key] = value
        self._link_targets = normalized

    def set_html(self, raw_html: str):
        markup, links = html_to_kivy_markup_with_links(raw_html)
        self.markup_text = markup
        self.plain_text = html_to_text(raw_html)
        self.set_link_targets(links)

    def _on_label_ref_press(self, _label: Label, ref_uid: str):
        url = str(self._link_targets.get(str(ref_uid or ""), "") or "").strip()
        if not url:
            return
        self.dispatch("on_link_press", url)

    def _on_parent_changed(self, *_args):
        if self.parent is None:
            self._unbind_cursor_tracking()
            self._set_link_hover_cursor(False)
            return
        self._ensure_cursor_binding()

    def has_active_selection(self) -> bool:
        selected_text = str(getattr(self._selector, "selection_text", "") or "").strip()
        if selected_text:
            return True
        if bool(getattr(self._selector, "focus", False)):
            return True
        for handle_name in ("_handle_left", "_handle_right", "_handle_middle"):
            handle_widget = getattr(self._selector, handle_name, None)
            if handle_widget is None:
                continue
            try:
                if float(getattr(handle_widget, "opacity", 0.0) or 0.0) > 0:
                    return True
            except Exception:  # noqa: BLE001
                continue
        return False

    def _refresh_layout(self, *_args):
        px_left, px_top, px_right, px_bottom = self._normalized_padding()
        inner_width = max(1.0, float(self.width) - px_left - px_right)

        markup_value = str(self.markup_text or "")
        explicit_plain = str(self.plain_text or "")
        derived_plain = self._strip_markup(markup_value) if markup_value else ""
        if explicit_plain and derived_plain:
            plain_value = explicit_plain if len(explicit_plain) >= len(derived_plain) else derived_plain
        else:
            plain_value = explicit_plain or derived_plain

        self._label.text = markup_value
        self._label.font_size = float(self.font_size or 16.0)
        self._label.color = list(self.text_color)
        self._label.text_size = (inner_width, None)
        self._label.texture_update()
        label_height = max(1.0, float(self._label.texture_size[1] or 0.0))

        self._plain_measure.text = plain_value
        self._plain_measure.font_size = float(self.font_size or 16.0)
        self._plain_measure.color = list(self.text_color)
        self._plain_measure.text_size = (inner_width, None)
        self._plain_measure.texture_update()
        plain_height = max(1.0, float(self._plain_measure.texture_size[1] or 0.0))

        text_height = max(label_height, plain_height)
        total_height = max(1.0, text_height + px_top + px_bottom)
        self.content_height = total_height

        top_anchor_offset = max(0.0, float(self.height) - total_height)
        content_y = float(self.y) + top_anchor_offset

        label_y = content_y + px_bottom + max(0.0, text_height - label_height)
        self._label.pos = (float(self.x) + px_left, label_y)
        self._label.size = (inner_width, label_height)

        selector_text_changed = str(self._selector.text or "") != plain_value
        self._selector.text = plain_value
        self._selector.font_size = float(self.font_size or 16.0)
        self._selector.selection_color = list(self.selection_color)
        self._selector.padding = [px_left, px_top, px_right, px_bottom]
        self._selector.pos = (float(self.x), content_y)
        self._selector.size = (max(1.0, float(self.width)), total_height)
        if selector_text_changed:
            self.clear_selection_handles()
        self._update_hover_cursor_from_window_pos()

    def _normalized_padding(self) -> tuple[float, float, float, float]:
        values = list(self.padding) if isinstance(self.padding, (list, tuple)) else []
        if len(values) >= 4:
            left, top, right, bottom = values[:4]
        elif len(values) == 2:
            left, top = values
            right, bottom = left, top
        elif len(values) == 1:
            left = top = right = bottom = values[0]
        else:
            left = 2.0
            top = 6.0
            right = 2.0
            bottom = 6.0
        try:
            return float(left), float(top), float(right), float(bottom)
        except Exception:  # noqa: BLE001
            return 2.0, 6.0, 2.0, 6.0

    @staticmethod
    def _strip_markup(value: str) -> str:
        text = re.sub(r"\[[^\]]+\]", "", str(value or ""))
        return text.replace("&bl;", "[").replace("&br;", "]")

    def _ensure_cursor_binding(self, *_args):
        if self._cursor_bound:
            return
        try:
            Window.bind(mouse_pos=self._on_window_mouse_pos)
            self._cursor_bound = True
        except Exception:  # noqa: BLE001
            self._cursor_bound = False

    def _unbind_cursor_tracking(self):
        if not self._cursor_bound:
            return
        try:
            Window.unbind(mouse_pos=self._on_window_mouse_pos)
        except Exception:  # noqa: BLE001
            pass
        self._cursor_bound = False

    def _on_window_mouse_pos(self, _window, pos):
        if not isinstance(pos, (tuple, list)) or len(pos) < 2:
            self._set_link_hover_cursor(False)
            return
        mouse_x = float(pos[0])
        mouse_y = float(pos[1])
        if not self.get_root_window():
            self._set_link_hover_cursor(False)
            return
        if bool(getattr(self, "disabled", False)) or float(getattr(self, "opacity", 1.0) or 0.0) <= 0.0:
            self._set_link_hover_cursor(False)
            return
        try:
            transformed_x, transformed_y = self.to_widget(mouse_x, mouse_y)
        except Exception:  # noqa: BLE001
            self._set_link_hover_cursor(False)
            return
        if not self.collide_point(transformed_x, transformed_y):
            self._set_link_hover_cursor(False)
            return
        self._set_link_hover_cursor(self._is_pos_over_ref(mouse_x, mouse_y))

    def _update_hover_cursor_from_window_pos(self):
        if not self._cursor_bound:
            return
        try:
            pos = tuple(getattr(Window, "mouse_pos", (0.0, 0.0)))
        except Exception:  # noqa: BLE001
            pos = (0.0, 0.0)
        self._on_window_mouse_pos(Window, pos)

    def _is_pos_over_ref(self, window_x: float, window_y: float) -> bool:
        refs = getattr(self._label, "refs", None)
        if not isinstance(refs, dict) or not refs:
            return False

        texture_w = float(self._label.texture_size[0] or 0.0)
        texture_h = float(self._label.texture_size[1] or 0.0)
        if texture_w <= 0.0 or texture_h <= 0.0:
            return False

        try:
            transformed_x, transformed_y = self._label.to_widget(float(window_x), float(window_y))
        except Exception:  # noqa: BLE001
            return False

        tx = transformed_x - float(self._label.center_x) + texture_w / 2.0
        ty = transformed_y - float(self._label.center_y) + texture_h / 2.0
        ty = texture_h - ty

        for zones in refs.values():
            if not isinstance(zones, (tuple, list)):
                continue
            for zone in zones:
                if not isinstance(zone, (tuple, list)) or len(zone) < 4:
                    continue
                x0, y0, x1, y1 = zone[:4]
                try:
                    if float(x0) <= tx <= float(x1) and float(y0) <= ty <= float(y1):
                        return True
                except Exception:  # noqa: BLE001
                    continue
        return False

    def _set_link_hover_cursor(self, hovering_link: bool):
        desired = bool(hovering_link)
        if desired == self._hovering_link:
            return
        self._hovering_link = desired
        try:
            Window.set_system_cursor("hand" if desired else "arrow")
        except Exception:  # noqa: BLE001
            pass


class SelectableHtmlLabel(SelectableMarkupLabel):
    """High-level HTML widget with built-in rendering and external link opening."""

    raw_html = StringProperty("")
    base_url = StringProperty("")
    auto_open_links = BooleanProperty(True)
    copy_link_on_open_failure = BooleanProperty(True)
    last_link_url = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(raw_html=self._render_html)
        self.bind(on_link_press=self._on_link_pressed)
        Clock.schedule_once(self._render_html, 0)

    def _render_html(self, *_args):
        html_value = str(self.raw_html or "")
        markup, links = html_to_kivy_markup_with_links(html_value)
        self.markup_text = markup or "[color=#9aa7bd]HTML message content unavailable.[/color]"
        self.plain_text = html_to_text(html_value)
        self.set_link_targets(links)

    def _on_link_pressed(self, _instance, url: str):
        resolved_url = resolve_link_url(url, base_url=str(self.base_url or ""))
        self.last_link_url = str(resolved_url or "")
        if not self.auto_open_links or not resolved_url:
            return
        open_external_link(
            resolved_url,
            copy_on_failure=bool(self.copy_link_on_open_failure),
        )
