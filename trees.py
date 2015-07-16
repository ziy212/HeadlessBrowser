from handler import TemplateTree
from handler import getTrees
from handler import fetchScriptsFromDB
from ASTAnalyzer import analyzeJSCodes
from ASTAnalyzer import analyzeJSON
from ASTAnalyzer import ASTOutputNode
from base64 import b64encode
from base64 import b64decode
import sys, os, re
import hashlib

#{tree_key: [(script, url, AST_nodes)]}
def extractScriptsAndGenerateASTNodesFromURLList(url_path):
  scriptdict = {}
  f = open(url_path)
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
      rs = analyzeJSCodes(inline)
      if rs == None:
        rs = analyzeJSON(inline)
        is_json = True
      if rs == None:
        continue
      m = hashlib.md5()
      if not is_json:
        for node in rs:
          m.update(node.tag)
      else:
        for k in rs:
           m.update(k)
      key = m.hexdigest()
      if not key in scriptdict:
        scriptdict[key] = [(inline,url,rs)]
        print "  add key  %s" %key
      else:
        contents = [x[0] for x in scriptdict[key]]
        if not inline in contents:
          scriptdict[key].append((inline,url, rs) )
          print "  item %s has %d distinct scripts" %(key, len(scriptdict[key]))
  f.close()
  return scriptdict


def matchTreesWithScriptsFromURLList(tree_path, url_path):
  trees = getTrees(tree_path)
  treedict = {} 
  for tree in trees:
    treedict[tree.key] = tree
  scriptdict = extractScriptsAndGenerateASTNodesFromURLList(url_path)
  match_script = 0
  nonmatch_script = 0
  for key in scriptdict:
    if key in treedict:
      match_script += len(scriptdict[key])
    else:
      nonmatch_script += len(scriptdict[key])
  print "matched scripts:%d  nonmatched scripts:%d" %(match_script, nonmatch_script)

def main():
  matchTreesWithScriptsFromURLList(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
  main()