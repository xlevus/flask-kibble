from werkzeug.utils  import cached_property
import flask

from google.appengine.ext import ndb

from .base import CrudView


class Table(object):
    def __init__(self, crud_view, query):
        self.crud_view = crud_view

        self._rows = query.map_async(self._map)

    @cached_property
    def headers(self):
        headers = []
        for attr_name in self.crud_view.list_display:
            headers.append(attr_name.replace("_", " ").strip().title())
        return headers

    @ndb.tasklet
    def _map(self, instance):
        retval = []

        for attr_name in self.crud_view.list_display:
            if hasattr(instance, attr_name):
                attr = getattr(instance, attr_name)
                args = ()

            elif hasattr(self.crud_view, attr_name):
                attr = getattr(self.crud_view, attr_name)
                args = (instance,)

            elif callable(attr_name):
                attr = attr_name
                args = (instance,)

            if callable(attr):
                future = attr(*args)

            if isinstance(future, ndb.Future):
                future = yield future

            retval.append(future)

            raise ndb.Return((instance, retval))

    def __iter__(self):
        for row in self._rows.get_result():
            yield row



class List(CrudView):
    action = 'list'

    list_display = ('__unicode__',)

    _url_patterns = [("/{kind}/", {})]
    _requires_instance = False

    def get_query(self):
        return self.model.query()

    def dispatch_request(self):
        context = self.base_context()

        context['table'] = Table(self, self.get_query())

        return flask.render_template(self.templates, **context)

