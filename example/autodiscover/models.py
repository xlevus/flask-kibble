from google.appengine.ext import ndb


class AutodiscoverTestModel(ndb.Model):
    name = ndb.StringProperty()

