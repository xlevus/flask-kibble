from google.appengine.ext import ndb


class TestModel(ndb.Model):
    name = ndb.StringProperty(required=True)

    def model_member(self):
        return "Model Member %s" % self.name

    @ndb.tasklet
    def model_member_async(self):
        raise ndb.Return("Model Member Async %s" % self.name)

    def __unicode__(self):
        return self.name

