import flask
from werkzeug.routing import BuildError

from .base import CrudView

from wtforms_ndb import model_form


class Fieldset(object):
    def __init__(self, form, name=None, fields=None, **kwargs):
        self.name = name
        self.form = form
        self.fields = fields or []
        self._kwargs = kwargs

    def __getattr__(self, attr):
        try:
            return self._kwargs[attr]
        except KeyError:
            raise AttributeError("Fieldset %r has no attribute %r" % (
                self.name, attr))

    def __iter__(self):
        for field in self.fields:
            yield self.form[field]


class FieldsetIterator(object):
    """
    Iterator to facilitate ordering and grouping fields.

    If not all fields are specified in the view's fieldsets parameter,
    a final group will be created containing the remainders.

    :param crud_view: The crud view instance.
    :param form: The form.
    """
    def __init__(self, crud_view, form):
        self.crud_view = crud_view
        self.form = form

        self._fields = set(self.form._fields.keys())

    def __iter__(self):
        for fieldset in self.crud_view.fieldsets:
            self._fields.difference_update(fieldset.get('fields', []))

            yield Fieldset(self.form, **fieldset)

        if self._fields:
            yield Fieldset(self.form, None, self._fields)


class FormView(CrudView):
    action = 'list'

    form = None

    #: An array of dictionaries specifying fieldsets. These should
    #: contain at least a ``name`` and ``fields`` values.
    #: All fields not specified will be grouped into an unordered
    #: remainder.
    #:
    #: Example ::
    #:
    #:  [
    #:      {'name':"Title", 'fields': ['title','slug']},
    #:  ]
    fieldsets = []

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

    def _form_logic(self, instance=None):
        form = self.form(flask.request.form, obj=instance)

        if flask.request.method == 'POST' and form.validate():
            instance = self.save_model(form, instance)
            flask.flash("{kind} saved".format(kind=self.kind()))
            return flask.redirect(self.get_success_redirect(instance))

        ctx = self.base_context()
        ctx['form'] = form
        ctx['fieldsets'] = FieldsetIterator(self, form)
        ctx['instance'] = instance

        return flask.render_template(self.templates, **ctx)


class Edit(FormView):
    action = 'edit'

    button_icon = 'pencil'

    _url_patterns = [
        ("/{kind_lower}/<ndbkey('{kind}'):key>/", {})
    ]
    _requires_instance = True

    def dispatch_request(self, key):
        instance = key.get()
        if instance is None:
            flask.abort(404)

        return self._form_logic(instance)


class Create(FormView):
    action = 'create'

    button_icon = 'plus-sign'

    _url_patterns = [
        ('/{kind_lower}/new/', {}),
    ]
    _requires_instance = False

    def dispatch_request(self):
        return self._form_logic(None)

