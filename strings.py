import sys, re, tldextract, json
from enum import Enum
from urlparse import urlparse

MIN_SAMPLE_SIZE = 10
ENUM_THRESHOLD = 0.3
PATTERN_MIN_PREFIX = 3

class StringType(Enum):
  CONST = "CONST"
  ENUM = "ENUM"
  NUMBER = "NUMBER"
  URI = "URI"
  OTHER = "OTHER"

class Pattern():
	def __init__(self, fixed_len=-1,\
		min_len=-1, max_len=-1, prefix=None, alphanumeric=False, \
		special_char_set = None, domain_set = None):
		self.fixed_len = fixed_len
		self.min_len = min_len
		self.max_len = max_len
		self.prefix = prefix
		self.alphanumeric = alphanumeric
		self.special_char_set = special_char_set
		self.domain_set = domain_set

	def check(self, string):
		string = string.lower()
		if self.fixed_len != -1 and self.fixed_len != len(string):
			print "%s length is not correct" %string
			return False
		if self.min_len != -1 and len(string) < self.min_len:
			print "%s length is too short" %string
			return False
		if self.max_len != -1 and len(string) > self.max_len:
			print "%s length is too short" %string
			return False
		if self.prefix != None and (not string.startswith(self.prefix)):
			print "%s prefix is too correct" %string
			return False
		if self.alphanumeric and (not stringIsNumeric(string)):
			print "%s is not alphanumeric" %string
			return False
		if self.special_char_set != None and \
			(not (getSpecialCharacters(string) <= self.special_char_set)):
			print "%s contains not allowed characters" %string
			return False
		if self.domain_set != None and \
			(not (getDomainsFromString(string) <= self.domain_set)):
			print "%s contains not allowed domains" %string
			return False
		return True

	def loads(self, obj):
		try:
			self.fixed_len = obj['fixed_len']
			self.min_len = obj['min_len']
			self.max_len = obj['max_len']
			self.prefix = obj['prefix']
			self.alphanumeric = obj['alphanumeric']
			self.special_char_set = obj['special_char_set']
			self.domain_set = obj['domain_set']
		except Exception as e:
			print >> sys.stderr, "error in loading contents to pattern ", str(e)
			return False

	def dumps(self):
		try:
			obj = {}
			obj['fixed_len'] = self.fixed_len
			obj['min_len'] = self.min_len
			obj['max_len'] = self.max_len
			obj['prefix'] = self.prefix
			obj['alphanumeric'] = self.alphanumeric
			obj['special_char_set'] = self.special_char_set
			obj['domain_set'] = self.domain_set
			return json.dumps(obj)
		except Exception as e:
			print >> sys.stderr, "error in dumping contents ", str(e)
			return json.dumps({})

def getEffectiveDomainFromURL(url):
  try:
    o = tldextract.extract(url.lower())
    return o.domain + '.' + o.suffix
  except Exception as e:
    print >> sys.stderr, "error in getting getEffectiveDomain ", str(e)
    return None

def getDomainsFromString(string):
	string = string.lower()
	pattern = re.compile("https?\:\/\/")
	pos = 0
	rs = set()
	try:
		while True:
			m = pattern.search(string, pos)
			if m == None:
				break
			domain = getEffectiveDomainFromURL(string[m.start():])
			rs.add(domain)
			pos = m.start() + 1
		return rs
	except Exception as e:
		print >> sys.stderr, "error in getDomainsFromString ", str(e)
		return set()

def stringIsNumeric(string):
	try:
		if string.isdigit():
			return True
		else:
			val = float(string)
			return True
	except:
		return False

def stringIsAlphanumericUnderscore(string):
	pattern = "^\w+$"
	try:
		m = re.match(pattern, string)
		return m != None
	except Exception as e:
		print >> sys.stderr, "error in stringIsAlphanumericUnderscore ", str(e)
		return False

def getSpecialCharacters(string):
	pattern = "\W"
	try:
		rs = re.findall(pattern, string)
	except Exception as e:
		print >> sys.stderr, "error in getSpecialCharacters ", str(e)
		return set()
	char_set = set(rs)
	return char_set

#return (type, value)
def analyzeStringListType(sample_list):
  if len(sample_list) < MIN_SAMPLE_SIZE:
  	print >>sys.stderr, "error: sample size too small"
  	return None, None

  # Test CONST
  sample_dict = {}
  for item in sample_list:
  	item = item.lower().strip()
  	if not item in sample_dict:
  		sample_dict[item] = 1
  	else:
  		sample_dict[item] += 1

  if len(sample_dict) == 1:
  	return StringType.CONST, None

  # Test ENUM
  percent = sorted(\
  	[float(sample_dict[k])/float(len(sample_list)) \
  		for k in sample_dict])
 	if percent[0] > ENUM_THRESHOLD:
 		return StringType.ENUM, sample_dict

 	# Test URI
 	unquoted_sample_list = [urllib.unquote_plus(x) for x in sample_list]
 	domain_set = set()
 	url_count = 0
 	pattern = "http(s?)\:\/\/"
 	for item in unquoted_sample_list:
	 	try:
	 		item = item.lower()
	 		o = urlparse(item)
	 		scheme = o.scheme
	 		if scheme == "http" or scheme == "https":
	 			url_count += 1
 			cur_domains = getDomainsFromString(item)
 			domain_set = domain_set.union(cur_domains)
	 	except Exception as e:
	 		print str(e)
	if url_count == len(unquoted_sample_list):
		return StringType.URI, domain_set

	# Test NUMBER
	numeric_count = 0
	for item in sample_list:
		if stringIsNumeric(item):
			numeric_count += 1
	if numeric_count == len(sample_list):
		return StringType.NUMBER, None

	# fixed_len, min_len, max_len
	patt = Pattern(domain_set=domain_set)
	length_list = sorted([len(x) for x in sample_list])
	min_len = length_list[0]
	max_len = length_list[-1]
	if min_len == max_len:
		patt.fixed_len = min_len
	if max_len - min_len <= 2:
		patt.min_len = min_len
		patt.max_len = max_len

	# prefix
	sorted_list = sorted(sample_list)
	for i in range(min_len):
		if sorted_list[0][i] != sorted_list[-1][0]:
			break
	if i >= PATTERN_MIN_PREFIX:
		patt.prefix = sorted_list[0][:i]

	# special_char_set
	special_char_set = set()
	for item in sample_list:
		s = getSpecialCharacters(item)
		special_char_set = getSpecialCharacters.union(s)
	if len(special_char_set) > 0:
		patt.special_char_set = special_char_set

	return StringType.OTHER, patt

analyzeStringListType(['YES','YES','NO','NO','NO','YES','NO','NO','NO','YES','NO']) 


