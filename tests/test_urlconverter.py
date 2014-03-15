import mock
import flask

from .base import TestCase

from google.appengine.ext import ndb

from flask_kibble.util.url_converter import NDBKeyConverter


class TestModel(ndb.Model):
    value = ndb.StringProperty()


class TestModel2(ndb.Model):
    value = ndb.StringProperty()


class NDBConverterTestCase(TestCase):
    def create_app(self):
        self.mock_view = mock.Mock()
        self.mock_view.required_methods = ()
        self.mock_view.return_value = 'ok'

        app = flask.Flask(__name__)
        app.url_map.converters.setdefault('ndbkey', NDBKeyConverter)

        app.add_url_rule(
            '/t/<ndbkey("TestModel"):key>/',
            methods=['GET'],
            view_func=self.mock_view,
            endpoint='parent')

        app.add_url_rule(
            '/a/<ndbkey("TestModel", "TestModel2"):key>/',
            methods=['GET'],
            view_func=self.mock_view,
            endpoint='ancestor')

        app.add_url_rule(
            '/cs/<ndbkey("TestModel", "TestModel2", separator="-"):key>/',
            methods=['GET'],
            view_func=self.mock_view,
            endpoint='custom_separator')

        app.add_url_rule(
            '/nu/<ndbkey("TestModel", "TestModel2", urlsafe=False):key>/',
            methods=['GET'],
            view_func=self.mock_view,
            endpoint='not_urlsafe')

        return app

    def test_to_url_toplevel(self):
        key1 = TestModel(value='1').put()

        self.assertEqual(
            flask.url_for('parent', key=key1),
            '/t/%s/' % key1.id())

    def test_to_url_ancestors(self):
        key1 = TestModel(value='1').put()
        key2 = TestModel2(value='2', parent=key1).put()
        self.assertEqual(
            flask.url_for('ancestor', key=key2),
            '/a/%s.%s/' % (key1.id(), key2.id()))

    def test_custom_separator(self):
        key1 = TestModel(value='1').put()
        key2 = TestModel2(value='2', parent=key1).put()
        self.assertEqual(
            flask.url_for('custom_separator', key=key2),
            '/cs/%s-%s/' % (key1.id(), key2.id()))

    def test_not_urlsafe(self):
        key1 = TestModel(value='1').put()
        key2 = TestModel2(value='2', parent=key1).put()
        self.assertEqual(
            flask.url_for('not_urlsafe', key=key2),
            '/nu/%s/' % (key2.urlsafe()))

    def test_from_url_toplevel(self):
        key1 = TestModel(value='1').put()
        resp = self.client.get('/t/%s/' % key1.id())

        self.mock_view.assert_called_once_with(key=key1)
        self.assert200(resp)

    def test_from_url_ancestors(self):
        key1 = TestModel(value='1').put()
        key2 = TestModel2(value='2', parent=key1).put()

        resp = self.client.get('/a/%s.%s/' % (key1.id(), key2.id()))

        self.mock_view.assert_called_once_with(key=key2)
        self.assert200(resp)

    def test_from_url_custom_sep(self):
        key1 = TestModel(value='1').put()
        key2 = TestModel2(value='2', parent=key1).put()

        resp = self.client.get('/cs/%s-%s/' % (key1.id(), key2.id()))

        self.mock_view.assert_called_once_with(key=key2)
        self.assert200(resp)

    def test_from_url_noturlsafe(self):
        key1 = TestModel(value='1').put()
        key2 = TestModel2(value='2', parent=key1).put()

        resp = self.client.get('/nu/%s/' % (key2.urlsafe()))

        self.mock_view.assert_called_once_with(key=key2)
        self.assert200(resp)

    def test_from_url_notulrsafe_bad_value(self):
        key1 = TestModel(value='1').put()

        bad_urls = [
            'WRONG',                    # Not base64
            'ZZZZ'.encode('base64'),    # Not Protobuf
            key1.urlsafe(),             # Wrong kinds
        ]

        for url in bad_urls:
            resp = self.client.get('/nu/%s/' % url)
            self.assert404(resp)

