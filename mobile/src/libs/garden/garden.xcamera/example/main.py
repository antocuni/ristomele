import datetime
from kivy.lang import Builder
from kivy.app import App
from kivy.uix.dropdown import DropDown
from kivy.garden.xcamera import LLCamera

kv = """
#:import XCamera kivy.garden.xcamera.XCamera

FloatLayout:
    orientation: 'vertical'

    XCamera:
        id: xcamera
        on_picture_taken: app.picture_taken(*args)

    BoxLayout:
        orientation: 'horizontal'
        size_hint: 1, None
        height: sp(50)

        Button:
            text: 'Set landscape'
            on_release: xcamera.force_landscape()

        Button:
            text: 'Restore orientation'
            on_release: xcamera.restore_orientation()

        Spinner:
            id: sizes
            on_text: app.set_picture_size(*args)

"""


class CameraApp(App):
    def build(self):
        all_sizes = self.get_all_sizes()
        #
        root = Builder.load_string(kv)
        spinner = root.ids.sizes
        spinner.values = all_sizes
        spinner.text = spinner.values[0]
        return root

    def get_all_sizes(self):
        sizes = LLCamera.get_supported_picture_sizes()
        return ['auto'] + [str(x) for x in sizes]

    def picture_taken(self, obj, filename):
        print 'Picture taken and saved to', filename

    def set_picture_size(self, obj, size):
        if self.root is None:
            return
        if size != 'auto':
            size = eval(size)
        self.root.ids.xcamera.picture_size = size

if __name__ == '__main__':
    CameraApp().run()
