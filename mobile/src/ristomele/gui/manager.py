from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.behaviors.focus import FocusBehavior

class Manager(ScreenManager):
    
    def __init__(self):
        transition = SlideTransition(duration=.35)
        super(Manager, self).__init__(transition=transition)
        self.history = []

    def open(self, view):
        self.unfocus_maybe()
        name = view.name
        if self.has_screen(name):
            self.remove_widget(self.get_screen(name))
        self.add_widget(view)
        self.transition.direction = 'left'
        self.current = name
        self.history.append(view)

    def go_back(self):
        if len(self.history) < 2:
            return False
        view = self.history.pop()
        if hasattr(view, 'close'):
            view.close()
        self.transition.direction = 'right'
        self.current = self.history[-1].name
        return True

    def unfocus_maybe(self):
        if not self.history:
            return
        screen = self.history[-1]
        for widget in screen.walk():
            if isinstance(widget, FocusBehavior):
                widget.focus = False

    @property
    def current_view(self):
        return self.history[-1]
