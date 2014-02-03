import flask
from werkzeug.routing import BuildError

from .base import CrudView

from wtforms_ndb import model_form


class FormView(CrudView):
    action = 'list'

    form = None

    _methods = ['GET', 'POST']

    def __init__(self, *args, **kwargs):
        super(FormView, self).__init__(*args, **kwargs)

        if not self.form:
            self.form = model_form(self.model)

    def save_model(self, form, instance=None):
        """
        Called when a form is saved with no errors.

        If no instance is present, it it up to this view to create
        a new instance.

        :param form: The form instance
        :param instance: The instance (if any) to save to.
        """
        if instance is None:
            instance = self.model()

        form.populate_obj(instance)
        instance.put()
        return instance

    def get_success_redirect(self, instance):
        """
        Called when the instance has been saved. Should return
        the URL to redirect to afterwards.

        :param instance: The successfully saved instance.
        """
        try:
            return flask.url_for(".%s_list" % self.kind())
        except BuildError:
            return flask.url_for(".index")

    def do_form(self, instance=None):
        form = self.form(flask.request.form, obj=instance)

        if flask.request.method == 'POST' and form.validate():
            instance = self.save_model(form, instance)
            flask.flash("{kind} saved".format(kind=self.kind()))
            return flask.redirect(self.get_success_redirect(instance))

        ctx = self.base_context()
        ctx['form'] = form
        ctx['instance'] = instance

        return flask.render_template(self.templates, **ctx)


class Edit(FormView):
    action = 'edit'

    _url_patterns = [
        ("/{kind_lower}/<ndbkey('{kind}'):key>/", {})
    ]
    _requires_instance = True

    def dispatch_request(self, key):
        instance = key.get()
        if instance is None:
            flask.abort(404)

        return self.do_form(instance)


class Create(FormView):
    action = 'create'

    _url_patterns = [
        ('/{kind_lower}/new/', {}),
    ]
    _requires_instance = False

    def dispatch_request(self):
        return self.do_form(None)

