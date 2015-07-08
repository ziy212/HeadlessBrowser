import sys, re,  distance,  editdistance, json
from urlparse import urlparse
from bs4 import BeautifulSoup
from bs4 import NavigableString

SCRIPT_COST = 20

class Node:
	def __init__(self, tag):
		self.tag = tag.lower()
		self.src = 'None'
		self.cls = 'None'
		self.val = ""
		self.children = []
		self.parent = 'None'
		self.href = 'None'
		self.tp = 'None'
		self.data_reactid = 'None'
		self.level = 0

	def toString(self):
		rs = "%s " % self.tag 
		if self.src != 'None':
			rs += " src:%s " % self.src.strip()
		if self.tp != 'None':
			rs += " type:%s " % self.tp.strip()
		if self.href != 'None':
			rs += " href:%s " % self.href.strip()
		if self.cls != 'None':
			rs += " cls:%s " % self.cls.strip()
		if self.val != "":
			rs += " val:%s " % self.val.strip()
		if self.data_reactid != 'None':
			rs += " data-reactid:%s" % self.data_reactid.strip()
		try:
			return rs.encode('utf-8')
		except UnicodeEncodeError as e:
			return rs

	def __ne__(self, other):
		rs = self.__eq__(other)
		return not rs

	def __eq__(self, other): 
		if self.tag != other.tag:
			return False

		if self.tag == "script":
			if self.src != 'None' and self.src == other.src:
				#print "DEBUG: euqal external scripts"
				return True
			elif self.src != 'None':
				#print "DEBUG: NOT equal external scripts"
				return False
			elif self.src == 'None' and self.src != other.src:
				#print "DEBUG: one external one internal scripts"
				return False
			else: # both src are None
				#print "DEBUG: compare two internal scripts"
				if 'json' in self.tp and 'json' in other.tp:
					try:
						#print "JSON: %s " %self.val
						obj1 = json.loads(self.val)
						keys1 = set(obj1.keys())
						obj2 = json.loads(other.val)
						keys2 = set(obj2.keys())
						intersect = keys1.intersection(keys2)
						if len(intersect) >= 2 and \
							len(intersect) > len(keys1)/2:
							#print "RESULT: TRUE"
							return True
						else:
							#print "RESULT FALSE %d %d %d" %(len(intersect), len(keys1), len(keys2))
							return False
					except Exception as e:
						print "failed parse JSON: %s " %str(e)
				return compare_two_string(self.val, other.val)

		if self.tag == "link":
			if self.href != 'None' and self.href == other.src:
				return True
			elif self.href != 'None':
				return False
			elif self.href == 'None' and self.href != other.href:
				return False
			else:
				self_data = "%s-%s" % (self.tp, self.data_reactid)
				other_data = "%s-%s" % (other.tp, other.data_reactid)
				return self_data == other_data

		self_data = "%s-%s" % (self.cls, self.val)
		other_data = "%s-%s" % (other.cls,other.val)
		return self_data == other_data


def traverseDOMTree(root, parent_node, level):
	if isinstance(root, NavigableString):
		#print "%s  %s" %(
		#	space,
		#	"NavigableString: "+root.string.encode('utf-8').strip())
		val = "%s" % root.string
		parent_node.val += val
		return

	node = Node(root.name.lower())
	node.level = level
	try:		
		parent_node.children.append(node)
		node.parent = parent_node
		src = ''
		cls = ''
		if root.get('src') != None:	
			src = root.get('src').strip().lower()
			o = urlparse(src)
			node.src = o.netloc
		
		if root.get('class') != None:
			cls = (','.join(sorted(root.get('class')) )).lower()
			node.cls = cls
		
		if root.get('type') != None:
			tp = root.get('type').strip().lower()
			node.tp = tp

		if root.get('href') != None:
			href = root.get('href').strip().lower()
			node.href = href

		if root.get("data-reactid") != None:
			data = root.get('data-reactid').strip().lower()
			node.data_reactid = data
		
		#print "%s%s src:%s cls:%s" % (space, root.name, src, root.get('class'))
	except Exception as e:
		#print repr(e)
		print "%s" % ( "Error:"+str(e)+" "+root.name)

	
	for child in root.contents:
		traverseDOMTree(child, node, level+1)

def preDisplayNode(root, level):
	space = ' '.ljust(level*2)
	print "%s%s" % (space, root.toString())

	for child in root.children:
		preDisplayNode(child, level+1)

def costUpdate(src_node, dst_node):
	if src_node == dst_node:
		return 0
	elif src_node.tag == "script" or dst_node.tag == "script":
		return SCRIPT_COST
	else:
		return 1

def costInsert(node):
	if node.tag == "script":
		return SCRIPT_COST
	else:
		return 1

def costDelete(node):
	if node.tag == "script":
		return SCRIPT_COST
	else:
		return 1

#src_ld and dst_ld start with index 1
def mmdiff(src_ld, dst_ld):
	M = len(src_ld) #1 + lenth of src_ld
	N = len(dst_ld)
	D = [[0 for x in range(N)] for x in range(M)] 
	print "src ld length: %d, dst ld length: %d" %(M, N)
	for i in range(1, M):
		D[i][0] = D[i-1][0] + costDelete(src_ld[i])

	for j in range(1, N):
		D[0][j] = D[0][j-1] + costInsert(dst_ld[j])

	for i in range(1, M):
		for j in range(1, N):
			m1 = 800000
			m2 = 800000
			m3 = 800000
			if src_ld[i].level == dst_ld[j].level:
				m1 = D[i-1][j-1] + costUpdate(src_ld[i],dst_ld[j])
			if j == N-1 or dst_ld[j+1].level <= src_ld[i].level:
				m2 = D[i-1][j] + costDelete(src_ld[i])
			if i == M-1 or src_ld[i+1].level <= dst_ld[j].level:
				m3 = D[i][j-1] + costInsert(dst_ld[j])
			D[i][j] = min(m1,m2,m3)
	print "Least cost %d " %D[M-1][N-1]
	return D

def mmdiffR(src_ld, dst_ld, D, \
	src_script_hosts, src_script_contents, \
	dst_script_hosts, dst_script_contents):
	M = len(src_ld) #[1 ... M-1]
	N = len(dst_ld) #[1 ... N-1]
	i = M - 1
	j = N - 1
	ins_scripts_hosts = set()
	del_scripts_hosts = set()

	ins_scripts_contents = set()
	del_scripts_contents = set()
	updated_scripts_count = 0

	while i >0 and j > 0:
		if (D[i][j] == D[i-1][j] + costDelete(src_ld[i])) and \
			(j == N-1 or dst_ld[j+1].level <= src_ld[i].level ):
			#print "DEL:",src_ld[i].tag
			if src_ld[i].tag == "script":
				if src_ld[i].src != 'None':
					del_scripts_hosts.add(src_ld[i].src)
				elif src_ld[i].val != "":
					del_scripts_contents.add(src_ld[i].val)
				try:
					print "  DEL:%s" % src_ld[i].toString().replace('\n','\t')
				except Exception as e:
					print "  Error displaying contents: ",str(e)
			i = i - 1
		elif (D[i][j] == D[i][j-1] + costInsert(dst_ld[j])) and \
			(i == M-1 or src_ld[i+1].level <= dst_ld[j].level):
			#print "INS:",dst_ld[j].tag
			if dst_ld[j].tag == "script":
				if dst_ld[j].src != 'None':
					ins_scripts_hosts.add(dst_ld[j].src)
				elif dst_ld[j].val != "":
					ins_scripts_contents.add(dst_ld[j].val)
				try:	
					print "  INS:%s" % dst_ld[j].toString().replace('\n','\t')
				except Exception as e:
					print "  Error displaying contents: ",str(e)
			j = j - 1
		elif not src_ld[i] == dst_ld[j]:
			#print "UPD: %s => %s " % (src_ld[i].tag, dst_ld[j].tag)
			if src_ld[i].tag == "script" and dst_ld[j].tag == "script":
				updated_scripts_count += 1
				try:
					print "  REPLACE SRC:",src_ld[i].toString().replace('\n','\t')
					print "          DST:",dst_ld[j].toString().replace('\n','\t')
					print "           RS:",compare_two_string(src_ld[i].val, dst_ld[j].val), "END"
				except Exception as e:
					print "  Error displaying contents: ",str(e)
			i = i - 1
			j = j - 1
		else:
			i = i - 1
			j = j - 1

	while i > 0:
		print "DEL:",src_ld[i].tag
		i = i - 1

	while j > 0:
		print "INS:",dst_ld[j].tag
		j = j - 1

	
	#print "insert hosts:"
	#for item in ins_scripts_hosts:
	#	print item
	#print "delete hosts"
	cost = 0
	for item in del_scripts_hosts:
		if item in dst_script_hosts:
			cost += (SCRIPT_COST-1)
		#print item
	for item in del_scripts_contents:
		for other in dst_script_contents:
			if compare_two_string(item, other):
				cost += (SCRIPT_COST-1)
				break
	for item in ins_scripts_hosts:
		if item in src_script_hosts:
			cost += (SCRIPT_COST-1)
		#print item
	for item in ins_scripts_contents:
		for other in src_script_contents:
			if compare_two_string(item, other):
				cost += (SCRIPT_COST-1)
				break

	print "inserted hosts scripts: %d" % len(ins_scripts_hosts)
	print "deleted hosts scripts: %d" % len(del_scripts_hosts)
	print "inserted hosts contents: %d" % len(ins_scripts_contents)
	print "deleted hosts contents: %d" % len(del_scripts_contents)
	print "updated scripts: %d" % updated_scripts_count

	'''
	print "insert contents:"
	for item in ins_scripts_contents:
		try:
			print item
		except Exception as e:
			print "Error: ",str(e)
	print "delete contentes:"
	for item in del_scripts_contents:
		try:
			print item
		except Exception as e:
			print "Error: ",str(e)
	'''
	rs = float(D[M-1][N-1] - cost)
	norm = float(M + N)
	print "Final cost: %f[%f]" %(rs/norm, D[M-1][N-1]/norm)
	return rs/norm

def getLDPairReprHelper(root, result, script_hosts, script_contents):
	result.append(root)
	if root.tag == "script":
		if root.src != "None":
			script_hosts.add(root.src)
		elif root.val != "":
			script_contents.add(root.val)

	for child in root.children:
		getLDPairReprHelper(child, result, script_hosts, script_contents)

def getLDPairRepr(root):
	result = [None]
	script_hosts = set()
	script_contents = set()
	getLDPairReprHelper(root, result, script_hosts, script_contents)
	return result, script_hosts, script_contents

def calcTwoHTMLDistanceFromFiles(dom_path1, dom_path2):	
	contents1 = open(dom1_path).read()
	contents2 = open(dom2_path).read()
	calcTwoHTMLDistance(contents1,contents2)


def calcTwoHTMLDistance(contents1, contents2):
	try:
		soup1 = BeautifulSoup(contents1, "html5lib")
	except Exception as e:
		print "Error parsing DOM using html5 ",str(e)
		soup1 = BeautifulSoup(contents1.decode('utf-8'), "html5lib")
	
	try:
		soup2 = BeautifulSoup(contents2, "html5lib")
	except Exception as e:
		print "Error parsing DOM using html5 ", str(e)
		soup2 = BeautifulSoup(contents2.decode('utf-8'), "html5lib")

	node1 = Node("doc")
	node2 = Node("doc")
	traverseDOMTree(soup1.html,node1, 0)
	traverseDOMTree(soup2.html,node2, 0)
	ld1, ld1_script_hosts, ld1_script_contents = getLDPairRepr(node1)
	ld2, ld2_script_hosts, ld2_script_contents = getLDPairRepr(node2)
	print "script length for ld1: %d %d " % (len(ld1_script_hosts),len(ld1_script_contents))
	print "script length for ld2: %d %d " % (len(ld2_script_hosts),len(ld2_script_contents))
	D = mmdiff(ld1, ld2)
	return mmdiffR(ld1, ld2, D, \
		ld1_script_hosts,ld1_script_contents, ld2_script_hosts, ld2_script_contents)


#################STRING##########################

def longest_common_substring(s1, s2):
	print "longest_common_substring"
	m = [[0] * (1 + len(s2)) for i in xrange(1 + len(s1))]
	longest, x_longest = 0, 0
	for x in xrange(1, 1 + len(s1)):
		for y in xrange(1, 1 + len(s2)):
			if s1[x - 1] == s2[y - 1]:
				m[x][y] = m[x - 1][y - 1] + 1
				if m[x][y] > longest:
					longest = m[x][y]
					x_longest = x
			else:
				m[x][y] = 0
	return s1[x_longest - longest: x_longest]

def similar_strings(s1, s2, threthold):
	new_s1 = s1
	new_s2 = s2
	if len(s1) < len(s2):
		new_s1 = s1 + ' '.ljust(len(s2) - len(s1))
		new_s2 = s2
	elif len(s1) > len(s2):
		new_s2 = s2 + ' '.ljust(len(s1) - len(s2))
		new_s1 = s1
	length = len(new_s1)
	hamming = distance.hamming(new_s1,new_s2,normalized=True)
	#print "hamming %f, threthold: %f" %(hamming, threthold)
	if hamming < 1 - threthold:
		return True

	#print "c1alculating levenshtein ...length: %d vs %d " %(len(s1), len(s2))
	
	integer_threthold = 0
	if min(len(s1), len(s2)) > 15000:
		s1_arr = re.split('[;,]',s1)
		s2_arr = re.split('[;,]',s2)
		#print "using fast levenshtein algorithm: s1-len:%d s2-len:%d" \
		#	%(len(s1_arr), len(s2_arr))
		levenshtein = editdistance.eval(s1_arr, s2_arr)
		integer_threthold = min(len(s1_arr), len(s2_arr)) * (1 - threthold)
	else:
		#print "using standard levenshtein algorithm"
		levenshtein = editdistance.eval(s1, s2)
		integer_threthold = min(len(s1), len(s2)) * (1 - threthold)
	#print "result levenshtein %d vs threthold %d " %(levenshtein,integer_threthold)
	if levenshtein <= integer_threthold:
		return True
	else:
		return False

	return False

def compare_two_string(str1, str2, threthold=0.8):
	if str1 == str2:
		return True
	whilespace = re.compile(r"\s+", re.MULTILINE)
	str1 = whilespace.sub('', str1.lower())
	str2 = whilespace.sub('', str2.lower())
	if str1 == str2:
		return True

	if len(str1) == 0 or len(str2) == 0:
		return False

	# Contain
	if str1 in str2 or str2 in str1:
		print "[INCLUDE: %s IN %s]" % (str1, str2)
		return True
	
	# Short string comparison
	if len(str1) <= 50 and len(str2) <= 50:
		return str1 == str2
	
	# Length difference larger than a threthold
	if abs(len(str1) - len(str2)) > max(len(str1), len(str2)) * 0.3 :
		#print "diff:%d threthold:%f" %(abs(len(str1) - len(str2)), max(len(str1), len(str2)) * 0.1)
		return False

	# Longest string
	return similar_strings(str1, str2, threthold)

##################################################

def main():
	calcTwoHTMLDistanceFromFiles(sys.argv[1], sys.argv[2])

if __name__ == "__main__":
	main()

'''
print "length: ld1:%d  ld2:%d" %(len(ld1), len(ld2))
for i in range(min(len(ld1),len(ld2)) ):
	if ld1[i] == ld2[i]:
		print "YES ",
	else:
		print "NO ",
'''

'''
f1 = open(sys.argv[1])
f2 = open(sys.argv[2])
str1 = ""
str2 = ""
count = 0
for line in f1:
	count += 1
	if count == 60:
		str1 = line.strip()
		break
count = 0
for line in f2:
	count += 1
	if count == 60:
		str2 = line.strip()
		break
print "length: %d vs %d " % (len(str1), len(str2))
'''
#similar_strings(str1, str2, 0.7)
#str3 = longest_common_substring(str1,str2)
#print compareTwoString(str1, str2)