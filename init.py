#Import falsk libraruies and mySQL
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors

app = Flask(__name__)

#Configure MySQL
# conn = pymysql.connect(host='localhost',
# 						user='root',
# 						password='root',
# 						db='meetup',
# 						charset='utf8mb4',
# 						cursorclass=pymysql.cursors.DictCursor)
	

#Define a route to 'Hello'/the Home page
@app.route('/')
def hello():
	return render_template('index.html')

#Route for the login page
@app.route('/login')
def login():
	return render_template("login.html")

#route for the registration page
@app.route('/register')
def register():
	return render_template('register.html')

#Authenticate the login, check for username and password in db
@app.route('/loginAuth', methods = ['GET', 'POST'])
def loginAuth():
	username = request.form('username')
	password = request.form('password')

	cursor = conn.cursor()

	query = 'SELECT * FROM user WHERE username = %s and password = %s'
	cursor.execute(query, (username, password))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	cursor.close()
	error = None
	if(data):
		#creates a session for the the user
		#session is a built in
		session['username'] = username
		return redirect(url_for('home'))
	else:
		#returns an error message to the html page
		error = 'Invalid login or username'
		return render_template('templates/Login/index.html', error=error)

app.secret_key = 'secret key 123'
#Run the app on local host port 5000
app.secret_key='databases'
if __name__=='__main__':
	app.run('127.0.0.1',5000,debug=True)

