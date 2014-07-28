import wtforms
import flask

from google.appengine.api import users
from google.appengine.ext import ndb
import flask_kibble as kibble
from flask_kibble.util.forms import ModelConverter


class KibbleUser(ndb.Model):
    email = ndb.StringProperty(required=True)
    enabled = ndb.BooleanProperty(default=True)
    superuser = ndb.BooleanProperty()
    permissions = ndb.StringProperty(repeated=True)

    def __unicode__(self):
        return self.email


class KibbleUserList(kibble.List):
    model = KibbleUser
    list_display = ['email', 'enabled', 'superuser']


class KibbleUserForm(ModelConverter.model_form(KibbleUser)):
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


class KibbleUserEdit(_UserEditBase, kibble.Edit):
    pass


class KibbleUserCreate(_UserEditBase, kibble.Create):
    pass


class KibbleUserDelete(kibble.Delete):
    model = KibbleUser


class ModelAuthenticatior(kibble.Authenticator):
    def is_logged_in(self):
        return bool(users.get_current_user())

    def has_permission_for(self, model, action, **kwargs):
        if users.is_current_user_admin():
            return True

        u = KibbleUser.get_by_id(users.get_current_user().email())
        if u is None:
            return False

        return '{}:{}'.format(model._get_kind() if model else 'view', action) in u.permissions

    def get_login_url(self):
        return users.create_login_url(flask.url_for('.index'))

    @classmethod
    def register_views(cls, kibble_blueprint):
        for klass in [KibbleUserList, KibbleUserCreate, KibbleUserDelete,
                      KibbleUserEdit]:
            kibble_blueprint.register_view(klass)

