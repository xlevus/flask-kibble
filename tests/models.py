from google.appengine.ext import ndb


class InnerModel(ndb.Model):
    value = ndb.StringProperty()

class TestModel(ndb.Model):
    name = ndb.StringProperty(required=True)

    other_field_1 = ndb.StringProperty(default='other1')
    other_field_2 = ndb.StringProperty(default='other2')
    other_field_3 = ndb.StringProperty(default='other3')

    def model_member(self):
        return "Model Member %s" % self.name

    @ndb.tasklet
    def model_member_async(self):
        raise ndb.Return("Model Member Async %s" % self.name)

    def __unicode__(self):
        return self.name


class ComplexTestModel(TestModel):
    inner = ndb.StructuredProperty(InnerModel, required=False)
