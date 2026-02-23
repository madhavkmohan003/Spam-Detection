from flask import Flask, render_template, request, g, jsonify, redirect, url_for, Response, session
import pickle
import sqlite3
import io
import csv
from datetime import datetime

app = Flask(__name__)
app.config['DATABASE'] = 'spam_data.db'
app.secret_key = 'super_secret_key_change_this'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                source TEXT,
                result TEXT,
                probability TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                user_label TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

# Initialize DB structure
init_db()

model = pickle.load(open("model/spam_model.pkl", "rb"))
vectorizer = pickle.load(open("model/vectorizer.pkl", "rb"))

import re

# ... existing code ...

SPAM_KEYWORDS = [
    "free", "win", "winner", "cash", "offer",
    "claim", "urgent", "prize", "money", "congratulations",
    "click", "link", "subscribe", "buy", "order", "limited", "verify", "account"
]

def get_smart_categories(message):
    tags = []
    msg_lower = message.lower()
    
    # Financial
    if any(w in msg_lower for w in ["bank", "transfer", "account", "verify", "credit", "card", "billing"]):
        tags.append("💳 Financial Risk")
    elif any(w in msg_lower for w in ["win", "winner", "cash", "prize", "money", "lottery", "100%", "deposit"]):
        tags.append("💰 Potential Scam")
        
    # Urgency
    if any(w in msg_lower for w in ["urgent", "immediate", "act now", "limited time", "expire", "warning"]):
        tags.append("🚨 High Urgency")
        
    # Phishing/Links
    if "http" in msg_lower or ".com" in msg_lower or "click" in msg_lower:
        tags.append("🔗 Link Analysis")
        
    return tags

   # Enhanced URL Scanner with Risk Score
def extract_urls(text):
    urls = re.findall(r'(https?://\S+|www\.\S+)', text)
    results = []
    
    suspicious_tlds = ['.xyz', '.top', '.club', '.info', '.gq', '.tk', '.ml', '.ga', '.cf']
    suspicious_keywords = ['login', 'verify', 'account', 'update', 'secure', 'bank', 'prize', 'win']
    
    for url in urls:
        risk_score = 0
        reasons = []
        
        # Check TLD
        if any(tld in url for tld in suspicious_tlds):
            risk_score += 50
            reasons.append("Suspicious TLD")
            
        # Check Keywords
        if any(kw in url.lower() for kw in suspicious_keywords):
            risk_score += 30
            reasons.append("Suspicious Keyword")
            
        # Check for IP address based URL
        if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url):
            risk_score += 80
            reasons.append("IP Address URL")
            
        risk_level = "Low"
        if risk_score > 70:
            risk_level = "CRITICAL"
        elif risk_score > 30:
            risk_level = "High"
        elif risk_score > 0:
            risk_level = "Medium"
            
        results.append({
            "url": url,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "reasons": ", ".join(reasons) if reasons else "None"
        })
        
    return results

# Authentication Routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username == "admin" and password == "1234":
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route("/admin/delete_feedback/<int:id>", methods=["POST"])
def delete_feedback(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    db = get_db()
    db.execute('DELETE FROM feedback WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('admin'))

@app.route("/", methods=["GET", "POST"])
def index():
    # Auto-Logout Admin if they return to the main app
    if session.get('logged_in'):
        session.pop('logged_in', None)

    prediction = ""
    probability = ""
    keywords_found = []
    tags = []
    urls_found = []

    db = get_db()

    if request.method == "POST":
        message = request.form.get("message")
        source = request.form.get("source")

        if message and message.strip():
            # 1. Check Feedback Override (Database)
            # Prioritize ADMIN labels first
            override = db.execute(
                'SELECT user_label FROM feedback WHERE message = ? ORDER BY CASE WHEN user_label LIKE "ADMIN%" THEN 1 ELSE 2 END, timestamp DESC LIMIT 1', 
                (message,)
            ).fetchone()
            
            # URL Scan
            urls_found = extract_urls(message)
            if any(u['risk_score'] > 0 for u in urls_found):
                tags.append("🔗 Link Analysis")

            if override:
                result = override['user_label']
                # Strip ADMIN_ prefix if present
                display_result = result.replace("ADMIN_", "")
                
                spam_prob = 50.0
                prediction = "🚫 SPAM" if "SPAM" in display_result else "✅ NOT SPAM"
                probability = "50% (Verified)"
                tags.append("👤 User/Admin Override")
            else:
                # 2. AI Model Prediction
                data = vectorizer.transform([message])
                result = model.predict(data)[0]
                probs = model.predict_proba(data)[0]

                spam_prob = probs[list(model.classes_).index("spam")] * 100
                prediction = "🚫 SPAM" if result == "spam" else "✅ NOT SPAM"
                probability = f"{spam_prob:.2f}%"
                
                # Smart Categorization
                smart_tags = get_smart_categories(message)
                tags.extend(smart_tags)

            keywords_found = [k for k in SPAM_KEYWORDS if k in message.lower()]

            db.execute(
                'INSERT INTO history (message, source, result, probability) VALUES (?, ?, ?, ?)',
                (message, source, prediction, probability)
            )
            db.commit()

    # Fetch History
    history_rows = db.execute('SELECT * FROM history ORDER BY timestamp DESC').fetchall()
    
    # Calculate Data for Radar Chart
    tag_counts = {
        "Financial": 0,
        "Urgency": 0,
        "Phishing": 0, 
        "Scam": 0
    }
    
    for row in history_rows:
         msg = row['message']
         smart = get_smart_categories(msg)
         if "💳 Financial Risk" in smart: tag_counts["Financial"] += 1
         if "🚨 High Urgency" in smart: tag_counts["Urgency"] += 1
         if "🔗 Link Analysis" in smart or "http" in msg: tag_counts["Phishing"] += 1
         if "💰 Potential Scam" in smart: tag_counts["Scam"] += 1

    # Calculate Traffic (Activity by Hour)
    hours = [f"{i:02d}:00" for i in range(24)]
    traffic_data = {h: 0 for h in hours}
    
    for row in history_rows:
        try:
            # Timestamp format: YYYY-MM-DD HH:MM:SS
            ts = row['timestamp']
            if ts:
                hour_key = f"{int(ts.split()[1].split(':')[0]):02d}:00"
                if hour_key in traffic_data:
                    traffic_data[hour_key] += 1
        except:
            pass

    # Fetch Feedback
    feedback_rows = db.execute('SELECT * FROM feedback ORDER BY timestamp DESC').fetchall()

    # Statistics
    total = len(history_rows)
    spam_count = sum(1 for h in history_rows if "SPAM" in h['result'])
    ham_count = total - spam_count

    return render_template(
        "index.html",
        prediction=prediction,
        probability=probability,
        keywords=keywords_found,
        tags=tags,
        urls=urls_found,
        history=history_rows,
        total=total,
        spam_count=spam_count,
        ham_count=ham_count,
        feedback=feedback_rows,
        radar_data=tag_counts,
        traffic_data=traffic_data
    )

@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.json
    message = data.get("message", "")
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    # Check Override
    db = get_db()
    cursor = db.execute('SELECT user_label FROM feedback WHERE message = ? ORDER BY id DESC LIMIT 1', (message,))
    override = cursor.fetchone()
    
    if override:
        prediction = override['user_label'].lower()
        spam_prob = 50.0
        is_spam = prediction == "spam"
    else:
        vec_data = vectorizer.transform([message])
        result = model.predict(vec_data)[0]
        probs = model.predict_proba(vec_data)[0]
        spam_prob = probs[list(model.classes_).index("spam")] * 100
        prediction = "spam" if result == "spam" else "ham"
        is_spam = bool(result == "spam")
    
    tags = get_smart_categories(message) if is_spam else []
    
    return jsonify({
        "prediction": prediction,
        "spam_probability": spam_prob,
        "is_spam": is_spam,
        "tags": tags
    })

@app.route("/feedback", methods=["POST"])
def feedback():
    message = request.form.get("message")
    user_label = request.form.get("user_label") # Expecting "SPAM" or "NOT SPAM"
    
    if message and user_label:
        db = get_db()
        db.execute(
            'INSERT INTO feedback (message, user_label) VALUES (?, ?)',
            (message, user_label)
        )
        db.commit()
        
    return redirect(url_for('index'))

@app.route("/delete_history/<int:id>", methods=["POST"])
def delete_history_item(id):
    db = get_db()
    db.execute('DELETE FROM history WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('index'))

@app.route("/clear_history", methods=["POST"])
def clear_history():
    db = get_db()
    db.execute('DELETE FROM history')
    db.commit()
    return redirect(url_for('index'))

@app.route("/export_csv")
def export_csv():
    db = get_db()
    cur = db.execute('SELECT * FROM history')
    rows = cur.fetchall()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Message', 'Source', 'Result', 'Probability', 'Timestamp'])
    
    for row in rows:
        writer.writerow([row['id'], row['message'], row['source'], row['result'], row['probability'], row['timestamp']])
        
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=spam_history.csv"}
    )




@app.route("/admin")
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    db = get_db()
    
    # Calculate stats for admin dashboard
    total = db.execute('SELECT COUNT(*) FROM history').fetchone()[0]
    spam_count = db.execute('SELECT COUNT(*) FROM history WHERE result LIKE "%SPAM%"').fetchone()[0]
    ham_count = total - spam_count
    
    # Fetch ONLY User Feedback (Exclude Admin's own actions)
    feedback_queue = db.execute('SELECT * FROM feedback WHERE user_label NOT LIKE "ADMIN%" ORDER BY timestamp DESC').fetchall()
    
    return render_template('admin.html', 
                           feedback=feedback_queue, 
                           total=total, 
                           spam_count=spam_count, 
                           ham_count=ham_count)

@app.route("/admin/train", methods=["POST"])
def admin_train():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    message = request.form.get("message")
    label = request.form.get("label") # Expected: SPAM or NOT SPAM
    
    if message and label:
        db = get_db()
        # Mark as Admin Verified by prefixing
        admin_label = f"ADMIN_{label}" # e.g., ADMIN_SPAM
        
        # We can either update the existing row OR insert a new one.
        # User asked: "instead of filling up... by adding again and again"
        # So we should try to UPDATE the user's feedback if it exists, or insert if new.
        # But since we might have multiple user reports for same message, let's just mark the message as resolved.
        # Simplest way to "hide" it from queue is to INSERT a new row with 'ADMIN_...' 
        # AND (crucially) the queue filter `NOT LIKE "ADMIN%"` won't hide the *user's* row unless we update it.
        
        # Better approach: DELETE the user row(s) for this message and INSERT the Admin Rule.
        # This keeps the table clean and the queue empty.
        
        db.execute('DELETE FROM feedback WHERE message = ?', (message,))
        db.execute(
            'INSERT INTO feedback (message, user_label) VALUES (?, ?)',
            (message, admin_label)
        )
        db.commit()
    
    return redirect(url_for('admin'))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
