import uuid
import random
import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

class TransactionGenerator:
    """Generates realistic financial transactions with fraud patterns"""
    
    MERCHANT_CATEGORIES = {
        'Grocery': 0.30,
        'Restaurant': 0.20,
        'Retail': 0.15,
        'Gas': 0.10,
        'Healthcare': 0.08,
        'Travel': 0.05,
        'Electronics': 0.04,
        'Entertainment': 0.03,
        'Online Shopping': 0.03,
        'Other': 0.02
    }
    
    AMOUNT_RANGES = {
        'Grocery': (5, 300, 75),
        'Restaurant': (10, 200, 45),
        'Retail': (15, 500, 80),
        'Gas': (10, 80, 35),
        'Healthcare': (20, 1000, 150),
        'Travel': (100, 5000, 500),
        'Electronics': (50, 3000, 300),
        'Entertainment': (10, 150, 40),
        'Online Shopping': (10, 500, 60),
        'Other': (5, 1000, 100)
    }
    
    def __init__(self, fraud_rate=0.05, start_date=None, end_date=None):
        self.fraud_rate = fraud_rate
        self.start_date = start_date or datetime.now() - timedelta(days=30)
        self.end_date = end_date or datetime.now()
        self.users = self._generate_users(500)
        
    def _generate_users(self, num_users):
        users = []
        for _ in range(num_users):
            user = {
                'user_id': uuid.uuid4(),
                'email': fake.email(),
                'phone': fake.phone_number(),
                'address': fake.street_address(),
                'city': fake.city(),
                'state': fake.state_abbr(),
                'zip_code': fake.zipcode(),
                'country': 'USA',
                'home_lat': float(fake.latitude()),
                'home_lon': float(fake.longitude())
            }
            users.append(user)
        return users
    
    def _generate_normal_transaction(self, user, timestamp):
        categories = list(self.MERCHANT_CATEGORIES.keys())
        weights = list(self.MERCHANT_CATEGORIES.values())
        category = random.choices(categories, weights=weights)[0]
        
        min_amt, max_amt, typical = self.AMOUNT_RANGES[category]
        amount = np.random.lognormal(mean=np.log(typical), sigma=0.5)
        amount = min(max(amount, min_amt), max_amt)
        amount = round(amount, 2)
        
        lat = user['home_lat'] + random.uniform(-0.1, 0.1)
        lon = user['home_lon'] + random.uniform(-0.1, 0.1)
        
        return {
            'transaction_id': uuid.uuid4(),
            'user_id': user['user_id'],
            'timestamp': timestamp,
            'amount': amount,
            'currency': 'USD',
            'card_number': fake.credit_card_number(),
            'card_provider': fake.credit_card_provider(),
            'merchant_name': fake.company(),
            'merchant_category': category,
            'merchant_city': fake.city(),
            'merchant_state': fake.state_abbr(),
            'merchant_country': 'USA',
            'latitude': lat,
            'longitude': lon,
            'device_id': fake.uuid4(),
            'ip_address': fake.ipv4(),
            'is_fraud': False,
            'fraud_type': None
        }
    
    def _apply_fraud_patterns(self, transaction, user):
        fraud_types = ['structuring', 'velocity', 'location_mismatch', 'amount_anomaly', 'off_hours']
        fraud_type = random.choice(fraud_types)
        
        fraud_txn = transaction.copy()
        fraud_txn['is_fraud'] = True
        fraud_txn['fraud_type'] = fraud_type
        
        if fraud_type == 'structuring':
            fraud_txn['amount'] = round(random.uniform(9500, 9999), 2)
            fraud_txn['merchant_category'] = 'Other'
            
        elif fraud_type == 'velocity':
            fraud_txn['amount'] = round(random.uniform(10, 500), 2)
            
        elif fraud_type == 'location_mismatch':
            fraud_txn['latitude'] = user['home_lat'] + random.uniform(10, 50)
            fraud_txn['longitude'] = user['home_lon'] + random.uniform(10, 50)
            fraud_txn['merchant_state'] = random.choice(['CA', 'NY', 'TX', 'FL'])
            fraud_txn['merchant_country'] = random.choice(['CAN', 'MEX', 'GBR'])
            
        elif fraud_type == 'amount_anomaly':
            _, _, typical = self.AMOUNT_RANGES[fraud_txn['merchant_category']]
            fraud_txn['amount'] = round(typical * random.uniform(8, 15), 2)
            
        elif fraud_type == 'off_hours':
            hour = random.choice([1, 2, 3, 4, 5])
            fraud_txn['timestamp'] = fraud_txn['timestamp'].replace(hour=hour, minute=random.randint(0, 59))
        
        return fraud_txn, fraud_type
    
    def generate_transactions(self, num_transactions):
        transactions = []
        fraud_count = 0
        target_fraud = int(num_transactions * self.fraud_rate)
        
        with tqdm(total=num_transactions, desc="Generating transactions") as pbar:
            for i in range(num_transactions):
                user = random.choice(self.users)
                days_offset = random.expovariate(0.1)
                timestamp = self.end_date - timedelta(days=min(days_offset, 30))
                transaction = self._generate_normal_transaction(user, timestamp)
                
                if fraud_count < target_fraud and random.random() < 0.5:
                    transaction, applied_fraud = self._apply_fraud_patterns(transaction, user)
                    if applied_fraud:
                        fraud_count += 1
                
                transaction['is_weekend'] = transaction['timestamp'].weekday() >= 5
                transaction['hour_of_day'] = transaction['timestamp'].hour
                transaction['is_foreign_transaction'] = transaction.get('merchant_country', 'USA') != 'USA'
                
                transactions.append(transaction)
                pbar.update(1)
        
        df = pd.DataFrame(transactions)
        
        print(f"\n✅ Generated {len(df)} transactions")
        print(f"💰 Fraud transactions: {fraud_count} ({100*fraud_count/num_transactions:.2f}%)")
        
        if fraud_count > 0:
            print("\n📊 Fraud type distribution:")
            fraud_counts = df[df['is_fraud']]['fraud_type'].value_counts()
            for fraud_type, count in fraud_counts.items():
                print(f"  - {fraud_type}: {count} ({100*count/fraud_count:.1f}%)")
        
        return df

if __name__ == "__main__":
    print("=" * 50)
    print("PHASE 1: DATA GENERATION")
    print("=" * 50)
    
    generator = TransactionGenerator(fraud_rate=0.05)
    df = generator.generate_transactions(10000)
    
    df.to_csv('transactions_raw.csv', index=False)
    print(f"\n💾 Data saved to: transactions_raw.csv")
    print(f"📋 Columns: {list(df.columns)}")