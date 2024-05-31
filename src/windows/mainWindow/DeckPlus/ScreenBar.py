"""
Author: Core447
Year: 2024

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This programm comes with ABSOLUTELY NO WARRANTY!

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
# Import gtk modules
import threading
import time
import gi

from PIL import Image

from src.backend.DeckManagement.ImageHelpers import image2pixbuf
from src.backend.DeckManagement.HelperMethods import recursive_hasattr

from StreamDeck.Devices.StreamDeck import DialEventType, TouchscreenEventType

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

import globals as gl

from gi.repository import Gtk, Adw, Gdk, GLib, Gio

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.windows.mainWindow.elements.PageSettingsPage import PageSettingsPage

class ScreenBar(Gtk.Frame):
    def __init__(self, page_settings_page: "PageSettingsPage", **kwargs):
        self.page_settings_page = page_settings_page
        self.identifier = "touchscreen" # TODO: change
        super().__init__(**kwargs)
        self.set_css_classes(["key-button-frame-hidden"])
        self.set_halign(Gtk.Align.CENTER)
        self.set_hexpand(True)
        # self.set_size_request(80, 10)

        self.pixbuf = None

        # self.image = Gtk.Image(css_classes=["key-image", "plus-screenbar"], hexpand=True, vexpand=True)
        # self.image.set_overflow(Gtk.Overflow.HIDDEN)
        # self.image.set_from_file("Assets/800_100.png")

        self.image = ScreenBarImage()
        self.image.set_image(Image.new("RGB", (800, 100), (255, 0, 0)))
        self.set_child(self.image)

        # self.set_child(self.image)
        focus_controller = Gtk.EventControllerFocus()
        self.image.add_controller(focus_controller)
        focus_controller.connect("enter", self.on_focus_in)

        self.click_ctrl = Gtk.GestureClick().new()
        self.click_ctrl.connect("pressed", self.on_click)
        self.click_ctrl.connect("released", self.on_released)
        self.click_ctrl.set_button(0)
        self.image.add_controller(self.click_ctrl)

        # Make image focusable
        self.set_focus_child(self.image)
        self.image.set_focusable(True)

        self.min_drag_distance = 20
        self.long_press_treshold = 0.5

        self.drag_start_xy: tuple[int, int] = None
        self.drag_start_time: float = None

    def on_click(self, gesture, n_press, x, y):
        # print(f"Click: {self.parse_xy(x, y)}")
        self.drag_start_xy = None
        self.drag_start_time = None
        if gesture.get_current_button() == 1 and n_press == 1:
            if self.image.has_focus():
                self.drag_start_xy = self.parse_xy(x, y)
                self.drag_start_time = time.time()
            # Single left click
            # Select key
            self.image.grab_focus()

            for t in self.page_settings_page.deck_controller.touchscreens:
                if t.identifier == self.identifier:
                    active_state = t.get_active_state().state
                    gl.app.main_win.sidebar.load_for_screen(t.identifier, active_state)
        elif gesture.get_current_button() == 1 and n_press == 2:
            print("Double click")
            pass
            # Double left click
            # Simulate key press
            # self.simulate_press()

    def on_released(self, gesture, n_press, x, y):
        if None in [self.drag_start_xy, self.drag_start_time]:
            return
        # print(f"Release: {self.parse_xy(x, y)}")
        x, y = self.parse_xy(x, y)
        start_x, start_y = self.drag_start_xy
        drag_distance = abs(x - start_x) + abs(y - start_y)

        visible_child = gl.app.main_win.leftArea.deck_stack.get_visible_child()
        if visible_child is None:
            return
        active_controller = visible_child.deck_controller
        if active_controller is None:
            return

        if drag_distance > self.min_drag_distance:
            # print(f"Drag from {start_x}, {start_y} to {x}, {y}")
            value = {
                "x": start_x,
                "y": start_y,
                "x_out": x,
                "y_out": y
            }
            active_controller.touchscreen_event_callback(active_controller.deck, TouchscreenEventType.DRAG, value)
            return
        
        if time.time() - self.drag_start_time > self.long_press_treshold:
            # print(f"Long press at {x}, {y}")

            active_controller.touchscreen_event_callback(active_controller.deck, TouchscreenEventType.LONG, {"x": x, "y": y})
            return
        
        else:
            active_controller.touchscreen_event_callback(active_controller.deck, TouchscreenEventType.SHORT, {"x": x, "y": y})
            # print(f"Short press at {x}, {y}")
            return

    def parse_xy(self, x, y) -> tuple[int, int]:
        width = self.image.get_width()
        height = self.image.get_height()

        # Map xy to 800x100
        x, y = int(x * 800 / width), int(y * 100 / height)

        x = max(0, min(x, 800))
        y = max(0, min(y, 100))

        return x, y


    def on_focus_in(self, *args):
        self.set_border_active(True)

    def set_border_active(self, active: bool):
        if active:
            if self.page_settings_page.deck_config.active_widget not in [self, None]:
                self.page_settings_page.deck_config.active_widget.set_border_active(False)
            self.page_settings_page.deck_config.active_widget = self
            self.set_css_classes(["key-button-frame"])
        else:
            self.set_css_classes(["key-button-frame-hidden"])
            self.page_settings_page.deck_config.active_widget = None

class ScreenBarImage(Gtk.Picture):
    def __init__(self, **kwargs):
        super().__init__(keep_aspect_ratio=True, can_shrink=True, content_fit=Gtk.ContentFit.SCALE_DOWN,
                         halign=Gtk.Align.CENTER, hexpand=False, width_request=80, height_request=10,
                         valign=Gtk.Align.CENTER, vexpand=False, css_classes=["plus-screenbar-image"],
                         **kwargs)
        
    def set_image(self, image: Image.Image):
        width = 385 #TODO: Find a better way to do this
        image.thumbnail((width, width/8))

        pixbuf = image2pixbuf(image)
        self.set_pixbuf(pixbuf)
        del pixbuf