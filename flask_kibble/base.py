import flask
from flask.views import View
from werkzeug.utils import cached_property

from google.appengine.ext import ndb


class KibbleView(View):
    #: The name of the action this view performs.
    action = None

    #: The associated ndb.Model class this action deals with
    model = None

    #: A list of associated views that this action can link to.
    #: Can either be a KibbleView subclass or an action name.
    linked_actions = []

    #: Bootstrap3 icon classes to use when rendering button icon. If not
    #: present, text will be used
    button_icon = None
    #: Bootstrap3 button class to be used when rendering button.
    button_class = 'btn-default'

    _methods = ['GET']
    _url_patterns = [("/{kind_lower}/{action}/", {})]
    _requires_instance = True

    @classmethod
    def kind(cls):
        return cls.model._get_kind()

    @classmethod
    def view_name(cls):
        return "%s_%s" % (cls.kind().lower(), cls.action)

    @property
    def templates(self):
        return [
            'kibble/%s.html' % self.action,
            'kibble/%s_%s.html' % (self.kind().lower(), self.action)
        ]

    def base_context(self):
        return {
            'view': self,
        }

    @classmethod
    def has_permission_for(cls, key=None):
        """
        Check if the user has the permissions required for this view.

        :param key: A ndb.Key instance to link to (optional)
        :param instance: A ndb.Model instance to link to (optional)
        """
        if isinstance(key, ndb.Model):
            key = key.key

        return flask.g.kibble.auth.has_permission_for(
            cls.model,
            cls.action,
            key=key)

    @classmethod
    def url_for(cls, key=None, blueprint=''):
        """
        Get the URL for this view.

        :param blueprint: The blueprint name the view is registered to. If not
            provided, the current requests blueprint will be used. (optional)
        :param key: A ndb.Key instance to link to (optional)
        :param instance: A ndb.Model instance to link to (optional)
        """
        if isinstance(key, ndb.Model):
            key = key.key

        return flask.url_for(
            '%s.%s' % (blueprint, cls.view_name()),
            key=key)

    @cached_property
    def _linked_actions(self):
        views = []
        for v in self._linked_actions:
            if issubclass(v, KibbleView):
                views.append(v)
            else:
                try:
                    v.append(flask.g.kibble.registry[self.kind()][v])
                except KeyError:
                    pass
        return v

