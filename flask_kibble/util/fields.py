import wtforms
from . import widgets

from google.appengine.ext import blobstore


class BlobKeyField(wtforms.StringField):
    widget = widgets.JSUploadWidget()

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.data = blobstore.BlobKey(valuelist[0])
        else:
            self.data = None


