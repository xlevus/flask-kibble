from google.appengine.ext import ndb


@ndb.tasklet
def instance_and_ancestors_async(key):
    """
    Retrieve the instance for ``key`` and all it's ancestors.

    :param key: :py:class:`google.appengine.ext.ndb.Key` to retrieve.
    :returns: Array of :py:class:`google.appengine.ext.ndb.Model` instances
        with the topmost ancestor first, and the instance last.
    """
    futures = []
    while key:
        futures.append(key.get_async())
        key = key.parent()
    objs = yield futures
    raise ndb.Return(objs[::-1])


def instance_and_ancestors(key):
    return instance_and_ancestors_async(key).get_result()


