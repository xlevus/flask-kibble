import flask

import models

import flask_ndbcrud as crud

app = flask.Flask(__name__)
app.debug = True

my_crud = crud.Crud(
    'crud', __name__, crud.Authenticator,
    static_url_path='/crud/static'
)


class ContactList(crud.List):
    model = models.Contact

my_crud.register_view(ContactList)

app.register_blueprint(my_crud)

