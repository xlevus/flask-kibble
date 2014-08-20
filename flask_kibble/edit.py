from functools import partial
import logging
import flask

from .base import KibbleView
from .util.forms import KibbleModelConverter, BaseCSRFForm

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
            try:
                field = self.form[field]
            except KeyError:
                pass  # Field is missing, ignore it.
            else:
                yield field

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
    def __init__(self, form, fieldsets):
        self.fieldsets = fieldsets
        self.form = form

        self._fields = set(self.form._fields.keys())

    def __iter__(self):
        for fieldset in self.fieldsets:
            self._fields.difference_update(fieldset.get('fields', []))

            yield Fieldset(self.form, **fieldset)

        if self._fields:
            yield Fieldset(self.form, None, self._fields)


class FormView(KibbleView):
    #: Action name
    action = 'list'

    #: A :py:class:`wtforms_ndb.ModelConverter` class used to convert the
    #: NDB model to a form
    model_converter = KibbleModelConverter

    #: The base formclass to generate the form from. By default this is an
    #: empty CSRF protected form.
    base_form = BaseCSRFForm

    #: The :py:class:`wtforms.Form` class to use. If not provided
    #: one will be generated through :py:func:`wtforms_ndb.model_form`.
    form = None

    #: If no form is provided, These per-field arguments will passed through
    #: to :py:func:`wtforms_ndb.model_form`.
    form_field_args = None

    #: An array of fields to only use when generating the form.
    only_fields = None

    #: An array of fields to skip when generating the form.
    exclude_fields = None

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

    def get_success_response(self, instance):
        """
        Called when the instance has been saved. Should return
        the URL to redirect to afterwards.

        :param instance: The successfully saved instance.
        :returns: URL to redirect to.
        """
        url = None
        cont = flask.request.form.get('__continue', None)

        url_for = flask.g.kibble.url_for

        if cont == "edit":
            # User has hit "Save and continue editing"
            url = url_for(self.path(), 'edit', instance=instance)

        elif cont == "new":
            # User has hit "save and create another"
            url = url_for(self.path(), 'create')

        if url:
            # One of the above url_for's have returned a URL, so
            # redirect to it.
            # n.b. If the user has no permissions, no url will be returned.
            return flask.redirect(url)

        if self._is_popup():
            # We're in a popup, so dismiss it.
            return flask.make_response(flask.render_template(
                'kibble/dismiss_popup.html',
                instance=instance))

        return flask.redirect(
            (url_for(self.path(), 'list') or flask.url_for('.index')))

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

    def get_form_class(self):
        if not self.form:
            return self.model_converter.model_form(
                self.model,
                base_class=self.base_form,
                field_args=self.form_field_args,
                only=self.only_fields,
                exclude=self.exclude_fields)
        return self.form

    def get_form_instance(self, instance=None):
        """
        Returns an instance of the form for the view.

        :param instance: The instance to edit or None.
        """
        formcls = self.get_form_class()
        return formcls(flask.request.form, obj=instance)

    def _form_logic(self, instance=None, ancestor_key=None):
        form = self.get_form_instance(instance)

        if flask.request.method == 'POST' and form.validate():

            self.pre_signal.send(
                self.__class__,
                instance=instance,
                ancestor_key=ancestor_key,
                key=instance.key if instance else None)

            instance = self.save_model(form, instance, ancestor_key)

            self.post_signal.send(
                self.__class__,
                instance=instance,
                ancestor_key=ancestor_key,
                key=instance.key if instance else None)

            flask.flash(self.get_success_message(instance), 'success')

            return self.get_success_response(instance)

        ctx = self.base_context()
        ctx['form'] = form
        ctx['fieldsets'] = FieldsetIterator(form, self.fieldsets)
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


