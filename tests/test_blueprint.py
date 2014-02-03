import mock

from .base import TestCase, TestAuthenticator
from .models import TestModel

import flask_ndbcrud as crud
from flask_ndbcrud.base import CrudView


class DummyView(CrudView):
    action = 'dummy'
    model = TestModel

    _url_patterns = [
        ('/{kind_lower}/{action}/<test>/', {}),
        ('/{kind_lower}/{action}/', {'test': None})
    ]
    _methods = ['GET', 'DELETE']


class BlueprintTestCase(TestCase):
    def create_app(self):
        return self._create_app(DummyView)

    def test_register(self):
        """
        Check that when registering a view class, the associated _url_patterns
        are registered.

        Also check the view gets added to the internal registry.
        """
        bp = crud.Crud('test_crud', __name__, TestAuthenticator())

        mpo = mock.patch.object
        with mpo(bp, 'add_url_rule', wraps=bp.add_url_rule) as add_url_rule:
            bp.register_view(DummyView)

            self.assertEqual(add_url_rule.call_args_list, [
                mock.call('/testmodel/dummy/<test>/',
                          methods=['GET', 'DELETE'],
                          defaults={},
                          view_func=mock.ANY),
                mock.call('/testmodel/dummy/',
                          methods=['GET', 'DELETE'],
                          defaults={'test': None},
                          view_func=mock.ANY)])

            self.assertEqual(bp.registry, {'TestModel': {'dummy': DummyView}})

    def test_context_processor(self):
        self.assertEqual(self.crud._context_processor(), {
            'crud': self.crud,
        })


class BlueprintIndexTestCase(TestCase):
    """
    Index view tests. Also covers permission checks.
    """
    def create_app(self):
        return self._create_app(DummyView)

    def test_index(self):
        resp = self.client.get('/')
        self.assert200(resp)
        self.assertTemplateUsed('crud/index.html')

        self.authenticator.has_permission_for.assert_called_once_with(
            None, 'index')

    def test_index_noperm(self):
        # Maybe the user should always have the index permission?
        self.authenticator.has_permission_for.return_value = False
        resp = self.client.get('/')
        self.assert403(resp)

    def test_index_loggedout(self):
        self.authenticator.is_logged_in.return_value = False

        resp = self.client.get('/')
        self.assertRedirects(resp, self.authenticator.get_login_url())


