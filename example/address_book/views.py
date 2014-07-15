from flask.ext import kibble

from address_book import models


class ContactList(kibble.List):
    model = models.Contact
    linked_actions = ['delete', 'create']
    list_display = ['name']


class ContactCreate(kibble.Create):
    model = models.Contact
    fieldsets = [
        {'name': 'Base',
         'fields': ['name', 'birthday']},
        {'name': 'Contact Details',
         'fields': ['phone']},
    ]


class ContactEdit(kibble.Edit):
    model = models.Contact
    linked_actions = ['delete', 'Contact/Address:list']
    fieldsets = ContactCreate.fieldsets


class ContactDelete(kibble.Delete):
    model = models.Contact


class AddressCreate(kibble.Create):
    model = models.Address
    ancestors = [models.Contact]


class AddressEdit(kibble.Edit):
    model = models.Address
    ancestors = [models.Contact]


class AddressList(kibble.List):
    model = models.Address
    ancestors = [models.Contact]
    linked_actions = ['create']
