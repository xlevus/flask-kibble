import mock
import flask
from werkzeug.datastructures import MultiDict

from .base import TestCase
from .models import TestModel

import flask_kibble as kibble
from flask_kibble import edit


class TestCreate(kibble.Create):
    model = TestModel


class TestEdit(kibble.Edit):
    model = TestModel

    fieldsets = [
        {'name': 'Name', 'fields': ['name']},
        {
            'name': 'Other',
            'fields': ['other_field_1', 'other_field_2'],
            'other_arg': mock.sentinel.OTHER_ARG
        }
    ]


class CreateTestCase(TestCase):
    def create_app(self):
        return self._create_app(TestCreate, TestEdit)

    def test_view_name(self):
        self.assertEqual(
            TestCreate.view_name(),
            'testmodel_create')

    def test_url(self):
        self.assertEqual(
            flask.url_for('kibble.testmodel_create'),
            '/testmodel/new/')

    @mock.patch.object(TestCreate, 'form')
    def test_get(self, form):
        resp_create = self.client.get('/testmodel/new/')
        self.assert200(resp_create)

        self.authenticator.has_permission_for.assert_called_once_with(
            TestModel, 'create')

        self.assertTemplateUsed('kibble/create.html')

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

        self.assertFlashes("TestModel saved", "success")

        inst = TestModel.query().get()

        save_model.assert_called_once_with(mock.ANY, None)
        get_success_redirect.assert_called_once_with(inst)


class EditTestCase(TestCase):
    def create_app(self):
        return self._create_app(TestCreate, TestEdit)

    def setUp(self):
        self.inst = TestModel(id='test', name='test')
        self.inst.put()

    def test_view_name(self):
        self.assertEqual(
            TestEdit.view_name(),
            'testmodel_edit')

    def test_url(self):
        self.assertEqual(
            flask.url_for('kibble.testmodel_edit', key=self.inst.key),
            '/testmodel/i-test/')

    @mock.patch('flask_kibble.edit.FieldsetIterator')
    @mock.patch.object(TestEdit, 'form')
    def test_get(self, form, fieldset_iterator):
        resp = self.client.get('/testmodel/i-test/')
        self.assert200(resp)
        self.authenticator.has_permission_for.assert_called_once_with(
            TestModel, 'edit', key=self.inst.key)

        fieldset_iterator.assert_called_once_with(mock.ANY, form())

        self.assertTemplateUsed('kibble/edit.html')
        self.assertContext('form', form())
        self.assertContext('instance', self.inst)
        self.assertContext('fieldsets', fieldset_iterator())

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

        self.assertFlashes("TestModel saved", "success")

        inst = self.inst.key.get()
        save_model.assert_called_once_with(mock.ANY, inst)
        get_success_redirect.assert_called_once_with(inst)


class FieldsetIteratorTestCase(TestCase):
    def create_app(self):
        return self._create_app(TestCreate, TestEdit)

    def get_iterator(self):
        view = TestEdit()
        form = view.form()
        return edit.FieldsetIterator(view, form)

    def test_iter(self):
        fsi = self.get_iterator()

        fieldsets = list(fsi)

        self.assertEqual(fieldsets[0].name, 'Name')
        self.assertEqual(
            [x.name for x in fieldsets[0]],
            ['name']
        )

        self.assertEqual(fieldsets[1].name, 'Other')
        self.assertEqual(
            [x.name for x in fieldsets[1]],
            ['other_field_1', 'other_field_2']
        )
        self.assertEqual(fieldsets[1].other_arg, mock.sentinel.OTHER_ARG)

        self.assertEqual(fieldsets[2].name, None)
        self.assertEqual(
            [x.name for x in fieldsets[2]],
            ['other_field_3']
        )

