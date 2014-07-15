from base64 import b64encode
from functools import partial

import flask
import wtforms
from wtforms.widgets import HTMLString

from wtforms_ndb import ModelConverter
from wtforms.csrf.session import SessionCSRF

from google.appengine.ext import blobstore


class BaseCSRFForm(wtforms.Form):
    class Meta:
        csrf = True
        csrf_class = SessionCSRF

        @property
        def csrf_secret(self):
            return flask.current_app.config['CSRF_SECRET_KEY']

        @property
        def csrf_context(self):
            return flask.session


class TabluarFormListWidget(object):
    template = 'kibble/widgets/tabularformlist.html'

    def __call__(self, field, **kwargs):
        html = flask.render_template(
            self.template,
            field=field,
            kwargs=kwargs,
            empty_row=partial(self.empty_row, field),
            base64=b64encode,
        )
        return HTMLString(html)

    def empty_row(self, field, token='{{ row_count }}'):
        token = HTMLString(token)
        inner_form = field.unbound_field.args[0]
        prefix = field.name + '-' + token
        f = inner_form(prefix=prefix)
        return f


class JSUploadWidget(object):
    template = 'kibble/widgets/jsupload.html'

    def __call__(self, field, **kwargs):
        kwargs['name'] = field.name
        ctx = {
            'upload_url': blobstore.create_upload_url(
                flask.url_for('.upload')),
            'filename': '',
            'value': str(field.data or ''),
            'field_args': kwargs,
        }
        if field.data:
            ctx['filename'] = blobstore.BlobInfo(field.data).filename

        return HTMLString(
            flask.render_template(self.template,
                                  **ctx))


class BlobKeyField(wtforms.StringField):
    widget = JSUploadWidget()

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.data = blobstore.BlobKey(valuelist[0])
        else:
            self.data = None


class KibbleModelConverter(ModelConverter):
    def convert_BlobKeyProperty(self, model, prop, field_args):
        return BlobKeyField(**field_args)

    def convert_StructuredProperty(self, model, prop, field_args):
        if prop._repeated:
            field_args.setdefault('LIST', {})['widget'] = \
                TabluarFormListWidget()

        return super(KibbleModelConverter, self).\
            convert_StructuredProperty(model, prop, field_args)


