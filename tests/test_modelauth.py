import flask
from .base import TestCase
from .models import TestModel

from flask_kibble.modelauth import ModelAuthenticatior, KibbleUser, \
    KibbleUserGroup


class ModelauthTestCase(TestCase):
    def create_app(self):
        return flask.Flask(__name__)

    def auth(self):
        return ModelAuthenticatior()

    def create_user(self, email, enabled=True, superuser=False,
                    perms=None, groups=None):
        perms = perms or []
        groups = groups or []

        u = KibbleUser(
            id=email,
            email=email,
            enabled=enabled,
            superuser=superuser,
            permissions=perms,
            groups=groups)
        u.put()
        return u

    def create_group(self, name, perms=None):
        perms = perms or []
        g = KibbleUserGroup(
            name=name,
            permissions=perms)
        return g.put()

    def test_is_logged_in(self):
        auth = self.auth()

        self.login_appengine_user("test@example.com", "test")
        self.assertTrue(auth.is_logged_in())

        self.logout_appengine_user()
        self.assertFalse(auth.is_logged_in())

    def test_is_admin(self):
        """
        Appengine administrators should have access to everything.
        """
        auth = self.auth()
        self.login_appengine_user("norow@example.com", "admin", True)
        self.assertTrue(auth.has_permission_for(TestModel, 'FOOBAR'))
        self.assertTrue(auth.has_permission_for(TestModel, 'XYZZY'))
        self.assertTrue(auth.has_permission_for(int, 'XYZZY'))

    def test_is_superuser(self):
        auth = self.auth()
        self.create_user("test@example.com", superuser=True)
        self.login_appengine_user("test@example.com", "test")
        self.assertTrue(auth.has_permission_for(TestModel, 'FOOBAR'))
        self.assertTrue(auth.has_permission_for(TestModel, 'XYZZY'))
        self.assertTrue(auth.has_permission_for(int, 'XYZZY'))

        self.create_user("disabled@example.com", enabled=False, superuser=True)
        self.login_appengine_user("disabled@example.com", "disabled")
        self.assertFalse(auth.has_permission_for(TestModel, 'FOOBAR'))
        self.assertFalse(auth.has_permission_for(TestModel, 'XYZZY'))
        self.assertFalse(auth.has_permission_for(int, 'XYZZY'))

    def test_has_permission_for(self):
        self.create_user('test@example.com', perms=['TestModel:edit'])

        auth = self.auth()
        self.login_appengine_user('test@example.com', 'test')

        self.assertTrue(auth.has_permission_for(TestModel, 'edit'))
        self.assertFalse(auth.has_permission_for(TestModel, 'delete'))

    def test_no_user_in_db(self):
        """
        Check that when there is no KibbleUser object  the user nas no perms
        """
        self.create_user('test@example.com', perms=['TestModel:edit'])

    def test_has_permission_for(self):
        self.create_user('test@example.com', perms=['TestModel:edit'])

        auth = self.auth()
        self.login_appengine_user('test@example.com', 'test')

        self.assertTrue(auth.has_permission_for(TestModel, 'edit'))
        self.assertFalse(auth.has_permission_for(TestModel, 'delete'))

    def test_no_user_in_db(self):
        """
        Check that when there is no KibbleUser object  the user nas no perms
        """
        self.create_user('test@example.com', perms=['TestModel:edit'])

        auth = self.auth()
        self.login_appengine_user('wronguser@example.com', 'test')

        self.assertFalse(auth.has_permission_for(TestModel, 'edit'))
        self.assertFalse(auth.has_permission_for(TestModel, 'delete'))

    def test_user_disabled(self):
        """
        Disabled users should have no permissions
        """
        self.create_user('test@example.com', enabled=False,
                         perms=['TestModel:edit'])

        auth = self.auth()
        self.login_appengine_user('test@example.com', 'test')

        self.assertFalse(auth.has_permission_for(TestModel, 'edit'))
        self.assertFalse(auth.has_permission_for(TestModel, 'delete'))

    def test_group(self):
        g = self.create_group('test1', ['TestModel:edit'])
        self.create_user('test@example.com', groups=[g],
                         perms=['TestModel:delete'])

        auth = self.auth()
        self.login_appengine_user('test@example.com', 'test')
        self.assertTrue(auth.has_permission_for(TestModel, 'edit'))
        self.assertTrue(auth.has_permission_for(TestModel, 'delete'))
        self.assertFalse(auth.has_permission_for(TestModel, 'borkborkbork'))


