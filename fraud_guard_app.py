from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib
matplotlib.use('Agg')  

# App Initialization
app = Flask(__name__)
app.secret_key = 'nivedha'

# SQLAlchemy Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Nivedha%4018@localhost/fraud_guard_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Create DB tables
with app.app_context():
    db.create_all()

# Load ML Model and Dataset
data = pickle.load(open('./model/raw_data.pkl', 'rb'))
model = pickle.load(open('./model/model.pkl', 'rb'))

# Generate dashboard charts
def generate_dashboard_charts(df):
    fraud_count = df[df['class'] == 1].shape[0]
    legal_count = df[df['class'] == 0].shape[0]
    total = len(df)

    fraud_percent = round((fraud_count / total) * 100, 2)
    legal_percent = round((legal_count / total) * 100, 2)

    top_countries_series = df[df['class'] == 1]['country_name'].value_counts().head(5)
    fraud_by_browser = df[df['class'] == 1]['browser'].value_counts()

    img_dir = os.path.join('static', 'images')
    os.makedirs(img_dir, exist_ok=True)

    plt.figure(figsize=(6, 6))
    plt.pie([fraud_percent, legal_percent],
            labels=['Fraud', 'Legal'],
            autopct='%1.1f%%',
            startangle=90,
            colors=["#22d3ee", "#7e3ff4"])
    plt.title('Fraud vs Legal Transactions')
    plt.tight_layout()
    plt.savefig(os.path.join(img_dir, 'fraud_vs_legal_pie_chart.png'))
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.barplot(x=top_countries_series.values, y=top_countries_series.index, palette='crest')
    plt.title('Top 5 Fraud-Prone Countries')
    plt.xlabel('Fraud Transactions')
    plt.tight_layout()
    plt.savefig(os.path.join(img_dir, 'top_fraud_countries_bar_chart.png'))
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.barplot(x=fraud_by_browser.index, y=fraud_by_browser.values, palette='flare')
    plt.title('Fraud Transactions by Browser')
    plt.xlabel('Browser')
    plt.ylabel('Fraud Count')
    plt.tight_layout()
    plt.savefig(os.path.join(img_dir, 'fraud_by_browser_bar_chart.png'))
    plt.close()

    return fraud_count, legal_count

# ---------------- Routes ----------------

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    prediction = session.pop('prediction', None)
    risk_score = session.pop('risk_score', None)
    transaction_id = session.pop('transaction_id', None)

    return render_template(
        'index.html',
        prediction=prediction,
        risk_score=risk_score,
        transaction_id=transaction_id,
        sources=sorted(data['source'].unique()),
        browsers=sorted(data['browser'].unique()),
        sexs=sorted(data['sex'].unique()),
        country_names=sorted(data['country_name'].unique()),
        signup_day_names=sorted(data['signup_day_name'].unique()),
        purchase_day_names=sorted(data['purchase_day_name'].unique())
    )

@app.route('/predict', methods=['POST'])
def predict():
    form = request.form

    query = pd.DataFrame([[form['source'], form['browser'], form['sex'], int(form['age']),
        form['country_name'], int(form['n_device_occur']),
        int(form['signup_month']), int(form['signup_day']), form['signup_day_name'],
        int(form['purchase_month']), int(form['purchase_day']), form['purchase_day_name'],
        float(form['purchase_over_time'])]],
        columns=['source', 'browser', 'sex', 'age', 'country_name', 'n_device_occur',
        'signup_month', 'signup_day', 'signup_day_name',
        'purchase_month', 'purchase_day', 'purchase_day_name', 'purchase_over_time']
    )

    prediction = int(model.predict(query)[0])
    risk_score = float(model.predict_proba(query)[0][1])

    import uuid
    transaction_id = str(uuid.uuid4())[:8]

    session['prediction'] = prediction
    session['risk_score'] = round(risk_score * 100, 2)
    session['transaction_id'] = transaction_id

    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    df = pd.read_csv("data/fraud_data_de.csv")
    generate_dashboard_charts(df)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    fraud_count = int(df[df['class'] == 1].shape[0])
    legal_count = int(df[df['class'] == 0].shape[0])

    top_countries = df[df['class'] == 1]['country_name'].value_counts().head(5)
    country_labels = [str(label) for label in top_countries.index]
    country_values = [int(value) for value in top_countries.values]

    browser_counts = df[df['class'] == 1]['browser'].value_counts()
    browser_labels = [str(label) for label in browser_counts.index]
    browser_values = [int(value) for value in browser_counts.values]

    total = fraud_count + legal_count
    fraud_percent = float(round((fraud_count / total) * 100, 2))
    legal_percent = float(round((legal_count / total) * 100, 2))

    df['signup_time'] = pd.to_datetime(df['signup_time'])
    df['signup_hour'] = df['signup_time'].dt.hour

    fraud_by_hour = df[df['class'] == 1]['signup_hour'].value_counts().sort_index()
    signup_hour_labels = [str(h) for h in fraud_by_hour.index]
    signup_hour_values = fraud_by_hour.values.tolist()

    return render_template("dashboard.html",
        fraud_count=fraud_count,
        legal_count=legal_count,
        country_labels=country_labels,
        country_values=country_values,
        browser_labels=browser_labels,
        browser_values=browser_values,
        signup_hour_labels=signup_hour_labels,
        signup_hour_values=signup_hour_values,
        fraud_percent=fraud_percent,
        legal_percent=legal_percent
    )

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if password != confirm:
            return render_template("register.html", error="Passwords do not match")

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return render_template("register.html", error="Username or email already exists")

        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    generate_dashboard_charts(data)
    app.run(debug=True, port=5000)
