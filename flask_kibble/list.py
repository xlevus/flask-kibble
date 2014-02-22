import flask
from werkzeug.utils import cached_property

from google.appengine.ext import ndb

from .base import KibbleView
from . import query_composers


class Table(object):
    def __init__(self, kibble_view, query, query_params):
        self.kibble_view = kibble_view

        self._rows = query.map_async(self._map, **query_params)

    @property
    def row_count(self):
        return len(self._rows.get_result())

    @cached_property
    def headers(self):
        headers = []
        for attr_name in self.kibble_view.list_display:
            if callable(attr_name):
                attr_name = attr_name.__name__
            headers.append(attr_name.replace("_", " ").strip().title())
        return headers

    @ndb.tasklet
    def _map(self, instance):
        retval = []

        for attr_name in self.kibble_view.list_display:
            if callable(attr_name):
                attr = attr_name
                args = (instance,)

            elif hasattr(instance, attr_name):
                attr = getattr(instance, attr_name)
                args = ()

            elif hasattr(self.kibble_view, attr_name):
                attr = getattr(self.kibble_view, attr_name)
                args = (instance,)

            elif callable(attr_name):
                attr = attr_name
                args = (instance,)

            else:
                attr = attr_name
                args = ()

            if callable(attr):
                attr = attr(*args)

            if isinstance(attr, ndb.Future):
                attr = yield attr

            retval.append(attr)
        raise ndb.Return((instance, retval))

    def __iter__(self):
        for row in self._rows.get_result():
            yield row


class List(KibbleView):
    action = 'list'

    #: Columns to display in the list table. Can be one of:
    #:  * callable: Will be called with the instance as the first argument
    #:  * model member: If callable, will be called
    #:  * view member: If callable, will be called with instance as first
    #:    argument.
    list_display = (unicode,)

    #: Link to the object in the first column.
    link_first = True

    #: Number of results to display per page.
    page_size = 20

    #: A list of query composers to perform query operations
    #: e.g. Filtering, sorting, pagination. See :mod:`~flask_kibble.query_composers`
    query_composers = [
        query_composers.Paginator
    ]

    button_icon = 'list'

    _url_patterns = [
        ("/{kind_lower}/", {'page': 1}),
        ("/{kind_lower}/page-<int:page>/", {}),
    ]
    _requires_instance = False

    def get_query(self):
        """
        Returns the base query to display on the list.

        :returns: ``ndb.Query``
        """
        return self.model.query()

    def dispatch_request(self, page):
        context = self.base_context()

        query = self.get_query()
        query_params = {}

        for composer_cls in self.query_composers:
            composer = composer_cls(self, query)
            context[composer.context_var] = composer

            query = composer.get_query()
            query_params.update(composer.get_query_params())

        context['table'] = Table(self, query, query_params)

        return flask.render_template(self.templates, **context)

