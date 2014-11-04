import flask
import wtforms

from wtforms_ndb import ModelConverter
from wtforms.csrf.session import SessionCSRF

from flask_kibble.util import widgets
from flask_kibble.util import fields


class BaseCSRFForm(wtforms.Form):
    class Meta:
        csrf_class = SessionCSRF

        @property
        def csrf(self):
            return flask.current_app.config.get('CSRF_ENABLED', True)

        @property
        def csrf_secret(self):
            return flask.current_app.config['CSRF_SECRET_KEY']

        @property
        def csrf_context(self):
            return flask.session


class KibbleModelConverter(ModelConverter):
    def convert_BlobKeyProperty(self, model, prop, field_args):
        return fields.BlobKeyField(**field_args)

    def convert_StructuredProperty(self, model, prop, field_args):
        if prop._repeated:
            field_args.setdefault('LIST', {}).setdefault(
                'widget',
                widgets.TabluarFormListWidget())

        return super(KibbleModelConverter, self).\
            convert_StructuredProperty(model, prop, field_args)

    def convert_KeyProperty(self, model, prop, field_args):
        widget_args = {}
        if prop._repeated:
            widget_args['multiple'] = True
        widget = widgets.KeyWidget(prop._kind, **widget_args)
        field_args.setdefault('widget', widget)

        return super(KibbleModelConverter, self).convert_KeyProperty(
            model, prop, field_args)

