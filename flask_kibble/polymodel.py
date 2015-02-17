"""
Basic PolyModel support for Kibble.

As Poly classes all have the same Kind, things don't entirely work.

In order to use PolyModels you need to do two things :

    1. Subclass `kibble.polymodel.Create` and `kibble.polymodel.Edit` views
       for each subclass of PolyModel you want to create/edit.

    2. Create a `kibble.polymodel.PolymodelList`,
       `kibble.polymodel.PolymodelCreate` and `kibble.polymodel.PolymodelEdit`
       views for the 'root' class you want.

The views for the parent classes dispatch requests to the subclass views based
on the kind of the instance, or requested url parameter.

Notes:
    * Permissions are /probably/ all tied around Polymodel, not the actual
      classes
    * You'll probably get some funky shit WRT to ancestors.
"""

import flask
import logging
import blinker
from collections import defaultdict
#from google.appengine.ext import ndb
from google.appengine.ext.ndb import polymodel

from . import base as base_base
from . import edit as base_edit
from . import list as base_list

logger = logging.getLogger(__name__)


class PolymodelMeta(base_base.KibbleMeta):
    """
    Custom metaclass to store a map of `_class_key()` to
    dispatch requests to the right type.
    """
    cls_map = defaultdict(dict)

    def __new__(mcls, name, bases, attrs):
        cls = super(base_base.KibbleMeta, mcls)\
            .__new__(mcls, name, bases, attrs)

        if not getattr(cls, 'model', None) or \
                not issubclass(cls.model, polymodel.PolyModel):
            return cls

        if blinker and cls.model:
            cls.pre_signal = blinker.signal("{}-pre-{}".format(
                cls.kind(), cls.action))

            cls.post_signal = blinker.signal("{}-post-{}".format(
                cls.kind(), cls.action))
        else:
            cls.pre_signal = base_base.StubSignal()
            cls.post_signal = base_base.StubSignal()

        mcls.cls_map[tuple(cls.model._class_key())][cls.action] = cls

        return cls


class PolymodelMixin(object):
    __metaclass__ = PolymodelMeta


class Create(PolymodelMixin, base_edit.Create):
    pass


class Edit(PolymodelMixin, base_edit.Edit):
    pass



def _dispatch_polyrequest(action, poly_kind, base_kind, **kwargs):
    base_key = tuple(base_kind._class_key())

    for cls_key, views in PolymodelMeta.cls_map.items():
        if action not in views:
            continue

        if cls_key[-1].lower() == poly_kind.lower() and \
                cls_key[:len(base_key)] == base_key:
            v = views[action]()
            return v.dispatch_request(**kwargs)

    logger.debug("No %r view for PolyModel subclass %r found",
                    action, poly_kind)
    flask.abort(404)



class PolymodelList(base_list.List):
    @classmethod
    def kind(cls):
        return cls.model._class_name()


class PolymodelEdit(base_base.KibbleView):
    """
    Dispatch class for Edit views.
    """
    action = 'edit'

    button_icon = 'pencil'

    _url_patterns = [
        ("/{key}/", {}),
    ]

    @classmethod
    def kind(cls):
        return cls.model._class_name()

    def dispatch_request(self, key):
        instance = key.get()
        if instance is None:
            logger.debug("Unable to find instance with key %r", key)
            flask.abort(404)

        return _dispatch_polyrequest(
            'edit',
            instance._class_name(),
            self.model,
            key=key)


class PolymodelCreate(base_base.KibbleView):
    """
    Class to dispatch create requests based on the polymodel subclass
    type.
    """
    action = 'new'

    button_icon = 'plus-sign'

    _url_patterns = [
        ('/{kind_lower}/new/<poly_kind>/', {'ancestor_key': None}),
        ('/{ancestor_key}/{kind_lower}/new/<poly_kind>/', {}),
        ('/{kind_lower}/new/', {'ancestor_key': None, 'poly_kind': None}),
        ('/{ancestor_key}/{kind_lower}/new/', {'poly_kind': None}),
    ]
    _methods = ['GET', 'POST']
    _requires_instance = False

    @classmethod
    def kind(cls):
        return cls.model._class_name()

    @property
    def templates(self):
        kwargs = {
            'action': self.action,
            'path': self.path().lower(),
            'kind': self.kind().lower(),
        }
        return [
            'kibble/polymodel/{path}/{action}.html'.format(**kwargs),
            'kibble/polymodel/{kind}/{action}.html'.format(**kwargs),
            'kibble/polymodel/{action}.html'.format(**kwargs),
        ]

    def _sub_kinds(cls):
        root_key = tuple(cls._class_key())
        l = len(root_key)

    def dispatch_request(self, ancestor_key, poly_kind):
        if poly_kind:
            return _dispatch_polyrequest(
                'create',
                poly_kind,
                self.model,
                ancestor_key=ancestor_key)
        return self.select_class(ancestor_key)

    def select_class(self, ancestor_key=None):
        classes = []

        for cls_key, views in PolymodelMeta.cls_map.items():
            if 'create' not in views:
                continue

            base_path = tuple(self.model._class_key())

            if cls_key[:len(base_path)] == base_path:
                model = views['create'].model
                classes.append((model, self.url_for(
                    ancestor_key=ancestor_key,
                    poly_kind=cls_key[-1].lower())))

        ctx = self.base_context()
        ctx['classes'] = classes
        return flask.render_template(self.templates, **ctx)

