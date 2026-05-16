import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_score, recall_score, f1_score
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# Model path
MODEL_PATH = 'models/'
os.makedirs(MODEL_PATH, exist_ok=True)

print("=" * 60)
print("TRAINING ISOLATION FOREST")
print("=" * 60)

# Load data
train_df = pd.read_csv('train_data.csv')
test_df = pd.read_csv('test_data.csv')

X_train = train_df.drop('is_fraud', axis=1)
y_train = train_df['is_fraud']
X_test = test_df.drop('is_fraud', axis=1)
y_test = test_df['is_fraud']

# Train Isolation Forest
print("\n📊 Training Isolation Forest...")
iso_forest = IsolationForest(
    contamination=0.05,
    random_state=42,
    n_estimators=100,
    max_samples='auto'
)

iso_forest.fit(X_train)

# Predictions
y_pred_test = iso_forest.predict(X_test)
y_pred_test_binary = (y_pred_test == -1).astype(int)

# Evaluation
print("\n📈 ISOLATION FOREST PERFORMANCE:")
print("\nTest Set Classification Report:")
print(classification_report(y_test, y_pred_test_binary))

roc_auc = roc_auc_score(y_test, y_pred_test_binary)
print(f"\nROC AUC Score: {roc_auc:.4f}")

cm = confusion_matrix(y_test, y_pred_test_binary)
print("\nConfusion Matrix:")
print(cm)

precision = precision_score(y_test, y_pred_test_binary, zero_division=0)
recall = recall_score(y_test, y_pred_test_binary, zero_division=0)
f1 = f1_score(y_test, y_pred_test_binary, zero_division=0)

print(f"\nPrecision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1-Score: {f1:.4f}")

# Save model
joblib.dump(iso_forest, f'{MODEL_PATH}isolation_forest.pkl')
print(f"\n✅ Model saved to {MODEL_PATH}isolation_forest.pkl")

# Plot confusion matrix (saves only, no popup)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.title('Isolation Forest - Confusion Matrix')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.savefig(f'{MODEL_PATH}isolation_forest_cm.png', dpi=150, bbox_inches='tight')
plt.close()

print(f"✅ Confusion matrix saved to {MODEL_PATH}isolation_forest_cm.png")
print("\n✅ Isolation Forest training complete!")