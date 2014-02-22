.. _installation:

Installation
============

Flask-Kibble is meant for deployment on Google App Engine. There are a number of
installation options available.

Copy Paste
----------

The simplest option, is to copy the entire flask-kibble module into your project. To
look something like this ::

    MyProject/
        app.yaml
        flask_kibble/
            __init__.py
            ...
        cron.yaml
        queue.yaml
        web.py


Package Bundling
----------------

Another option is to use a script to bundle packages into your project. 

 * `fabengine`_ - ``fabengine.bundle`` will package .whl files into your project
   directory.

 .. _fabengine: http://github.com/xlevus/fabengine/


Static Assets
-------------

Kibble has its own HTML assets that you must configure your ``app.yaml``
to serve. Assuming you've copied Flask-Kibble to your project root, this
can be done like so ::

    - url: /kibble/static
      static_dir: flask_kibble/static

