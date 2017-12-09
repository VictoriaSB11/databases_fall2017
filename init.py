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

@app.route('/password')
def password():
	return render_template('password.html')

@app.route('/forgotPassword', methods=['GET','POST'])
def forgotPassword():
	#grab infor from the reset password form
	username = request.form['username']
	newpass = request.form['password1']
	confirmpass = request.form['password2']

	cursor = conn.cursor()

	query = 'SELECT * FROM Person WHERE username=%s'
	cursor.execute(query, (username))
	data = cursor.fetchone()
	cursor.close()

	error = None
	message = not None

	if newpass != confirmpass:
		error = 'The passwords do not match'
		return render_template('password.html', error=error)
	else:
		newpass_hex = sha1(newpass).hexdigest()
		confirmpass_hex = sha1(confirmpass).hexdigest()

		cursor = conn.cursor()
		update = 'UPDATE Person SET password = %s WHERE username = %s'
		cursor.execute(update, (newpass_hex, username))
		conn.commit()

		query = 'SELECT * FROM person WHERE username = %s AND password = %s'
		cursor.execute(query, (username, newpass))

		new_data = cursor.fetchone()
		print(new_data)
		message = "Password successfully changed, you are logged back in!"
		cursor.close()
		return render_template('index.html')

@app.route('/home')
def home():
	username = session['username']
	cursor = conn.cursor();
	query1 = 'SELECT id, username, content_name, file_path, timest\
	FROM content WHERE username = %s || public = %s || id in \
	(SELECT id FROM Share, Member WHERE Share.group_name = Member.group_name  && Member.username = %s) ORDER BY timest DESC'
	cursor.execute(query1, (username, True, username))

	query2 = 'SELECT timest, content_name, file_path FROM Content WHERE username = %s && public = 1 ORDER BY timest DESC'
	cursor.execute(query2, (username))
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
	query = 'INSERT INTO Content(username, file_path, content_name, public) VALUES(%s, %s, %s, %s,%s)'
	cursor.execute(query, (username, file_path, content_name, public))
	conn.commit()
	cursor.close()
	return redirect(url_for('home'))

@app.route('/friends')
def friends():
	username = session['username']
	cursor = conn.cursor();
	query = 'SELECT DISTINCT group_name, username_creator FROM member WHERE username = %s OR username_creator = %s'
	cursor.execute(query, (username, username))
	data = cursor.fetchall()
	cursor.close()
	return render_template('friends.html', username=username, groups=data)

@app.route('/addFriend')
def addFriend():
	username = session['username']
	cursor = conn.cursor();
	query = 'SELECT DISTINCT group_name FROM FriendGroup WHERE username = %s'
	cursor.execute(query, (username))
	data = cursor.fetchall()
	cursor.close()
	return render_template('addFriend.html', username=username, groups=data)

@app.route('/addFriendtoGroup', methods=['GET','POST'])
def addFriendtoGroup():
	username = session['username']
	selectedGroup = request.form.get('select_group')
	memFirst = request.form['memfname']
	memLast = request.form['memlname']
	memUsername = request.form['memUsername']
	cursor = conn.cursor();

	#check that there is one person with this name
	queryFindMemUsername = "SELECT username FROM Person	WHERE first_name = %s AND last_name = %s"
	cursor.execute(queryFindMemUsername, (memFirst, memLast))
	friendUsername = cursor.fetchall()

	if( friendUsername > 1):
		error = "More than one person with that name: %s. Please provide the username as well" % (friendUsername)
		return redirect(url_for('addFriend', error=error))

	queryAlreadyInGroup = "SELECT * FROM member WHERE username = %s AND group_name = %s"
	cursor.execute(queryAlreadyInGroup, (friendUsername, selectedGroup))
	data = cursor.fetchall()

	if(data):
		error = "This person is already in the group"
		return redirect(url_for('addFriend', error=error))

	if(memUsername):
		queryAddFriend = "INSERT INTO Member(username, group_name, username_creator) VALUES(%s, %s, %s)"
		cursor.execute(queryAddFriend, (memUsername, selectedGroup, username))
		conn.commit()
		cursor.close()
		return redirect(url_for('addFriend'))

	else:
		queryAddFriend = "INSERT INTO Member(username, group_name, username_creator) VALUES(%s, %s, %s)"
		cursor.execute(queryAddFriend, (friendUsername, selectedGroup, username))
		conn.commit()
		cursor.close()
		return redirect(url_for('addFriend'))


@app.route('/tagandshare')
def tagandshare():
	username=session['username']
	cursor = conn.cursor();
	query2 = 'SELECT timest, content_name, file_path FROM Content WHERE username = %s ORDER BY timest DESC'
	cursor.execute(query2, (username))
	data1 = cursor.fetchall()
	query = 'SELECT group_name FROM member WHERE username = %s'
	cursor.execute(query, (username))
	data2 = cursor.fetchall()
	cursor.close()
	return render_template('tagandshare.html', username=username, posts=data1, groups=data2,sel=1)



@app.route('/addFriendGroup', methods=['GET','POST'])
def addFriendGroup():
	username = session['username']
	cursor = conn.cursor();
	friendGroupName = request.form['groupName']
	mFirstName = request.form['memfname']
	mLastName = request.form['memlname']
	
	queryFindMemUsername = "SELECT username FROM Person	WHERE first_name = %s AND last_name = %s"
	cursor.execute(queryFindMemUsername, (mFirstName, mLastName))
	memUsername = cursor.fetchone().get('username')
	 
	#create freind group only after we have ensured that 
	#person we want to create the group with exists 
	queryFG = "INSERT INTO FriendGroup (group_name, username) VALUES(%s, %s)"
	cursor.execute(queryFG, (friendGroupName, username))
	#add yourself as member

	queryMeAsMem = "INSERT INTO Member (username, group_name, username_creator) VALUES(%s, %s, %s)"
	cursor.execute(queryMeAsMem, (username, friendGroupName, username))
	#add other person as member
	queryAddMember = "INSERT INTO Member (username, group_name, username_creator) VALUES(%s, %s, %s)"
	cursor.execute(queryAddMember, (memUsername, friendGroupName, username))
	conn.commit()
	cursor.close()
	return redirect(url_for('friends'))

@app.route('/parties')
def parties():
	username = session['username']
	cursor = conn.cursor();
	query = 'SELECT DISTINCT party.party_name, username_host, datetime, going FROM invites JOIN party ON invites.party_name = party.party_name WHERE invites.username = %s OR username_host = %s'
	cursor.execute(query, (username, username))
	data = cursor.fetchall()
	cursor.close()
	return render_template('parties.html', username=username, parties=data)

@app.route('/createParty', methods=['GET','POST'])
def createParty():
	username = session['username']
	cursor = conn.cursor();
	partyName = request.form['partyName']
	partyLocation = request.form['partyLocation']
	partyDatetime = request.form['partyDatetime']
	partyDescription = request.form['partyDescription']
	 
	queryNewParty = "INSERT INTO Party (party_name, username, description, datetime, location) VALUES(%s, %s, %s, %s, %s)"
	cursor.execute(queryNewParty, (partyName, username, partyDescription, partyDatetime, partyLocation))
	
	queryMeAsHost = "INSERT INTO Invites (username, party_name, username_host, going) VALUES(%s, %s, %s, %s)"
	cursor.execute(queryMeAsHost, (username, partyName, username, True))

	queryPeople = "SELECT username, first_name, last_name FROM Person"
	cursor.execute(queryPeople)
	dataPeople = cursor.fetchall()

	conn.commit()
	cursor.close()
	return redirect(url_for('parties'))

@app.route('/invite')
def invite():
	username = session['username']
	cursor = conn.cursor();

	queryMyParties = "SELECT party_name FROM Party WHERE username = %s"
	cursor.execute(queryMyParties, (username))
	data = cursor.fetchall()

	conn.commit()
	cursor.close()
	return render_template('invite.html', parties=data)

@app.route('/invitePeople', methods=['GET','POST'])
def invitePeople():
	username = session['username']
	selectedParty = request.form.get('select_party')
	inviteeFirst = request.form['invfname']
	inviteeLast = request.form['invlname']
	cursor = conn.cursor();

	#ensure person exists and get their username
	queryFindMemUsername = "SELECT username FROM Person	WHERE first_name = %s AND last_name = %s"
	cursor.execute(queryFindMemUsername, (inviteeFirst, inviteeLast))
	inviteeUsername = cursor.fetchone().get('username')

	queryAlreadyInvited = "SELECT * FROM Invites WHERE username = %s AND party_name = %s"
	cursor.execute(queryAlreadyInvited, (inviteeUsername, selectedParty))
	data = cursor.fetchall()

	if(data):
		error = "This person was already invited"
		return redirect(url_for('invite', error=error))
	else:
		querySendInvite = "INSERT INTO Invites(username, party_name, username_host, going) VALUES(%s, %s, %s, %s)"
		cursor.execute(querySendInvite, (inviteeUsername, selectedParty, username, False))
		conn.commit()
		cursor.close()
		return redirect(url_for('invite'))

@app.route('/viewInvites')
def viewInvites():
	username = session['username']
	cursor = conn.cursor();

	queryPartyGoing = "SELECT username_host, Party.party_name, description, location, going, datetime FROM Invites JOIN Party ON Invites.party_name = Party.party_name WHERE Invites.username = %s AND going = %s"
	cursor.execute(queryPartyGoing, (username, True))
	goingData = cursor.fetchall()

	queryPartyNotGoing = "SELECT username_host, Party.party_name, description, location, going, datetime FROM Invites JOIN Party ON Invites.party_name = Party.party_name WHERE Invites.username = %s AND going = %s"
	cursor.execute(queryPartyNotGoing, (username, False))
	notGoingData = cursor.fetchall()

	conn.commit()
	cursor.close()
	return render_template('rsvp.html', going=goingData, notGoing=notGoingData)

@app.route('/rsvp', methods=['GET','POST'])
def rsvp():
	username = session['username']
	selectedParty = request.form.get('select_party')
	cursor = conn.cursor();

	#ensure person exists and get their username
	queryUpdateRSVP = "UPDATE Invites SET going = %s WHERE username = %s AND party_name = %s"
	cursor.execute(queryUpdateRSVP, (True, username, selectedParty))
	conn.commit()
	cursor.close()
	return redirect(url_for('rsvp'))

@app.route('/unrsvp', methods=['GET','POST'])
def unrsvp():
	username = session['username']
	selectedParty = request.form.get('select_party')
	cursor = conn.cursor();

	#ensure person exists and get their username
	queryUpdateRSVP = "UPDATE Invites SET going = %s WHERE username = %s AND party_name = %s"
	cursor.execute(queryUpdateRSVP, (False, username, selectedParty))
	conn.commit()
	cursor.close()
	return redirect(url_for('rsvp'))

@app.route('/profile')
def backProfile():
	return render_template('index.html', message=not None)

@app.route('/logout')
def logout():
	session['username'] = ''
	return render_template('index.html')

app.static_folder = 'static'
app.secret_key = 'secret key 123'
#Run the app on local host port 5000
if __name__=='__main__':
	app.run('127.0.0.1',5000,debug=True)

