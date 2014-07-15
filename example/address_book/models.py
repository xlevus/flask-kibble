from google.appengine.ext import ndb


class PhoneNumber(ndb.Model):
    type = ndb.StringProperty(choices=['home', 'work', 'other'])
    number = ndb.StringProperty()


class Contact(ndb.Model):
    name = ndb.StringProperty(required=True)
    birthday = ndb.DateProperty(required=False)

    notes = ndb.TextProperty(required=False)

    phone = ndb.StructuredProperty(PhoneNumber, repeated=True)

    def __unicode__(self):
        return self.name


class Address(ndb.Model):
    """
    Ancestors of Contact
    """
    line_1 = ndb.StringProperty()
    line_2 = ndb.StringProperty()

    city = ndb.StringProperty()
    country = ndb.StringProperty()
    zip = ndb.StringProperty()

