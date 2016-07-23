import time
import subprocess

def special_task():
	time.sleep(20)

def evaluateCode(problem , runID , language , ext):
	time.sleep(20)
	inpfile = "input/" + problem + ".txt"
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
		start = time.time()
		try:
			subprocess.call('timeout 1s python ' + filename + ' < ' + inpfile + ' > ' + outfile , shell = True)
		except subprocess.CalledProcessError , e:
			print e
			return
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

def handle_everything(runID , code , language , problem):
	ret = generate_user_output(runID , code , language , problem)
	print ret
	response = {}
	if ret is not None:
		response['verdict'] = 'Compilation Error'
		return 
	f1 = open("output/" + str(runID) + ".txt" , "r")
	f2 = open("output/" + problem + ".txt" , "r")
	print "user output"
	v1 =  f1.read()
	v2 = f2.read()
	print v1
	print "V2" 
	print v2
	if v1 == v2:
		# print "equal"
		# print v1
		# print v2
		# return '<h1> Correct Solution </h1>'
		response['verdict'] = 'Correct Answer'
		return
	response['verdict'] = 'Wrong Answer'
	return
