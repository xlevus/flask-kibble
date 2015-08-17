from flask.signals import Namespace

namespace = Namespace()

pre_action = namespace.signal('pre-action')
post_action = namespace.signal('post-action')

