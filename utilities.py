import sys

def displayErrorMsg(fun_name, msg=''):
  print >>sys.stderr, "error in %s: %s" %(fun_name, msg)