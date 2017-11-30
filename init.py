#Import flask libraries and mySQL
#!/usr/bin/python
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
from hashlib import sha1
import time

app = Flask(__name__)

#Configure MySQL

conn = pymysql.connect(host='localhost',
					   port=8889,
                       user='root',
                       passwd='password',
                       db='prichosha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)
	

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
	username = request.form['username']
	password = request.form['password']

	cursor = conn.cursor()

	query = 'SELECT * FROM Person WHERE username = %s AND password = %s'
	cursor.execute(query, (username, sha1(password).hexdigest()))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	cursor.close()
	error = None
	if(data):
		#creates a session for the the user
		#session is a built in
		session['username'] = username
		return render_template('index.html',message= not None)
	else:
		#returns an error message to the html page
		error = 'Invalid login or username'
		return render_template('login.html', error=error)

#Register and new user for PriChoSha
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
	#grabs information from the forms
	username = request.form['new_username']
	password = request.form['new_password']
	fname = request.form['fname']
	lname = request.form['lname']

	#cursor used to send queries
	cursor = conn.cursor()
	#executes query
	query = 'SELECT * FROM Person WHERE username = %s'
	cursor.execute(query, (username))
	#stores the results in a variable
	data = cursor.fetchone()
	#use fetchall() if you are expecting more than 1 data row
	error = None
	message=not None

	if(data):
		#If the previous query returns data, then user exists
		error = 'This user already exists'
		return render_template('register.html', error = error)
	else:
		ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s)'
		cursor.execute(ins, (username, sha1(password).hexdigest(), fname, lname))
		conn.commit()
		cursor.close()
		return render_template('index.html', message=message)

@app.route('/home')
def home():
	username = session['username']
	cursor = conn.cursor();
	query = 'SELECT id, username, content_name, file_path, timest\
	FROM content WHERE username = %s || public = %s || id in \
	(SELECT id FROM Share, Member WHERE Share.group_name = Member.group_name  && Member.username = %s) ORDER BY timest DESC'
	cursor.execute(query, (username, True, username))
	data = cursor.fetchall()
	cursor.close()
	return render_template('home.html', username=username, posts=data)

@app.route('/post', methods=['GET', 'POST'])
def post():
	username = session['username']
	cursor = conn.cursor();
	file_path = request.form['image_path']
	content_name = request.form['content_name']
	public=request.form['optradio']
	query = 'INSERT INTO Content(username, file_path, content_name, public) VALUES(%s, %s, %s, %s)'
	cursor.execute(query, (username, file_path, content_name, public))
	conn.commit()
	cursor.close()
	return redirect(url_for('index'))


@app.route('/logout')
def logout():
	session.pop('username')
	return redirect('/')

app.static_folder = 'static'
app.secret_key = 'secret key 123'
#Run the app on local host port 5000
if __name__=='__main__':
	app.run('127.0.0.1',5000,debug=True)

