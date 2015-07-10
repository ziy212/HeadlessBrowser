from html_parser import calcTwoHTMLDistanceFromFiles
from html_parser import extractScriptFromContents
from html_parser import compare_two_string
from db_client import storeScripts
from db_client import fetchScripts
from db_client import fetchURLContents
from db_client import findAverageContents
import sys

def extractAndStoreScriptsFromFileList(file_list_path):
  f = open(file_list_path)
  urls = set()
  for line in f:
    urls.add(line.strip())

  for url in urls:
    print "prcossing scripts of %s " % url
    hosts, inlines = fetchScriptsFromDB(url)
    if hosts == None or inlines == None:
      contents = fetchURLContents(url)
      if contents == None or len(contents) == 0:
        print >> sys.stderr, "%s doesn't have contents " %url
        continue
      content = findAverageContents(contents)
      if content == None:
        print >> sys.stderr, "failed to extract average content for %s" %url
        continue
      extractAndStoreScriptsFromDOM(url, content)

    else:
      print "%s already has %d hosts and %d inline scripts " \
        %(url, len(hosts), len(inlines))   

def fetchScriptsFromDB(url):
  hosts, inlines = fetchScripts(url)
  return hosts, inlines

def extractAndStoreScriptsFromDOM(url, dom):
  hostset, contset = extractScriptFromContents(dom)
  host_list = []
  cont_list = []
  for item in hostset:
    try:
      new_item = item.encode('utf-8')
      host_list.append(new_item)
    except Exception as e:
      print "Exception in decoding: "+str(e)
      host_list.append(item)

  for item in contset:
    try:
      new_item = item.encode('utf-8')
      cont_list.append(new_item)
    except Exception as e:
      print "Exception in decoding: "+str(e)
      cont_list.append(item)
  print "extracted %d script hosts and %d inline scripts for %s " \
    %(len(host_list), len(cont_list), url)

  #for item in cont_list:
  #  print "content: %s" %item
  #print "storing scripts to DB"
  if storeScripts(url, host_list, cont_list):
    print "successfully store %s scripts to DB " %url
  else:
    print "failed to store %s scripts to DB " % url

def fetchAndDisplayScriptsFromDB(url):
  hosts, inlines = fetchScripts(url)
  if hosts == None or inlines == None:
    print "%s has no scripts: " %url
    return 
  for host in hosts:
    print host
  for inline in inlines:
    print inline
  print len(inlines)

def main():
  #contents = open(sys.argv[1]).read()
  #extractAndStoreScriptsFromDOM("http://www.cnn.com/", contents )
  #fetchAndDisplayScriptsFromDB("http://www.cnn.com/")
  extractAndStoreScriptsFromFileList(sys.argv[1])

if __name__ == "__main__":
  main()

'''
#print calcTwoHTMLDistanceFromFiles(sys.argv[1],sys.argv[2])
content1 = open(sys.argv[1]).read()
content2 = open(sys.argv[2]).read()
hostset1, contset1 = extractScriptFromContents(content1)
hostset2, contset2 = extractScriptFromContents(content2)

inter = hostset1.intersection(hostset2)
print len(inter)

diffc1 = []
for c1 in contset1:
  c1.replace('\n','\t')
  print "C1:%s" % c1
  good = False
  for c2 in contset2:
    if compare_two_string(c1, c2):
      good = True
      break
  if not good:
    diffc1.append(c1)

diffc2 = []
for c2 in contset2: 
  good = False
  c2.replace('\n','\t')
  print "C2:%s" % c2
  for c1 in contset1:
    if compare_two_string(c1, c2):
      good = True
      break
  if not good:
    diffc2.append(c2)

print len(diffc1),len(diffc2)
for item in diffc1:
  item.replace('\n','\t')
  print "DIFFC1: "+item

for item in diffc2:
  item.replace('\n','\t')
  print "DIFFC2: "+item
print "%d %d vs %d %d" %(len(hostset1), len(contset1), len(hostset2), len(contset2))
'''