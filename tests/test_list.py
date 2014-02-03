import mock

import flask
from google.appengine.ext import ndb

from .models import TestModel
from .base import TestCase

import flask_ndbcrud as crud
from flask_ndbcrud import list


class TestList(crud.List):
    model = TestModel

    list_display = [
        unicode, 'name', 'static_string',
        'view_member', 'view_member_async',
        'model_member', 'model_member_async',
    ]

    def view_member(self, instance):
        return 'view_member_' + instance.name

    @ndb.tasklet
    def view_member_async(self, instance):
        raise ndb.Return('view_member_async_' + instance.name)

    view_attr = "Test"


class ListTestCase(TestCase):
    def create_app(self):
        return self._create_app(TestList)

    def test_view_name(self):
        self.assertEqual(TestList.view_name(), 'testmodel_list')

    def test_url(self):
        self.assertEqual(flask.url_for('crud.testmodel_list'), '/testmodel/')

    @mock.patch.object(list, 'Table')
    @mock.patch.object(TestList, 'get_query')
    def test_get(self, get_query, Table):
        resp = self.client.get('/testmodel/')
        self.assert200(resp)

        Table.assert_called_once_with(mock.ANY, get_query())

        self.assertTemplateUsed('crud/list.html')
        self.assertContext('table', Table())

    def test_get_missing_perm(self):
        self.authenticator.has_permission_for.return_value = False
        resp = self.client.get('/testmodel/')
        self.assert403(resp)


class ListTableTestCase(TestCase):
    def create_app(self):
        return self._create_app(TestList)

    def get_table(self):
        return list.Table(TestList(), TestModel.query().order(TestModel.name))

    def test_headers(self):
        t = self.get_table()
        self.assertEqual(t.headers, [
            'Unicode', 'Name', 'Static String',
            'View Member', 'View Member Async',
            'Model Member', 'Model Member Async',
        ])

    def test_iter(self):
        i2 = TestModel(name='2').put()
        i1 = TestModel(name='1').put()
        i3 = TestModel(name='3').put()

        t = self.get_table()
        for i, (key, (instance, columns)) in enumerate(zip((i1, i2, i3), t)):
            self.assertEqual(key.get(), instance)

            self.assertEqual(columns, [
                instance.name, instance.name, "static_string",
                'view_member_%s' % instance.name,
                'view_member_async_%s' % instance.name,
                "Model Member %s" % instance.name,
                "Model Member Async %s" % instance.name,
            ])

