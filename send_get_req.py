import urllib2
import urllib
import sys


def sendTask(url, times):
	template = "http://localhost:8081/task?url=%s&times=%d"
	url_par = urllib.quote(url)
	times_par = int(times)
	url = template%(url_par,times_par)
	print url
	response = urllib2.urlopen(url)
	the_page = response.read()
	print the_page

sendTask(sys.argv[1],sys.argv[2])