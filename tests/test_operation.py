import mock

import flask

from .models import TestModel
from .base import TestCase

import flask_ndbcrud as crud


class DummyOperation(crud.Operation):
    action = 'dummy'
    past_tense = 'dummied'

    model = TestModel


class OperationTestCase(TestCase):
    def setUp(self):
        self.instance = TestModel(name='test', id='test')
        self.instance.put()

        runp = mock.patch.object(DummyOperation, 'run',
                                 return_value=mock.sentinel.RUN)
        self.run = runp.start()
        self.addCleanup(runp.stop)

        redp = mock.patch.object(DummyOperation, 'get_redirect',
                                 return_value='/dummy-redirect/')
        self.get_redirect = redp.start()
        self.addCleanup(redp.stop)

        msgp = mock.patch.object(DummyOperation, 'get_message',
                                 return_value='dummy-message')
        self.get_message = msgp.start()
        self.addCleanup(msgp.stop)

    def create_app(self):
        return self._create_app(DummyOperation)

    def test_url(self):
        self.assertEqual(
            flask.url_for('crud.testmodel_dummy', key=self.instance),
            '/testmodel/i-test/dummy/')

    def test_get(self):
        resp = self.client.get('/testmodel/i-test/dummy/')
        self.assert200(resp)
        self.assertTemplateUsed('crud/operation.html')
        self.assertContext('instance', self.instance)

        self.assertFalse(self.run.called)
        self.assertFalse(self.get_message.called)
        self.assertFalse(self.get_redirect.called)

    def test_post(self):
        resp = self.client.post('/testmodel/i-test/dummy/')
        self.assertRedirects(resp, '/dummy-redirect/')

        self.run.assert_called_once_with(self.instance)
        self.get_message.assert_called_once_with(
            self.instance, mock.sentinel.RUN)

        self.get_redirect.assert_called_once_with(
            self.instance, mock.sentinel.RUN)

        self.assertFlashes("dummy-message", "success")

    def test_post_response_class(self):
        self.run.return_value = flask.make_response("OK")

        resp = self.client.post('/testmodel/i-test/dummy/')
        self.assert200(resp)
        self.assertEqual(resp.data, "OK")

        self.run.assert_called_once_with(self.instance)

    def test_post_failure(self):
        failure = crud.Operation.Failure("")
        self.run.side_effect = failure

        resp = self.client.post('/testmodel/i-test/dummy/')
        self.assertRedirects(resp, '/dummy-redirect/')

        self.run.assert_called_once_with(self.instance)
        self.get_message.assert_called_once_with(
            self.instance, failure)

        self.get_redirect.assert_called_once_with(
            self.instance, failure)

        self.assertFlashes("dummy-message", "error")


