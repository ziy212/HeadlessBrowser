from html_parser import calcTwoHTMLDistanceFromFiles
from html_parser import extractScriptFromContents
from html_parser import compare_two_string
from db_client import storeScripts
from db_client import storeTree
from db_client import fetchTrees
from db_client import fetchScripts
from db_client import fetchURLContents
from db_client import findAverageContents
from ASTAnalyzer import analyzeJSCodes
from ASTAnalyzer import analyzeJSCodesFinerBlock
from ASTAnalyzer import analyzeJSON
from ASTAnalyzer import ASTOutputNode
from utilities import displayErrorMsg
from base64 import b64encode
from base64 import b64decode
import sys, os, re, json, hashlib
from strings import NodePattern
from strings import analyzeStringListType


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
      print >> sys.stderr, "Exception in decoding: "+str(e)
      host_list.append(item)

  for item in contset:
    try:
      new_item = item.encode('utf-8')
      cont_list.append(new_item)
    except Exception as e:
      print >> sys.stderr, "Exception in decoding: "+str(e)
      cont_list.append(item)
  print >> sys.stderr, "extracted %d script hosts and %d inline scripts for %s " \
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
    self.strings = {}
    #value = {index : (StringType, data) }
    self.string_types_str = {}
    self.string_types = {}

    self.objects = {}
    #value = {index : {key : (StringType, data) }}
    self.object_types_str = {}
    self.object_types = {}

    self.arrays = {}
    #value = {index : {key : (StringType, data) }}
    self.array_types_str = {}
    self.array_types = {}

    if nodes == None:
      #print >> sys.stderr, "This is a null TemplateTree"
      return

    if len(nodes) == 0:
      #print >> sys.stderr, "TemplateTree nodes' length is zero"
      return

    if isinstance(nodes, dict):
      self.type = "json"
    elif nodes[0].__class__.__name__ == "ASTOutputNode":
      self.type = "js"
    else:
      print >> sys.stderr, "TemplateTree nodes format error: %s" \
            %(nodes[0].__class__)
      return

    if key == None:
      self.calc_key()

  def calc_key(self):
    if self.nodes != None:
      m = hashlib.md5()
      if self.type == "json":
        keys = sorted(self.nodes.keys())
        for k in keys:
          m.update(k)
      elif self.type == "js":
        for node in self.nodes:
          m.update(node.tag)
      else:
        debug_msg = "TemplateTree nodes format error: %s %d %d" \
          %(self.nodes[0].__class__, id(type(self.nodes[0])), id(ASTOutputNode))
        displayErrorMsg('TemplateTree.calc_key', debug_msg)
        self.key = None
      key = m.hexdigest()
    else:
      displayErrorMsg('TemplateTree.calc_key', "Nodes are None")
      self.key = None
    self.key = key

  def debug(self):
    if self.type == "json":
      val = ','.join(sorted(nodes.keys()))
    else:
      val = ""
      for i in range(len(self.nodes)):
        item = self.nodes[i]
        if item.value == None:
          item.value = 'None'
        if item.tag == 'String':
          v = ' ['+item.value+']'
        elif item.tag == 'Array' or item.tag =='Object':
          v = ' ['+str(item.value)+']'
        else:
          v = ' ['+item.tag+']'
      val += v
    return val

  def match(self, target_tree):
    if not isinstance(target_tree, TemplateTree):
      print >> sys.stderr, "matching tree, target tree should be TemplateTree"
      return False

    if self.key != target_tree.key:
      return False

    if self.type == 'json' and target_tree.type == 'json':
      return True
    elif self.type != target_tree.type:
      return False

    length = len(target_tree.nodes)
    #try:
    for i in range(length):
      if self.nodes[i].tag != target_tree.nodes[i].tag:
        return False
      if self.nodes[i].tag == 'String':
        #keys = [str(k) for k in self.string_types]
        #print type(self.string_types[i])
        #print 'string_type keys:',str(keys)
        if not self.string_types[str(i)].match(target_tree.nodes[i].value):
          return False
      elif self.nodes[i].tag == 'Object':
        #target_obj = 
        target_obj = extractObjectValues(target_tree.nodes[i].value)
        print "DEBUG: ",str(target_obj)
        for k in target_obj:
          if isinstance(target_obj[k], list):
            for item in target_obj[k]:
              if not self.object_types[str(i)][k].match(item):
                return False
          else:
            if not self.object_types[str(i)][k].match(target_obj[k]):
              return False
      elif self.nodes[i].tag == 'Array':
        target_obj = arrayToDict(target_tree.nodes[i].value)
        target_obj = extractObjectValues(target_obj)
        for k in target_obj:
          #print 'target: ',str(target_obj)
          #print "k's class: ",k.__class__.__name__, ' target: ',target_obj.__class__.__name__
          if isinstance(target_obj[k], list):
            for item in target_obj[k]:
              if not self.array_types[str(i)][k].match(item):
                return False
          else:
            if not self.array_types[str(i)][k].match(target_obj[k]):
              return False
    return True
    #except Exception as e:
    #  displayErrorMsg('TemplateTree.match','%s: %s' %(str(e), target_tree.nodes[i].tag))
    #  return False

  def get_length(self):
    return len(self.nodes)

  def get_data(self):
    pass

  '''
    { type : [json|js],
      tree : ['encoded_node1,encoded_node2...'|'{}'],
      string_types_str : '{index : val },
      object_types_str : '{index : {k:type_val} }',
      array_types_str  : '{index : {k:type_val} }' }
  '''
  def dumps(self):
    try:
      obj = {'type' : self.type}
      if self.type == 'json':
        obj['tree'] = self.nodes
      else:
        obj['tree'] = ','.join([b64encode(x.tag) for x in self.nodes])
      obj['string_types_str'] = self.string_types_str
      obj['object_types_str'] = self.object_types_str
      obj['array_types_str'] = self.array_types_str
      return json.dumps(obj)
    except Exception as e:
      displayErrorMsg("TemplateTree.dumps", str(e))
      return None

  def loads(self, obj_str):
    try:
      obj = json.loads(obj_str)
      self.type = obj['type']
      if self.type == 'json':
        self.nodes = obj['tree']
      elif self.type == 'js':
        nodes = obj['tree'].split(',')
        self.nodes = [ASTOutputNode(b64decode(x)) for x in nodes]
      self.calc_key()
      
      self.string_types_str = obj['string_types_str']
      for key in self.string_types_str:
        node_pattern = NodePattern()
        node_pattern.loads(self.string_types_str[key])
        self.string_types[key] = node_pattern
      #print "successfully loaded %d string patterns" %(len(self.string_types_str))

      self.object_types_str = obj['object_types_str']
      for index in self.object_types_str:
        self.object_types[index] = {}
        for key in self.object_types_str[index]:
          node_pattern = NodePattern()
          node_pattern.loads(self.object_types_str[index][key])
          self.object_types[index][key] = node_pattern
            
      #print "successfully loaded %d object patterns" %(len(self.object_types_str))  
         
      self.array_types_str = obj['array_types_str']
      for index in self.array_types_str:
        self.array_types[index] = {}
        for key in self.array_types_str[index]:
          node_pattern = NodePattern()
          node_pattern.loads(self.array_types_str[index][key])
          self.array_types[index][key] = node_pattern
            
      #print "successfully loaded %d array patterns" %(len(self.array_types_str)) 

      return True
    except Exception as e:
      displayErrorMsg("TemplateTree.loads", str(e))
      return False
    

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
        tree = TemplateTree(rs, None)
        if not tree.key in scriptdict:
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
 
  #start to analyze trees
  #scriptdict[tree_key] = [(script, url, tree, index)]
  trees = []
  insufficient_urls = {}
  keys = sorted(scriptdict.keys(), key=lambda k:len(scriptdict[k]))
  for key in keys:
    name = "%d_%s" %(len(scriptdict[key]),key)
    fw = open(os.path.join(dst_path,name), 'w')
    for item in scriptdict[key]:
      fw.write(item[1]+"||"+str(item[3])+"  "+str(item[0])+"\n")
    
    #make sure all inlines in a template have same sequential size
    script_list = scriptdict[key]
    length_list = sorted([len(item[2].nodes) for item in script_list])
    seq_length = 0
    if length_list[0] != length_list[-1]:
      fw.write("[ALERT] seq length is not consistent")
      fw.close()
      continue
    else:
      seq_length = length_list[0]

    #only handle JavaScript for now
    tree = script_list[0][2]
    if tree.type == "json":
      print "the inline is json!"
      fw.write("[TODO]: the inline is json. This is next step\n")
      fw.close()
      trees.append(tree)
      continue  
    
    #process String/Object/Array nodes
    #script_list: [(script, url, tree, index)]
    fw.write("start analyzeing values\n")    
    script_length = len(script_list)
    for i in range(seq_length):
      node = script_list[0][2].nodes[i]
      try:
        if node.tag == "String":
          vals = [item[2].nodes[i].value for item in script_list]
          encoded_val = [b64encode(x) for x in vals]
          #item = 'string%d: %s' %(i, ','.join(encoded_val))
          #fw.write(item+"\n")
          tree.strings[i] = vals
          node_pattern = analyzeStringListType(vals)
          tree.string_types_str[str(i)] = node_pattern.dumps()
          if node_pattern.is_insufficient():
            if not key in insufficient_urls:
              insufficient_urls[key] = \
                [item[1] for item in script_list]
            else:
              insufficient_urls[key] += [item[1] for item in script_list]
          # testing
          #node_pattern = NodePattern()
          #r = node_pattern.loads(tree.string_types_str[i])
          #if r == False:
          #  print "node_pattern failed to load: "+tree.string_types_str[i]
          #else:
          #  print "successfully loaded tree: "+tree.string_types_str[i]
          print "STRING%d: [TYPE:%s] [VALUE:%s]" \
            %(i, tree.string_types_str[str(i)],','.join(encoded_val))
        if node.tag == "Object":
          #debug = "tag:%s val:%s" \
          #  %(script_list[0][2].nodes[i].tag,str(script_list[0][2].nodes[i].value))
          #print "DEBUG: %s" %debug
          rs = analyzeObjectResultHelper(script_list, i)
          rs = extractObjectValues(rs)
          type_dict = {}
          for k in rs:
            encoded_val = [b64encode(x) for x in rs[k]]
            node_pattern = analyzeStringListType(rs[k])
            type_dict[k] = node_pattern.dumps()
            if node_pattern.is_insufficient():
              if not key in insufficient_urls:
                insufficient_urls[key] = \
                  [item[1] for item in script_list]
              else:
                insufficient_urls[key] += [item[1] for item in script_list]
            #testing
            #node_pattern = NodePattern()
            #r = node_pattern.loads(type_dict[k])
            #if r == False:
            #  print "node_pattern failed to load: "+type_dict[k]
            #else:
            #  print "successfully loaded tree: "+type_dict[k]
            print "OBJECT%d: [TYPE:%s] [KEY:%s][VALUE:%s]" \
              %(i, type_dict[k], k, ','.join(encoded_val))
          tree.objects[i] = rs
          tree.object_types_str[str(i)] = type_dict
        if node.tag == "Array":
          rs = analyzeArrayResultHelper(script_list, i)
          rs = extractObjectValues(rs)
          type_dict = {}
          for k in rs:
            encoded_val = [b64encode(x) for x in rs[k]]
            #fw.write("array%d: %s:%s\n" % (i, k, ','.join(encoded_val)) )
            node_pattern = analyzeStringListType(rs[k])
            type_dict[k] = node_pattern.dumps()
            if node_pattern.is_insufficient():
              if not key in insufficient_urls:
                insufficient_urls[key] = \
                  [item[1] for item in script_list]
              else:
                insufficient_urls[key] += [item[1] for item in script_list]
            #testing
            #node_pattern = NodePattern()
            #r = node_pattern.loads(type_dict[k])
            #if r == False:
            #  print "node_pattern failed to load: "+type_dict[k]
            #else:
            #  print "successfully loaded tree: "+type_dict[k]
            print "ARRAY%d: [TYPE:%s] [KEY:%s][VALUE:%s]" \
              %(i, type_dict[k], k, ','.join(encoded_val))
          tree.arrays[i] = rs
          tree.array_types_str[str(i)] = type_dict
      except Exception as e:
        displayErrorMsg("fetchAndProcessScriptsOfURLsFromFile",\
           "excpetion in analyzing node %d %s " %(i, str(e))) 
    
    print "Done writing %d items for file %s " %(len(scriptdict[key]), name)
    trees.append(tree)
    
    fw.close()
  
  # display insufficient_urls
  #for key in insufficient_urls:
  #  print "URL: %s %s " %(key, insufficient_urls[key])

  #store trees
  trees = sorted(trees, key=lambda x:x.get_length())
  fw = open(os.path.join(dst_path,"trees"), 'w')
  fw_json = open(os.path.join(dst_path,"jsons"), 'w')
  for i in range(len(trees)):
    tree_val = trees[i].dumps()
    url = scriptdict[trees[i].key][0][1]
    storeTree(url,trees[i].key, tree_val)
    fw.write( "1 %.3d: %s\n" %(i, tree_val))
    new_tree = TemplateTree(None, None)
    new_tree.loads(tree_val)

    if trees[i].type == "js":
      fw.write( "2 %.3d: %s\n" %(i, getTreeSeq(new_tree.nodes)))
    elif trees[i].type == 'json':
      fw.write("2 %.3d: %s\n" % (i, json.dumps(new_tree.nodes)))
  fw.close()
  fw_json.close()
  print "generate %d trees for %d scripts uniqe[%d]" \
    %(len(trees), total_script_blocks, total_uniq_script_blocks)

  return insufficient_urls

def getTreesForDomainFromDB(domain):
  tree_strings = fetchTrees(domain)
  if tree_strings == None:
    return None

  tree_dict = {} #{key : TemplateTree}
  for key in tree_strings:
    tree = TemplateTree(None, None)
    try:
      tree.loads(tree_strings[key])
      tree_dict[key] = tree
    except Exception as e:
      displayErrorMsg("getTreesForDomainFromDB",str(e))
  
  return tree_dict  

def getTrees(path):
  f = open(path)
  node_pattern = "(.+)\[(\d+)\]"
  trees = []
  for line in f:
    tree_nodes = []
    try:
      tmp = line.split(':')
      try:
        line = ':'.join(tmp[1:])
        obj = json.loads(line)
        tree = TemplateTree(obj, None)
        print "read JSON tree %d with key %s " %(len(trees), tree.key)
        trees.append(tree)
        continue
      except Exception as ee:
        pass
      line = tmp[1].strip()
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

#key : [val1, val2]
def mergeTwoArrayDict(left, right):
  for k in right:
    if k in left:
      left[k] = left[k] + right[k]
    else:
      left[k] = right[k]

#guarantees no array in results
def extractArrayValues(data):
  rs = []
  for item in data:
    if isinstance(item, basestring) or isinstance(item, int) or isinstance(item, float):
      rs.append(item)
    elif isinstance(item, list) or isinstance(item, tuple):
      val = extractArrayValues(item)
      rs += val
    elif isinstance(item, dict):
      rs.append(extractObjectValues(item))
    else:
      displayErrorMsg('extractArrayValues', "unknown type "+str(type(item)))
  return rs

#{key : [string or number]}
def extractObjectValues(data):
  rs = {} #key : [val1, val2]
  for k in data:
    if not k in rs:
      rs[k] = []
    val = data[k]
    if isinstance(val, dict):
      sub_rs = extractObjectValues(val)
      mergeTwoArrayDict(rs, sub_rs)
    elif isinstance(val, list) or isinstance(val, tuple):
      arr = extractArrayValues(val)
      for item in arr:
        if isinstance(item, dict):
          mergeTwoArrayDict(rs, item)
        elif isinstance(item, basestring) or isinstance(item, int) or isinstance(item, float):
          rs[k].append(item)
        else:
          displayErrorMsg('extractObjectValues',\
            "shouldn't have other types"+str(type(item)))
    elif isinstance(val, basestring) or isinstance(val, int) or isinstance(val, float):
      rs[k].append(val)
    else:
      displayErrorMsg('extractObjectValues',\
            "unknown type:"+str(type(val)))
      continue
  invalid_keys = [k for k in rs if len(rs[k]) == 0]
  for k in invalid_keys:
    del rs[k]
  return rs

#script_list: [(script, url, tree)]
#return {key: [val]}
def analyzeObjectResultHelper(script_list, index):
  script_len = len(script_list)
  rs = {}
  for i in range(script_len):
    try:
      tree = script_list[i][2]
      obj = tree.nodes[index].value
      #print str(i)," analyzeObjectResultHelper obj: ", str(obj), obj.__class__.__name__
      for k in obj:
        val = obj[k]
        if not k in rs:
          rs[k] = [val]
        else:
          rs[k].append(val)
    except Exception as e:
      print >> sys.stderr,\
        "error in analyzeObjectResultHelper "+str(e)
  return rs

def arrayToDict(arr):
  rs = {}
  try:
    for obj in arr:
      if isinstance(obj, basestring):
        if not "basestring_" in rs:
          rs['basestring_'] = [obj]
        else:
          rs['basestring_'].append(obj)
      elif isinstance(obj, list):
        subarr = extractArrayValues(obj)
        subrs = arrayToDict(subarr)
        mergeTwoArrayDict(rs,subrs)
      else:
        for k in obj:
          if not k in rs:
            rs[k] = [obj[k]]
          else:
            rs[k].append(obj[k])
  except Exception as e:
    displayErrorMsg('arrayToDict',str(e))
    return {}

def analyzeArrayResultHelper(script_list, index):
  script_len = len(script_list)
  rs = {}
  for i in range(script_len):
    try:
      tree = script_list[i][2]
      arr = tree.nodes[index].value
      subrs = arrayToDict(arr)
      mergeTwoArrayDict(rs, subrs)
    except Exception as e:
      print >> sys.stderr, \
        "error in analyzeArrayResultHelper "+str(e)
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
