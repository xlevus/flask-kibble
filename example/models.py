from google.appengine.ext import ndb

class Contact(ndb.Model):
    name = ndb.StringProperty()

