from urlparse import urlparse
from urllib import unquote_plus
import sys,os
import HTMLParser, tldextract
html_parser = HTMLParser.HTMLParser()

def decodeURL(url):
  url = url.lower()
  unquote_url = unquote_plus(url)
  unescape_url = html_parser.unescape(unquote_url)
  return unescape_url

def generateGoogleURLKey(url):
  url = decodeURL(url)
  o = urlparse(url)
  if "aclk" in o.path and \
    "adurl=" in o.query:
    return None
  query = None
  if o.query != "":
    tmp = o.query.split('&')
    for item in tmp:
      if item.startswith('q='):
        query = item.strip()
        break
  if query != None:
    url = o.scheme + "://" + o.netloc + o.path +'&'+query
  else:
    url = o.scheme + "://" + o.netloc + o.path
  return url

def preProcessGoogleURLList(url_list):
  url_dict = {}
  for url in url_list:
    key = generateGoogleURLKey(url)
    if key == None:
      continue
    if key in url_dict:
      continue
    url_dict[key] = url
  return url_dict

def getEffectiveDomainFromURL(url):
  try:
    o = tldextract.extract(url.lower())
    return o.domain + '.' + o.suffix
  except Exception as e:
    print >> sys.stderr, "error in getting getEffectiveDomain ", str(e)
    return None

def getEssentialPartOfURL(url):
  try:
    o = urlparse(url)
    if o.params == '' and o.query=='' and o.fragment=='':
      x = o.path.split('/')
      if len(x) > 1:
        path = '/'.join(x[:-1])
        return o.scheme + "://" + o.netloc + path 
    return o.scheme + "://" + o.netloc + o.path 
  except Exception as e:
    print >> sys.stderr, "error in getting getEssentialPartOfURL ", str(e)
    return None

def preProcessRegularURLLlist(main_url, url_list):
  main_domain = getEffectiveDomainFromURL(main_url)
  if main_domain == None or url_list == None:
    return None
  url_dict = {}
  for url in url_list:
    domain = getEffectiveDomainFromURL(url)
    #print "domain %s of %s " %(domain, url)
    if domain == None or domain != main_domain:
      continue
    u = getEssentialPartOfURL(url)
    if u == None:
      continue
    if u not in url_dict:
      url_dict[u] = []
    url_dict[u].append(url.lower())
  return url_dict

def main():
  #USAGE: file_name dst_folder_name
  file_name = os.path.basename(sys.argv[1].lower())
  if not file_name.endswith('.txt'):
    print "filename should be domain.txt"
    return
  domain = file_name[:-4]
  print domain
  full_dst_name = os.path.join(sys.argv[2], domain+'.txt')
  train_dst_name = os.path.join(sys.argv[2], domain+'_train.txt')
  test_dst_name = os.path.join(sys.argv[2], domain+'_test.txt')

  f = open(sys.argv[1])
  f_full = open(full_dst_name,'w')
  f_train = open(train_dst_name, 'w')
  f_test = open(test_dst_name, 'w')

  url_list = []
  for line in f:
    line = line.strip()
    url_list.append(line)
  print "Read %d lines of urls" %(len(url_list))
  print 'main url: %s'%(url_list[0])
  
  url_dict = preProcessRegularURLLlist(url_list[0], url_list)
  print "After processing, generating %d lines of urls" %(len(url_dict))
  count = 0
  for k in url_dict:
    vals = list(set(url_dict[k]))[:10]
    for v in vals:
      count += 1
      f_full.write(v+'\n')
      if count < 2000:
        f_train.write(v+'\n')
      elif count <2500:
        f_test.write(v+'\n')

  
  f_full.close()
  f_train.close()
  f_test.close()
  f.close()

if __name__=="__main__":
  main()
    
