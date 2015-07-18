from html_parser import calcTwoHTMLDistanceFromFiles
from html_parser import extractScriptFromContents
from html_parser import compare_two_string
from db_client import storeScripts
from db_client import fetchScripts
from db_client import fetchURLContents
from db_client import findAverageContents
from ASTAnalyzer import analyzeJSCodes
from ASTAnalyzer import analyzeJSCodesFinerBlock
from ASTAnalyzer import analyzeJSON
from ASTAnalyzer import ASTOutputNode
from base64 import b64encode
from base64 import b64decode
import sys, os, re
import hashlib

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
  print "receive %d inlines " % (len(inlines)) 

  for inline in inlines:
    rs = analyzeJSCodes(inline)
    if rs == None:
      rs = analyzeJSON(inline)
    if rs == None:
      continue
    #for item in rs:
    #  print item,
    print len(rs)
  #for host in hosts:
  #  print host
  #for inline in inlines:
  #  print inline
  #print len(inlines)

class TemplateTree():
  def __init__(self, nodes, key):
    self.nodes = nodes
    
    if key == None:
      if nodes != None:
        m = hashlib.md5()
        if isinstance(nodes, dict):
          for k in nodes:
            m.update(k)
        elif nodes[0].__class__.__name__ == "ASTOutputNode":
          for node in nodes:
            m.update(node.tag)
        else:
          print "TemplateTree nodes format error: %s %d %d" \
            %(nodes[0].__class__, id(type(nodes[0])), id(ASTOutputNode))
          return None
          
        key = m.hexdigest()
          
    self.key = key
    self.strings = {}
    self.objects = {}
    self.arrays = {}
    self.identifiers = {}

  def get_length(self):
    return len(self.nodes)


def fetchAndProcessScriptsOfURLsFromFile(path,dst_path):
  f = open(path)
  scriptdict = {}
  total_script_blocks = 0
  total_uniq_script_blocks = 0
  for line in f:
    url = line.strip()
    print "process url "+url
    hosts, inlines = fetchScriptsFromDB(url)
    if inlines==None or len(inlines) ==0:
      print "no inlines for "+url
      continue
    for inline in inlines:
      #print "INLINE:%s" % inline
      is_json = False
      #rs = analyzeJSCodes(inline)
      rs, sc = analyzeJSCodesFinerBlock(inline)
      if rs == None:
        rs = analyzeJSON(inline)
        is_json = True
      if rs == None:
        continue
      
      if is_json:
        tree = TemplateTree(seq, None)
        if tree.key in scriptdict:
          scriptdict[tree.key] = [(inline, url, tree, -1)]
        else:
          contents = [x[0] for x in scriptdict[key]]
          if not inline in contents:
            scriptdict[tree.key].append((inline, url, tree, -1))
            total_uniq_script_blocks += 1
        total_script_blocks += 1
      else:
        for index in range(len(rs)):
          total_script_blocks += 1
          seq = rs[index]
          tree = TemplateTree(seq, None)
          key = tree.key
          if not key in scriptdict:
            scriptdict[key] = [(sc[index], url, tree, index)]
            print "  add key  %s" %key
          else:
            contents = [x[0] for x in scriptdict[key]]
            if not sc[index] in contents: 
              scriptdict[key].append((sc[index],url, tree, index))
              print "  item %s has %d unique scripts" %(key, len(scriptdict[key]))
              total_uniq_script_blocks += 1
 
  trees = []
  keys = sorted(scriptdict.keys(), key=lambda k:len(scriptdict[k]))
  for key in keys:
    name = "%d_%s" %(len(scriptdict[key]),key)
    fw = open(os.path.join(dst_path,name), 'w')
    for item in scriptdict[key]:
      fw.write(item[1]+"||"+str(item[3])+"  "+str(item[0])+"\n")
    
    '''
    #make sure all inlines in a template have same sequential size
    cur_len = 0
    seq_length = 0
    consistent = True
    script_list = scriptdict[key]
    for i in range(len(script_list)):
      cur_len = len(script_list[i][2])
      if seq_length == 0:
        seq_length = cur_len
        continue
      if cur_len != seq_length:
        print "WARNING not equal size sequential for %s" % name
        consistent = False
        break
    if not consistent:
      fw.write("Alert!!! not consistent")
      fw.close()
      continue
    if seq_length == 0:
      fw.write("Alert!!! seq length is zero")
      fw.close()
      continue

    if not isinstance(script_list[0][2][0], ASTOutputNode):
      print "the inline is JSON script!"
      fw.write("the inline is JSON script\n")
      fw.close()
      continue
    
    fw.write("start analyzeing values")
    tree = TemplateTree(script_list[0][2], key)
    #iterate tree list and write string/array/object values
    script_length = len(script_list)
    for i in range(seq_length):
      try:
        if not isinstance(script_list[0][2][i], ASTOutputNode):
          print "the inline is JSON script [shouldn't appear]"
          fw.write("the inline is JSON script\n")
          break
        if script_list[0][2][i].tag == "String":
          val = []
          for j in range(script_length):
            val.append(script_list[j][2][i].value)
          encoded_val = [b64encode(x) for x in val]
          #item = 'string%d: %s' %(i, '||'.join(val))
          item = 'string%d: %s' %(i, ','.join(encoded_val))
          fw.write(item+"\n")
          tree.strings[i] = val
        if script_list[0][2][i].tag == "Object":
          rs = analyzeObjectResultHelper(script_list, i)
          for k in rs:
            encoded_val = [b64encode(x) for x in rs[k]]
            fw.write("object%d: %s:%s\n" % (i, k, ','.join(encoded_val)) )
          tree.objects[i] = rs
        if script_list[0][2][i].tag == "Array":
          rs = analyzeArrayResultHelper(script_list, i)
          for k in rs:
            encoded_val = [b64encode(x) for x in rs[k]]
            fw.write("array%d: %s:%s\n" % (i, k, ','.join(encoded_val)) )
          tree.arrays[i] = rs
        if script_list[0][2][i].tag.startswith("Var_"):
          val = []
          for j in range(script_length):
            val.append(script_list[j][2][i].value)
          encoded_val = [b64encode(x) for x in val]
          item = 'identifier%d: %s' %(i, ','.join(encoded_val))
          fw.write(item+"\n")
          tree.identifiers[i] = val
      except Exception as e:
        print "excpetion in analyzing values %d %s " %(i, str(e)) 
    '''
    print "Done writing %d items for file %s " %(len(scriptdict[key]), name)
    tree = scriptdict[key][0][2]
    trees.append(tree)
    
    fw.close()

  trees = sorted(trees, key=lambda x:x.get_length())

  #display trees
  fw = open(os.path.join(dst_path,"trees"), 'w')
  for i in range(len(trees)):
    fw.write( "%.3d: %s\n" %(i, getTreeSeq(trees[i].nodes)))
  fw.close()
  print "generate %d trees for %d scripts uniqe[%d]" \
    %(len(trees), total_script_blocks, total_uniq_script_blocks)
  
  #count = 0
  #for i in range(len(trees)):
  #  for j in range(i+1, len(trees)):
  #    if isSubTree(trees[i], trees[j]):
  #      print "tree %d is a subtree of %d " %(i, j)
  #      count  += 1
  #print "%d subtrees " %count

def getTrees(path):
  f = open(path)
  node_pattern = "(.+)\[(\d+)\]"
  trees = []
  for line in f:
    tree_nodes = []
    try:
      line = line.split(':')[1].strip()
      nodes = line.split()
      for n in nodes:
        m = re.match(node_pattern, n)
        if m == None:
          print "format error in getting tress: %s" %line
          continue
        node = ASTOutputNode(m.group(1))
        node.child_num = int(m.group(2))
        tree_nodes.append(node)
      tree = TemplateTree(tree_nodes, None)
      print "read tree %d with key %s " %(len(trees), tree.key)
      trees.append(tree)
    except Exception as e:
      print "exception in getTrees %s" %(str(e))
  return trees
    
#TemplateTree
def isSubTree(left, right):
  if len(left.nodes) > len(right.nodes):
    tmp = left
    left = right
    right = tmp
  if len(left.nodes) == 0:
    return False
  left_len = len(left.nodes)
  right_len = len(right.nodes)

  if not isinstance(left.nodes[0], ASTOutputNode) or\
    not isinstance(right.nodes[0], ASTOutputNode):
    return False
  
  for i in range(right_len):
    if i + left_len > right_len:
      break
    if (left.nodes[0].tag == right.nodes[i].tag) and \
      (left_len == right.nodes[i].child_num):
      succ = True
      for j in range(left_len):
        if left.nodes[j].tag != right.nodes[i+j].tag:
          succ = False
          break
      if succ:
        return True

  return False

def getTreeSeq(nodes):
  string = ""
  for item in nodes:
    string += '%s[%d] ' % (item.tag, item.child_num)
  return string

#script_list: [(script, url, node_list)]
#return {key: [val]}
def analyzeObjectResultHelper(script_list, index):
  script_len = len(script_list)
  rs = {}
  for i in range(script_len):
    try:
      obj = script_list[i][2][index].value
      for k in obj:
        if not k in rs:
          rs[k] = [obj[k]]
        else:
          rs[k].append(obj[k])
    except Exception as e:
      print "error in analyzeObjectResultHelper "+str(e)
  return rs

def analyzeArrayResultHelper(script_list, index):
  script_len = len(script_list)
  rs = {}
  for i in range(script_len):
    try:
      arr = script_list[i][2][index].value
      for obj in arr:
        #obj = arr[j]
        if isinstance(obj, basestring):
          if not "basestring_" in rs:
            rs['basestring_'] = [obj]
          else:
            rs['basestring_'].append(obj)
        else:
          for k in obj:
            if not k in rs:
              rs[k] = [obj[k]]
            else:
              rs[k].append(obj[k])
    except Exception as e:
      print "error in analyzeArrayResultHelper "+str(e)
  return rs

def extractAndAnalyzeScriptsFromFile(path):
  content = open(path).read()
  hostset, contset = extractScriptFromContents(content)
  rs_list = []
  for item in contset:
    m = hashlib.md5()
    #print len(item)
    rs = analyzeJSCodes(item)
    for node in rs:
      m.update(node)
    rs = m.digest()
    rs_list.append(rs)
  return rs_list


def main():
  #contents = open(sys.argv[1]).read()
  #print "done reading"
  #extractAndStoreScriptsFromDOM("http://www.cnn.com/", contents )
  #fetchAndDisplayScriptsFromDB("http://www.google.com/")
  #extractAndStoreScriptsFromFileList(sys.argv[1])
  '''
  print "First one"
  list1 = extractAndAnalyzeScriptsFromFile(sys.argv[1])
  print "Next one"
  list2 = extractAndAnalyzeScriptsFromFile(sys.argv[2])
  for item in list1:
    if not item in list2:
      print "error"
  '''
  fetchAndProcessScriptsOfURLsFromFile(sys.argv[1],sys.argv[2])

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
