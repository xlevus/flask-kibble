import flask


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

    PAGE_ARG = 'page'

    def __init__(self, *args, **kwargs):
        super(Paginator, self).__init__(*args, **kwargs)

        self._total_objects = self.crud_view.get_query().count_async()

    def get_query_params(self):
        return {
            'limit': self.per_page,
            'offset':  self.per_page * (self.page_number - 1),
        }

    @property
    def per_page(self):
        return min(self.crud_view.page_size, 50)

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

