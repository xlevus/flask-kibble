"""
PolyModel mixins for Kibble.
============================

Admin interfaces for polymodels are done by creating a view of the desired
action for the top-level polymodel, and mixing it in with one of
`PolyClassPicker` or `PolyDispatcher`.

`PolyClassPicker` will display a choose-a-class dialog before displaying the
interface, and `PolyDispatcher` will dispatch the request to the appropiate
view based on the instance type.

"""

import flask

from . import base as base_base


class PolyMeta(base_base.KibbleMeta):
    def __new__(mcls, name, bases, attrs):
        _super = lambda c: super(c, mcls).__new__(mcls, name, bases, attrs)  # noqa

        if name in ('PolyClassPicker', 'PolyDispatcher'):
            return _super(base_base.KibbleMeta)

        if PolyClassPicker in bases or PolyDispatcher in bases:
            attrs['_sub_views'] = {}
            cls = _super(PolyMeta)
            return cls

        cls = _super(base_base.KibbleMeta)
        for base in bases:
            if issubclass(base, (PolyClassPicker, PolyDispatcher)):
                model = tuple(cls.model._class_key())
                base._sub_views[model] = cls
                break
        return cls

    def mro(mcls):
        # Redfine the MRO of our child class. Immediate descendents of
        # PolyClassPicker should have the normal MRO.
        mro = super(PolyMeta, mcls).mro()
        for cls in mcls.__bases__:
            if cls.__name__ in ('PolyClassPicker', 'PolyDispatcher'):
                return mro

        # Calls to dispatch_request of the child PolyClassPicker's would
        # result in an infinate loop, so remove the PolyClassPicker from the
        # MRO to allow 'normal' resolution.
        new_mro = [
            c for c in mro if
            c.__name__ not in ('PolyClassPicker', 'PolyDispatcher')
        ]
        return new_mro


class PolyClassPicker(object):
    """
    Polymodel mixin that provides users with an interim "Choose a class"
    view.
    This will then dispatch the request to the correct descendant KibbleView.
    """
    __metaclass__ = PolyMeta

    def dispatch_request(self, *args, **kwargs):
        cls_name = flask.request.args.get('class', None)
        for cls_key, view_cls in self._sub_views.items():
            if cls_key[-1] == cls_name:
                v = view_cls()
                return v.dispatch_request(*args, **kwargs)

        ctx = self.base_context()
        ctx['sub_views'] = self._sub_views

        return flask.render_template(
            'kibble/polymodel/picker.html',
            **ctx)


class PolyDispatcher(object):
    """
    Polymodel mixin that selects the correct kibble view based on the
    instance type that is passed in.
    Assumes the instance is passed through the ``key`` parameter.
    """
    __metaclass__ = PolyMeta

    def dispatch_request(self, **kwargs):
        try:
            inst = kwargs['key'].get()
            view_cls = self._sub_views[tuple(inst._class_key())]
            return view_cls().dispatch_request(**kwargs)
        except KeyError:
            flask.abort(404)

