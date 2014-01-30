import os
from collections import defaultdict

import flask


class Authenticator(object):
    def get_user(self):
        return None

    def is_logged_in(self, user):
        True

    def has_permission_for(self, model, action):
        return True


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

        self.context_processor(self._context_processor)
        self.record_once(self._register_urlconverter)
        self.add_url_rule('/', view_func=self._index, endpoint='index')

    def register_view(self, view_class):
        """
        Register a class with the CRUD blueprint.

        :param view_class: A crud view class
        :param url_pattern: Override the URL pattern provided by the crud class.

        :raises ValueError: When the same (Class,Action) pair is already registered.
        """
        action = view_class.action
        model = view_class.model
        kind = view_class.kind()


        # Check for duplicates
        if action in self.registry[kind]:
            raise ValueError("%s already has view for %s.%s" % (
                self, kind, action))

        view_func = view_class.as_view(view_class.view_name())

        for pattern, defaults in view_class._url_patterns:
            self.add_url_rule(
                pattern.format(kind=kind, action=action),
                methods=view_class._methods,
                defaults=defaults,
                view_func = view_func)

        self.registry[kind][action] = view_class


    def _index(self):
        return flask.render_template('crud/index.html')

    def _context_processor(self):
        return {'crud': self}

    @classmethod
    def _register_urlconverter(self, setup_state):
        from .util.url_converter import NDBKeyConverter
        app = setup_state.app
        app.url_map.converters.setdefault('ndbkey', NDBKeyConverter)

