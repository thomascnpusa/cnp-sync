from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    print("Home route triggered!")
    return "Hello!"

@app.route('/sync')
def sync():
    print("Sync route triggered!")
    return "Sync works!"
