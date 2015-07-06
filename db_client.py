import json
import urllib2
import urllib
import sys
import base64
import os
import urlparse

def fetchURLContents(url):
    try:
        host = "http://localhost:4040/api/web-contents/fetch"
        req = urllib2.Request(host)
        req.add_header('Content-Type', 'application/json')
        url = urllib.quote_plus(url)
        data = { 'url' : url }
        response = urllib2.urlopen(req, json.dumps(data))
        rs = json.loads(response.read())
        decoded_rs = []
        if rs['success']:
            db_result = json.loads(rs['result'])
            print "get %d items "%(len(db_result))
            for item in db_result:
                decoded = base64.b64decode(item['contents'])
                print "size: %d" %(len(decoded))
                decoded_rs.append(decoded)
            return decoded_rs
        else:
            print "failed to fetch contents of url: "+url
            return None

    except Exception as e:
        print str(e)
        return None

rs = fetchURLContents(sys.argv[1])
o = urlparse.urlparse(sys.argv[1])
dir_name = o.path.replace('/','_')
#if dir_name.startswith('_'):
#    dir_name[1] = 'P'
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