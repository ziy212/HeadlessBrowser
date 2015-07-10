from slimit.parser import Parser
from slimit.visitors import nodevisitor
from slimit import ast
import itertools

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
  def visit_Object(self, node, level):
    space = ' '.ljust(level*2)
    print "%s%s" %(space, node.__class__.__name__)

    space = ' '.ljust(level*2+2)
    for prop in node:
      left, right = prop.left, prop.right
      print "%s%s = %s" %(space, left.value, right)
    #for child in node:
    #  self.visit(child, level+1)

  def visit(self, node, level):
    method = 'visit_%s' % node.__class__.__name__
    return getattr(self, method, self.generic_visit)(node, level)

  def generic_visit(self, node, level):
    space = ' '.ljust(level*2)
    print "%s%s" %(space, node.__class__.__name__)
    for child in node:
      self.visit(child, level+1)

def main():
  scripts = "for (var i=0; i<10; i++) { var x = {'a':i,'b':'AAAAA'};}"
  parser = Parser()
  tree = parser.parse(scripts)
  visitor = MyVisitor()
  visitor.visit(tree, 0)

#print tree
#for node in tree:
#  print node.__name__

if __name__=="__main__":
  main()