import sys, os

def removeDuplicateItemsFromFiles(target_file_path, sample_file_path):
  target_f = open(target_file_path)
  sample_f = open(sample_file_path)
  sample_set = set()
  for item in sample_f:
    item = item.strip()
    sample_set.add(item)
  result_set = set()
  for item in target_f:
    item = item.strip()
    if not item in sample_set:
      result_set.add(item)
  return result_set

def main():
  s = removeDuplicateItemsFromFiles(sys.argv[1],sys.argv[2])
  for item in s:
    print item

if __name__ == "__main__":
  main()