import mock
import flask

from flask_testing import TestCase as FTestCase

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from google.appengine.datastore import datastore_stub_util

import flask_ndbcrud as crud


ndb.utils.DEBUG = False


class TestAuthenticator(crud.Authenticator):
    def is_logged_in(self):
        return True

    def get_login_url(self):
        return '/login/'


class TestCase(FTestCase):
    def _pre_setup(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

        policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(
            probability=1)
        self.testbed.init_datastore_v3_stub(consistency_policy=policy)

        ctx = ndb.get_context()
        ctx.set_cache_policy(False)
        ctx.set_memcache_policy(False)

        self.testbed.init_memcache_stub()

        super(TestCase, self)._pre_setup()

    def _post_teardown(self):
        super(TestCase, self)._post_teardown()

    def _create_app(self, *crud_views):
        app = flask.Flask(__name__)

        app.config['SECRET_KEY'] = 'test_secret'
        app.config['DEBUG'] = True

        self.authenticator = mock.Mock(wraps=TestAuthenticator())

        self.crud = crud.Crud('crud', __name__, self.authenticator)

        for view in crud_views:
            self.crud.register_view(view)

        app.register_blueprint(self.crud)

        return app

    def assertFlashes(self, expected_message, expected_category='message'):
        with self.client.session_transaction() as session:
            try:
                category, message = session['_flashes'][0]
            except KeyError:
                raise AssertionError('nothing flashed')
            assert expected_message in message
            assert expected_category == category
