# from google.appengine.ext import ndb

from . import edit as base_edit
from . import list as base_list


class PolymodelMixin(object):
    @classmethod
    def kind(cls):
        return cls.model._class_name()


class List(PolymodelMixin, base_list.List):
    pass


class Edit(PolymodelMixin, base_edit.Edit):
    pass


class Create(PolymodelMixin, base_edit.Create):
    pass

"""
    _url_patterns = [
        ('/{kind_lower}/new/', {'ancestor_key': None, 'poly_kind': None}),
        ('/{ancestor_key}/{kind_lower}/new/', {'poly_kind': None}),
        ('/{kind_lower}/new/<poly_kind>/', {'ancestor_key': None}),
        ('/{ancestor_key}/{kind_lower}/new/<poly_kind>', {}),
    ]

    sub_classes = {}

    def pick_kind(self, ancestor_key=None):
        pass

    def dispatch_request(self, ancestor_key=None, poly_kind=None):
        if poly_kind is None:
            return self.pick_kind(ancestor_key)
        return super(PolymodelCreate, self).dispatch_request(ancestor_key)
"""

