import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import pickle

# Load Kaggle dataset
data = pd.read_csv("dataset/spam.csv", encoding="latin-1")

# Keep only required columns
data = data[['v1', 'v2']]
data.columns = ['label', 'message']

# Remove empty rows
data.dropna(inplace=True)

# Features & labels
X = data['message']
y = data['label']

# Convert text to numbers
vectorizer = TfidfVectorizer(stop_words='english')
X_vectorized = vectorizer.fit_transform(X)

# Train model
model = MultinomialNB()
model.fit(X_vectorized, y)

# Save model and vectorizer
pickle.dump(model, open("model/spam_model.pkl", "wb"))
pickle.dump(vectorizer, open("model/vectorizer.pkl", "wb"))

print("✅ Model trained successfully using Kaggle SMS Spam dataset!")