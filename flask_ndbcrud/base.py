import flask
from flask.views import View


class CrudView(View):
    action = None
    model = None

    _methods = ['GET']
    _url_patterns = [("/{kind_lower}/{action}/", {})]
    _requires_instance = True

    @classmethod
    def kind(cls):
        return cls.model._get_kind()

    @classmethod
    def view_name(cls):
        return "%s_%s" % (cls.kind().lower(), cls.action)

    @property
    def templates(self):
        return [
            'crud/%s.html' % self.action,
            'crud/%s_%s.html' % (self.kind().lower(), self.action)
        ]

    def base_context(self):
        return {
            'view': self,
        }

    @classmethod
    def has_permission_for(cls, key=None, instance=None):
        """
        Check if the user has the permissions required for this view.

        :param key: A ndb.Key instance to link to (optional)
        :param instance: A ndb.Model instance to link to (optional)
        """
        if instance:
            key = instance.key

        return flask.g.crud.auth.has_permission_for(
            cls.model,
            cls.action,
            key=key)

    @classmethod
    def url_for(cls, blueprint='', key=None, instance=None):
        """
        Get the URL for this view.

        :param blueprint: The blueprint name the view is registered to. If not
            provided, the current requests blueprint will be used. (optional)
        :param key: A ndb.Key instance to link to (optional)
        :param instance: A ndb.Model instance to link to (optional)
        """
        if instance:
            key = instance.key
        return flask.url_for('%s.%s' % (blueprint, cls.view_name()), key=key)

