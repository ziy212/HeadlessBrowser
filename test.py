from html_parser import calcTwoHTMLDistanceFromFiles
from html_parser import extractScriptFromContents
from html_parser import compare_two_string
import sys

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
