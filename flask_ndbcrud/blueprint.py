import logging
import os
from collections import defaultdict

import flask

logger = logging.getLogger(__name__)


class Authenticator(object):
    def is_logged_in(self):
        True

    def has_permission_for(self, model, action, **view_args):
        return True

    def get_login_url(self):
        return "/"


def index():
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
        if not self.auth.is_logged_in():
            logger.debug("User is not logged in.")
            flask.flash("You are not logged in.", 'warning')
            return flask.redirect(self.auth.get_login_url())

        view_func = flask.current_app.view_functions[flask.request.endpoint]
        view_class = getattr(view_func, 'view_class', None)

        if view_class:
            model = view_class.model
            action = view_class.action
        else:
            model = None
            action = view_func.__name__

        if not self.auth.has_permission_for(
                model, action,
                **flask.request.view_args):

            logger.debug("User is missing permission for %r",
                         flask.request.endpoint)
            return flask.render_template('crud/403.html'), 403

