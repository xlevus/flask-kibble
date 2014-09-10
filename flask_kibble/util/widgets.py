from base64 import b64encode
from functools import partial
import flask

import wtforms
from wtforms.widgets import HTMLString, html_params
from google.appengine.ext import blobstore


class JSUploadWidget(object):
    template = 'kibble/widgets/jsupload.html'

    def __call__(self, field, **kwargs):
        kwargs['name'] = field.name
        ctx = {
            'upload_url': blobstore.create_upload_url(
                flask.url_for('.upload'),
                gs_bucket_name=flask.g.kibble.gcs_bucket),
            'filename': '',
            'value': str(field.data or ''),
            'field_args': kwargs,
        }
        if field.data:
            ctx['filename'] = blobstore.BlobInfo(field.data).filename

        return HTMLString(
            flask.render_template(self.template,
                                  **ctx))


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


class TabularFormWidget(object):
    template = 'kibble/widgets/tabularform.html'

    def __init__(self, fieldsets=None):
        self.fieldsets = fieldsets or []

    def __call__(self, field, **kwargs):
        from flask_kibble.edit import FieldsetIterator

        html = flask.render_template(
            self.template,
            field=field,
            fieldsets=FieldsetIterator(field.form, self.fieldsets),
            kwargs=kwargs,
        )
        return HTMLString(html)


class KeyWidget(wtforms.widgets.Select):
    template = 'kibble/widgets/key.html'

    def __init__(self, kind, multiple=False):
        self.kind = kind
        self.multiple = multiple

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        if self.multiple:
            kwargs['multiple'] = True

        html = flask.render_template(
            self.template,
            kind=self.kind,
            html_params=html_params(name=field.name, **kwargs),
            kwargs=kwargs,
            widget=self,
            field=field)

        return HTMLString(html)

