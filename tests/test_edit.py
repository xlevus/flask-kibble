import mock
import flask
from werkzeug.datastructures import MultiDict

from .base import TestCase
from .models import TestModel

import flask_ndbcrud as crud


class TestCreate(crud.Create):
    model = TestModel


class TestEdit(crud.Edit):
    model = TestModel


class CreateTestCase(TestCase):
    def create_app(self):
        return self._create_app(TestCreate, TestEdit)

    def test_url(self):
        self.assertEqual(
            flask.url_for('crud.testmodel_create'),
            '/testmodel/new/')

    @mock.patch.object(TestCreate, 'form')
    def test_get(self, form):
        resp_create = self.client.get('/testmodel/new/')
        self.assert200(resp_create)

        self.authenticator.has_permission_for.assert_called_once_with(
            TestModel, 'create')

        self.assertTemplateUsed('crud/create.html')

        self.assertContext('form', form())
        self.assertContext('instance', None)

    def test_get_missing_perm(self):
        self.authenticator.has_permission_for.return_value = False
        resp = self.client.get('/testmodel/new/')
        self.assert403(resp)
        self.authenticator.has_permission_for.assert_called_once_with(
            TestModel, 'create')

    def test_post_invalid_form(self):
        data = MultiDict({'name': ''})

        resp = self.client.post('/testmodel/new/', data=data)
        self.assert200(resp)

        self.assertEqual(TestModel.query().count(), 0)

    @mock.patch.object(TestCreate, 'get_success_redirect', return_value='/t/')
    @mock.patch.object(TestCreate, 'save_model')
    def test_post_valid_data(self, save_model, get_success_redirect):
        def _save(form, inst=None):
            inst = TestModel()
            form.populate_obj(inst)
            inst.put()
            return inst
        save_model.side_effect = _save

        data = MultiDict({'name': 'Test2'})
        resp = self.client.post('/testmodel/new/', data=data)

        self.assertRedirects(resp, '/t/')

        self.assertFlashes("TestModel saved")

        inst = TestModel.query().get()

        save_model.assert_called_once_with(mock.ANY, None)
        get_success_redirect.assert_called_once_with(inst)


class EditTestCase(TestCase):
    def create_app(self):
        return self._create_app(TestCreate, TestEdit)

    def setUp(self):
        self.inst = TestModel(id='test', name='test')
        self.inst.put()

    def test_url(self):
        self.assertEqual(
            flask.url_for('crud.testmodel_edit', key=self.inst.key),
            '/testmodel/i-test/')

    @mock.patch.object(TestEdit, 'form')
    def test_get(self, form):
        resp = self.client.get('/testmodel/i-test/')
        self.assert200(resp)
        self.authenticator.has_permission_for.assert_called_once_with(
            TestModel, 'edit', key=self.inst.key)

        self.assertTemplateUsed('crud/edit.html')
        self.assertContext('form', form())
        self.assertContext('instance', self.inst)

    def test_get_missing_perm(self):
        self.authenticator.has_permission_for.return_value = False
        resp = self.client.get('/testmodel/i-test/')
        self.assert403(resp)

    @mock.patch.object(TestEdit, 'get_success_redirect', return_value='/t/')
    @mock.patch.object(TestEdit, 'save_model')
    def test_post_valid_data(self, save_model, get_success_redirect):
        def _save(form, inst):
            form.populate_obj(inst)
            inst.put()
            return inst
        save_model.side_effect = _save

        data = MultiDict({'name': 'Test2'})
        resp = self.client.post('/testmodel/i-test/', data=data)

        self.assertRedirects(resp, '/t/')

        self.assertFlashes("TestModel saved")

        inst = self.inst.key.get()
        save_model.assert_called_once_with(mock.ANY, inst)
        get_success_redirect.assert_called_once_with(inst)


