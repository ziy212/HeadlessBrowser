from slimit.parser import Parser
from slimit.visitors import nodevisitor
from slimit import ast
import itertools, sys, json, copy, hashlib, os

############TESING CODE##############
def nodeToString(node):
  try:
    v = str(node)
    tmp = v.split()
    tmp = tmp[0].split('.')
    return tmp[-1].strip()
  except Exception as e:
    return str(node)

def visitTree(node, level):
  space = ' '.ljust(level*2)
  print "%s%s" %(space, node.__class__.__name__)
  for child in node:
    visitTree(child,level+1)  

def getASTClasses(path):
  f = open(path)
  s = set()
  for c in f:
    s.add(c.strip())
  return s

####################################

class ASTOutputNode():
  def __init__(self, tag):
    self.tag = tag
    self.value = None
    self.child_num = 0

  def __eq__(self, other):
    if not isinstance(other, ASTOutputNode):
      return False
    return self.tag == other.tag

  def __ne__(self, other):
    return not self.__eq__(other)

class MyVisitor():
  def __init__(self, display=True):
    #only show class name and iterate children
    self.structure_class = set(["Block", "Node", \
      "FuncExpr", "FuncDecl", "This", "NewExpr", \
      ""])
    
    #leaf node and doesn't show value
    self.leaf_novalue_class = set(["Boolean", "Null", "Number", \
     "Regex"])

    #leaf node and show value
    self.leaf_value_class = set()

    self.node_order_list = []
    self.display = display
    
    self.current_id_map = {}
    self.identifier_map = []
    self.first_level_seq = []
    #self.string_value_list = []

  
  def is_structure_class(self, node):
    name = node.__class__.__name__
    if name in self.structure_class:
      return True
    return False 

  def is_leaf_novalue_class(self, node):
    name = node.__class__.__name__
    if name in self.leaf_novalue_class:
      return True
    return False 
  
  def is_leaf_value_class(self, node):
    name = node.__class__.__name__
    if name in self.leaf_value_class:
      return True
    return False 

  def visit_sensitive_node(self, node, level):
    val = None
    if isinstance(node,ast.FunctionCall) or \
        isinstance(node, ast.NewExpr) or \
        isinstance(node, ast.ExprStatement):
        self.visit(node, level)
        val = "[FunctionCall||NewExpr]"
    elif isinstance(node, ast.Object):
      #for prop in child:
      #  left, right = prop.left, prop.right
      #   print "  object: left:%s, right:%s" %(left, right)
      count = 0
      val = {}
      for child in node:
        if isinstance(child, ast.Assign):
          key = self.visit_sensitive_node(child.left, level+1)
          value = self.visit_sensitive_node(child.right, level+1)
          if key != None and value != None:
            val[key] = value
        else:
          #print "    NO-ASSIGN-CHILD ",str(count),child, node
          if not "unknown" in val:
            val['unknown'] = child.__class__.__name__
          else:
            val['unknown'].append(child.__class__.__name__)
        count += 1
    elif isinstance(node, ast.Array):
      val = self.visit_sensitive_children(node, level)
    elif isinstance(node, ast.String):
      val = node.value
    elif isinstance(node, ast.Identifier):
      val = node.value

    return val

  def visit_sensitive_children(self, node, level):
    rs = []
    #print "DEBUG in processing visit_sensitive_children :NODE ",node
    for child in node:
      val = self.visit_sensitive_node(child, level+1)
      if val != None:
        rs.append(val)

    return rs

  def visit_Object(self, node, level):
    #self.display = True
    space = ' '.ljust(level*2)
    tag =  node.__class__.__name__
    if level == 0:
      self.current_id_map = {}
      index = len(self.node_order_list)
    if self.display:
      print "%s%s" %(space, tag)
    output_node = ASTOutputNode(tag)
    self.node_order_list.append(output_node)
    no_child_len = len(self.node_order_list)
    #print "process object ",node
    val = {}
    for child in node:
      if isinstance(child, ast.Assign):
        key = self.visit_sensitive_node(child.left, level+1)
        value = self.visit_sensitive_node(child.right, level+1)
        if key != None and value != None:
          val[key] = value
      else:
        #print "    NO-ASSIGN-CHILD ",str(count),child, node
        if not "unknown" in val:
          val['unknown'] = child.__class__.__name__
        else:
          val['unknown'].append(child.__class__.__name__)

    output_node.value = val
    output_node.child_num = \
      len(self.node_order_list) - no_child_len
    if level == 0:
      self.identifier_map.append(self.current_id_map)
      self.first_level_seq.append(self.node_order_list[index:] )
    #if self.display:
    #  print "%s%d]" %(space, output_node.child_num)
    return val

  def visit_Array(self, node, level):
    space = ' '.ljust(level*2)
    tag =  node.__class__.__name__
    if self.display:
      print "%s%s" %(space, tag)
    #print "Array with %d child " % (len(node.items))
    if level == 0:
      self.current_id_map = {}
      index = len(self.node_order_list)

    output_node = ASTOutputNode(tag)
    self.node_order_list.append(output_node)
    no_child_len = len(self.node_order_list)
    v = self.visit_sensitive_children(node, level+1)
    output_node.value = v
    output_node.child_num = \
      len(self.node_order_list) - no_child_len

    if level == 0:
      self.identifier_map.append(self.current_id_map)
      self.first_level_seq.append(self.node_order_list[index:])
    #print "display array: %d" %len(v)
    #for item in v:
    #  print item
    #print "done displaying array"

    #if self.display:
    #  print "%s%d]" %(space, output_node.child_num)
    return output_node
    
  def visit_String(self, node, level):
    space = ' '.ljust(level*2)
    tag =  node.__class__.__name__
    output_node = ASTOutputNode(tag)
    output_node.value = node.value
    output_node.child_num = 0
    self.node_order_list.append(output_node)
    #self.string_value_list.append(node.value)
    if self.display:
      print "%s%s [%s]" %(space, tag, node.value)
    return output_node.value
  
  def create_next_identifier(self):
    length = len(self.current_id_map)
    return "Var_%d" %length 

  def visit_Identifier(self, node, level):
    space = ' '.ljust(level*2)
    name = node.value
    if name in self.current_id_map:
      tag = self.current_id_map[name]
    else:
      tag = self.create_next_identifier()
      self.current_id_map[name] = tag

    output_node = ASTOutputNode(tag)
    output_node.value = node.value
    output_node.child_num = 0
    self.node_order_list.append(output_node)
    #self.string_value_list.append(node.value)
    if self.display:
      print "%s%s" %(space, tag)
    return node.value

  def visit_FunctionCall(self, node, level):
    space = ' '.ljust(level*2)
    #tag = node.__class__.__name__ 
    tag = node.__class__.__name__ 
    if level == 0:
      self.current_id_map = {}
      index = len(self.node_order_list)

    output_node = ASTOutputNode(tag)
    self.node_order_list.append(output_node)
    no_child_len = len(self.node_order_list)

    if self.display:
      print "%s%s" %(space, tag)
    #self.visit(node.identifier, level+1)
    rs = {'name':"FunCall", 'val':[]}
    for child in node:
      v = self.visit(child, level+1)
      if not v == None:
        rs['val'].append(v)
        
    output_node.child_num = \
      len(self.node_order_list) - no_child_len

    if level == 0:
      self.identifier_map.append(self.current_id_map)
      self.first_level_seq.append(self.node_order_list[index:])
    return rs

  def visit_VarStatement(self, node, level):
    #child_num = 0
    for child in node:
      tmp = self.visit(child, level+1)
      #child_num += tmp
    
    return None

  def visit_Program(self, node, level):
    #child_num = 0
    for child in node:
      tmp = self.visit(child, level)
      #child_num += tmp
    return None

  def leaf_value_visit(self, node, level):
    space = ' '.ljust(level*2)
    tag = node.value
    output_node = ASTOutputNode(tag)
    self.node_order_list.append(output_node)
    if self.display:
      print "%s%s" %(space, tag)
    output_node.child_num = 0
    return tag

  def leaf_novalue_visit(self, node, level):
    space = ' '.ljust(level*2)
    tag = node.__class__.__name__
    output_node = ASTOutputNode(tag)
    output_node.value = node.value
    output_node.child_num = 0
    self.node_order_list.append(output_node)

    if self.display:
      print "%s%s" %(space, tag)
    return tag

  def generic_visit(self, node, level):
    space = ' '.ljust(level*2)
    tag = node.__class__.__name__
    if level == 0:
      self.current_id_map = {}
      index = len(self.node_order_list)

    output_node = ASTOutputNode(tag)
    self.node_order_list.append(output_node)
    no_child_len = len(self.node_order_list)
      
    if self.display:
      print "%s%s" %(space, tag)
    rs = {'name':tag, 'val': []}
    for child in node:
      v = self.visit(child, level+1)
      #child_num += tmp
      if not v == None:
        rs['val'].append(v)
    #v = '_'.join(rs)
    output_node.child_num = \
      len(self.node_order_list) - no_child_len
    if level == 0:
      self.identifier_map.append(self.current_id_map)
      self.first_level_seq.append(self.node_order_list[index:])
    #if self.display:
    #  print "%s%d]" %(space, output_node.child_num)
    return rs

  def visit(self, node, level):
    if self.is_leaf_novalue_class(node):
      self.leaf_novalue_visit(node,level)
      return

    if self.is_leaf_value_class(node):
      self.leaf_value_visit(node,level)
      return

    method = 'visit_%s' % node.__class__.__name__
    return getattr(self, method, self.generic_visit)(node, level)

def analyzeJSCodes(script, display=False):
  try:
    parser = Parser()
    tree = parser.parse(script)
    visitor = MyVisitor(display)
    visitor.visit(tree, 0)
    #print "first_level_seq: %d" %len(visitor.first_level_seq)
    return visitor.node_order_list
  except Exception as e:
    print >>sys.stderr, "error parsing script: "+str(e)+" "+script[:100]
    return None

def analyzeJSCodesBeta(script, display=False):
  try:
    parser = Parser()
    tree = parser.parse(script)
    visitor = MyVisitor(display)
    visitor.visit(tree, 0)
    #subtrees = {}
    print "first_level_seq: %d" %len(visitor.first_level_seq)
    #for subtree, we require variable name to be the same
    '''
    for seq in visitor.first_level_seq:
      for node in seq:
        if node.tag.startswith("Var_"):
          node.tag = node.value
    
    for seq in visitor.first_level_seq:
      m = hashlib.md5()
      for node in seq:
        m.update(node.tag)
        #print node.tag
      key = m.hexdigest()
      
      if not key in subtrees:
        subtrees[key] = [seq]
      else:
        subtrees[key].append(seq)
        #for s in subtrees[key]:
        #  print key,'_'.join([node.tag for node in s])
    '''
      
    return visitor.first_level_seq, visitor.identifier_map
  except Exception as e:
    print >>sys.stderr, "error parsing script: "+str(e)+" "+script[:100]
    return None, None

def analyzeJSON(script):
  try:
    obj = json.loads(script)
    rs = sorted(obj.keys())
    rs.insert(0, "JSON")
    return rs
  except Exception as e:
    print >>sys.stderr, "error parsing json: "+str(e)+" "+script[:100]
    return None

def main():
  #scripts = "for (var i=0; i<10; i++) { var x = {'a':i,'b':'AAAAA'}; " +\
  #          "var b = [{'a':1},{'b':'WW'}]} \n "+\
  #          "ma(123,'ddf'); ma('fff')"
  '''
  #compare scripts in a file
  f = open(sys.argv[1])
  scripts = []
  for line in f:
    scripts.append(line.strip())
  
  count = 0
  results = []
  strings = []
  for script in scripts:
    count += 1
    l = analyzeJSCodes(script, False)
    if l == None:
      continue
    print len(l)
    results.append(l)

  flag = True
  for i in range(len(results[0])):
    if not results[0][i] == results[1][i]:
      print "No"
      flag = False
    elif results[0][i].tag == "String":
      print "STRING:",results[0][i].value, " VS ", results[1][i].value
    elif results[0][i].tag == "Object":
      print "OBJECT:",results[0][i].value, " VS ", results[1][i].value 
    elif results[0][i].tag == "Array":
      for item in results[0][i].value:
        print "LEFTARRAY: ",item,
      print ""
      print "  VS  "
      for item in results[0][i].value:
        print "RIGHTARRAY: ",item,
      print ""
  if flag:
    print "DOOD"
  '''
  
  #f = open(sys.argv[2])
  #script2 = f.read()
  #if script1 == script2:
  #  print "two scripts are already the same"
  #  return
  from handler import TemplateTree
  subtree_dict = {}
  rs_list = []
  dir_name = sys.argv[1]
  files = os.listdir(dir_name)
  for fname in files:
    path = os.path.join(dir_name, fname)
    f = open(path)
    script = f.read()
    seq_list, id_map_list = analyzeJSCodesBeta(script)
    print "done processing file: %s %dsubtrees" %(fname, len(seq_list))

    for index in range(len(seq_list)):
      seq = seq_list[index]
     
      tree = TemplateTree(seq, None)
      key = tree.key
      if key in subtree_dict:
        subtree_dict[key].append((script, index))
      else:
        subtree_dict[key] = [(script, index)]

  total = 0
  for key in subtree_dict:
    total += len(subtree_dict[key])
    print "dict: %s => %d times" %(key, len(subtree_dict[key]) )
  print "%d blocks of scripts in %d trees" %(total, len(subtree_dict))
  
  #print "common %d" %common
  #l2 = analyzeJSCodes(script2)
  #print len(l1), len(l2)
  #for i in range(len(l1)):
  #  if l1[i].tag == l2[i].tag:
  #    continue
    #print "%d l1:%s || l2:%s" % (i, l1[i].tag, l2[i].tag )

  script = "var _gaq = _gaq || []; " +\
    "_gaq.push(['_setAccount', 'UA-XXXXX-X']);" +\
    "_gaq.push(['_trackPageview']);" +\
    "(function() { var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true; "+\
    "ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';"+\
    "var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);})();"
  #l, vl = analyzeJSCodes(script, True)
  #for item in vl:
  #  print item
  #for i in range(len(strings[0])):
  #  print strings[0][i]
  #  print strings[1][i]
  #  print ""
  
  #print len(results[0]),len(results[1])
  #for i in range(len(results[0])):
  #  if results[0][i] != results[1][i]:
  #    print "Error: %s vs %s [%d]" % (results[0][i],results[1][i],i)

  #print "Start illustrate %d" %count
  #for item in visitor.node_order_list:
  #  print item,
  #print "\nDone illustrate %d" %count

#print tree
#for node in tree:
#  print node.__name__

if __name__=="__main__":
  main()