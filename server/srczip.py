import flask
import zipfile
from server import config

MOBILE = config.ROOT.join('mobile')

class SrcZip(object):

    def __init__(self, mobiledir):
        self.mobiledir = mobiledir
        self.reload()

    def reload(self):
        self.zipfile = self.create_zip(self.mobiledir)
        self.md5 = self.zipfile.computehash()

    def create_zip(self, mobiledir):
        src = mobiledir.join('src')
        src_zip = mobiledir.join('src.zip')
        if src_zip.exists():
            src_zip.remove()
        zipf = zipfile.ZipFile(str(src_zip), 'w', zipfile.ZIP_DEFLATED)
        for f in src.visit():
            if f.ext in ('.pyc', '.pyo'):
                continue
            zipf.write(str(f), f.relto(mobiledir))
        zipf.close()
        return src_zip

SRC_ZIP = SrcZip(MOBILE)

def mobile_md5():
    if config.DEBUG:
        SRC_ZIP.reload()
    return flask.jsonify(md5=SRC_ZIP.md5)

def mobile_download():
    if config.DEBUG:
        SRC_ZIP.reload()
    return flask.send_file(str(SRC_ZIP.zipfile), as_attachment=True,
                           attachment_filename='src.zip')


def add_routes(app):
    app.route('/mobile/md5')(mobile_md5)
    app.route('/mobile/download')(mobile_download)
