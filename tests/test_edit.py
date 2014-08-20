import mock
import flask
from werkzeug.datastructures import MultiDict

from .base import TestCase, ModelEqualityTester
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

    def setUp(self):
        post_signal_p = mock.patch.object(TestCreate, 'post_signal')
        self.post_signal = post_signal_p.start()
        self.addCleanup(post_signal_p.stop)

        pre_signal_p = mock.patch.object(TestCreate, 'pre_signal')
        self.pre_signal = pre_signal_p.start()
        self.addCleanup(pre_signal_p.stop)

    def assertPreSignalSent(self, key=None, instance=None, ancestor_key=None):
        self.pre_signal.send.assert_called_once_with(
            TestCreate,
            key=key,
            instance=instance,
            ancestor_key=ancestor_key)

    def assertPostSignalSent(self, key=None, instance=None, ancestor_key=None):
        self.post_signal.send.assert_called_once_with(
            TestCreate,
            key=key,
            instance=instance,
            ancestor_key=ancestor_key)

    def assertNoPreSignalSent(self):
        self.assertFalse(self.pre_signal.send.called)

    def assertNoPostSignalSent(self):
        self.assertFalse(self.post_signal.send.called)

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
            TestModel, 'create', ancestor_key=None)

        self.assertTemplateUsed('kibble/create.html')

        self.assertContext('form', form())
        self.assertContext('instance', None)

        self.assertNoPreSignalSent()
        self.assertNoPostSignalSent()

    def test_get_missing_perm(self):
        self.authenticator.has_permission_for.return_value = False
        resp = self.client.get('/testmodel/new/')
        self.assert403(resp)
        self.authenticator.has_permission_for.assert_called_once_with(
            TestModel, 'create', ancestor_key=None)

        self.assertNoPreSignalSent()
        self.assertNoPostSignalSent()

    def test_post_invalid_form(self):
        data = MultiDict({'name': ''})

        resp = self.client.post('/testmodel/new/', data=data)
        self.assert200(resp)

        self.assertEqual(TestModel.query().count(), 0)

        self.assertNoPreSignalSent()
        self.assertNoPostSignalSent()

    @mock.patch.object(TestCreate, 'get_success_response')
    @mock.patch.object(TestCreate, 'save_model')
    def test_post_valid_data(self, save_model, get_success_response):
        get_success_response.return_value = "SUCCESS"

        def _save(form, inst=None, ancestor_key=None):
            inst = TestModel(parent=ancestor_key)
            form.populate_obj(inst)
            inst.put()
            return inst
        save_model.side_effect = _save

        data = MultiDict({'name': 'Test2'})
        resp = self.client.post('/testmodel/new/', data=data)
        self.assertEqual(resp.data, 'SUCCESS')

        inst = TestModel.query().get()

        # self.assertFlashes("<a href='%s'>'%s'</a> saved" % (
        #     self.kibble.url_for(TestModel, 'edit', inst),
        #     inst), "success")

        save_model.assert_called_once_with(mock.ANY, None, None)

        # Check that the keys match, as they're effectively the same
        # but asserting the instances are equal doesn't work
        self.assertEqual(
            get_success_response.call_args[0][0].key,
            inst.key)

        self.assertPreSignalSent()
        self.assertPostSignalSent(inst.key, inst)

    def test_get_success_response(self):
        view = TestCreate()
        inst = TestModel(id='test', name='test')
        inst.put()
        flask.g.kibble = self.kibble

        trq = (lambda u, **k: self.app.test_request_context(
            "/testmodel-test/"+u, method="POST", **k))

        # Basic success. No list view registered
        with trq(''):
            r1 = view.get_success_response(inst)
            self.assertEqual(r1.status_code, 302)
            self.assertEqual(r1.location, '/')

        # Popup with no __continue value
        with trq('?_popup=1', data={}):
            r2 = view.get_success_response(inst)
            self.assertEqual(r2.status_code, 200)
            self.assertTemplateUsed('kibble/dismiss_popup.html')

        for url_args in ('', '?_popup=1', '?_embed=1'):
            # Save and create another
            with trq(url_args, data={'__continue': 'new'}):
                r3 = view.get_success_response(inst)
                self.assertEqual(r3.status_code, 302)
                self.assertEqual(r3.location, '/testmodel/new/' + url_args)

            # Save and continue editing
            with trq(url_args, data={'__continue': 'edit'}):
                r4 = view.get_success_response(inst)
                self.assertEqual(r4.status_code, 302)
                self.assertEqual(r4.location, '/testmodel-test/' + url_args)

        # Register a list view
        class TestList(kibble.List):
            model = TestModel
        self.kibble.register_view(TestList)
        self.app.add_url_rule('/testmodel/', endpoint='kibble.testmodel_list')

        # Basic success. List view registered
        with trq(''):
            r1 = view.get_success_response(inst)
            self.assertEqual(r1.status_code, 302)
            self.assertEqual(r1.location, '/testmodel/')

        with trq('?_embed=1'):
            r1 = view.get_success_response(inst)
            self.assertEqual(r1.status_code, 302)
            self.assertEqual(r1.location, '/testmodel/?_embed=1')


class EditTestCase(TestCase):
    def create_app(self):
        return self._create_app(TestCreate, TestEdit)

    def setUp(self):
        self.inst = TestModel(id='test', name='test')
        self.inst.put()

        post_signal_p = mock.patch.object(TestEdit, 'post_signal')
        self.post_signal = post_signal_p.start()
        self.addCleanup(post_signal_p.stop)

        pre_signal_p = mock.patch.object(TestEdit, 'pre_signal')
        self.pre_signal = pre_signal_p.start()
        self.addCleanup(pre_signal_p.stop)

    def assertPreSignalSent(self, key=None, instance=None, ancestor_key=None):
        self.pre_signal.send.assert_called_once_with(
            TestEdit,
            key=key,
            instance=instance,
            ancestor_key=ancestor_key)

    def assertPostSignalSent(self, key=None, instance=None, ancestor_key=None):
        self.post_signal.send.assert_called_once_with(
            TestEdit,
            key=key,
            instance=instance,
            ancestor_key=ancestor_key)

    def assertNoPreSignalSent(self):
        self.assertFalse(self.pre_signal.send.called)

    def assertNoPostSignalSent(self):
        self.assertFalse(self.post_signal.send.called)

    def test_view_name(self):
        self.assertEqual(
            TestEdit.view_name(),
            'testmodel_edit')

    def test_url(self):
        self.assertEqual(
            flask.url_for('kibble.testmodel_edit', key=self.inst.key),
            '/testmodel-test/')

    @mock.patch('flask_kibble.edit.FieldsetIterator')
    @mock.patch.object(TestEdit, 'form')
    def test_get(self, form, fieldset_iterator):
        resp = self.client.get('/testmodel-test/')
        self.assert200(resp)
        self.authenticator.has_permission_for.assert_called_once_with(
            TestModel, 'edit', key=self.inst.key)

        fieldset_iterator.assert_called_once_with(form(), TestEdit.fieldsets)

        self.assertTemplateUsed('kibble/edit.html')
        self.assertContext('form', form())
        self.assertContext('instance', ModelEqualityTester(self.inst))
        self.assertContext('fieldsets', fieldset_iterator())

        self.assertNoPreSignalSent()
        self.assertNoPostSignalSent()

    def test_get_missing_perm(self):
        self.authenticator.has_permission_for.return_value = False
        resp = self.client.get('/testmodel-test/')
        self.assert403(resp)

        self.assertNoPreSignalSent()
        self.assertNoPostSignalSent()

    @mock.patch.object(TestEdit, 'get_success_response')
    @mock.patch.object(TestEdit, 'save_model')
    def test_post_valid_data(self, save_model, get_success_response):
        get_success_response.return_value = 'SUCCESS'

        def _save(form, inst, ancestor_key=None):
            form.populate_obj(inst)
            inst.put()
            return inst
        save_model.side_effect = _save

        data = MultiDict({'name': 'Test2'})
        resp = self.client.post('/testmodel-test/', data=data)
        self.assertEqual(resp.data, "SUCCESS")

        inst = self.inst.key.get()

        # self.assertFlashes("<a href='%s'>'%s'</a> saved" % (
        #     self.kibble.url_for(TestModel, 'edit', inst),
        #     inst), "success")

        save_model.assert_called_once_with(mock.ANY, inst, None)
        get_success_response.assert_called_once_with(inst)

        self.assertPreSignalSent(
            self.inst.key, mock.ANY)
        self.assertPostSignalSent(inst.key, inst)

    def test_get_success_response(self):
        view = TestEdit()
        inst = TestModel(id='test', name='test')
        inst.put()
        flask.g.kibble = self.kibble

        trq = (lambda u, **k: self.app.test_request_context(
            "/testmodel/new/"+u, method="POST", **k))

        # Basic success. No list view registered
        with trq(''):
            r1 = view.get_success_response(inst)
            self.assertEqual(r1.status_code, 302)
            self.assertEqual(r1.location, '/')

        # Popup with no __continue value
        with trq('?_popup=1', data={}):
            r2 = view.get_success_response(inst)
            self.assertEqual(r2.status_code, 200)
            self.assertTemplateUsed('kibble/dismiss_popup.html')

        for url_args in ('', '?_popup=1', '?_embed=1'):
            # Save and create another
            with trq(url_args, data={'__continue': 'new'}):
                r3 = view.get_success_response(inst)
                self.assertEqual(r3.status_code, 302)
                self.assertEqual(r3.location, '/testmodel/new/' + url_args)

            # Save and continue editing
            with trq(url_args, data={'__continue': 'edit'}):
                r4 = view.get_success_response(inst)
                self.assertEqual(r4.status_code, 302)
                self.assertEqual(r4.location, '/testmodel-test/' + url_args)

        # Register a list view
        class TestList(kibble.List):
            model = TestModel
        self.kibble.register_view(TestList)
        self.app.add_url_rule('/testmodel/', endpoint='kibble.testmodel_list')

        # Basic success. List view registered
        with trq(''):
            r1 = view.get_success_response(inst)
            self.assertEqual(r1.status_code, 302)
            self.assertEqual(r1.location, '/testmodel/')

        with trq('?_embed=1'):
            r1 = view.get_success_response(inst)
            self.assertEqual(r1.status_code, 302)
            self.assertEqual(r1.location, '/testmodel/?_embed=1')


class FieldsetIteratorTestCase(TestCase):
    def create_app(self):
        return self._create_app(TestCreate, TestEdit)

    def get_iterator(self):
        view = TestEdit()
        form = view.get_form_instance()
        return edit.FieldsetIterator(form, TestEdit.fieldsets)

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

