import subprocess

try :
	out = subprocess.check_output('g++ test.cpp' , stderr = subprocess.STDOUT , shell = True)
	out = subprocess.check_output('./a.out' , stderr = subprocess.STDOUT , shell = True)	
	print "out " , out
except subprocess.CalledProcessError as exc:
	print exc
	print exc.output

print "done"