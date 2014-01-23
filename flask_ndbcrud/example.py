from google.appengine.ext import ndb

from flask.ext import ndbcrud

my_crud = ndbcrud.Crud()

class ModelEdit(ndbcrud.Edit):
    model = my_model


my_crud.register(ModelEdit)
