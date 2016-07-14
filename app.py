from flask import Flask
from flask import render_template , redirect , url_for
from flask import request , g
from flask import session , escape
from functools import wraps
import subprocess
import mongo_db
import time
import redis


app = Flask(__name__)
app.redis = redis.StrictRedis(host = 'localhost' , port = 6379 , db = 0)
app.secret_key = 'secret_session_key'

def verify_user(username , password):
	x = {}
	x['username'] = username
	x['password'] = password
	return mongo_db.check_user(x)

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
	print "request from " , ip , " at " , time.time()
	key = app.redis.get(ip)
	if key is not None:
		print "redis.ttl " , app.redis.ttl(ip)
		return False
	print "setting key " , ip
	app.redis.set(ip , 1)
	print app.redis.get(ip)
	app.redis.expire(ip , 20)
	return True

#All problems must have <problem> key set in redis hash judge
@app.route('/problems/<problem>/')
@login_required
def problems(problem):
	if app.redis.hget('judge' , problem) is None:
		return '<h1> Problem does not exist </h1>'
	return render_template('problem.html' , problem = problem , ip = request.remote_addr)

def evaluateCode(problem , runID , language , ext):
	inpfile = "input/" + problem + ext
	outfile = "output/" + str(runID) + ".txt"
	print "creating outfile " , outfile
	if language == "C++":
		filename = "submissions/" + str(runID) + ".cpp"
		try :
			subprocess.check_output('g++ ' + filename, stderr = subprocess.STDOUT , shell=True);
		except subprocess.CalledProcessError, e:
			return (-1 , e.output)
		retval = subprocess.call('g++ ' + filename , shell = True)
		subprocess.call('timeout 1s ./a.out < ' + inpfile + ' > ' + outfile , shell = True)
	elif language == "C":
		filename = "submissions/" + str(runID) + ".c"
		try :
			subprocess.check_output('gcc ' + filename, stderr = subprocess.STDOUT , shell=True);
		except subprocess.CalledProcessError, e:
			return (-1 , e.output)
		retval = subprocess.call('gcc ' + filename , shell = True)
		subprocess.call('timeout 1s ./a.out < ' + inpfile + ' > ' + outfile , shell = True)
	elif language == "Python":
		print "running python code"
		filename = "submissions/" + str(runID) + ".py"
		try :
			subprocess.check_output('timeout 1s python ' + filename, stderr = subprocess.STDOUT , shell=True);
		except subprocess.CalledProcessError, e:
			print "error"
			print e.output
			return (-1 , e.output)
		start = time.time()
		retval = subprocess.call('timeout 1s python ' + filename + ' < ' + inpfile + ' > ' + outfile , shell = True)
		print "Execution time " , time.time() - start
	return None

def generate_user_output(runID , code , language , problem):
	#generate user code identified by runID
	ext = ""
	if language == "Python":
		ext = ".py"
	elif language == "C++":
		ext = ".cpp"
	elif language == "C":
		ext = ".c"
	print "Creating " + "submissions/" + str(runID) + ext
	f = open("submissions/" + str(runID) + ext , "w")
	f.write(code)
	f.close()
	evaluateCode(problem , runID , language , ext)
	return


#process the code that has been submitted
@app.route('/process' , methods = ['GET' , 'POST'])
@login_required
def process():
	if request.method == "POST":
		
		if limit_submissions(request.remote_addr) == False:
			return '<h1> One Submission Allowed every 10 seconds %s </h1>' %(escape(request.remote_addr))
		
		user = session['user']
		code = request.form['code']
		language = request.form['language']
		problem = request.form['problem']
		ip = request.remote_addr
		
		# return '<h3>%s %s %s %s %s </h3>' %( escape(ip) , escape(user) , escape(code) , escape(language) , escape(problem) )

		#verify such a problem exists
		if app.redis.hget('judge' , problem) is None:
			return '<h1> Problem %s does not exist </h1>' %(escape(problem))
		
		runID = app.redis.hget('judge' , 'runID')
		app.redis.hincrby('judge' , 'runID' , 1)

		ret = generate_user_output(runID , code , language , problem)
		print ret
		if ret is not None:
			return '<h1> Compilation Error </h1>'
		f1 = open("output/" + str(runID) + ".txt" , "r")
		f2 = open("output/" + problem + ".txt" , "r")
		print "user output"
		v1 =  f1.read()
		v2 = f2.read()
		print v1
		print "V2" 
		print v2
		if v1 == v2:
			print "equal"
			print v1
			print v2
			return '<h1> Correct Solution </h1>'
		return '<h1> Incorrect Solution </h1>'

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

def init():
	app.redis.hset('judge' , 'intest' , 1)
	app.redis.hset('judge' , 'runID' , 0)

if __name__ == '__main__':
	init()
	app.run(host = '0.0.0.0' , debug = True)
	
	# start = time.time()
	# try:
	# 	retval = subprocess.call('python sample.py',shell=True);
	# except subprocess.CalledProcessError , e:
	# 	pass
	# print "retval " , retval
	# if retval != 0:
	# 	try :
	# 		subprocess.check_output('python sample.py', stderr = subprocess.STDOUT,shell=True);
	# 	except subprocess.CalledProcessError, e:
	# 		print "this %s" , e.output
	# 	# print '<h1> Compilation Error </h1>'
	# print "time elapsed %f" , (time.time() - start)
	# 