import flask
from werkzeug.utils import cached_property

from google.appengine.ext import ndb
from google.appengine.api.datastore_errors import NeedIndexError

from .base import KibbleView
from . import query_composers
from .util.futures import wait_futures
from .util.ndb import instance_and_ancestors_async


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

            retval.append(attr)

        retval = yield wait_futures(retval)

        raise ndb.Return((instance, retval))

    def __iter__(self):
        for row in self._rows.get_result():
            yield row


class MissingIndexTable(Table):
    def __init__(self, kibble_view, query, query_params):
        self.kibble_view = kibble_view

    @property
    def row_count(self):
        return 0

    def __iter__(self):
        raise StopIteration()


class List(KibbleView):
    #: Action name
    action = 'list'

    #: Columns to display in the list table. Can be one of:
    #:  * *callable*: Will be called with the instance as the first argument
    #:  * model member: If callable, will be called
    #:  * view member: If callable, will be called with instance as first
    #:    argument.
    list_display = (unicode,)

    #: Link to the object in the first column.
    link_first = True

    #: A list of query composers to perform query operations
    #: e.g. Filtering, sorting, pagination. See
    #: :mod:`~flask_kibble.query_composers` for more information.
    query_composers = [
        query_composers.Filter,
        query_composers.Paginator,
    ]

    button_icon = 'list'

    _url_patterns = [
        ("/{kind_lower}/", {'page': 1, 'ancestor_key': None}),
        ("/{kind_lower}/page-<int:page>/", {'ancestor_key': None}),
        ("/{ancestor_key}/{kind_lower}/", {'page': 1}),
        ("/{ancestor_key}/{kind_lower}/page-<int:page>/", {}),
    ]
    _requires_instance = False

    def get_query(self, ancestor_key=None):
        """
        :returns: Base query for list.
        :rtype: :py:class:`ndb.Query`
        """
        return self.model.query(ancestor=ancestor_key)

    def _get_context(self, page, ancestor_key):
        context = self.base_context()
        if ancestor_key:
            ancestors = instance_and_ancestors_async(ancestor_key)
        else:
            ancestors = None
            ancestor = None

        query = self.get_query(ancestor_key)
        query_params = {}

        for composer_cls in self.query_composers:
            composer = composer_cls(
                _kibble_view=self,
                _query=query)
            context[composer.context_var] = composer

            query = composer.get_query()
            query_params.update(composer.get_query_params())

        context['table'] = Table(self, query, query_params)
        context['ancestor_key'] = ancestor_key
        context['ancestors'] = ancestors.get_result() if ancestors else None
        return context

    def dispatch_request(self, page, ancestor_key):
        context = self._get_context(page, ancestor_key)
        try:
            return flask.render_template(self.templates, **context)

        except NeedIndexError:
            # We've tried to generate a query that isn't handled by the
            # application. Render the page with no filters and such, allowing
            # the user to adjust their queries.
            context['_extends'] = "kibble/list.html"
            context['table'] = MissingIndexTable(self, None, None)
            context['paginator'] = None
            return flask.render_template(
                'kibble/list.need_index.html',
                **context)

