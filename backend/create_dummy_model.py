import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

print("Generating dummy model for testing...")
os.makedirs('model', exist_ok=True)

# Generate dummy features (17 features)
X = np.random.rand(100, 17)
y = np.random.randint(0, 2, 100)

# Train a small Random Forest classifier
model = RandomForestClassifier(n_estimators=10, random_state=42)
model.fit(X, y)

# Save dummy model files
joblib.dump(model, 'model/phishing_model.pkl')
features = [
    'length', 'dot_count', 'hyphen_count', 'slash_count', 'digit_count', 
    'special_char_count', 'has_https', 'has_ip', 'has_at', 'has_double_slash', 
    'has_port', 'entropy', 'has_punycode', 'suspicious_tld', 'subdomain_count', 
    'brand_in_subdomain', 'suspicious_words'
]
joblib.dump(features, 'model/feature_names.pkl')

print("Success! Dummy model saved at model/phishing_model.pkl")
print("You can now run 'python app.py' to start the server.")
