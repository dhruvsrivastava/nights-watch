from pymongo import MongoClient

def insert_user(db , x):
	complex_data = {
		"username" : x['username'],
		"password" : x['password']
	}
	db.users.insert(complex_data)

def get_db():
	client = MongoClient('localhost:27017')
	#create database codes if it does not exist
	db = client.judge
	return db

def printAll():
	print "all"
	db = get_db()
	data = db.users.find()
	for entry in data:
		print entry

def check(db , x):
	print "finding" 
	print x
	printAll
	data = db.users.find_one(x)
	print data
	if data is None:
		return False
	return True

def query(db):
	cursor = db.users.find()
	for document in cursor:
		print document

def check_user(x):
	print x
	db = get_db()
	return check(db , x)

def check_problem(x):
	db = get_db()
	data = db.problems.find_one( {"code" : x})
	if data is None:
		return False
	return True


def main():
	x = {}
	x['username'] = "gaurav"
	x['password'] = "sharma"
	db = get_db()
	printAll()
	# print check(db , x)
	# insert_user(db , x)
	# query(db)

if __name__ == "__main__":
	main()
