"""Run with: python -m unittest discover -s tests -v  (after installing requirements)."""
import importlib
import os
import re
import tempfile
import unittest
from pathlib import Path


class HopeLinkSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        os.environ['NGO_DB_PATH'] = str(Path(cls.temp.name) / 'test.db')
        os.environ['NGO_ADMIN_PASSWORD'] = 'test-only-admin-password'
        os.environ.pop('NGO_READ_ONLY', None)
        cls.module = importlib.import_module('app')
        cls.module.app.testing = True

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.client = self.module.app.test_client()

    def token(self, path='/login'):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        csrf = re.search(rb'name="_csrf_token" value="([^"]+)"', response.data)
        self.assertIsNotNone(csrf)
        return csrf.group(1).decode()

    def login(self):
        token = self.token()
        return self.client.post('/login', data={
            '_csrf_token': token, 'username': 'admin',
            'password': 'test-only-admin-password',
        })

    def test_pages_render(self):
        for path in ('/', '/donate', '/volunteer', '/projects', '/inventory', '/login'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'HopeLink', response.data)
                self.assertIn(b'site.css', response.data)

    def test_login_and_admin(self):
        self.assertEqual(self.client.get('/admin').status_code, 302)
        self.assertEqual(self.login().status_code, 302)
        self.assertEqual(self.client.get('/admin').status_code, 200)

    def test_csrf_and_authz(self):
        self.assertEqual(self.client.post('/submit-donation', data={}).status_code, 400)
        csrf = self.token('/login')
        response = self.client.post('/add-inventory', data={'_csrf_token': csrf,
              'item_name': 'Unauthorized', 'item_category': 'Education', 'item_qty': '5'})
        self.assertEqual(response.status_code, 403)

    def test_donation_and_receipt(self):
        csrf = self.token('/donate')
        result = self.client.post('/submit-donation', data={
            '_csrf_token': csrf, 'donor_name': 'Sample Tester',
            'donor_email': 'test@example.test', 'donation_amount': '125.50',
            'donation_cause': 'Community Learning Kits', 'donor_message': 'Demo',
        })
        self.assertEqual(result.status_code, 302)
        receipt = self.client.get(result.location)
        self.assertEqual(receipt.status_code, 200)
        self.assertIn(b'not proof of payment', receipt.data)
        self.assertEqual(self.module.app.test_client().get(result.location).status_code, 404)

    def test_read_only_blocks_writes(self):
        csrf = self.token('/donate')
        self.module.READ_ONLY = True
        try:
            result = self.client.post('/submit-donation', data={'_csrf_token': csrf})
            self.assertEqual(result.status_code, 302)
            self.assertIn('/', result.location)
        finally:
            self.module.READ_ONLY = False

    def test_admin_modification(self):
        self.login()
        csrf = self.token('/login')
        response = self.client.post('/add-inventory', data={
            '_csrf_token': csrf, 'item_name': 'Test masks',
            'item_category': 'Healthcare', 'item_qty': '10',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(b'Test masks', self.client.get('/inventory').data)


if __name__ == '__main__':
    unittest.main()
