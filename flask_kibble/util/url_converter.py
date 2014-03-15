import logging

from google.appengine.ext import ndb
from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError
from werkzeug.routing import BaseConverter, ValidationError

logger = logging.getLogger(__name__)


class NDBKeyConverter(BaseConverter):
    """
    URLConverter for NDB Key objects.

    :param *kinds: The NDB model kinds to retrieve
    :param urlsafe: If false, use ndb.Key.urlsafe()
    """

    def __init__(self, url_map, *kinds, **kwargs):
        super(NDBKeyConverter, self).__init__(url_map)
        self.kinds = kinds

        self.separator = kwargs.get('separator', '.')
        self.urlsafe = kwargs.get('urlsafe', True)

    def to_url(self, key):
        if self.urlsafe:
            if isinstance(key, ndb.Model):
                key = key.key

            return self.separator.join(unicode(i) for kind, i in key.pairs())
        else:
            return key.urlsafe()

    def _coerce_int(self, value):
        try:
            return int(value)
        except ValueError:
            return value

    def to_python(self, value):
        if self.urlsafe:
            return self.to_python_pairs(value)
        else:
            try:
                key = ndb.Key(urlsafe=value)
                if tuple([p[0] for p in key.pairs()]) != self.kinds:
                    raise TypeError
                return key
            except (TypeError, ProtocolBufferDecodeError):
                raise ValidationError("Invalid URL")

    def to_python_pairs(self, value):
        pairs = zip(
            self.kinds,
            map(self._coerce_int, value.split(self.separator)))

        print pairs

        key = ndb.Key(pairs=pairs)

        logger.debug("Key: %r", key)

        return key

