from slimit.parser import Parser
from slimit.visitors import nodevisitor
from slimit import ast
import itertools, sys, json

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

class MyVisitor():
  def __init__(self, display=True):
    #only show class name and iterate children
    self.structure_class = set(["Program", "Block", "Node", \
      "FuncExpr", "FuncDecl", "This", "NewExpr", \
      ""])
    
    #leaf node and doesn't show value
    self.leaf_novalue_class = set(["Boolean", "Null", "Number", \
      "String", "Regex", "Array", "Object"])

    #leaf node and show value
    self.leaf_value_class = set(["Identifier"])

    self.node_order_list = []
    self.display = display
  
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

  #def visit_Object(self, node, level):
  #  space = ' '.ljust(level*2)
  #  print "%s%s" %(space, node.__class__.__name__)

  def visit_FunctionCall(self, node, level):
    space = ' '.ljust(level*2)
    tag = node.__class__.__name__ 
    #try:
    #  tag = node.__class__.__name__ +'_'+node.identifier.value
    #except Exception as e:
    #  tag = node.__class__.__name__ +'_'+node.identifier.__class__.__name__
    self.node_order_list.append(tag)
    if self.display:
      print "%s%s" %(space, tag)

    for child in node:
      self.visit(child, level+1)

  def visit_VarStatement(self, node, level):
    for child in node:
      self.visit(child, level+1)

  def leaf_value_visit(self, node, level):
    space = ' '.ljust(level*2)
    tag = node.value
    self.node_order_list.append(tag)
    if self.display:
      print "%s%s" %(space, tag)

  def leaf_novalue_visit(self, node, level):
    space = ' '.ljust(level*2)
    tag = node.__class__.__name__
    self.node_order_list.append(tag)
    if self.display:
      print "%s%s" %(space, tag)

  def generic_visit(self, node, level):
    space = ' '.ljust(level*2)
    tag = node.__class__.__name__
    self.node_order_list.append(tag)
    if self.display:
      print "%s%s" %(space, tag)
    for child in node:
      self.visit(child, level+1)

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
    return visitor.node_order_list
  except Exception as e:
      print >>sys.stderr, "error parsing script: "+str(e)+" "+script[:100]
      return None

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
  f = open(sys.argv[1])
  scripts = []
  for line in f:
    scripts.append(line.strip())
  
  count = 0
  results = []
  for script in scripts:
    count += 1
    l = analyzeJSCodes(script,True)
    if l == None:
      continue

    results.append(l)
  
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