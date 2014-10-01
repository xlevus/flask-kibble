import mock

from .base import TestCase
from .models import TestModel

import flask_kibble as kibble


class TestDelete(kibble.Delete):
    model = TestModel


class TestDeleteRecursive(kibble.Delete):
    action = 'delete_recursive'
    model = TestModel
    recursive = True


class CreateTestCase(TestCase):
    def create_app(self):
        return self._create_app(TestDelete, TestDeleteRecursive)

    @mock.patch.object(TestDelete.form.Meta, 'csrf', False)
    def test_delete(self):
        inst = TestModel(name='test', id=1).put()
        child = TestModel(parent=inst, name='test2', id=2).put()

        resp = self.client.post('/testmodel-1/delete/')

        self.assertIsNone(inst.get())
        self.assertIsNotNone(child.get())

    @mock.patch.object(TestDelete.form.Meta, 'csrf', False)
    def test_delete_recursive(self):
        inst = TestModel(name='test', id=1).put()
        child = TestModel(parent=inst, name='test2', id=2).put()
        childchild = TestModel(parent=child, name='test3', id=3).put()

        resp = self.client.post('/testmodel-1/delete_recursive/')

        self.assertIsNone(inst.get())
        self.assertIsNone(child.get())
        self.assertIsNone(childchild.get())

