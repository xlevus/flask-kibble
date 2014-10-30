import flask
from markupsafe import Markup
# from werkzeug.utils import cached_property

from google.appengine.ext import ndb


class BaseFilter(object):
    """
    Base filter class.

    :param str field: Field column to filter on. If filtering on
        :py:class:`google.appengine.ext.ndb.StructuredProperty`, nested models
        can be specified with ``.``.
    :param str title: Column title, if ``None`` will be created based on field
        name.
    """
    def __init__(self, field, title=None):
        self.field = field
        self.title = title or field.replace('_', ' ').title()

    def preload(self):
        """
        Called when the view is first called. Used to pre-load any queries
        asynchronously.
        """

    def value_to_url(self, value):
        """
        Generate a url-safe value for the given pythonic value.

        :param value: Pythonic type for the given filter value.
        """
        return value

    def value_from_url(self, url_value):
        """
        Convert a url-safe value from the URL to a pythonic value.

        :param url_value: URLsafe representation of pythonic filter value.
        """

    def url_for_value(self, value):
        """
        Generate a URL for the given pythonc python value.

        :param value: Pythonic value to filter on.
        :returns: URL with filter parameters.
        """
        args = flask.request.view_args.copy()
        args.update(flask.request.args)
        args[self.field] = self.value_to_url(value)
        return flask.url_for(flask.request.endpoint, **args)

    def model_property(self, model):
        """
        Get the :py:class:`google.appengine.ext.ndb.Property` for the given
        ``model``.

        :param model: The :py:class:`google.appengine.ext.ndb.Model` to
            retrieve the property from.
        """
        path = self.field.split('.')
        prop = model
        while path:
            prop = getattr(prop, path.pop(0))
        return prop

    def filter(self, model, query):
        """
        Perform the filter on the query.

        :param model: The model class to filter.
        :param query:
        """
        val = self.get_value()
        if val:
            prop = getattr(model, self.field)
            return query.filter(prop == val)
        return query

    def get_value(self, default=None):
        return flask.request.args.get(self.field, default)

    def render(self):
        return ''


class ChoicesFilter(BaseFilter):
    def __init__(self, field, choices):
        super(ChoicesFilter, self).__init__(field)
        self.choices = choices

    def _render_choice(self, value, label):
        return Markup("<li  class='{klass}'><a href='{url}'>{label}</a></li>")\
            .format(
                klass='active' if value == self.get_value() else '',
                url=self.url_for_value(value),
                label=label)

    def render(self):
        choices = [self._render_choice(None, 'All')] + [
            self._render_choice(*c) for c in self.choices
        ]
        return Markup("<ul class='{}'>{}</ul>")\
            .format(
                'list-unstyled',
                Markup("").join(choices))


class BoolFilter(ChoicesFilter):
    def __init__(self, field):
        BaseFilter.__init__(self, field)

    @property
    def choices(self):
        return [('t', 'True'), ('f', 'False')]

    def filter(self, model, query):
        val = {
            't': True,
            'f': False,
        }.get(self.get_value())

        if isinstance(val, bool):
            prop = getattr(model, self.field)
            return query.filter(prop == val)
        return query


class KeyFilter(ChoicesFilter):
    def __init__(self, field, query):
        BaseFilter.__init__(self, field)
        if isinstance(query, type) and issubclass(query, ndb.Model):
            query = query.query()
        self.query = query

    def _make_key(self, key):
        return key.urlsafe()

    @property
    def choices(self):
        qit = self.query.iter()
        while qit.has_next():
            row = qit.next()
            yield (self._make_key(row.key), unicode(row))

    def filter(self, model, query):
        val = self.get_value()
        if val:
            val = ndb.Key(urlsafe=self.get_value())
            query = query.filter(
                getattr(model, self.field) == val)
        return query



