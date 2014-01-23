import flask

import models

import flask_ndbcrud as crud

app = flask.Flask(__name__)

my_crud = crud.Crud('crud', __name__, crud.Authenticator)


app.register_blueprint(my_crud)

