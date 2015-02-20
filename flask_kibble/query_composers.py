import sys
import flask
import wtforms
from werkzeug import cached_property
from markupsafe import Markup

from google.appengine.ext import ndb


class UnboundComposer(object):
    """
    Class to hold constructor arguments in while outside of a request.
    """
    def __init__(self, composer_cls, *args, **kwargs):
        self._cls = composer_cls
        self._args = args
        self._kwargs = kwargs

    def __call__(self, kibble_view, query):
        kw = dict(_kibble_view=kibble_view, _query=query, **self._kwargs)
        return self._cls(*self._args, **kw)


class QueryComposer(object):
    context_var = None

    def __new__(cls, *args, **kwargs):
        if '_kibble_view' in kwargs and '_query' in kwargs:
            return super(QueryComposer, cls).__new__(cls)
        else:
            return UnboundComposer(cls, *args, **kwargs)

    def __init__(self, _kibble_view=None, _query=None):
        self.kibble_view = _kibble_view
        self.query = _query

    def get_query(self):
        return self.query.filter()

    def get_query_params(self):
        return {}

    def __getattr__(self, attr):
        return getattr(
            self.kibble_view,
            self.context_var + '_' + attr)


class Paginator(QueryComposer):
    """
    Paginates the query into smaller chunks.
    """
    context_var = 'paginator'

    PAGE_ARG = 'page'
    PERPAGE_ARG = 'page-size'
    DEFAULT_PAGE_SIZE = 20

    def __init__(self, *args, **kwargs):
        super(Paginator, self).__init__(*args, **kwargs)

        self._total_objects = self.query.count_async()

    def get_query_params(self):
        return {
            'limit': self.per_page,
            'offset':  self.per_page * (self.page_number - 1),
        }

    @cached_property
    def per_page(self):
        page_size = getattr(self, 'page_size', self.DEFAULT_PAGE_SIZE)

        if self.PERPAGE_ARG in flask.request.args:
            try:
                page_size = int(flask.request.args[self.PERPAGE_ARG])
            except ValueError:
                pass

        return min(
            page_size,
            getattr(self, "max_page_size", sys.maxint))

    @property
    def total_objects(self):
        return self._total_objects.get_result()

    @property
    def page_number(self):
        try:
            p = flask.request.view_args.get(self.PAGE_ARG)
            return p or int(flask.request.args.get(self.PAGE_ARG, '1'))
        except ValueError:
            return 1

    @property
    def pages(self):
        from math import ceil
        return int(ceil(self.total_objects / float(self.per_page)))

    def iter_page_numbers(self, left_edge=2, left_current=2,
                          right_current=5, right_edge=2):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page_number - left_current - 1
                and
                num < self.page_number + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

    def url_for_page(self, number):
        args = flask.request.view_args.copy()
        args.update(flask.request.args)

        args[self.PAGE_ARG] = number
        return flask.url_for(flask.request.endpoint, **args)

    @property
    def has_next(self):
        return self.page_number < self.pages

    @property
    def has_prev(self):
        return self.page_number > 1

    @property
    def prev(self):
        return self.page_number - 1

    @property
    def next(self):
        return self.page_number + 1


class Filter(QueryComposer):
    """
    Filter on column values.
    """
    context_var = 'filter'

    def __init__(self, *filters, **kwargs):
        super(Filter, self).__init__(**kwargs)

        if filters:
            self.filters = filters

        for f in self:
            f.preload()

    def __nonzero__(self):
        return bool(self._filters)

    def __iter__(self):
        return iter(self._filters)

    @property
    def _filters(self):
        return getattr(self, 'filters', [])

    def get_query(self):
        q = self.query
        for f in self:
            q = f.filter(self.kibble_view.model, q)
        return q


class Sort(QueryComposer):
    context_var = 'sort'

    def __init__(self, default_order=None, **kwargs):
        super(Sort, self).__init__(**kwargs)

        if default_order:
            self.default_order = default_order

    def _parse_sort(self, sort_string):
        if sort_string[0] == '-':
            return -ndb.GenericProperty(sort_string[1:])
        else:
            return ndb.GenericProperty(sort_string)

    def get_query(self):
        q = self.query
        if getattr(self, 'default_order', None):
            q = q.order(self._parse_sort(self.default_order))
        return q

