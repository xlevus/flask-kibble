import flask

import models

import flask_ndbcrud as crud

app = flask.Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'notasecret'

my_crud = crud.Crud(
    'crud', __name__, crud.Authenticator,
    static_url_path='/crud/static'
)


class ContactList(crud.List):
    model = models.Contact

    list_display = [
        'name', 'home_phone', 'work_phone',
    ]

class ContactCreate(crud.Create):
    model = models.Contact

class ContactEdit(crud.Edit):
    model = models.Contact


my_crud.register_view(ContactList)
my_crud.register_view(ContactCreate)
my_crud.register_view(ContactEdit)

app.register_blueprint(my_crud)
