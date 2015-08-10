from flask import render_template, request, Flask
#from app import app (make sure this is commented out)

app = Flask(__name__)

# code goes here

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000,debug=True)
