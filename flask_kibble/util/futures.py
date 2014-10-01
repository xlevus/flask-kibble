from google.appengine.ext import ndb


@ndb.tasklet
def _make_future(val):
    """
    If it's not a future, turn it into one.
    """
    raise ndb.Return(val)


@ndb.tasklet
def wait_futures(values):
    """
    Convert values that may or may not contain futures to values.
    """
    to_wait = []

    for v in values:
        if hasattr(v, 'get_result'):
            to_wait.append(v)
        else:
            to_wait.append(_make_future(v))

    values = yield to_wait

    raise ndb.Return(values)

