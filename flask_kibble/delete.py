from google.appengine.ext import ndb

from .operation import Operation


class Delete(Operation):
    action = 'delete'
    past_tense = 'deleted'

    button_icon = 'trash'
    button_class = 'btn-danger'

    #: Delete the object and its descendants recursively?
    recursive = False

    def run(self, instance, form):
        if self.recursive:
            self._delete(instance.key).get_result()
        else:
            instance.key.delete()
        return True

    @ndb.tasklet
    def _delete(self, key):
        descendents = yield ndb.Query(ancestor=key).fetch_async(keys_only=True)

        yield [x.delete_async() for x in descendents]

        raise ndb.Return(None)
