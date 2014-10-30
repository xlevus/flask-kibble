import flask
import mock

from .base import TestCase

from flask_kibble import query_composers as qc


class QueryComposerTestCase(TestCase):
    def create_app(self):
        return flask.Flask(__name__)

    def test_creation(self):
        unbound = qc.QueryComposer()
        self.assertIsInstance(unbound, qc.UnboundComposer)

        c = unbound(
            mock.sentinel.KIBBLE_VIEW,
            mock.sentinel.QUERY)

        self.assertIsInstance(c, qc.QueryComposer)
        self.assertEqual(c.kibble_view, mock.sentinel.KIBBLE_VIEW)
        self.assertEqual(c.query, mock.sentinel.QUERY)

    def test_creation_noargs(self):
        composer = qc.QueryComposer(
            _kibble_view=mock.sentinel.KIBBLE_VIEW,
            _query=mock.sentinel.QUERY)

        self.assertIsInstance(composer, qc.QueryComposer)
        self.assertEqual(composer.kibble_view, mock.sentinel.KIBBLE_VIEW)
        self.assertEqual(composer.query, mock.sentinel.QUERY)


class TestPaginator(TestCase):
    def create_app(self):
        return flask.Flask(__name__)

