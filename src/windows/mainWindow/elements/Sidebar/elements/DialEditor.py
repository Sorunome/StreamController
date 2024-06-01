from gi.repository import Gtk, Adw

from typing import TYPE_CHECKING

from src.windows.mainWindow.elements.Sidebar.elements.ActionManager import ActionManager
from src.windows.mainWindow.elements.Sidebar.elements.StateSwitcher import StateSwitcher

if TYPE_CHECKING:
    from src.windows.mainWindow.elements.Sidebar.Sidebar import Sidebar

import globals as gl

class DialEditor(Gtk.ScrolledWindow):
    def __init__(self, sidebar: "Sidebar"):
        self.sidebar = sidebar
        super().__init__(hexpand=True, vexpand=True)

        self.build()

    def build(self):
        self.clamp = Adw.Clamp(hexpand=True, vexpand=True)
        self.set_child(self.clamp)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        self.clamp.set_child(self.main_box)

        self.state_switcher = StateSwitcher("dials", margin_start=20, margin_end=20, margin_top=10, margin_bottom=10, hexpand=True)
        self.state_switcher.add_switch_callback(self.on_state_switch)
        self.state_switcher.add_add_new_callback(self.on_add_new_state)
        self.state_switcher.set_n_states(0)
        self.main_box.append(self.state_switcher)

        self.action_group = Adw.PreferencesGroup(title="Dial")
        self.main_box.append(self.action_group)

        self.action_manager = ActionManager(self.sidebar)
        self.action_group.add(self.action_manager)

        self.remove_state_button = Gtk.Button(label="Remove State", css_classes=["destructive-action"], margin_top=15, margin_bottom=15, margin_start=15, margin_end=15)
        self.remove_state_button.connect("clicked", self.on_remove_state)
        self.main_box.append(self.remove_state_button)

    def on_state_switch(self, *args):
        print("on_state_switch")
        state = self.state_switcher.get_selected_state()
        # self.sidebar.active_state = self.state_switcher.get_selected_state()

        visible_child = gl.app.main_win.leftArea.deck_stack.get_visible_child()
        if visible_child is None:
            return
        controller = visible_child.deck_controller
        if controller is None:
            return
        
        dial = controller.dials[int(self.sidebar.active_identifier)]

        dial.set_state(state, update_sidebar=True)
        print(state)
        print("on_state_switch end")

    def on_add_new_state(self, state):
        controller = gl.app.main_win.get_active_controller()
        if controller is None:
            return
        
        dial = controller.dials[int(self.sidebar.active_identifier)]
        dial.add_new_state()

        self.remove_state_button.set_visible(self.state_switcher.get_n_states() > 1)

    def on_remove_state(self, button):
        if self.state_switcher.get_n_states() <= 1:
            return

        controller = gl.app.main_win.get_active_controller()
        if controller is None:
            return
        
        active_state = self.state_switcher.get_selected_state()
        
        dial = controller.dials[int(self.sidebar.active_identifier)]
        dial.remove_state(active_state)

        self.remove_state_button.set_visible(self.state_switcher.get_n_states() > 1)

    def load_for_dial(self, n: int, state: int):
        visible_child = gl.app.main_win.leftArea.deck_stack.get_visible_child()
        if visible_child is None:
            return
        controller: DeckController = visible_child.deck_controller
        if controller is None:
            return

        dial = controller.dials[n]
        self.state_switcher.set_n_states(len(dial.states.keys()))
        self.state_switcher.select_state(state)
        dial.set_state(state)

        self.remove_state_button.set_visible(self.state_switcher.get_n_states() > 1)

        self.sidebar.active_type = "dials"
        self.sidebar.active_identifier = str(n)

        self.action_manager.load_for_dial(n, state)