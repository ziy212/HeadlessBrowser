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


def analyzeStringListType(strings):
  if len(strings) < MIN_SAMPLE_SIZE:
  	print >>sys.stderr, "error "
  	return None