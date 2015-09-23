import requests
import lxml
import time
import csv
from lxml import html
from html.parser import HTMLParser

# Generic fallback class for HTMLScanner
class Generic():
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

# HTML Parser class which geretes a list of found links
class LinkParser(HTMLParser):
  link_list = []
  exclude_list = []
  
  def handle_starttag(self, tag, attrs):
    for item in attrs:
      if item[0] == 'src' or item[0] == 'href':
        add = True
        for ex in self.exclude_list:
          if ex in item[1]:
            add = False
        if add:
          self.link_list.append(item[1])

# HTML Parser class which geretes a list of found links
class MetaParser(HTMLParser):
  meta_list = {}
  current_url_data = {}
  target_obj = Generic()
  title_tag = False

  def handle_starttag(self, tag, attrs):
    # Check if title tag
    if tag == 'title':
      self.title_tag = True
    elif tag == 'meta':
      metadata = {}
      # Get the name and content properties
      for item in attrs:
        metadata[item[0]] = item[1]
      # Now, insert these properties IF they are part of our report
      if 'name' in metadata:
        if metadata['name'] == 'description' or metadata['name'] == 'keywords' or metadata['name'] == 'abstract':
          self.meta_list[metadata['name']] = metadata['content']
    elif tag == 'img':
      metadata = {}
      for item in attrs:
        if item[0] == 'src' or item[0] == 'alt' or item[0] == 'title':
          metadata[item[0]] = item[1]
      data = {}
      data['url'] = metadata['src']
      del(metadata['src'])
      data['source'] = self.current_url_data['url']
      data['prefix'] = self.current_url_data['prefix']
      data['meta'] = metadata
      self.target_obj.image_metadata_queued.append(data)
      

  def handle_data(self, data):
    if self.title_tag:
      self.meta_list['title'] = data
  
  def handle_endtag(self, tag):
    if tag == 'title':
      self.title_tag = False


# HTML Scanner
#
# Inputs:
#
# settings:
# read_list: A list of URLs to scan. These should be full URLs
# target_obj: Update a target object with information returned by the scanner
# 
# Outputs:
# 
# HTML Scanner doesn't return anything, but does port report data to a 
# target object. This report data is formatted as a list of dicts 
# (URL prefixes), with each dict containing a dict for each scanned URL.
# This dict, in turn, contains a dict with:
# - The scanned URL
# - The page it was found on
# - The page load time
# - Cache hit/miss data
class HTMLScanner():
  # Settings for HTML scanner
  settings = {}
  read_list = []
  target_obj = Generic()
  url_data = {}
  aggregate_data = {}
  # Initial setup
  #
  # settings: Dictionary of settings needed to set up the scanner
  # 
  # init_list: List of URLs to kick off site scan
  #
  # target_obj: Target object to update
  def __init__(self, settings, read_list, target_obj = Generic()):
    self.settings = settings
    self.read_list = read_list
    self.target_obj = target_obj
  
  # Sort links into file-type links, external links, and internal links
  # All links should be complete URLs (with http) when entered.
  def is_valid_link(self, url, settings):
    options = settings['option']
    dom = settings['domain']
    # Get last element in URL. The file extension, etc. is here.
    url_parts = url.split('/')
    url_last = url_parts[len(url_parts) - 1]
    # Check if link is internal. If so, it is always valid 
    if dom in url:
      if not '.' in url_last or '.htm' in url_last:
        return True
      # Next, check for internal files
      elif 'files' in options:
        return True
      else:
        return False
    # Finally, look at external links
    elif 'external' in options:
      return True
    else:
      return False
  
  def is_excluded(self, url, exclude_list):
    excluded = False
    for ex in exclude_list:
      if ex in url:
        excluded = True
    return excluded
  
  # Given a valid page, extract all links by category, and return a list
  # of categorized links with the right prefix
  def extract_links_from_page(self, url, domain, prefix, exclude_list):
    # Start the list with the URL we are scanning
    link_list = [url]
    if not 'index-only' in self.settings['option']:
      # First, read the page and get every link out of it.
      try:
        req = requests.get(url, headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'})
        parser = LinkParser()
        parser.exclude_list = exclude_list
        parser.feed(str(req.text.encode("utf-8")))
        for link in parser.link_list:
          skip = False
          # Next, some link cleanup. Check if link has http
          if 'http' in link:
            pass
          # If not, determine if the link is a relative link.
          elif '/' in link[0]:
            # Link with // at the start. Add http
            if len(link) > 1 and link[1] == '/':
              link = 'http:' + link
            # Link with prefix but not domain. Add domain
            elif prefix and prefix != 'none' and prefix in link:
              link = domain + link
            # Link with neither domain nor prefix. Add both
            else:
              if not self.is_excluded(link, exclude_list):
                if prefix != 'none':
                  link = domain + prefix + link
                else:
                  link = domain + link
              else:
                link = domain
                skip = True
          # In this case, we have a same-level link (i.e. href="here.html")
          else:
            base = url.split('?')
            base = base[0]
            link = base + '/' + link
          # Remove exclusions
          if not self.is_excluded(link, exclude_list) and not skip and not link in self.url_data:
            link_list.append(link)
          else:
            pass
        # Return the cleaned list:
        return link_list
      except:
        return link_list
    else:
      return link_list
        
  
  # Check headers for cache and other information
  def check_headers(self, header_dict = {}):
    # Check for whether the page has been cached
    cache_bool = False
    for h in header_dict:
      if (h == 'x-cache' or h == 'x-drupal-cache') and header_dict[h] == 'HIT':
        cache_bool = True
    if cache_bool:
      return 'HIT'
    else:
      return 'MISS'

  def get_section(self,url):
    sec = url.split('/')
    if len(sec) >= 6:
      return sec[5]
    else:
      return ''

  # Process a URL: Read the page, update running list
  def process_url(self, url, source):
    try:
      s = time.time()
      req = requests.get(url, headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'})
      e = time.time()
      url_data = {}
      url_data['source'] = source
      url_data['url'] = url
      url_data['section'] = self.get_section(url)
      url_data['status'] = req.status_code
      url_data['time'] = e - s
      url_data['cache'] = self.check_headers(req.headers)
      if 'meta' in self.settings['option']:
        meta = MetaParser()
        meta.target_obj = self.target_obj
        meta.current_url_data = url_data
        meta.current_url_data['prefix'] = self.settings['prefix']
        meta.feed(bytes(req.text, 'utf-8').decode('utf-8'))
        url_data['meta'] = meta.meta_list
      else:
        url_data['meta'] = {'Meta':'No Metadata recorded'}
    except:
      return {'source': source, 'url':url, 'section': self.get_section(url), 'status': 'Crawl Error', 'time': 0, 'cache': 'Error', 'meta': {'title':'Not read'}}
    return url_data
  
  # Determine whether to scan a domain, or a list of URLs:
  def scan_site(self):
    if 'file_path' in self.settings:
      self.scan_by_list(self.settings['file_path'])
    else:
      self.scan_by_domain()

  #Scan a CSV list of URLs. Assumes all URLs are full links
  def scan_by_list(self, f):
    if '.csv' in self.settings['file_path']:
      with open(self.settings['file_path'], 'rt') as fi:
        reader = csv.reader(fi, delimiter=',', quotechar='|')
        for row in reader:
          url = row[0]
          settings = self.settings
          # Extract a domain for is_valid_link()
          l = url.split('/')
          dom = l[2]
          link_list = self.extract_links_from_page(row[0], 'http://' + dom, settings['prefix'], settings['exclude'])
          for link in link_list:
            if self.is_valid_link(link, {'domain': dom,'option': settings['option']}) and not link in self.url_data:
              self.target_obj.active_url = link
              self.url_data[link] = self.process_url(link, url)
              self.url_data[link]['prefix'] = 'csv'
              self.target_obj.scan_data_queued.append(self.url_data[link])
      # Once the scan is complete, set the scanner back to idle
      self.target_obj.idle = True
    else:
      print('Not a CSV file')

  # Scan a site given the settings
  def scan_by_domain(self):
    self.url_data = {}
    for url in self.read_list:
      # Build list of links on page
      link_list = self.extract_links_from_page(url, self.settings['domain'], self.settings['prefix'], self.settings['exclude'])
      for link in link_list:
        settings = self.settings
        if self.is_valid_link(link, settings) and not link in self.url_data:
          self.target_obj.active_url = link
          self.url_data[link] = self.process_url(link, url)
          self.url_data[link]['prefix'] = self.settings['prefix']
          self.target_obj.scan_data_queued.append(self.url_data[link])
          # If the link is a valid internal link, add it to the read list:
          if self.is_valid_link(link, {'domain': settings['domain'], 'option':['interal']}):
            self.read_list.append(link)
    # debug
    # Once the scan is complete, set the scanner back to idle
    self.target_obj.idle = True
