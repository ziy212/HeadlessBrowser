from handler import TemplateTree
from handler import getTrees
from handler import getTreesForDomainFromDB
from handler import isSubTree
from handler import fetchScriptsFromDB
from ASTAnalyzer import analyzeJSCodes
from ASTAnalyzer import analyzeJSCodesFinerBlock
from ASTAnalyzer import analyzeJSON
from ASTAnalyzer import ASTOutputNode
from base64 import b64encode
from base64 import b64decode
import sys, os, re, json
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

def extractScriptsAndGenerateASTNodesFromURLListFinerBlock(path):
  f = open(path)
  scriptdict = {}
  total_script_count = {}
  total_uniq_script_blocks = 0
  total_json_count = {}
  total_uniq_json_blocks = 0
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
          scriptdict[tree.key] = [(json.dumps(rs), url, tree, -1)]
          total_json_count[tree.key] = 1
          total_script_count[tree.key] = 1
        else:
          scriptdict[tree.key].append((inline, url, tree, -1))
          total_json_count[tree.key] += 1
          total_script_count[tree.key] += 1
      else:
        for index in range(len(rs)):
          seq = rs[index]
          tree = TemplateTree(seq, None)
          key = tree.key
          if not key in scriptdict:
            scriptdict[key] = [(sc[index], url, tree, index)]
            total_script_count[key] = 1
            print "  add key  %s" %key
          else:
            contents = [x[0] for x in scriptdict[key]]
            if not sc[index] in contents: 
              scriptdict[key].append((sc[index],url, tree, index))
              print "  item %s has %d unique scripts" %(key, len(scriptdict[key]))
            total_script_count[key] += 1

  return scriptdict, total_script_count, total_json_count

def compareTrees(tree_path1, tree_path2):
  tree1 = getTrees(tree_path1)
  tree2 = getTrees(tree_path2)
  treedict = {}
  for t in tree1:
    treedict[t.key] = t
  match = 0
  non_match = 0
  for t in tree2:
    if t.key in treedict:
      match += 1
    else:
      non_match += 1
  print "match:%d nonmatch:%d" %(match, non_match)

def matchTreesWithScriptsFromURLList(tree_path, url_path):
  trees = getTrees(tree_path)
  treedict = {} 
  for tree in trees:
    treedict[tree.key] = tree
  scriptdict, count_dict, json_count = extractScriptsAndGenerateASTNodesFromURLListFinerBlock(url_path)
  match_script = 0
  match_uniq_script = 0
  nonmatch_script = 0
  nonmatch_uniq_script = 0
  nonmatch_tree = 0
  nomatch_list = []
  for key in scriptdict:
    if key in treedict:
      match_uniq_script += len(scriptdict[key])
      match_script += count_dict[key]
    else:
      nonmatch_uniq_script += len(scriptdict[key])
      nonmatch_script += count_dict[key]
      nonmatch_tree += 1
      print "non match script: %s " %(scriptdict[key][0][0])

  print "matched scripts:%d[%d] \n nonmatched scripts:%d[%d] nonmatch_tree:%d" \
    %(match_uniq_script,match_script, nonmatch_uniq_script, nonmatch_script, nonmatch_tree)

def matchTreesFromDomainWithScriptsFromURLList(domain, url_list_path):
  treedict = getTreesForDomainFromDB(domain)
  if treedict == None or len(treedict) == 0:
    print "failed to fetch trees for domain ", domain
    return
  print "fetched %d trees for domain" %(len(treedict))
  scriptdict, count_dict, json_count = extractScriptsAndGenerateASTNodesFromURLListFinerBlock(url_list_path)
  match_script = 0
  match_uniq_script = 0
  nonmatch_script = 0
  nonmatch_uniq_script = 0
  nonmatch_tree = 0
  nomatch_list = []
  for key in scriptdict:
    if key in treedict:
      flag = True
      for item in scriptdict[key]:
        target_tree = item[2]
        if not treedict[key].match(target_tree):
          print "Matching failure "
          print "  template_tree: %s " %(treedict[key].debug())
          print "  target_tree:   %s " %(target_tree.debug())
          nonmatch_uniq_script += len(scriptdict[key])
          nonmatch_script += count_dict[key]
          flag = False
          break
      if flag:
        match_uniq_script += len(scriptdict[key])
        match_script += count_dict[key]
    else:
      nonmatch_uniq_script += len(scriptdict[key])
      nonmatch_script += count_dict[key]
      nonmatch_tree += 1
      print "non match script: %s " %(scriptdict[key][0][0])
  print "matched scripts:%d[%d] \n nonmatched scripts:%d[%d] nonmatch_tree:%d" \
    %(match_uniq_script,match_script, nonmatch_uniq_script, nonmatch_script, nonmatch_tree)

def matchTreesFromDomainWithScript(domain, script):
  treedict = getTreesForDomainFromDB(domain)
  if treedict == None or len(treedict) == 0:
    print "failed to fetch trees for domain ", domain
    return
  print "fetched %d trees for domain" %(len(treedict))
  
  is_json = False
  rs, sc = analyzeJSCodesFinerBlock(script)
  if rs == None:
    rs = analyzeJSON(script)
    is_json = True
  if rs == None:
    print "no script nor json"
    return []

  allowed_sc = []
  print "generate %d subtrees for target script" %(len(rs))
  for index in range(len(rs)):
    seq = rs[index]
    tree = TemplateTree(seq, None)
    key = tree.key

    #comparison
    if key in treedict:
      allowed_sc.append(sc[index])

  print "allowed %d blocks for target scripts" %(len(allowed_sc))
  return allowed_sc


def main():
  #matchTreesWithScriptsFromURLList(sys.argv[1], sys.argv[2])
  #matchTreesWithScriptsFromURLList(sys.argv[1], sys.argv[2])
  matchTreesFromDomainWithScriptsFromURLList(sys.argv[1], sys.argv[2])
  #getTrees(sys.argv[1])
  #rs = matchTreesFromDomainWithScript(sys.argv[1], open(sys.argv[2]).read())
  #for item in rs:
  #  print '[S] %s' % (item)


if __name__ == "__main__":
  main()