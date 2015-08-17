import logging


import flask
import wtforms
from werkzeug import cached_property

from google.appengine.ext import ndb

from . import signals
from .base import KibbleView
from .util.forms import BaseCSRFForm
from .util.ndb import instance_and_ancestors_async

logger = logging.getLogger(__name__)


class Fieldset(object):
    def __init__(self, form, name=None, fields=None, **kwargs):
        self.name = name
        self.form = form
        self.fields = fields or []
        self._kwargs = kwargs

    def __repr__(self):
        return "<Fieldset %s %s>" % (self.name, self._present_fields)

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

    def __len__(self):
        return len(self._present_fields)

    @cached_property
    def _present_fields(self):
        return [f for f in self.fields if f in self.form._fields]


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

    def _visible_fields(self):
        return [
            x for x in self._fields
            if not isinstance(self.form[x], wtforms.HiddenField)
        ]

    @property
    def hidden_fields(self):
        return [
            self.form[x] for x in self._fields
            if isinstance(self.form[x], wtforms.HiddenField)
        ]

    def __iter__(self):
        for fieldset in self.fieldsets:
            self._fields.difference_update(fieldset.get('fields', []))

            fs = Fieldset(self.form, **fieldset)
            if len(fs):
                yield fs

        if self._visible_fields():
            yield Fieldset(self.form, None, self._visible_fields())


class FormView(KibbleView):
    #: Action name
    # action = 'list'

    #: A :py:class:`wtforms_ndb.ModelConverter` class used to convert the
    #: NDB model to a form. If default will use the blueprint-global model
    #: converter.
    model_converter = None

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

    #: Help text per field
    field_help_text = {}

    _methods = ['GET', 'POST']
    _requires_ancestor = True

    _transaction_retries = 3

    def __init__(self, *args, **kwargs):
        super(FormView, self).__init__(*args, **kwargs)

    @property
    def _model_converter(self):
        return self.model_converter or flask.g.kibble.model_converter

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

        # We've got to perform some hokum here. As dispatch_request
        # is likely to end up as a xg transaction due to having other
        # queries on the page, we're kinda forced to do the transaction
        # here.
        # As a result, we have to re-query the instance, and write the
        # changes to the DB. in this closure. See GAE issue 10200.
        @ndb.transactional(retries=self._transaction_retries)
        def _tx(key):
            if key is None:
                inst = self.model(parent=ancestor_key)
            else:
                inst = key.get()

            form.populate_obj(inst)
            inst.put()
            return inst

        return _tx(instance.key if instance else None)

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
            url = url_for(self.path(), 'edit', instance=instance,
                          _embed=self._is_embed())

        elif cont == "new":
            # User has hit "save and create another"
            url = url_for(self.path(), 'create',
                          _embed=self._is_embed())

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

        url = url_for(self.path(), 'list', ancestor=instance.key.parent(),
                      _embed=self._is_embed())
        if url:
            return flask.redirect(url)

        return flask.redirect(flask.url_for('.index'))

    def get_success_message(self, instance):
        """
        Returns the message to flash to the user on a successful action.

        :param instance: The successfully saved instance.
        :returns: Message to flash.
        """
        tmpl = u"{kind} '{instance}' saved."

        return tmpl.format(
            instance=instance,
            kind=self.kind_label())

    def get_form_class(self, instance=None):
        if not self.form:
            return self._model_converter.model_form(
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
        formcls = self.get_form_class(instance)
        return formcls(flask.request.form, obj=instance)

    def get_form_fieldsets(self, instance=None):
        """
        Returns the fieldsets for the form.

        :param instance: The instance being edited.

        :returns: Fieldset array
        """
        return self.fieldsets

    def _form_logic(self, instance=None, ancestor_key=None):
        if instance:
            ancestors = instance_and_ancestors_async(instance.key.parent())
        elif ancestor_key:
            ancestors = instance_and_ancestors_async(ancestor_key)
        else:
            ancestors = None

        form = self.get_form_instance(instance)

        if flask.request.method == 'POST' and form.validate():

            signals.pre_action.send(
                self.action,
                view_class=self.__class__,
                instance=instance,
                ancestor_key=ancestor_key,
                key=instance.key if instance else None)

            instance = self.save_model(form, instance, ancestor_key)

            signals.post_action.send(
                self.action,
                view_class=self.__class__,
                instance=instance,
                ancestor_key=ancestor_key,
                key=instance.key if instance else None)

            flask.flash(self.get_success_message(instance), 'success')

            return self.get_success_response(instance)

        ctx = self.base_context()
        ctx['form'] = form
        ctx['fieldsets'] = FieldsetIterator(
            form,
            self.get_form_fieldsets(instance))
        ctx['instance'] = instance
        ctx['ancestors'] = (ancestors.get_result()
                            if ancestors is not None
                            else [])
        ctx['help_text'] = self.field_help_text

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


