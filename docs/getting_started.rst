.. _getting_started:

Getting Stared
==============

Create your Blueprint
---------------------

Create a Flask-Kibble ``flask_kibble.Kibble`` blueprint.

.. code-block: python

    admin = kibble.Kibble(
        'admin', 
        __name__,
        kibble.Authenticator(),
        label='Kibble Admin',
        static_url_path='/kibble/static')


Create some Views
-----------------

Now create some views, and register them to your blueprint.

For each model and action (e.g. List, Create, Edit Delete) you should have
one view class.

.. code-block: python
  
    from flask.ext import kibble
    from myapp.models import MyModel

    class MyModelList(kibble.List):
        model = MyModel


    class MyModelCreate(kibble.Create):
        model = MyModel


    class MyModelEdit(kibble.Edit):
        model = MyModel


    admin.register_view(MyModelList)
    admin.register_view(MyModelCreate)
    admin.register_view(MyModelEdit)


Register your blueprint to your app
-----------------------------------

.. code-block: python

    import flask
    app = flask.Flask(__name__)

    app.register_blueprint(admin, url_prefix='/admin')

