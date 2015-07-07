import json
import urllib2
import urllib
import sys
import base64
import os
import urlparse
from html_parser import calcTwoHTMLDistance
import logging

logger = logging.getLogger('DOMCluster')
hdlr = logging.FileHandler('./cluster.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.addHandler(consoleHandler)
logger.setLevel(logging.DEBUG)

def fetchURLContents(url):
    try:
        host = "http://localhost:4040/api/web-contents/fetch"
        req = urllib2.Request(host)
        req.add_header('Content-Type', 'application/json')

        if url != '*':
            url = urllib.quote_plus(url)
        data = { 'url' : url.strip() }

        response = urllib2.urlopen(req, json.dumps(data))
        rs = json.loads(response.read())
        
        decoded_rs = []
        if rs['success']:
            db_result = json.loads(rs['result'])
            print "get %d items "%(len(db_result))
            for item in db_result:
                decoded = base64.b64decode(item['contents'])
                #print "%s size: %d" %(item['url'],len(decoded))
                decoded_rs.append(decoded)
            return decoded_rs
        else:
            print "failed to fetch contents of url: "+url
            return None

    except Exception as e:
        print str(e)
        return None

def findContentsFromURLList(list):
    for url in list:
        url = url.strip()
        rs = fetchURLContents(url)
        for i in range(len(rs)):
            for j in range(i+1, len(rs)):    
                logger.debug("%s : %f " %(\
                    url, calcTwoHTMLDistance(rs[i],rs[j])) )
#rs = fetchURLContents(sys.argv[1])
#rs = fetchURLContents("*")
findContentsFromURLList(["http://www.google.com"])
'''
o = urlparse.urlparse(sys.argv[1])
dir_name = o.path.replace('/','_')

path = os.path.join('./tmp',dir_name)
if not os.path.exists(path):
    os.makedirs(path)

count = 1
for item in rs:
    file_path = os.path.join(path,'%d.txt'%count)
    f = open(file_path,'w')
    f.write(item+'\n')
    f.close()
    count += 1
'''