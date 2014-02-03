import logging

from google.appengine.ext import ndb
from werkzeug.routing import BaseConverter, ValidationError

logger = logging.getLogger(__name__)


class NDBKeyConverter(BaseConverter):
    def __init__(self, url_map, kind):
        super(NDBKeyConverter, self).__init__(url_map)
        self.kind = kind

    def to_url(self, key):
        if isinstance(key, ndb.Model):
            key = key.key

        if key.parent():
            return 'u-' + key.urlsafe()
        else:
            return 'i-' + unicode(key.id())

    def to_python(self, value):
        if value.startswith('u-'):
            key = ndb.Key(urlsafe=value[2:])
            if key.kind() != self.kind:
                logger.debug("Key %r does not match kind" % value)
                raise ValidationError()
        else:
            value = value[2:]
            try:
                value = int(value)
            except ValueError:
                logger.debug("Key %r not an integer", value)
                pass
            key = ndb.Key(self.kind, value)

        logger.debug("Key: %r", key)

        return key

