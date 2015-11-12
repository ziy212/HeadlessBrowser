from template import TemplateTree
from template import getTrees
from template import getTreesForDomainFromDB
from template import isSubTree
from template import extractArrayValues
from template import extractObjectValues
from db_client import fetchTrees
from db_client import fetchScripts
from node_pattern import global_count
from node_pattern import StringType

from script_analyzer import analyzeJSCodes
from script_analyzer import analyzeJSCodesFinerBlock
from script_analyzer import analyzeJSON
from script_analyzer import ASTOutputNode
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
    hosts, inlines = fetchScripts(url)
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
    hosts, inlines = fetchScripts(url)
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
      match_uniq_script += len(scriptdict[key])
      match_script += count_dict[key]
    else:
      nonmatch_uniq_script += len(scriptdict[key])
      nonmatch_script += count_dict[key]
      nonmatch_tree += 1
      print "non match script: %s " %(scriptdict[key][0][0])
  print "matched scripts:%d[%d] \n nonmatched scripts:%d[%d] nonmatch_tree:%d" \
    %(match_uniq_script,match_script, nonmatch_uniq_script, nonmatch_script, nonmatch_tree)

def completeMatchTreesFromDomainWithScriptsFromURLList(domain, url_list_path):
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

def compare(treedict, target_tree):
  key = target_tree.key
  if key in treedict:
    tree = treedict[key]
    return tree.match(target_tree)

def simpleCompare(treedict, target_tree):
  return target_tree.key and target_tree.key in treedict

def matchTreesFromDomainWithScriptsFromURLListS2(domain, url_list_path):
  treedict = getTreesForDomainFromDB(domain)
  if treedict == None or len(treedict) == 0:
    print "failed to fetch trees for domain ", domain
    return None, None
  passed_sc = []
  failed_sc = []
  f = open(url_list_path)
  for line in f:
    url = line.strip()
    print "process url "+url
    hosts, inlines = fetchScripts(url)
    if inlines==None or len(inlines) ==0:
      print "no inlines for "+url
      continue
    for inline in inlines:
      passed, failed = matchTreesFromDomainWithScript(domain, inline, treedict)
      if passed == None:
        print "failed for inline [S] ", inline[:100],' [E]'
      else:
        passed_sc += passed
        failed_sc += failed
  rate = float(len(passed_sc))/float(len(passed_sc)+len(failed_sc))
  print "passed %d; failed: %d; rate:%f" %(len(passed_sc), len(failed_sc), rate)
  print "match details : ", str(global_count)

def matchTreesFromDomainWithScript(domain, script, treedict = None):
  if treedict == None:
    treedict = getTreesForDomainFromDB(domain)
  if treedict == None or len(treedict) == 0:
    print "failed to fetch trees for domain ", domain
    return None, None
  #print "fetched %d trees for domain" %(len(treedict))
  
  is_json = False
  rs, sc = analyzeJSCodesFinerBlock(script)
  if rs == None:
    rs = analyzeJSON(script)
    is_json = True
  if rs == None:
    print "no script nor json"
    return [], []

  allowed_sc = []
  failed_sc = []

  if is_json:
    tree = TemplateTree(rs, None)
    #if simpleCompare(treedict, tree):
    if compare(treedict, tree):
      allowed_sc.append(rs)
      print "JSON allowed "
    else:
      failed_sc.append(rs)
      print "JSON failed "
  else:
    print "generate %d subtrees for target script" %(len(rs))
    for index in range(len(rs)):
      seq = rs[index]
      tree = TemplateTree(seq, None)
      key = tree.key

      if simpleCompare(treedict, tree):
      #if compare(treedict, tree):
        allowed_sc.append(sc[index])
      else:
        failed_sc.append(sc[index])

    print "allowed %d blocks, failed %d blocks" %(len(allowed_sc), len(failed_sc))
  return allowed_sc, failed_sc

def getTreesEvaluation(domain):
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

def evalTrees(domain):
  tree_dict = getTreesEvaluation(domain)
  print len(tree_dict)
  tree_number = 0
  node_number = 0
  obj_number = 0
  string_number = 0
  array_number = 0
  type_number = 0
  dangers_number = 0
  for key in tree_dict:
    tree = tree_dict[key]
    node_len = len(tree.nodes)
    node_number += node_len

    string_len = len(tree.string_types)
    string_number += string_len
    type_number += string_len

    obj_len = len(tree.object_types)
    obj_number += obj_len

    array_len = len(tree.array_types)
    array_number += array_len
    #print 'nodes:%d, string:%d, object:%d, array:%d' \
    #  %(node_len, string_len, obj_len, array_len)
    for k in tree.string_types:
      string = tree.string_types[k]
      if (string.tp == StringType.OTHER) \
        and (not string.val.alphanumeric) and (string.val.special_char_set)\
        and (('%' in string.val.special_char_set) or \
            (':' in string.val.special_char_set)):
              
        dangers_number += 1 
    for kk in tree.object_types:
      obj = tree.object_types[kk]
      obj_key_len = len(obj)
      type_number += obj_key_len
      for k in obj:
        if (obj[k].tp == StringType.OTHER )\
          and (not obj[k].val.alphanumeric) and (obj[k].val.special_char_set)\
          and (('%' in obj[k].val.special_char_set) or \
            (':' in obj[k].val.special_char_set)):
          dangers_number += 1
    for kk in tree.array_types:
      arr = tree.array_types[kk]
      arr_key_len = len(arr)
      #print '  arr_key: %d' %arr_key_len
      type_number += arr_key_len
      for k in arr:
        if (arr[k].tp == StringType.OTHER) \
          and (not arr[k].val.alphanumeric) and (arr[k].val.special_char_set)\
          and (('%' in arr[k].val.special_char_set) or \
            (':' in arr[k].val.special_char_set)):
          dangers_number += 1
  print "treeNumber:%d nodeNumber:%d stringNumber:%d arrNumber:%d objNumber:%d typeNumber:%d" \
    %(tree_number, node_number, string_number, array_number, obj_number, type_number)
  print "dangers: %d" %dangers_number


def evalTrees2(domain):
  tree_dict = getTreesEvaluation(domain)
  print len(tree_dict)
  tree_number = 0
  node_number = 0
  obj_number = 0
  string_number = 0
  array_number = 0
  type_number = 0
  dangers_number = 0

  

  for key in tree_dict:
    tree = tree_dict[key]
    node_len = len(tree.nodes)
    node_number += node_len

    string_len = len(tree.string_types)
    string_number += string_len
    type_number += string_len

    obj_len = len(tree.object_types)
    obj_number += obj_len

    array_len = len(tree.array_types)
    array_number += array_len
    #print 'nodes:%d, string:%d, object:%d, array:%d' \
    #  %(node_len, string_len, obj_len, array_len)
    for k in tree.string_types:
      string = tree.string_types[k]
      if (string.tp == StringType.OTHER) \
        and (not string.val.alphanumeric) and (string.val.special_char_set)\
        and (('%' in string.val.special_char_set) or \
            (':' in string.val.special_char_set)):
              
        dangers_number += 1 
    for kk in tree.object_types:
      obj = tree.object_types[kk]
      obj_key_len = len(obj)
      type_number += obj_key_len
      for k in obj:
        if (obj[k].tp == StringType.OTHER )\
          and (not obj[k].val.alphanumeric) and (obj[k].val.special_char_set)\
          and (('%' in obj[k].val.special_char_set) or \
            (':' in obj[k].val.special_char_set)):
          dangers_number += 1
    for kk in tree.array_types:
      arr = tree.array_types[kk]
      arr_key_len = len(arr)
      #print '  arr_key: %d' %arr_key_len
      type_number += arr_key_len
      for k in arr:
        if (arr[k].tp == StringType.OTHER) \
          and (not arr[k].val.alphanumeric) and (arr[k].val.special_char_set)\
          and (('%' in arr[k].val.special_char_set) or \
            (':' in arr[k].val.special_char_set)):
          dangers_number += 1
  print "treeNumber:%d nodeNumber:%d stringNumber:%d arrNumber:%d objNumber:%d typeNumber:%d" \
    %(tree_number, node_number, string_number, array_number, obj_number, type_number)
  print "dangers: %d" %dangers_number
def main():
  #matchTreesWithScriptsFromURLList(sys.argv[1], sys.argv[2])
  #matchTreesWithScriptsFromURLList(sys.argv[1], sys.argv[2])
  #matchTreesFromDomainWithScriptsFromURLList(sys.argv[1], sys.argv[2])
  
  #matchTreesFromDomainWithScriptsFromURLListS2(sys.argv[1], sys.argv[2])
  evalTrees(sys.argv[1])
  
  #getTrees(sys.argv[1])
  #rs = matchTreesFromDomainWithScript(sys.argv[1], open(sys.argv[2]).read())
  #for item in rs:
  #  print '[S] %s' % (item)


if __name__ == "__main__":
  main()
