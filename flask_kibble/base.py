import flask
from flask.views import View
from werkzeug.utils import cached_property

from google.appengine.ext import ndb


class KibbleMeta(type):
    _autodiscover = set([])

    def __new__(mcls, name, bases, attrs):
        cls = super(KibbleMeta, mcls).__new__(mcls, name, bases, attrs)
        mcls._autodiscover.add(cls)

        return cls


class KibbleView(View):
    __metaclass__ = KibbleMeta

    #: The name of the action this view performs.
    action = None

    #: The associated :py:class:`ndb.Model` class this action deals with
    model = None

    #: An array of ancestor :py:class:`ndb.Model` classes.
    ancestors = []

    #: A list of associated views that this action can link to.
    #: Can either be a :class:`~flask_kibble.KibbleView` subclass or an action
    #: name.
    linked_actions = []

    #: A list of linked views for descendants.
    linked_descendant_views = []

    #: Bootstrap3 icon classes to use when rendering the views button. If
    #: not provided, text will be used
    button_icon = None
    #: Bootstrap3 button class to be used when rendering the views button.
    button_class = 'btn-default'

    _methods = ['GET']  # Duplicate?

    #: List of the views url patterns. Should be a tuple of ``(pattern,
    #: defaults)``. Pattern is formatted with the following arguments:
    #:  * ``key`` a template for the objects key
    #:  * ``ancestor_key`` a template for the ancestoral key
    #:  * ``kind`` the model's kind.
    #:  * ``kind_lower`` lowercase model kind
    #:  * ``action`` the name of the action.
    _url_patterns = [("/{kind_lower}/{action}/", {})]

    #: Does the view require an instance to act against. Used
    #: when rendering buttons.
    _requires_instance = True

    @classmethod
    def kind(cls):
        """
        Returns the name of the associated :py:class:`ndb.Model`.
        """
        return cls.model._get_kind()

    @classmethod
    def view_name(cls):
        """
        Returns the name of the flask endpoint for this view.

        Defaults to ``<kind.lower>_<action>`` or
        ``<ancestor.lower>_<kind.lower>_<action>`` for ancestor views.
        """
        return "_".join(
            [a._get_kind().lower() for a in cls.ancestors] +
            [cls.kind().lower(), cls.action])

    @property
    def templates(self):
        """
        The views templates.

        Defaults to:
            * ``kibble/{action}.html``
            * ``kibble/{kind.lower}_{action}.html``
        """
        return [
            'kibble/%s.html' % self.action,
            'kibble/%s_%s.html' % (self.kind().lower(), self.action)
        ]

    def base_context(self):
        """
        The base context the view should provide to the template.

        :returns: Context dictionary
        """
        return {
            'view': self,
        }

    @classmethod
    def has_permission_for(cls, key=None):
        """
        Check if the user has the permissions required for this view.

        :param key: A a :py:class:`ndb.Model` instance or :py:class:`ndb.Key`
            to perform row-level permission checks against.
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

        :param key: A a :py:class:`ndb.Model` instance or :py:class:`ndb.Key`
            to link to (optional)
        :param blueprint: The blueprint name the view is registered to. If not
            provided, the current requests blueprint will be used. (optional)
        :returns: View URL
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

