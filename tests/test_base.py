import flask
import mock

from .base import TestCase
from .models import TestModel

from flask_kibble.base import KibbleView


class DummyView(KibbleView):
    action = 'dummy'
    model = TestModel

    _url_patterns = [
        ('/{kind_lower}/{action}/<test>/', {}),
        ('/{kind_lower}/{action}/', {'test': None})
    ]
    _methods = ['GET', 'DELETE']


class BaseKibbleViewTestCase(TestCase):
    def create_app(self):
        return self._create_app(DummyView)

    def get_view(self):
        return DummyView()

    def setUp(self):
        self.inst = TestModel(id='test', name='test')
        self.inst.put()

    def test_templates(self):
        v = self.get_view()

        self.assertEqual(v.templates, [
            'kibble/dummy.html',
            'kibble/testmodel_dummy.html',
        ])

    def test_has_permission_for(self):
        v = self.get_view()

        flask.g.kibble = self.kibble

        with mock.patch.object(self.kibble.auth, 'has_permission_for') as auth:
            v.has_permission_for()
            auth.assert_called_once_with(TestModel, 'dummy', key=None)
            auth.reset_mock()

            v.has_permission_for(self.inst)
            auth.assert_called_once_with(TestModel, 'dummy', key=self.inst.key)
            auth.reset_mock()

            v.has_permission_for(self.inst.key)
            auth.assert_called_once_with(TestModel, 'dummy', key=self.inst.key)
            auth.reset_mock()

    @mock.patch.object(flask, 'url_for')
    def test_url_for(self, url_for):
        v = self.get_view()

        v.url_for()
        url_for.assert_called_once_with('.testmodel_dummy', key=None)
        url_for.reset_mock()

        v.url_for(self.inst)
        url_for.assert_called_once_with('.testmodel_dummy', key=self.inst.key)
        url_for.reset_mock()

        v.url_for(self.inst.key)
        url_for.assert_called_once_with('.testmodel_dummy', key=self.inst.key)
        url_for.reset_mock()

        v.url_for(blueprint='fudge')
        url_for.assert_called_once_with('fudge.testmodel_dummy', key=None)
        url_for.reset_mock()

