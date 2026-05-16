import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_score, recall_score, f1_score, accuracy_score
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
print("TRAINING XGBOOST")
print("=" * 60)

# Load data
train_df = pd.read_csv('train_data.csv')
test_df = pd.read_csv('test_data.csv')

X_train = train_df.drop('is_fraud', axis=1)
y_train = train_df['is_fraud']
X_test = test_df.drop('is_fraud', axis=1)
y_test = test_df['is_fraud']

print(f"\nTraining samples: {len(X_train)}")
print(f"Test samples: {len(X_test)}")
print(f"Fraud rate in training: {y_train.mean():.4f}")

# Calculate class weights
scale_pos_weight = (len(y_train) - y_train.sum()) / y_train.sum()

# Train XGBoost
print("\n📊 Training XGBoost Classifier...")
xgb_model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    scale_pos_weight=scale_pos_weight,
    random_state=42,
    eval_metric='auc'
)

eval_set = [(X_train, y_train), (X_test, y_test)]
xgb_model.fit(X_train, y_train, eval_set=eval_set, verbose=False)

# Predictions
y_pred = xgb_model.predict(X_test)
y_pred_proba = xgb_model.predict_proba(X_test)[:, 1]

# Evaluation
print("\n📈 XGBOOST PERFORMANCE:")
print("\nTest Set Classification Report:")
print(classification_report(y_test, y_pred))

roc_auc = roc_auc_score(y_test, y_pred_proba)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
accuracy = accuracy_score(y_test, y_pred)

print(f"\nROC AUC Score: {roc_auc:.4f}")
print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1-Score: {f1:.4f}")

cm = confusion_matrix(y_test, y_pred)
print("\nConfusion Matrix:")
print(cm)

# Feature Importance
feature_importance = pd.DataFrame({
    'feature': X_train.columns,
    'importance': xgb_model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n📊 Feature Importance:")
print(feature_importance.head(10))

# Save model
joblib.dump(xgb_model, f'{MODEL_PATH}xgboost_model.pkl')
print(f"\n✅ Model saved to {MODEL_PATH}xgboost_model.pkl")

# Save optimal threshold
optimal_threshold = 0.5
best_f1 = 0
for threshold in np.arange(0.1, 0.9, 0.01):
    preds = (y_pred_proba >= threshold).astype(int)
    f1 = f1_score(y_test, preds)
    if f1 > best_f1:
        best_f1 = f1
        optimal_threshold = threshold

with open(f'{MODEL_PATH}optimal_threshold.txt', 'w') as f:
    f.write(str(optimal_threshold))

print(f"✅ Optimal threshold: {optimal_threshold:.2f}")

# Plot feature importance
plt.figure(figsize=(10, 6))
plt.barh(feature_importance['feature'].head(10), feature_importance['importance'].head(10))
plt.xlabel('Importance')
plt.title('XGBoost - Top 10 Feature Importance')
plt.gca().invert_yaxis()
plt.savefig(f'{MODEL_PATH}xgboost_feature_importance.png', dpi=150, bbox_inches='tight')
plt.close()

print(f"✅ Feature importance plot saved to {MODEL_PATH}xgboost_feature_importance.png")

# Plot confusion matrix
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.title('XGBoost - Confusion Matrix')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.savefig(f'{MODEL_PATH}xgboost_cm.png', dpi=150, bbox_inches='tight')
plt.close()

print(f"✅ Confusion matrix saved to {MODEL_PATH}xgboost_cm.png")
print("\n✅ XGBoost training complete!")