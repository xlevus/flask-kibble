from google.appengine.ext import ndb

class Contact(ndb.Model):
    name = ndb.StringProperty(required=True)

    home_phone = ndb.StringProperty()
    work_phone = ndb.StringProperty()

    address_1 = ndb.StringProperty()
    address_2 = ndb.StringProperty()
    address_3 = ndb.StringProperty()

    is_a_fish = ndb.BooleanProperty()

