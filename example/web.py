import flask

import models

import flask_ndbcrud as crud

app = flask.Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'notasecret'

my_crud = crud.Crud(
    'crud', __name__, crud.Authenticator(),
    static_url_path='/crud/static'
)


class ContactDelete(crud.Delete):
    model = models.Contact


class ContactCreate(crud.Create):
    model = models.Contact

    fieldsets = [
        {'name': "Name", 'fields': ['name']},
        {'name': 'Address', 'fields': [
            'address_1', 'address_2', 'address_3']},
        {'name': 'Contact Details', 'fields': [
            'home_phone', 'work_phone']},
    ]


class ContactList(crud.List):
    model = models.Contact

    page_size = 5

    list_display = [
        'name', 'home_phone', 'work_phone',
    ]
    actions = [
        ContactCreate,
        ContactDelete,
    ]


class ContactEdit(crud.Edit):
    model = models.Contact

    fieldsets = ContactCreate.fieldsets


class OtherList(crud.List):
    model = models.OtherThing


my_crud.register_view(ContactList)
my_crud.register_view(ContactCreate)
my_crud.register_view(ContactEdit)
my_crud.register_view(ContactDelete)

my_crud.register_view(OtherList)

app.register_blueprint(my_crud)
