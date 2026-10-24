import os
import unittest
from app import app
from db import init_db

class TestBriefIQ(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        init_db()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'BriefIQ', response.data)
        self.assertIn(b'Distill Lengthy Documents', response.data)
        print("PASS: Home page rendered")

    def test_about_page(self):
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'About BriefIQ', response.data)
        self.assertIn(b'T5 Deep Learning Model', response.data)
        print("PASS: About page rendered")

    def test_login_page(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to BriefIQ', response.data)
        print("PASS: Login page rendered")

    def test_register_page(self):
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create BriefIQ Account', response.data)
        print("PASS: Register page rendered")

    def test_demo_login_and_profile(self):
        # Demo login
        response = self.client.post('/demo-login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Alex', response.data)
        print("PASS: Demo login succeeded")

        # Profile page
        profile_res = self.client.get('/profile')
        self.assertEqual(profile_res.status_code, 200)
        self.assertIn(b'Alex Morgan', profile_res.data)
        print("PASS: Profile page rendered with user details")

    def test_sample_csv_analysis(self):
        response = self.client.get('/sample/csv', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Individual Performance', response.data)
        self.assertIn(b'Full Tabular Dataset Preview', response.data)
        print("PASS: Sample CSV analyzed and result displayed")

    def test_sample_pdf_analysis(self):
        response = self.client.get('/sample/pdf', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Key Thematic Takeaways', response.data)
        print("PASS: Sample PDF analyzed with T5 summary and result displayed")

    def test_pdf_report_download(self):
        # First trigger sample to have a history record
        self.client.get('/sample/csv', follow_redirects=True)
        # Download PDF report for id 1
        res = self.client.get('/download-report/1/pdf')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, 'application/pdf')
        self.assertTrue(len(res.data) > 1000)
        print(f"PASS: PDF Report generated and downloaded ({len(res.data)} bytes)")

if __name__ == '__main__':
    unittest.main()
