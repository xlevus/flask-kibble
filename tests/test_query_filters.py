import flask
import mock

from google.appengine.ext import ndb

from .base import TestCase
from .models import TestModel

from flask_kibble import query_filters as qf


class QueryComposerTestCase(TestCase):
    klass = qf.BaseFilter

    def create_app(self):
        return flask.Flask(__name__)

    def create_filter(self, *args, **kwargs):
        return self.klass(kwargs.pop('field', 'field'), *args, **kwargs)

    def get_value(self):
        return "Value"

    def test_to_url(self):
        v = self.get_value()
        f = self.create_filter()

        url = f.value_to_url(v)
        v2 = f.url_to_value(url)

        self.assertEqual(v, v2)

    def test_get(self):
        f = self.create_filter()

        with mock.patch.object(f, 'url_to_value') as m:
            with self.app.test_request_context('/?field=foobar'):
                val = f.get()
                m.assert_called_once_with('foobar')
                self.assertEqual(val, m())

        # Test type coercion
        f2 = self.create_filter(type=int)
        with self.app.test_request_context('/?field=123'):
            val = f2.get()
            self.assertEqual(val, 123)

    def test_model_property(self):
        # Check ID as you can't do an equality operator on fields
        f1 = self.create_filter(field='name')
        self.assertEqual(id(f1.model_property(TestModel)), id(TestModel.name))

        f2 = self.create_filter(field='inner.value')
        self.assertEqual(
            id(f2.model_property(TestModel)),
            id(TestModel.inner.value))

    def test_filter(self):
        query = mock.Mock(spec=ndb.Query)

        f1 = self.create_filter(field='name')

        with self.app.test_request_context('/?name=123'):
            q2 = f1.filter(TestModel, query)
            query.filter.assert_called_once_with(TestModel.name == '123')

            self.assertEqual(q2, query.filter())

