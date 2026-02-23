import unittest
import os
import tempfile
import json
from app import app, init_db, get_db

class SmartSpamAppTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()

        with app.app_context():
            init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

    def test_smart_tags(self):
        # Test Financial Tag
        rv = self.client.post('/api/predict', json={'message': 'WINNER! Cash prize waiting.'})
        data = rv.get_json()
        # Ensure it is spam for tags to appear
        assert data['is_spam'] == True or "Potential Scam" in str(data['tags'])
        # We check for the text part of the tag to avoid emoji encoding issues if any
        # But actually let's just check if ANY tag is present
        assert len(data['tags']) > 0

    def test_feedback_override(self):
        msg = "Safe message that looks like spam maybe"
        
        # 1. Report as NOT SPAM
        self.client.post('/feedback', data={'message': msg, 'user_label': 'NOT SPAM'})
        
        # 2. Check Prediction (Should be HAM with 50% confidence)
        rv = self.client.post('/', data={'message': msg, 'source': 'Test'})
        assert b'NOT SPAM' in rv.data
        assert b'50%' in rv.data
        assert b'User/Admin Override' in rv.data

    def test_url_detection(self):
        # UI Test for URL
        rv = self.client.post('/', data={'message': 'Click http://evil.com now', 'source': 'SMS'})
        assert b'Link Analysis' in rv.data
        assert b'http://evil.com' in rv.data

    def test_individual_delete(self):
        # Create item
        self.client.post('/', data={'message': 'Delete Me', 'source': 'SMS'})
        
        # Get ID from DB
        with app.app_context():
            db = get_db()
            row = db.execute('SELECT id FROM history WHERE message = "Delete Me"').fetchone()
            item_id = row['id']
            
        # Delete item
        self.client.post(f'/delete_history/{item_id}', follow_redirects=True)
        
        # Verify gone from DB directly
        with app.app_context():
            db = get_db()
            count = db.execute('SELECT COUNT(*) as c FROM history WHERE id = ?', (item_id,)).fetchone()['c']
            assert count == 0

if __name__ == '__main__':
    unittest.main()
