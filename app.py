from flask import Flask, render_template, request, session, redirect, url_for
import pymysql.cursor

app = Flask(__name__)

conn = pymysql.connect()

@app.route('/')
def hello():
	return render_template('index.html')

@app.route('/login')
def login():
	return render_template('login.html')

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
		return render_template('login.html', error=error)

if __name__=='__main__':
	app.run()

