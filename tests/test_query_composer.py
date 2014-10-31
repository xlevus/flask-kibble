import flask
import mock
from flask_kibble.base import KibbleView

from google.appengine.ext import ndb

from .base import TestCase

from flask_kibble import query_composers as qc


class QueryComposerTestCase(TestCase):
    klass = qc.QueryComposer

    def create_app(self):
        return flask.Flask(__name__)

    def create_composer(self, view, query, *args, **kwargs):
        kwargs['_kibble_view'] = view
        kwargs['_query'] = query
        return self.klass(*args, **kwargs)

    def create_query(self, count=111):
        q = mock.Mock(spec=ndb.Query)
        q.count_async.return_value = self.create_mock_future(count)
        q.count.return_value = count
        return q

    def create_view(self):
        return mock.Mock(spec=KibbleView)

    def test_creation(self):
        unbound = self.klass()
        self.assertIsInstance(unbound, qc.UnboundComposer)

        v = self.create_view()
        q = self.create_query()

        c = unbound(v, q)

        self.assertIsInstance(c, self.klass)
        self.assertEqual(c.kibble_view, v)
        self.assertEqual(c.query, q)

    def test_creation_noargs(self):
        v = self.create_view()
        q = self.create_query()

        composer = self.klass(
            _kibble_view=v,
            _query=q)

        self.assertIsInstance(composer, self.klass)
        self.assertEqual(composer.kibble_view, v)
        self.assertEqual(composer.query, q)


class TestPaginator(QueryComposerTestCase):
    klass = qc.Paginator

    def create_app(self):
        app = flask.Flask(__name__)

        @app.route('/', defaults={'page': None})
        @app.route('/<int:page>')
        def index(page):
            return str(page)

        @app.route('/abcd/')
        def abcd():
            return "abcd"

        return app

    def test_per_page(self):
        view = self.create_view()
        query = self.create_query()

        # Default
        p1 = self.create_composer(view, query)
        self.assertEqual(p1.per_page, 20)

        # paginator_page_size set on view
        view.paginator_page_size = 201
        p2 = self.create_composer(view, query)
        self.assertEqual(p2.per_page, 201)

        # When page-size is passed in through URL args
        with self.app.test_request_context('/?page-size=329'):
            p3 = self.create_composer(view, query)
            self.assertEqual(p3.per_page, 329)

            # When view has max page size specified
            view.paginator_max_page_size = 2
            p4 = self.create_composer(view, query)
            self.assertEqual(p4.per_page, 2)

    def test_total_objects(self):
        """
        Check total_objects returns the count of the query
        """
        view = self.create_view()
        query = self.create_query()

        p1 = self.create_composer(view, query)
        self.assertEqual(p1.total_objects, 111)

    def test_page_number(self):
        view = self.create_view()
        query = self.create_query()

        # Page number from view args
        with self.app.test_request_context('/123'):
            p1 = self.create_composer(view, query)
            self.assertEqual(p1.page_number, 123)

        # Page number from request.args
        with self.app.test_request_context('/?page=112'):
            p2 = self.create_composer(view, query)
            self.assertEqual(p2.page_number, 112)

    def test_pages(self):
        view = self.create_view()
        query = self.create_query()

        p1 = self.create_composer(view, query)
        self.assertEqual(p1.pages, 6)

        with self.app.test_request_context('/?page-size=1'):
            p2 = self.create_composer(view, query)
            self.assertEqual(p2.pages, 111)

    def test_url_for_page(self):
        view = self.create_view()
        query = self.create_query()

        # Check that when there is a <page> param in the url args update that
        # andd preserve GET values
        with self.app.test_request_context('/?foo=bar&baz=bong'):
            p1 = self.create_composer(view, query)
            self.assertEqual(p1.url_for_page(12), '/12?foo=bar&baz=bong')

        # Check that when there is no <page> param in the url args, update GET
        # and preserve the existing values in there
        with self.app.test_request_context('/abcd/?foo=bar&baz=bong'):
            p2 = self.create_composer(view, query)
            self.assertEqual(
                p2.url_for_page(2),
                '/abcd/?foo=bar&baz=bong&page=2')

    def test_get_query_params(self):
        self.fail("Not tested")


class FilterTestCase(QueryComposerTestCase):
    klass = qc.Filter

