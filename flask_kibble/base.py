import re
from warnings import warn
import flask
from flask.views import View
from werkzeug.utils import cached_property

from google.appengine.ext import ndb

try:
    import blinker
except ImportError:
    warn("Blinker not installed, using stub signals.")
    blinker = None


class StubSignal(object):
    """
    Stub signal class for when blinker isn't installed.
    """
    def send(self, *args, **kwargs):
        pass

    def connnect(self, *args, **kwargs):
        pass


class KibbleMeta(type):
    _autodiscover = set([])

    def __new__(mcls, name, bases, attrs):
        cls = super(KibbleMeta, mcls).__new__(mcls, name, bases, attrs)

        if blinker and cls.model:
            cls.pre_signal = blinker.signal("{}-pre-{}".format(
                cls.kind(), cls.action))

            cls.post_signal = blinker.signal("{}-post-{}".format(
                cls.kind(), cls.action))
        else:
            cls.pre_signal = StubSignal()
            cls.post_signal = StubSignal()

        mcls._autodiscover.add(cls)

        return cls


class KibbleView(View):
    __metaclass__ = KibbleMeta

    #: The name of the action this view performs.
    action = None

    #: The associated :py:class:`ndb.Model` class this action deals with
    model = None

    #: A grouping value for the index page.
    group = None

    #: Hidden classes will not be visible on the index and menu pages
    #: Can still be explicitly linked to with linked_actions.
    hidden = False

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

    #: Does the view require an ancestor key if `ancestors` are present?
    _requires_ancestor = False

    @classmethod
    def kind(cls):
        """
        Returns the name of the associated :py:class:`ndb.Model`.
        """
        return cls.model._get_kind()

    KIND_LABEL_RE = re.compile(r'([a-z])([A-Z0-9])')

    @classmethod
    def _make_label(cls, kind):
        if issubclass(kind, ndb.Model):
            kind = kind._get_kind()

        label = flask.current_app.config.get('KIBBLE_KIND_LABELS', {}).get(
            kind)

        if label:
            return label

        return cls.KIND_LABEL_RE.sub(r'\1 \2', kind)

    @classmethod
    def kind_label(cls):
        """
        Returns a user friendly label for the associated :py:class`ndb.Model`.
        
        Alternate labels can be defined in the Flask application setting 
        ``KIBBLE_KIND_LABELS``.
        """
        return cls._make_label(cls.model)

    @classmethod
    def ancestor_labels(cls):
        """
        Labels for each of the ancestors in Path.
        """
        return [cls._make_label(a) for a in cls.ancestors]

    @classmethod
    def view_name(cls):
        """
        Returns the name of the flask endpoint for this view.

        Defaults to ``<kind.lower>_<action>`` or
        ``<ancestor.lower>_<kind.lower>_<action>`` for ancestor views.
        """
        return cls.path().lower().replace('/', '_') + '_' + cls.action

    @classmethod
    def path(cls):
        """
        The "Path" of the view. Will return slash-separated
        ancestral path.
        """
        p = [a._get_kind() for a in cls.ancestors] +\
            [cls.kind()]
        return "/".join(p)

    @classmethod
    def url_patterns(cls):
        return cls._url_patterns

    @property
    def templates(self):
        """
        The views templates.

        Defaults to:
            * ''kibble/{path.lower}/{action}.html``
            * ``kibble/{kind.lower}/{action}.html``
            * ``kibble/{action}.html``
        """
        kwargs = {
            'action': self.action,
            'path': self.path().lower(),
            'kind': self.kind().lower(),
        }
        return [
            'kibble/{path}/{action}.html'.format(**kwargs),
            'kibble/{kind}/{action}.html'.format(**kwargs),
            'kibble/{action}.html'.format(**kwargs),
        ]

    def base_context(self):
        """
        The base context the view should provide to the template.

        :returns: Context dictionary
        """
        return {
            'view': self,
            'is_popup': self._is_popup(),
            'is_embed': self._is_embed(),
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
    def url_for(cls, key=None, ancestor_key=None, blueprint='', **kwargs):
        """
        Get the URL for this view.

        :param key: A a :py:class:`ndb.Model` instance or :py:class:`ndb.Key`
            to link to (optional)
        :param blueprint: The blueprint name the view is registered to. If not
            provided, the current requests blueprint will be used. (optional)
        :returns: View URL
        """

        kwargs.setdefault('_popup', cls._is_popup())
        kwargs.setdefault('_embed', cls._is_embed())

        if cls.ancestors:
            if (key or ancestor_key) is None and cls._ancestor_required():
                # No ancestor provided
                return None

            if isinstance(ancestor_key, ndb.Model):
                ancestor_key = ancestor_key.key
                key = None
        else:
            if isinstance(key, ndb.Model):
                key = key.key
            # No ancestors, so this value isn't necessary
            ancestor_key = None

        return flask.url_for(
            '%s.%s' % (blueprint, cls.view_name()),
            key=key,
            ancestor_key=ancestor_key,
            **kwargs)

    @cached_property
    def _linked_actions(self):
        views = []
        for v in self.linked_actions:
            if isinstance(v, type) and issubclass(v, KibbleView):
                views.append(v)
            else:
                try:
                    path, action = v.split(":")
                except ValueError:
                    path = self.path()
                    action = v

                try:
                    views.append(flask.g.kibble.registry[path][action])
                except KeyError:
                    pass
        return views

    @classmethod
    def _is_popup(self):
        """
        Checks if the current request is in a popup state.
        For the sake of url-building convenince, returns either 1 or None.
        """
        return (1 if '_popup' in flask.request.args else None)

    @classmethod
    def _is_embed(self):
        """
        Checks if the current request is in a embedded state.
        For the sake of url-building convenince, returns either 1 or None.
        """
        return (1 if '_embed' in flask.request.args else None)

    @classmethod
    def _ancestor_required(cls):
        return cls._requires_ancestor and len(cls.ancestors) != 0

    @ndb.tasklet
    def _inst_and_ancestors(self, key):
        futures = []
        while key:
            futures.append(key.get_async())
            key = key.parent()
        objs = yield futures
        raise ndb.Return(objs[::-1])

