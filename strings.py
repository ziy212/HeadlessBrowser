import sys
from enum import Enum
from urlparse import urlparse

MIN_SAMPLE_SIZE = 10
ENUM_THRESHOLD = 0.3
PATTERN_MIN_PREFIX = 3

class StringType(Enum):
  CONST = 1
  ENUM = 2
  PATTERN = 3
  URI = 4
  URI_PATH = 5
  PLAIN_TEXT = 6
  NUMBER = 7

class Attributes():
	def __init__(self, contain_url=False, fixed_len=-1,\
		min_len=-1, max_len=-1, prefix=None):
	pass

def stringIsNumeric(string):
	try:
		if string.isdigit():
			return True
		else:
			val = float(string)
			return True
	except:
		return False

#return (type, value, optional)
def analyzeStringListType(sample_list):
  if len(sample_list) < MIN_SAMPLE_SIZE:
  	print >>sys.stderr, "error: sample size too small"
  	return None, None, None

  sample_dict = {}
  for item in sample_list:
  	item = item.lower().strip()
  	if not item in sample_dict:
  		sample_dict[item] = 1
  	else:
  		sample_dict[item] += 1

  if len(sample_dict) == 1:
  	return StringType.CONST, sample_list[0].lower()

  percent = sorted(\
  	[float(sample_dict[k])/float(len(sample_list)) \
  		for k in sample_dict])
 	if percent[0] > ENUM_THRESHOLD:
 		return StringType.ENUM, sample_dict, None

 	unquoted_sample_list = [urllib.unquote_plus(x) for x in sample_list]
 	is_url = False
 	contain_url = False
 	pattern = "http(s?)\:\/\/"
 	for item in unquoted_sample_list:
	 	try:
	 		item = item.lower()
	 		o = urlparse(item)
	 		scheme = o.scheme
	 		if scheme == "http" or scheme == "https":
	 			is_url = True
 			m = re.match(pattern, item[1:])
 			if m != None:
 				contain_url = True
	 	except Exception as e:
	 		print str(e)
	if is_url = True:
		return StringType.URI, unquoted_sample_list, contain_url

	is_pattern = False
	min_count = len(sample_list)
	for i in range(len(sample_list) - 1):
		count = 0
		rs = [x == y for (x, y) in zip(sample_list[i], sample_list[i+1])]
		for item in rs:
			if item == True:
				count += 1
		if min_count > count:
			min_count = count
	if min_count >= PATTERN_MIN_PREFIX:
		is_pattern = True

	is length_fixed = False
	length_list = sorted([len(x) for x in sample_list])
	min_len = length_list[0]
	max_len = length_list[-1]
	if max_len - min_len <= 2:
		length_fixed = True

  #for item in percent:
  #	print item

analyzeStringListType(['YES','YES','NO','NO','NO','YES','NO','NO','NO','YES','NO']) 


