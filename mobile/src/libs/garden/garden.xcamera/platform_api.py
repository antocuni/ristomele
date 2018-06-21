from __future__ import absolute_import
from kivy.utils import platform

def play_shutter():
    # bah, apparently we need to delay the import of kivy.core.audio, lese
    # kivy cannot find a camera provider, at lease on linux. Maybe a
    # gstreamer/pygame issue?
    from kivy.core.audio import SoundLoader
    sound = SoundLoader.load("data/xcamera/shutter.wav")
    sound.play()


if platform == 'android':
    from .android_api import *

else:

    LANDSCAPE = 'landscape'
    PORTRAIT = 'portrait'

    def get_orientation():
        return get_orientation.value
    get_orientation.value = PORTRAIT

    def set_orientation(value):
        previous = get_orientation()
        print 'FAKE orientation set to', value
        get_orientation.value = value
        return previous


    class LLCamera(object):
        """
        Generic fallback for taking pictures. Probably not the best quality,
        it is meant mostly for testing
        """

        def __init__(self, widget):
            self.widget = widget

        def take_picture(self, filename, on_success):
            self.widget.texture.save(filename, flipped=False)
            play_shutter()
            on_success(filename)

        def set_picture_size(self, size):
            print 'FAKE set_picture_size', size

        @classmethod
        def get_supported_picture_sizes(cls):
            # this is fake
            return [(640, 480), (800, 600), (1024, 768)]
