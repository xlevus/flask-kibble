import flask

import models

import flask_kibble as kibble

app = flask.Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'notasecret'

admin = kibble.Kibble(
    'kibble',
    __name__,
    kibble.Authenticator(),
    label='Example Kibble Admin',
    static_url_path='/kibble/static'
)

admin.autodiscover(
    paths=[
        'autodiscover'
    ],
    models=[
        'AutodiscoverTestModel'
    ])


class ContactDelete(kibble.Delete):
    model = models.Contact


class ContactCreate(kibble.Create):
    model = models.Contact

    fieldsets = [
        {'name': "Name", 'fields': ['name']},
        {'name': 'Address', 'fields': [
            'address_1', 'address_2', 'address_3']},
        {'name': 'Contact Details', 'fields': [
            'home_phone', 'work_phone']},
    ]


class ContactList(kibble.List):
    model = models.Contact

    page_size = 5

    list_display = [
        'name', 'home_phone', 'work_phone',
    ]
    actions = [
        ContactCreate,
        ContactDelete,
    ]


class ContactEdit(kibble.Edit):
    model = models.Contact

    fieldsets = ContactCreate.fieldsets


class OtherList(kibble.List):
    model = models.OtherThing


admin.register_view(ContactList)
admin.register_view(ContactCreate)
admin.register_view(ContactEdit)
admin.register_view(ContactDelete)

admin.register_view(OtherList)

app.register_blueprint(admin)
