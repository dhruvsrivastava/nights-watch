from flask import Flask
from flask import render_template , redirect , url_for
from flask import request , g
from flask import session , escape
from functools import wraps
import subprocess
import mongo_db
import time
import redis
from rq import Queue
import perform_task

app = Flask(__name__)
app.redis = redis.StrictRedis(host = 'localhost' , port = 6379 , db = 0)
app.secret_key = 'secret_session_key'

#redis-queue to process tasks
q = Queue(connection = redis.StrictRedis())

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

@app.route('/api/enqueue')
def enqueue():
	job = q.enqueue(perform_task.special_task)
	return '<h1> Task processed with ID %s </h1>' %(job.id)

@app.route('/api/active')
def active():
	jobs = q.jobs
	queued_job_ids = q.job_ids # Gets a list of job IDs from the queue
	print "number of jobs %d" %(len(q.jobs))
	res = []
	for job in jobs:
		res.append( (job.id , job.status) )
	return render_template('active.html' , res = res)


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

		job = q.enqueue(perform_task.handle_everything , args = (runID , code , language , problem))
		return '<h1> Task processed with ID %s </h1>' %(job.id)
	return '<h1> POST request required </h1>'

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