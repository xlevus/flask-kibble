import flask
from google.appengine.ext import ndb

from .base import KibbleView
from .edit import FieldsetIterator
from .util.forms import BaseCSRFForm


class BaseOperationForm(BaseCSRFForm):
    pass


class Operation(KibbleView):
    action = None

    #: The past tense verb of the action. Used to display default messages
    #: e.g. delete/deleted.
    past_tense = None

    #: If true, the user will be taken to an intermediate confirmation page
    #: otherwise, the operation will be performed immediately.
    require_confirmation = True

    #: The form used when requiring confirmation. By default this is an empty
    #: csrf-protected form
    confirmation_form = BaseOperationForm
    confirmation_fieldsets = []

    _url_patterns = [
        ("/{key}/{action}/", {}),
    ]
    _requires_instance = True
    _methods = ['GET', 'POST']

    class Failure(Exception):
        """To be raised when an operation fails."""
        pass

    @property
    def templates(self):
        return [
            'kibble/operation.html',
            'kibble/%s.html' % self.action,
            'kibble/%s_%s.html' % (self.kind().lower(), self.action)
        ]

    def run(self, instance, form=None):
        """
        Perform the operation on the given instance.

        If the operation fails, this function should raise a
        ``Operation.Failure``. All other exception types will result in a
        HTTP-500 error.

        :param instance: The instance.

        :returns: Any value. If the response is a :py:class:`flask.Response`,
            it will be returned to the user.

        :raises: :class:`~Operation.Failure` to signify the operation failed.
        """
        raise self.Failure('Not Implemented')

    def get_redirect(self, instance, result):
        """
        Upon success or failure, this will be called to determine where to
        redirect the user to.

        :param instance: The instance operated on.
        :param result: The return value of ``self.run()`` or an
            ``Operation.Failure`` exception.

        :returns: The url to redirect to on success.
        """
        return flask.url_for('.index')

    def get_message(self, instance, result):
        """
        Upon success or failure, this will be called to determine which
        message to flash to the user.

        :param instance: The instance operated on.
        :param result: The return value of ``self.run()`` or an
            :class:`~Operation.Failure` exception.

        :returns: The message to flash to the user.
        """
        if isinstance(result, self.Failure):
            m = u"Failed to {verb} {instance}: {result.message}"
        else:
            m = u"Successfully {past_tense} {instance}"

        return m.format(
            verb=self.action,
            past_tense=self.past_tense,
            result=result,
            instance=instance)

    def dispatch_request(self, key):
        instance = key.get()
        form = self.confirmation_form(flask.request.form, obj=instance)
        if instance is None:
            flask.abort(404)

        if not self.require_confirmation or \
                (flask.request.method == 'POST' and form.validate()):
            try:
                result = self.run(
                    instance, form if self.require_confirmation else None)
                if isinstance(result, ndb.Future):
                    result = result.get_result()
                success = True
            except self.Failure, result:
                success = False
            finally:
                if isinstance(result, flask.current_app.response_class):
                    return result

                flask.flash(
                    self.get_message(instance, result),
                    'success' if success else 'error')
                return flask.redirect(
                    self.get_redirect(instance, result))

        ctx = self.base_context()
        ctx['instance'] = instance
        ctx['form'] = form
        ctx['fieldsets'] = FieldsetIterator(form, self.confirmation_fieldsets)
        return flask.render_template(self.templates, **ctx)

