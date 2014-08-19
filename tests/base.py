import mock
import flask

from flask_gae.testing import TestCase as GAETestCase

from google.appengine.ext import ndb

import flask_kibble as kibble


ndb.utils.DEBUG = False


class ModelEqualityTester(object):
    """
    Utility to assert rough equality of models.
    """
    def __init__(self, key):
        if isinstance(key, ndb.Model):
            key = key.key
        self.key = key

    def __eq__(self, other):
        return getattr(other, 'key', object()) == self.key


class TestAuthenticator(kibble.Authenticator):
    def is_logged_in(self):
        return True

    def get_login_url(self):
        return '/login/'


class TestCase(GAETestCase):
    render_templates = False

    def _create_app(self, *kibble_views):
        app = flask.Flask(__name__)

        app.config['SECRET_KEY'] = 'test_secret'
        app.config['CSRF_SECRET_KEY'] = 'test_secret'
        app.config['CSRF_ENABLED'] = False
        app.config['DEBUG'] = True

        self.authenticator = mock.Mock(wraps=TestAuthenticator())

        self.kibble = kibble.Kibble('kibble', __name__, self.authenticator)

        for view in kibble_views:
            self.kibble.register_view(view)

        app.register_blueprint(self.kibble)

        return app

    def assertFlashes(self, expected_message, expected_category='message'):
        with self.client.session_transaction() as session:
            try:
                category, message = session['_flashes'][0]
            except KeyError:
                raise AssertionError('nothing flashed')
            self.assertIn(
                expected_message, message,
                msg="Message %r not found" % message)
            self.assertEqual(
                expected_category, category,
                msg="Message category mismatch. Expected %r got %r" % (
                    expected_category, category))

