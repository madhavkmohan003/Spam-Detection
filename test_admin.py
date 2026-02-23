import unittest
import os
import tempfile
import json
from app import app, init_db, get_db

class AdminAppTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()

        with app.app_context():
            init_db()
            
        # Login as Admin via route
        self.client.post('/login', data={'username': 'admin', 'password': '1234'}, follow_redirects=True)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

    def test_admin_access(self):
        rv = self.client.get('/admin')
        assert rv.status_code == 200
        assert b'AdminPanel' in rv.data

    def test_admin_train(self):
        # Admin manually marks a message as SPAM
        msg = "Ambiguous message"
        self.client.post('/admin/train', data={'message': msg, 'label': 'SPAM'})
        
        # Check prediction matches Admin's label
        rv = self.client.post('/', data={'message': msg, 'source': 'Test'})
        assert b'SPAM' in rv.data
        assert b'User/Admin Override' in rv.data

    def test_enhanced_url_scanner(self):
        # 1. IP Address URL (Critical Risk)
        rv = self.client.post('/', data={'message': 'Click http://192.168.1.1/login', 'source': 'SMS'})
        assert b'CRITICAL RISK' in rv.data
        assert b'IP Address URL' in rv.data
        
        # 2. Suspicious Keyword (High Risk)
        rv = self.client.post('/', data={'message': 'Verify your bank account at http://secure-login.com', 'source': 'Email'})
        assert b'Suspicious Keyword' in rv.data

    def test_delete_feedback(self):
        # 1. Add some feedback
        self.client.post('/feedback', data={'message': 'Bad spam', 'user_label': 'SPAM'})
        
        # 2. Get the ID (we can't easily get it without parsing, but we can rely on order if we just allow deleting any)
        with app.app_context():
            db = get_db()
            feedback = db.execute('SELECT * FROM feedback').fetchall()
            fid = feedback[0]['id']
            
        # 3. Delete it
        rv = self.client.post(f'/admin/delete_feedback/{fid}', follow_redirects=True)
        assert rv.status_code == 200
        
        # 4. Verify it's gone
        with app.app_context():
            db = get_db()
            f = db.execute('SELECT * FROM feedback WHERE id = ?', (fid,)).fetchone()
            assert f is None

    def test_session_logout(self):
        # 1. Login
        self.client.post('/login', data={'username': 'admin', 'password': '1234'}, follow_redirects=True)
        # 2. Access Admin (should be OK)
        rv = self.client.get('/admin')
        assert rv.status_code == 200
        # 3. Go to Index (should logout)
        self.client.get('/')
        # 4. Access Admin again (should redirect to login)
        rv = self.client.get('/admin', follow_redirects=True)
        assert b'Login' in rv.data

if __name__ == '__main__':
    unittest.main()
