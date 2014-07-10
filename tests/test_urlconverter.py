import mock
import flask

from .base import TestCase

from google.appengine.ext import ndb

from flask_kibble.util.url_converter import NDBKeyConverter


class UrlTestModel(ndb.Model):
    value = ndb.StringProperty()


class UrlTestModel2(ndb.Model):
    value = ndb.StringProperty()


class NDBConverterTestCase(TestCase):
    def create_app(self):
        self.mock_view = mock.Mock()
        self.mock_view.required_methods = ()
        self.mock_view.return_value = 'ok'

        app = flask.Flask(__name__)
        app.url_map.converters.setdefault('ndbkey', NDBKeyConverter)

        app.add_url_rule(
            '/t/<ndbkey("UrlTestModel"):key>/',
            methods=['GET'],
            view_func=self.mock_view,
            endpoint='parent')

        app.add_url_rule(
            '/t/<ndbkey("UrlTestModel2"):key>/',
            methods=['GET'],
            view_func=self.mock_view,
            endpoint='parent')

        app.add_url_rule(
            '/a/<ndbkey("UrlTestModel", "UrlTestModel2"):key>/',
            methods=['GET'],
            view_func=self.mock_view,
            endpoint='ancestor')

        app.add_url_rule(
            '/cs/<ndbkey("UrlTestModel", "UrlTestModel2", separator="-"):key>/',
            methods=['GET'],
            view_func=self.mock_view,
            endpoint='custom_separator')

        app.add_url_rule(
            '/nu/<ndbkey("UrlTestModel", "UrlTestModel2", urlsafe=False):key>/',
            methods=['GET'],
            view_func=self.mock_view,
            endpoint='not_urlsafe')

        return app

    def test_to_url_toplevel(self):
        """
        Test url-component for top level entities looks like::

            /<kind>-<id>/
        """
        key1 = UrlTestModel(value='1').put()

        self.assertEqual(
            flask.url_for('parent', key=key1),
            '/t/urltestmodel-%s/' % key1.id())

    def test_to_url_ancestors(self):
        """
        Test urls for ancestor entities look like::

            /<ancestor.kind>-<ancestor-id>.<child.kind>-<child-id>/
        """
        key1 = UrlTestModel(value='1', id=902430982).put()
        key2 = UrlTestModel2(value='2', id=209824, parent=key1).put()
        self.assertEqual(
            flask.url_for('ancestor', key=key2),
            '/a/urltestmodel-%s/urltestmodel2-%s/' % (key1.id(), key2.id()))

    def test_not_urlsafe(self):
        """
        Test urls for keys with non-urlsafe IDs look like::

            /<key.urlsafe()>/
        """
        key1 = UrlTestModel(value='1').put()
        key2 = UrlTestModel2(value='2', parent=key1).put()
        self.assertEqual(
            flask.url_for('not_urlsafe', key=key2),
            '/nu/%s/' % (key2.urlsafe()))

    def test_from_url_toplevel(self):
        """
        Test top-level urls route to the correct view w/ correct arguments.
        """
        key1 = UrlTestModel(value='1').put()
        resp = self.client.get('/t/urltestmodel-%s/' % key1.id())
        self.mock_view.assert_called_once_with(key=key1)
        self.mock_view.reset_mock()

        key2 = UrlTestModel2(value='2', id=102342).put()
        resp = self.client.get('/t/urltestmodel2-%s/' % key2.id())
        self.mock_view.assert_called_once_with(key=key2)

        self.assert200(resp)

    def test_from_url_ancestors(self):
        """
        Test ancestor-urls route to the correct view w/ correct arguments.
        """
        key1 = UrlTestModel(value='1', id=2342265).put()
        key2 = UrlTestModel2(value='2', id=2342542, parent=key1).put()

        resp = self.client.get('/a/urltestmodel-%s/urltestmodel2-%s/' % (key1.id(), key2.id()))

        self.mock_view.assert_called_once_with(key=key2)
        self.assert200(resp)

    def test_from_url_noturlsafe(self):
        """
        Test non-urlsafe keys route to the correct view w/ correct arguments.
        """
        key1 = UrlTestModel(value='1').put()
        key2 = UrlTestModel2(value='2', parent=key1).put()

        resp = self.client.get('/nu/%s/' % (key2.urlsafe()))

        self.mock_view.assert_called_once_with(key=key2)
        self.assert200(resp)

    def test_from_url_notulrsafe_bad_value(self):
        """
        Test badly formed arguments for non-urlsafe keys result in 404s.
        """
        key1 = UrlTestModel(value='1').put()

        bad_urls = [
            'WRONG',                    # Not base64
            'ZZZZ'.encode('base64'),    # Not Protobuf
            key1.urlsafe(),             # Wrong kinds
        ]

        for url in bad_urls:
            resp = self.client.get('/nu/%s/' % url)
            self.assert404(resp)

