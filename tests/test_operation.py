import mock

import flask

from .models import TestModel
from .base import TestCase

import flask_kibble as kibble


class DummyOperation(kibble.Operation):
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

        post_signal_p = mock.patch.object(DummyOperation, 'post_signal')
        self.post_signal = post_signal_p.start()
        self.addCleanup(post_signal_p.stop)

        pre_signal_p = mock.patch.object(DummyOperation, 'pre_signal')
        self.pre_signal = pre_signal_p.start()
        self.addCleanup(pre_signal_p.stop)

    def create_app(self):
        return self._create_app(DummyOperation)

    def test_url(self):
        self.assertEqual(
            flask.url_for('kibble.testmodel_dummy', key=self.instance),
            '/testmodel-test/dummy/')

    def assertPreSignalSent(self):
        self.pre_signal.send.assert_called_once_with(
            DummyOperation, key=self.instance.key)

    def assertPostSignalSent(self):
        self.post_signal.send.assert_called_once_with(
            DummyOperation, key=self.instance.key,
            result=self.run.return_value)

    def test_get(self):
        resp = self.client.get('/testmodel-test/dummy/')
        self.assert200(resp)
        self.assertTemplateUsed('kibble/operation.html')
        self.assertContext('instance', self.instance)

        self.assertFalse(self.run.called)
        self.assertFalse(self.get_message.called)
        self.assertFalse(self.get_redirect.called)

        self.assertFalse(self.pre_signal.send.called)
        self.assertFalse(self.post_signal.send.called)

    def test_post(self):
        resp = self.client.post('/testmodel-test/dummy/')
        self.assertRedirects(resp, '/dummy-redirect/')

        self.run.assert_called_once_with(self.instance, mock.ANY)
        self.get_message.assert_called_once_with(
            self.instance, mock.sentinel.RUN)

        self.get_redirect.assert_called_once_with(
            self.instance, mock.sentinel.RUN)

        self.assertPreSignalSent()
        self.assertPostSignalSent()

        self.assertFlashes("dummy-message", "success")

    def test_post_response_class(self):
        """
        run() returns a response class. This should be displayed
        directly to the user.
        """
        self.run.return_value = flask.make_response("OK")

        resp = self.client.post('/testmodel-test/dummy/')
        self.assert200(resp)
        self.assertEqual(resp.data, "OK")

        self.assertPreSignalSent()
        self.assertPostSignalSent()

        self.run.assert_called_once_with(self.instance, mock.ANY)

    def test_post_failure(self):
        """
        run() raises Failure. Flash a failure message to the user
        and redirect them back to wherever they were.
        """
        failure = kibble.Operation.Failure("")
        self.run.side_effect = failure

        resp = self.client.post('/testmodel-test/dummy/')
        self.assertRedirects(resp, '/dummy-redirect/')

        self.run.assert_called_once_with(self.instance, mock.ANY)
        self.get_message.assert_called_once_with(
            self.instance, failure)

        self.get_redirect.assert_called_once_with(
            self.instance, failure)

        self.assertPreSignalSent()
        # self.assertPostSignalSent()

        self.assertFlashes("dummy-message", "error")

    @mock.patch.object(DummyOperation, 'confirmation_form')
    def test_post_bad_form(self, confirmation_form):
        """
        Form is invalid, don't call run(), return the rendered form back
        to the user.
        """
        confirmation_form().validate.return_value = False

        resp = self.client.post('/testmodel-test/dummy/')
        self.assertFalse(self.run.called)

        self.assert200(resp)

        self.assertFalse(self.pre_signal.send.called)
        self.assertFalse(self.post_signal.send.called)

