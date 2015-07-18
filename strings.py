import sys
from enum import Enum

MIN_SAMPLE_SIZE = 10

class StringType(Enum):
  CONST = 1
  ENUM = 2
  PATTERN = 3
  URI = 4
  URI_PATH = 5
  PLAIN_TEXT = 6


def analyzeStringListType(sample_list):
  if len(sample_list) < MIN_SAMPLE_SIZE:
  	print >>sys.stderr, "error "
  	return None

  sample_dict = {}
  for item in sample_list:
  	item = item.strip()
  	if not item in sample_list:
  		sample_dict[item] = 1
  	else:
  		sample_dict[item] += 1

  if len(sample_dict) == 1:
  	return StringType.CONST
