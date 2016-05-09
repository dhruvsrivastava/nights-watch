from flask import Flask
from flask import render_template , redirect , url_for
from flask import request , g
from flask import session , escape
from functools import wraps
import subprocess
import mongo_db
import time


app = Flask(__name__)
app.secret_key = 'secret_session_key'

def verify_user(username , password):
	x = {}
	x['username'] = username
	x['password'] = password
	return mongo_db.check_user(x)

def verify_problem(problem):
	return mongo_db.check_problem(problem)

@app.route('/login' , methods = ['GET' , 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		if verify_user(username , password) == False:
			return render_template('login.html' , error = "Invalid Username or Password")
		session['user'] = request.form['username']
		return redirect(url_for('index'))
	return render_template('login.html' , error = None)

def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		try :
			if session['user'] is None:
				return redirect(url_for('login'))
			return f(*args , **kwargs)
		except KeyError:
			return redirect(url_for('login'))
	return decorated_function


@app.route('/logout')
def logout():
	session.pop('user' , None)
	return redirect(url_for('index'))

@app.route('/test')
@login_required
def test():
	return '<h1>Test here</h1>';

submissions = {}
def limit_submissions(ip):
	if ip in submissions:
		last_submission = submissions[ip];
		if (time.time() - last_submission) < 10:
			print "Invalid Submission"
			return False
	submissions[ip] = time.time()
	return True

@app.route('/problems/<problem>/')
@login_required
def problems(problem):
	# if verify_problem(problem) == False:
	# 	return '<h1> Problem %s does not exist </h1>' %(escape(problem))
	return render_template(problem + '.html' , problem = problem , ip = request.remote_addr)


#process the code that has been submitted
@app.route('/process' , methods = ['GET' , 'POST'])
@login_required
def process():
	if request.method == "POST":
		user = session['user']
		code = request.form['code']
		language = request.form['language']
		problem = request.form['problem']
		ip = request.remote_addr
	return '<h3>%s %s %s %s %s </h3>' %( escape(ip) , escape(user) , escape(code) , escape(language) , escape(problem) )

	#verify such a problem exists
	if verify_problem(problem) == False:
		return '<h1> Problem %s does not exist </h1>' %(escape(problem))
	generate_user_output()
	generate_correct_output()
	verify()

	start = time.time()
	retval = subprocess.call('python sample.py',shell=True);
	if retval != 0:
		try :
			subprocess.check_output('python sample.py', stderr = subprocess.STDOUT,shell=True);
		except subprocess.CalledProcessError, e:
			pass
		return '<h1> Compilation Error </h1>'
	print "time elapsed %f" , (time.time() - start)
	print subprocess.check_output('python sample.py',shell=True)
	if limit_submissions(request.remote_addr) == False:
		return '<h1> One Submission Allowed every 10 seconds %s </h1>' %(escape(request.remote_addr))
	return render_template('child.html' , code = problem , ip = request.remote_addr)


@app.route('/')
def first_page():
	return redirect(url_for('index'))

@app.route('/index')
def index():
	user = None
	try:
		user = session['user']
	except KeyError:
		user = None
	return render_template('index.html' , username = user)  # render a template

if __name__ == '__main__':
	app.run(host = '0.0.0.0' , debug = True)