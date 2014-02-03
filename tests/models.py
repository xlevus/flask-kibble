from google.appengine.ext import ndb


class TestModel(ndb.Model):
    name = ndb.StringProperty(required=True)

