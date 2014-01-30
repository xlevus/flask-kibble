from google.appengine.ext import ndb
from werkzeug.routing import BaseConverter, ValidationError

class NDBKeyConverter(BaseConverter):
    def __init__(self, url_map, kind):
        super(NDBKeyConverter, self).__init__(url_map)
        self.kind = kind

    def to_url(self, key):
        if isinstance(key, ndb.Model):
            key = key.key()

        if key.parent():
            return 'u-'+key.urlsafe()
        else:
            return 'i-'+unicode(key.id())

    def to_python(self, value):
        if value.startswith('u-'):
            key = ndb.Key(urlsafe=value[2:])
            if key.kind() != self.kind:
                raise ValidationError()
        else:
            value = value[2:]
            try:
                value = int(value)
            except ValueError:
                pass
            key = ndb.Key(self.kind, value[2:])

        return key

