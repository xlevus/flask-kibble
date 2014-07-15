
import flask
from google.appengine.api import users


class Authenticator(object):
    def is_logged_in(self):
        """
        Should return true if the current user is logged in.

        :rtype: :py:class:`bool`
        """
        return True

    def can_upload_file(self, file):
        """
        Check if the user is eligible to upload a file. If not, the uploaded
        file will be deleted.

        :param file: A Blobinfo or Fileinfo object.
        """
        return True

    def has_permission_for(self, model, action, key=None, **view_args):
        """
        Should return true if the current user has the permissions for
        the Model/Action/ViewArgs.

        :param model: The model class that is being operated on
        :param action: The KibbleView.action that is being executed or the
            name of the view (for non-CBVs)
        :param key: The ndb.Key of the object currently operating on.
        :param \*\*view_args: The current view args.

        :rtype: :py:class:`bool`
        """
        return True

    def get_login_url(self):
        """
        Should return a URL the user can use to log in.
        """
        return '/'


class GAEAuthenticator(Authenticator):
    """
    Authenticator for Google App Engine accounts
    (:py:class:`google.appengine.api.users`).

    Will grant all permissions to all GAE accounts, or all GAE administrators.
    """
    def __init__(self, admin_only=False):
        """
        :param admin_only: Only administrators have permissions.
        """
        self.admin_only = admin_only

    def is_logged_in(self):
        return bool(users.get_current_user())

    def has_permission_for(self, model, action, key=None, **view_args):
        if self.admin_only:
            return users.is_current_user_admin()
        return self.is_logged_in()

    def get_login_url(self):
        return users.create_login_url(flask.url_for('.index'))

