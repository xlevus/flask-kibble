import flask
import wtforms
from wtforms_ndb import model_form as orig_model_form
from wtforms.csrf.session import SessionCSRF


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


def model_form(model, base_class=BaseCSRFForm, only=None, exclude=None,
               field_args=None, converter=None):
    return orig_model_form(model, base_class, only, exclude,
                           field_args, converter)

