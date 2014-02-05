import flask
from google.appengine.ext import ndb

from .base import CrudView


class Operation(CrudView):
    action = None

    #: The past tense verb of the action. Used to display default messages
    #: e.g. delete/deleted.
    past_tense = None

    #: If true, the user will be taken to an intermediate confirmation page
    #: otherwise, the operation will be performed immediately.
    require_confirmation = True

    _url_patterns = [
        ("/{kind_lower}/<ndbkey('{kind}'):key>/{action}/", {}),
    ]
    _requires_instance = True
    _methods = ['GET', 'POST']

    class Failure(Exception):
        """To be raised when an operation fails."""
        pass

    @property
    def templates(self):
        return [
            'crud/operation.html',
            'crud/%s.html' % self.action,
            'crud/%s_%s.html' % (self.kind().lower(), self.action)
        ]

    def run(self, instance):
        """
        Perform the operation on the given instance.

        If the operation fails, this function should raise a
        ``Operation.Failure``. All other exception types will result in a
        HTTP-500 error.

        :param instance: The instance.

        :raises Operation.Failure: to signify the operation failed.
        :returns: Any value. If the response is a
            flask.current_app.response_class, it will be returned to the user.
        """
        raise self.Failure('Not Implemented')

    def get_redirect(self, instance, result):
        """
        Upon success or failure, this will be called to determine where to
        redirect the user to.

        :param instance: The instance operated on.
        :param result: The return value of ``self.run()`` or an
            ``Operation.Failure`` exception.
        """
        return flask.url_for('.index')

    def get_message(self, instance, result):
        """
        Upon success or failure, this will be called to determine which
        message to flash to the user.

        :param instance: The instance operated on.
        :param result: The return value of ``self.run()`` or an
            ``Operation.Failure`` exception.
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
        if instance is None:
            flask.abort(404)

        if not self.require_confirmation or flask.request.method == 'POST':
            try:
                result = self.run(instance)
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
        return flask.render_template(self.templates, **ctx)

