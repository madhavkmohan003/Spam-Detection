# AI-Driven Spam Detection System

An intelligent web-based application that detects spam messages using Machine Learning.
Built using **Python, Flask, and Scikit-learn**, this system classifies messages as **Spam or Not Spam** with additional insights like probability, keywords, and feedback analysis.

---

## Features

*  Spam / Not Spam Classification
*  Prediction Probability (%)
*  Keyword Detection (Explainability)
*  URL Risk Analysis
*  User Feedback System
*  Admin Dashboard for Validation
*  Message History Tracking
*  Statistics Dashboard
*  Dark Mode UI

---

## Tech Stack

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Flask (Python)
* **Machine Learning:** Scikit-learn
* **Database:** SQLite
* **Libraries:** Pandas, NumPy

---

## Project Structure

```
SpamDetection/
│
├── dataset/
│   └── spam.csv
│
├── model/
│   ├── spam_model.pkl
│   └── vectorizer.pkl
│
├── static/
│   └── style.css
│
├── templates/
│   ├── index.html
│   ├── admin.html
│   └── login.html
│
├── app.py
├── train_model.py
├── requirements.txt
└── README.md
```

---

## Installation & Setup

### 1️⃣ Clone the Repository

```
git clone https://github.com/your-username/spam-detection.git
cd spam-detection
```

### 2️⃣ Install Dependencies

```
pip install -r requirements.txt
```

### 3️⃣ Train the Model

```
python train_model.py
```

### 4️⃣ Run the Application

```
python app.py
```

### 5️⃣ Open in Browser

```
http://127.0.0.1:5000
```

---

## How It Works

1. User enters a message
2. Message is processed and vectorized
3. ML model predicts spam or not spam
4. System displays:

   * Prediction
   * Probability
   * Keywords
   * URL risk analysis
5. Data is stored in the database
6. User can provide feedback
7. Admin validates feedback

---

## Admin Access

* Access Admin Panel: `/admin`
* Login credentials (default):

```
Username: admin
Password: 1234
```

---

## Example Spam Messages

```
URGENT: Your bank account will be blocked. Verify immediately!
```

```
Congratulations! You have won ₹50,000. Claim now!
```

---

## Future Enhancements

* Deep Learning models (LSTM / NLP transformers)
* Real-time API integration
* Mobile app version
* Multilingual spam detection

---

## Contribution

Feel free to fork this repository and improve the project.
Pull requests are welcome!

---

## License

This project is for educational purposes.

---

## Author

**Madhav K Mohan**
B.Tech CSE (AI & ML)
SRM Institute of Science and Technology

---
