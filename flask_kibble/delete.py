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
        futures = []
        futures.append(key.delete_async())

        qit = ndb.Query(ancestor=key).iter(keys_only=True)
        while (yield qit.has_next_async()):
            k = qit.next()
            futures.append(self._delete(k))

        yield futures
        raise ndb.Return(None)
