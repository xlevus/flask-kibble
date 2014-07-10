import logging
import flask

from .base import KibbleView

from flask_kibble.util import forms

logger = logging.getLogger(__name__)


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

    def __bool__(self):
        return len(self.fields) > 0


class FieldsetIterator(object):
    """
    Iterator to facilitate ordering and grouping fields.

    If not all fields are specified in the view's fieldsets parameter,
    a final group will be created containing the remainders.

    :param kibble_view: The kibble view instance.
    :param form: The form.
    """
    def __init__(self, kibble_view, form):
        self.kibble_view = kibble_view
        self.form = form

        self._fields = set(self.form._fields.keys())

    def __iter__(self):
        for fieldset in self.kibble_view.fieldsets:
            self._fields.difference_update(fieldset.get('fields', []))

            yield Fieldset(self.form, **fieldset)

        if self._fields:
            yield Fieldset(self.form, None, self._fields)


class FormView(KibbleView):
    #: Action name
    action = 'list'

    #: The :py:class:`wtforms.Form` class to use. If not provided
    #: one will be generated through :py:func:`wtforms_ndb.model_form`.
    form = None

    #: If no form is provided, These per-field arguments will passed through
    #: to :py:func:`wtforms_ndb.model_form`.
    form_field_args = None

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
            self.form = forms.model_form(
                self.model,
                field_args=self.form_field_args)

    def save_model(self, form, instance=None, ancestor_key=None):
        """
        Called when a form is saved with no errors.

        If no instance is present, it it up to this view to create
        a new instance.

        :param form: The form instance
        :param instance: The instance (if any) to save to.

        :returns: The saved instance
        :rtype: :py:class:`ndb.Model`
        """
        if instance is None:
            instance = self.model(parent=ancestor_key)

        form.populate_obj(instance)
        instance.put()
        return instance

    def get_success_redirect(self, instance):
        """
        Called when the instance has been saved. Should return
        the URL to redirect to afterwards.

        :param instance: The successfully saved instance.
        :returns: URL to redirect to.
        """
        return (
            flask.g.kibble.url_for(self.model, 'list')
            or flask.g.kibble.url_for(self.model, 'edit', instance)
            or flask.url_for('.index')
        )

    def get_success_message(self, instance):
        """
        Returns the message to flash to the user on a successful action.

        :param instance: The successfully saved instance.
        :returns: Message to flash.
        """
        url = flask.g.kibble.url_for(self.model, 'edit', instance)
        if url:
            tmpl = u"{kind} <a href='{url}'>'{instance}'</a> saved."
        else:
            tmpl = u"{kind} '{instance}' saved."

        return tmpl.format(
            url=url,
            instance=instance,
            kind=self.kind())

    def _form_logic(self, instance=None, ancestor_key=None):
        form = self.form(flask.request.form, obj=instance)

        if flask.request.method == 'POST' and form.validate():
            instance = self.save_model(form, instance, ancestor_key)
            flask.flash(self.get_success_message(instance), 'success')
            return flask.redirect(self.get_success_redirect(instance))

        ctx = self.base_context()
        ctx['form'] = form
        ctx['fieldsets'] = FieldsetIterator(self, form)
        ctx['instance'] = instance

        return flask.render_template(self.templates, **ctx)


class Edit(FormView):
    #: View name
    action = 'edit'

    button_icon = 'pencil'

    _url_patterns = [
        ("/{key}/", {})
    ]
    _requires_instance = True

    def dispatch_request(self, key):
        instance = key.get()
        if instance is None:
            logger.debug("Unable to find instance with key %r", key)
            flask.abort(404)

        return self._form_logic(instance)


class Create(FormView):
    #: View name
    action = 'create'

    button_icon = 'plus-sign'

    _url_patterns = [
        ('/{kind_lower}/new/', {'ancestor_key': None}),
        ('/{ancestor_key}/{kind_lower}/new/', {}),
    ]
    _requires_instance = False

    def dispatch_request(self, ancestor_key=None):
        return self._form_logic(None, ancestor_key)

