import wtforms
import flask
from werkzeug.utils import cached_property

from google.appengine.api import users
from google.appengine.ext import ndb
import flask_kibble as kibble
from flask_kibble.util.forms import KibbleModelConverter


class KibbleUserGroup(ndb.Model):
    name = ndb.StringProperty()
    permissions = ndb.StringProperty(repeated=True)


class KibbleUser(ndb.Model):
    email = ndb.StringProperty(required=True)
    enabled = ndb.BooleanProperty(default=True)
    superuser = ndb.BooleanProperty()
    permissions = ndb.StringProperty(repeated=True)

    groups = ndb.KeyProperty(KibbleUserGroup, repeated=True)

    def __unicode__(self):
        return self.email

    @cached_property
    def all_permissions(self):
        groups = ndb.get_multi(self.groups)

        s = set(self.permissions)
        for g in groups:
            if g:
                s.update(g.permissions)

        return s


class KibbleUserForm(KibbleModelConverter.model_form(KibbleUser)):
    permissions = wtforms.SelectMultipleField()


class KibbleGroupForm(KibbleModelConverter.model_form(KibbleUserGroup)):
    permissions = wtforms.SelectMultipleField()


class _UserEditBase(object):
    model = KibbleUser
    fieldsets = [
        {'name': 'User', 'fields': ['email', 'enabled', 'superuser']},
        {'name': 'Permissions', 'fields': ['permissions']},
    ]
    form = KibbleUserForm

    def get_form_instance(self, instance=None):
        form = self.form(flask.request.form, obj=instance)
        form.permissions.choices = [
            ("{}:{}".format(m._get_kind() if m else 'view', a),)*2 for m, a in
            flask.g.kibble.all_permissions()
        ]
        return form

    def save_model(self, form, instance=None, ancestor_key=None):
        if instance is None:
            instance = self.model(parent=ancestor_key, id=form.data['email'])
        form.populate_obj(instance)
        instance.put()
        return instance


class _GroupEditBase(object):
    model = KibbleUserGroup
    fieldsets = [
        {'name': 'Group', 'fields': ['name', 'permissions']}
    ]
    form = KibbleGroupForm

    def get_form_instance(self, instance=None):
        form = self.form(flask.request.form, obj=instance)
        form.permissions.choices = [
            ("{}:{}".format(m._get_kind() if m else 'view', a),)*2 for m, a in
            flask.g.kibble.all_permissions()
        ]
        return form


class KibbleUserList(kibble.List):
    model = KibbleUser
    list_display = ['email', 'enabled', 'superuser']
    linked_actions = ['create', 'edit', 'delete']


class KibbleUserEdit(_UserEditBase, kibble.Edit):
    pass


class KibbleUserCreate(_UserEditBase, kibble.Create):
    pass


class KibbleUserDelete(kibble.Delete):
    model = KibbleUser


class KibbleGroupList(kibble.List):
    model = KibbleUserGroup
    list_display = ['name']
    linked_actions = ['create', 'edit', 'delete']


class KibbleGroupEdit(_GroupEditBase, kibble.Edit):
    pass


class KibbleGroupCreate(_GroupEditBase, kibble.Create):
    pass


class KibbleGroupDelete(kibble.Delete):
    model = KibbleUserGroup


class ModelAuthenticatior(kibble.Authenticator):
    def is_logged_in(self):
        return bool(users.get_current_user())

    def has_permission_for(self, model, action, **kwargs):
        if users.is_current_user_admin():
            return True

        u = KibbleUser.get_by_id(users.get_current_user().email())
        if u is None or not u.enabled:
            return False

        if u.superuser:
            return True

        return (
            '{}:{}'.format(model._get_kind() if model else 'view', action)
            in u.all_permissions)

    def get_login_url(self):
        return users.create_login_url(flask.url_for('.index'))

    @classmethod
    def register_views(cls, kibble_blueprint):
        for klass in [KibbleUserList, KibbleUserCreate, KibbleUserDelete,
                      KibbleUserEdit]:
            kibble_blueprint.register_view(klass)

