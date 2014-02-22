.. _quickstart:

Quickstart
==========

Eager to get started? This page gives a good introduction to
Flask-Kibble. It assumes you already have Flask-Kibble installed. If you do not, head over to
the :ref:`installation` section.

Lets assume we have these models to work with ::

    from google.appengine.ext import ndb

    class MyModel(ndb.Model):
        name = ndb.StringProperty()
        description = ndb.TextProperty()


    class AnotherModel(ndb.Model):
        name = ndb.StringProperty()


A minimal Admin
---------------

Flask-Kibble provides :class:`flask_kibble.Kibble` (A :py:class:`flask.Blueprint` subclass ) to manage
templates, url-routes, and permissions. 

::

    import flask
    from flask.ext import kibble

    app = flask.Flask(__name__)
    admin = kibble.Kibble(
        'admin',
        __name__,
        kibble.Authenticator(),
        label='My Kibble Admin',
        static_url_path='/kibble/static'
    )

    app.register_blueprint(admin, url_prefix='/admin')


There's a few extra parameters you'll need to pass in:

 * A :class:`flask_kibble.Authenticator` instance to handle permissions. See
   :ref:`authentication` for more details.
 * An optional ``label`` parameter. This will be whats shown in your
   admin's menu.
 * The ``static_url_path`` for the media assets. See :ref:`installation`
   for more details.

If you run dev_appserver and head over to `http://127.0.0.1:8080/admin/
<http://127.0.0.1:8080/admin/>`_ you should see the start of your admin
interface.

But this isn't really helpful as we haven't defined any views for our
models.


A View or two
-------------

Each action (Create, Edit, List, etc) in your admin has its own View
class. Lets create a few views for ``MyModel`` to allow creation of new
instances, and a list view. ::


    from flask.ext import kibble

    class MyModelCreate(kibble.Create):
        model = models.MyModel

    class MyModelList(kibble.List):
        model = models.MyModel


Now we need to register the views with our :class:`~flask_kibble.Kibble`
instance. You can either do this manually with
:meth:`~flask_kibble.Kibble.register_view` ::

    admin = kibble.Kibble('admin', __name__, kibble.Authenticator())
    
    import views
    admin.register_view(views.MyModelCreate)
    admin.register_view(views.MyModelList)


or, have your admin autodiscovered with
:meth:`~flask_kibble.Kibble.autodiscover` ::

    admin = kibble.Kibble('admin', __name__, kibble.Authenticator())
    admin.autodiscover(modules=['views'])

n.b. You must register your views before you register your blueprint.

