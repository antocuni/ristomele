from __future__ import absolute_import
from jnius import autoclass, PythonJavaClass, java_method, JavaException
from kivy.logger import Logger

Camera = autoclass('android.hardware.Camera')
AndroidActivityInfo = autoclass('android.content.pm.ActivityInfo')
AndroidPythonActivity = autoclass('org.renpy.android.PythonActivity')

class ShutterCallback(PythonJavaClass):
    __javainterfaces__ = ('android.hardware.Camera$ShutterCallback', )

    @java_method('()V')
    def onShutter(self):
        # apparently, it is enough to have an empty shutter callback to play
        # the standard shutter sound. If you pass None instead of shutter_cb
        # below, the standard sound doesn't play O_o
        pass


class PictureCallback(PythonJavaClass):
    __javainterfaces__ = ('android.hardware.Camera$PictureCallback', )

    def __init__(self, filename, on_success):
        super(PictureCallback, self).__init__()
        self.filename = filename
        self.on_success = on_success

    @java_method('([BLandroid/hardware/Camera;)V')
    def onPictureTaken(self, data, camera):
        s = data.tostring()
        with open(self.filename, 'wb') as f:
            f.write(s)
        Logger.info('xcamera: picture saved to %s', self.filename)
        camera.startPreview()
        self.on_success(self.filename)


class AutoFocusCallback(PythonJavaClass):
    __javainterfaces__ = ('android.hardware.Camera$AutoFocusCallback', )

    def __init__(self, filename, on_success):
        super(AutoFocusCallback, self).__init__()
        self.filename = filename
        self.on_success = on_success

    @java_method('(ZLandroid/hardware/Camera;)V')
    def onAutoFocus(self, success, camera):
        if success:
            Logger.info('xcamera: autofocus succeeded, taking picture...')
            shutter_cb = ShutterCallback()
            picture_cb = PictureCallback(self.filename, self.on_success)
            camera.takePicture(shutter_cb, None, picture_cb)
        else:
            Logger.info('xcamera: autofocus failed')


class LLCamera(object):

    def __init__(self, widget):
        self.widget = widget

    @property
    def camera(self):
        # to call the android API, we need access to the underlying
        # android.hardware.Camera instance. However, there is no official way
        # to retrieve it from the camera widget, so we need to dig into
        # internal attributes :-( This works at least on kivy 1.9.1, but it
        # might break any time soon.
        return self.widget._camera._android_camera

    def take_picture(self, filename, on_success):
        camera = self.camera
        params = camera.getParameters()
        #params.setFocusMode("continuous-picture")
        params.setFocusMode("auto")
        camera.setParameters(params)
        cb = AutoFocusCallback(filename, on_success)
        Logger.info('xcamera: starting autofocus...')
        try:
            camera.autoFocus(cb)
        except JavaException, e:
            Logger.info('Error when calling autofocus: {}', e)

    def set_picture_size(self, size):
        Logger.info('xcamera: setting picture size to %s' % (size,))
        width, height = size
        params = self.camera.getParameters()
        params.setPictureSize(width, height)
        self.camera.setParameters(params)

    @classmethod
    def get_supported_picture_sizes(cls):
        camera = Camera.open(0)
        try:
            params = camera.getParameters()
        finally:
            camera.release()
        #
        result = []
        sizes = params.getSupportedPictureSizes();
        for i in range(sizes.size()):
            size = sizes.get(i)
            result.append((size.width, size.height))
        return result


PORTRAIT = AndroidActivityInfo.SCREEN_ORIENTATION_PORTRAIT
LANDSCAPE = AndroidActivityInfo.SCREEN_ORIENTATION_LANDSCAPE

def set_orientation(value):
    previous = get_orientation()
    AndroidPythonActivity.mActivity.setRequestedOrientation(value)
    return previous

def get_orientation():
    return AndroidPythonActivity.mActivity.getRequestedOrientation()

