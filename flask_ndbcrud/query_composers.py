
class QueryComposer(object):
    context_var = None

    def __init__(self, crud_view, query):
        self.crud_view = crud_view
        self._query = query

    def get_query(self):
        return self._query.filter()

    def get_query_params(self):
        return {}


class Paginator(QueryComposer):
    context_var = 'paginator'



