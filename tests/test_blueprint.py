import mock
from cStringIO import StringIO
from google.appengine.ext import ndb

from .base import TestCase, TestAuthenticator
from .models import TestModel

import flask_kibble as kibble
from flask_kibble.base import KibbleView


class DummyView(KibbleView):
    action = 'dummy'
    model = TestModel

    _url_patterns = [
        ('/{kind_lower}/{action}/<test>/', {}),
        ('/{kind_lower}/{action}/', {'test': None})
    ]
    _methods = ['GET', 'DELETE']


class BlueprintTestCase(TestCase):
    def create_app(self):
        return self._create_app(DummyView)

    def test_register(self):
        """
        Check that when registering a view class, the associated _url_patterns
        are registered.

        Also check the view gets added to the internal registry.
        """
        bp = kibble.Kibble('test_kibble', __name__, TestAuthenticator())

        mpo = mock.patch.object
        with mpo(bp, 'add_url_rule', wraps=bp.add_url_rule) as add_url_rule:
            bp.register_view(DummyView)

            self.assertEqual(add_url_rule.call_args_list, [
                mock.call('/testmodel/dummy/<test>/',
                          methods=['GET', 'DELETE'],
                          defaults={},
                          view_func=mock.ANY),
                mock.call('/testmodel/dummy/',
                          methods=['GET', 'DELETE'],
                          defaults={'test': None},
                          view_func=mock.ANY)])

            self.assertEqual(bp.registry, {'TestModel': {'dummy': DummyView}})

    def test_context_processor(self):
        self.assertEqual(self.kibble._context_processor(), {
            'kibble': self.kibble,
        })

    @mock.patch.object(DummyView, 'url_for')
    def test_url_for(self, dummy_url_for):
        dummy_url_for.return_value = mock.sentinel.URL_FOR

        # get url from view w/o instance
        self.assertEqual(
            self.kibble.url_for(TestModel, 'dummy'),
            mock.sentinel.URL_FOR)
        dummy_url_for.assert_called_once_with(None, None, blueprint='kibble')
        dummy_url_for.reset_mock()

        # Get URL for instance
        self.assertEqual(
            self.kibble.url_for(TestModel, 'dummy', mock.sentinel.INSTANCE),
            mock.sentinel.URL_FOR)
        dummy_url_for.assert_called_once_with(
            mock.sentinel.INSTANCE, None, blueprint='kibble')
        dummy_url_for.reset_mock()

        # URL for ancestor
        self.assertEqual(
            self.kibble.url_for(TestModel, 'dummy', mock.sentinel.INSTANCE,
                                mock.sentinel.ANCESTOR),
            mock.sentinel.URL_FOR)
        dummy_url_for.assert_called_once_with(
            mock.sentinel.INSTANCE, mock.sentinel.ANCESTOR, blueprint='kibble')
        dummy_url_for.reset_mock()

        # View not installed. Return empty string
        self.assertEqual(
            self.kibble.url_for(TestModel, 'not_registered'),
            '')

        # Neither model nor view registerd
        class OtherModel(ndb.Model):
            pass

        self.assertEqual(self.kibble.url_for(OtherModel, 'other'), '')


class BlueprintIndexTestCase(TestCase):
    """
    Index view tests. Also covers permission checks.
    """
    def create_app(self):
        return self._create_app(DummyView)

    def test_index(self):
        resp = self.client.get('/')
        self.assert200(resp)
        self.assertTemplateUsed('kibble/index.html')

        self.authenticator.has_permission_for.assert_called_once_with(
            None, 'kibble.index')

    def test_index_noperm(self):
        # Maybe the user should always have the index permission?
        self.authenticator.has_permission_for.return_value = False
        resp = self.client.get('/')
        self.assert403(resp)

    def test_index_loggedout(self):
        self.authenticator.is_logged_in.return_value = False

        resp = self.client.get('/')
        self.assertRedirects(resp, self.authenticator.get_login_url())


class BlueprintUploadTestCase(TestCase):
    def create_app(self):
        return self._create_app(DummyView)

    def test_get(self):
        resp = self.client.get('/_upload/')
        self.assert405(resp)

    def test_post(self):
        from google.appengine.ext import blobstore
        ct = 'message/external-body; '\
            'blob-key="BLOBKEY"; '\
            'access-type="X-AppEngine-BlobKey"'

        f = (StringIO("file"), 'test.txt', ct)

        with mock.patch.object(self.authenticator, 'can_upload_file') as cuf:
            resp = self.client.post('/_upload/', data={'file': f})

            self.assert200(resp)
            self.assertEqual(resp.json, {
                'file': {
                    'blobkey': 'BLOBKEY',
                    'filename': 'test.txt',
                },
            })

            cuf.assert_called_once_with(blobstore.BlobInfo.get('BLOBKEY'))
