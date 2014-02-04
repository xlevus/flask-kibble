import logging
import os
from collections import defaultdict

from google.appengine.ext import ndb

import flask

logger = logging.getLogger(__name__)


class Authenticator(object):
    def is_logged_in(self):
        """
        Should return true if the current user is logged in.
        """
        return True

    def has_permission_for(self, model, action, key=None, **view_args):
        """
        Should return true if the current user has the permissions for
        the Model/Action/ViewArgs.

        :param model: The model class that is being operated on
        :param action: The CrudView.action that is being executed or the name
            of the view (for non-CBVs)
        :param key: The ndb.Key of the object currently operating on.
        :param **view_args: The current view args.
        """
        return True

    def get_login_url(self):
        """
        Should return a URL the user can use to log in.
        """
        return "/"


def index():
    """
    Crud index view. Lists the registered classes and views.
    """
    return flask.render_template('crud/index.html')


class Crud(flask.Blueprint):
    def __init__(self, name, import_name, authenticator, **kwargs):

        kwargs.setdefault(
            'template_folder',
            os.path.join(os.path.dirname(__file__), 'templates'))

        kwargs.setdefault(
            'static_folder',
            os.path.join(os.path.dirname(__file__), 'static'))

        super(Crud, self).__init__(name, import_name, **kwargs)
        self.auth = authenticator

        self.registry = defaultdict(dict)

        self.add_url_rule('/', view_func=index, endpoint='index')

        self.record_once(self._register_urlconverter)

        self.before_request(self._before_request)
        self.context_processor(self._context_processor)

    def register_view(self, view_class):
        """
        Register a class with the CRUD blueprint.

        :param view_class: A crud view class
        :param url_pattern: Override the URL pattern provided by the crud
        class.

        :raises ValueError: When the same (Class,Action) pair is already
        registered.
        """
        action = view_class.action
        kind = view_class.kind()

        # Check for duplicates
        if action in self.registry[kind]:
            raise ValueError("%s already has view for %s.%s" % (
                self, kind, action))

        view_func = view_class.as_view(view_class.view_name())

        for pattern, defaults in view_class._url_patterns:
            self.add_url_rule(
                pattern.format(
                    kind=kind,
                    kind_lower=kind.lower(),
                    action=action),
                methods=view_class._methods,
                defaults=defaults,
                view_func=view_func)

        self.registry[kind][action] = view_class

    def _context_processor(self):
        return {'crud': self}

    @classmethod
    def _register_urlconverter(self, setup_state):
        from .util.url_converter import NDBKeyConverter
        app = setup_state.app
        app.url_map.converters.setdefault('ndbkey', NDBKeyConverter)

    def _before_request(self):
        flask.g.crud = self         # Set global var

        if not self.auth.is_logged_in():
            # User not logged in, redirect to the login url.
            logger.debug("User is not logged in.")
            flask.flash("You are not logged in.", 'warning')
            return flask.redirect(self.auth.get_login_url())

        view_func = flask.current_app.view_functions[flask.request.endpoint]
        view_class = getattr(view_func, 'view_class', None)

        if view_class:
            # for CBVs, use the model and action parameters.
            model = view_class.model
            action = view_class.action
        else:
            # For non-CBVs, use the view name as the permission values.
            model = None
            action = view_func.__name__

        if not self.auth.has_permission_for(
                model, action,
                **flask.request.view_args):

            logger.debug("User is missing permission for %r",
                         flask.request.endpoint)
            return flask.render_template('crud/403.html'), 403

    def url_for(self, model, action, key=None, instance=None):
        """
        Get the URL for a specific Model/Action/Instance.

        If the view isn't registered, returns an empty string.
        """
        if issubclass(model, ndb.Model):
            model = model._get_kind()

        view = self.registry.get(model, {}).get(action)

        if not view:
            return ""

        return view.url_for(self.name, key, instance)

