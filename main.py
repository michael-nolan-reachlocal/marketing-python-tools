import kivy
kivy.require('1.9.0') # replace with your current kivy version !

# Non-Kivy libraries

import lxml
from lxml import html
from time import sleep
import threading
from scanner import HTMLScanner
import csv
import csv_tools
import csv_stats
import os

# Apps, layout
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.scrollview import ScrollView
from kivy.uix.filechooser import FileChooserListView

# UI devices
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.togglebutton import ToggleButton

# Generic fallback class for HTMLScanner
class Generic():
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

class AppScreen(FloatLayout):
  count = 0
  idle = True
  aggregate_data = {}
  scan_data = {}
  scan_data_queued = []
  image_metadata = {}
  image_metadata_queued = []
  active_url = ''
  report_widgets = {}
  thread_list = []

  def select(self, *args):
    try: 
      self.ids['import_list'].file_path = args[1][0]
      if '.csv' in self.ids['import_list'].file_path:
        self.ids['import_dialog'].text = "Selected: " + args[1][0]
      else:
        self.ids['import_dialog'].text = "Not a CSV File!"
    except:
      pass

  def start_scan(self):
    #First check that we are idle
    if self.idle:
      # Lock the button until the scan is complete
      self.ids.runButton.text = 'Scanning ...'

      # Get settings
      settings = self.get_settings()

      # Update aggregate report screen
      self.ids.welcome_text.text = ""
      self.ids.welcome_text.size_hint_x = 0
      self.ids.welcome_text.size_hint_y = 0
      
      # Create Aggregate Report
      w = self.ids['report_aggregate_grid']
      w.size_hint_y = 0.9
      l1 = Label(text='Prefix', id='prefix')
      l2 = Label(text='Response Codes', id='status')
      l3 = Label(text='Cache', id='cache')
      l4 = Label(text='Avg. Load Time', id='speed')
      for l in [l1,l2,l3,l4]:
            w.add_widget(l)
            self.report_widgets[l.id] = l
      
      # Check whether we are using the CSV Option, and set up accordingly
      if settings['domain'] == 'csv_import':
        w = self.ids['report_aggregate_grid']
        l1 = Label(text='CSV Import', id='csv')
        l2 = Label(text='200: 0', id='csvstatus')
        l3 = Label(text='Hits: 0, Misses: 0', id='csvcache')
        l4 = Label(text='0 sec', id='csvspeed')
        for l in [l1,l2,l3,l4]:
            w.add_widget(l)
            self.report_widgets[l.id] = l
        # Launch scanner
        settings['prefix'] = ''
        settings['exclude'] = ['#', 'tel:', '+', 'mailto:', 'field_event_date']
        self.aggregate_data = self.aggregate_data[prefix] = {'total': 0, 'status':{200: 0}, 'cache':{'HIT': 0, 'MISS': 0}, 'speed': 0, 'total_time': 0}
        scanner = HTMLScanner(settings, [settings['domain']], self)
        t = threading.Thread(target=scanner.scan_site)
        self.idle = False
        t.start()
        
      else:
        w = self.ids['report_aggregate_grid']
        for country in settings['country']:
          l1 = Label(text=country, id=country)
          l2 = Label(text='200: 0', id=country+'status')
          l3 = Label(text='Hits: 0, Misses: 0', id=country+'cache')
          l4 = Label(text='0 sec', id=country+'speed')
          for l in [l1,l2,l3,l4]:
            w.add_widget(l)
            self.report_widgets[l.id] = l

        # Launch scanner
        for prefix in settings['country']:
          loc_settings = {}
          loc_settings['prefix'] = prefix
          loc_settings['exclude'] = settings['country'][prefix]
          loc_settings['domain'] = settings['domain']
          loc_settings['option'] = settings['option']
          self.aggregate_data[prefix] = {'total': 0, 'status':{200: 0}, 'cache':{'HIT': 0, 'MISS': 0}, 'speed': 0, 'total_time': 0}
          init_link = settings['domain']
          if loc_settings['prefix'] != 'none':
            init_link = init_link + loc_settings['prefix']
          scanner = HTMLScanner(loc_settings, [init_link], self)
          t = threading.Thread(target=scanner.scan_site)
          self.thread_list.append(t)
  
  def get_settings(self):
    # Generate a list of all prefixes
    xlist = ['#', 'tel:', '+', 'mailto:', 'field_event_date', '%23', '?q=', '&q=', '%5B', '%5D']
    for i in self.ids:
      itm = self.ids[i]
      n = itm.__class__.__name__
      if n == 'CButton':
        xlist.append(itm.urlprefix)
    
    # Create global settings; this will be parsed for the scanner later
    settings = {'country':{}, 'domain': '', 'option': []}
    for i in self.ids:
      itm = self.ids[i]
      n = itm.__class__.__name__
      if n == 'CButton':
        if self.ids[i].state == 'down':
          xlist.remove(itm.urlprefix)
          settings['country'][itm.urlprefix] = []
          for it in xlist:
            settings['country'][itm.urlprefix].append(it)
          for item in itm.exclude:
            settings['country'][itm.urlprefix].append(item)
          xlist.append(itm.urlprefix)
      if n == 'DomButton':
        if self.ids[i].state == 'down':
          settings['domain'] = self.ids[i].domain
      if n == 'OptButton':
        if self.ids[i].state == 'down':
          settings['option'].append(i)
    # If we chose a CSV import, add the file path option
    if settings['domain'] == 'csv_import' and '.csv' in self.ids['import_list'].file_path:
      settings['file_path'] = self.ids['import_list'].file_path
    return settings

  def export_raw_to_csv(self):
    # Create local copy of data
    scan_data = self.scan_data
    image_metadata = self.image_metadata
    # Format export list
    export_data = [['URL Prefix','URL Scanned','URL Source','URL section','HTTP Response Code','Cache','Time to DOM Load','Metadata']]
    for item in scan_data:
      d = scan_data[item]
      m = ''
      for i in d['metadata']:
        m = m + i + ': ' + d['metadata'][i].replace(',','*') + '; '
      d_list = [d['prefix'],d['url'],d['source'],d['section'],d['status'],d['cache'],d['time'],m]
      export_data.append(d_list)
    # Add to a csv file
    with open('raw_output.csv', 'wt', newline='') as f:
      writer = csv.writer(f, delimiter=',', quotechar='|')
      for row in export_data:
        writer.writerow(row)
    # Now, repeat the above
    image_data = [['URL Prefix','Image URL','Image Source','Metadata']]
    for item in image_metadata:
      d = image_metadata[item]
      m = ''
      for i in d['metadata']:
        m = m + i + ': ' + d['metadata'][i].replace(',','*') + '; '
      if not m:
        m = 'No Data'
      d_list = [d['prefix'],d['url'],d['source'],m]
      image_data.append(d_list)
    # Add to a csv file
    with open('raw_image_output.csv', 'wt', newline='') as f:
      writer = csv.writer(f, delimiter=',', quotechar='|')
      for row in image_data:
        writer.writerow(row)
  
  def generate_detail_report(self):
    # Create local copy of data
    scan_data = self.scan_data
    # Get Settings
    settings = []
    field_settings = []
    meta_settings = []
    for i in self.ids:
      itm = self.ids[i]
      n = itm.__class__.__name__
      if n == 'ReportOptButton':
        if itm.state == 'down':
          if 'field' in itm.opt or 'meta' in itm.opt:
            field_settings.append(itm.opt)
          else:
            settings.append(itm.opt)
    # Create raw field report
    if "include_raw_report" in settings:
      self.generate_raw_field_report(scan_data, field_settings, settings)
    # Create count report
    if "include_count_report" in settings:
      self.generate_count_report(scan_data, field_settings, settings)
    # Create metadata report
    if "include_image_report" in settings:
      image_data = self.image_metadata
      self.generate_image_metadata_report(image_data, field_settings, settings)

  def sort_data_by_prefix(self, data):
    ret = {}
    for d in data:
      if data[d]['prefix'] in ret:
        ret[data[d]['prefix']].append(data[d])
      else:
        ret[data[d]['prefix']] = []
        ret[data[d]['prefix']].append(data[d])
    return ret

  def list_data_as_global(self, data):
    ret = {'global':[]}
    for d in data:
      ret['global'].append(data[d])
    return ret
      

  def generate_raw_field_report(self, data, field_settings, settings):
    # Sort if we were asked to sort
    if "sort_by_prefix" in settings:
      scan_data = self.sort_data_by_prefix(data)
    else:
      scan_data = self.list_data_as_global(data)
    # Prepare labels
    export_data = [['URL Prefix']]
    labels = [('field_url','URL Scanned'),
    ('field_source','URL Source'),
    ('field_section','URL Section'),
    ('field_status','HTTP Response Code'),
    ('field_cache','Cache'),
    ('field_time','Time to DOM Load'),
    ('meta_title','Meta: Page Title'),
    ('meta_description','Meta: Description'),
    ('meta_abstract','Meta: Abstract'),
    ('meta_keywords','Meta: Keywords')]
    # Add labels
    field_list = []
    meta_list = []
    for l in labels:
      if l[0] in field_settings:
        export_data[0].append(l[1])
        if 'field' in l[0]:
          f = l[0].replace('field_', '')
          field_list.append(f)
        elif 'meta' in l[0]:
          f = l[0].replace('meta_', '')
          meta_list.append(f)
    for prefix in scan_data:
      # Format export list
      for data in scan_data[prefix]:
        data_list = [prefix]
        for field in field_list:
          if field in data:
            data_list.append(data[field])
          else:
            data_list.append('no data')
        for meta in meta_list:
          if meta in data['metadata']:
            data_str = data['metadata'][meta].replace(',','*')
            data_list.append(data_str)
          else:
            data_list.append('no data')
        export_data.append(data_list)

    # Add to a csv file
    with open('field_report.csv', 'wt', newline='') as f:
      writer = csv.writer(f, delimiter=',', quotechar='|')
      for row in export_data:
        writer.writerow(row)

  def generate_count_report(self, data, field_settings, settings):
    # Sort if we were asked to sort
    if "sort_by_prefix" in settings:
      scan_data = self.sort_data_by_prefix(data)
    else:
      scan_data = self.list_data_as_global(data)
    # Remove time property
    '''for prefix in scan_data:
      for item in scan_data[prefix]:
        if 'time' in item:
          del(item['time'])'''
    # Prepare labels
    export_data = [['URL Prefix']]
    labels = [('field_url','URL Scanned'),
    ('field_source','URL Source'),
    ('field_section','URL Section'),
    ('field_status','HTTP Response Code'),
    ('field_cache','Cache'),
    ('meta_title','Meta: Page Title'),
    ('meta_description','Meta: Description'),
    ('meta_abstract','Meta: Abstract'),
    ('meta_keywords','Meta: Keywords')]
    # Add labels
    total_field_list = ['prefix']
    field_list = []
    meta_list = []
    for l in labels:
      if l[0] in field_settings:
        export_data[0].append(l[1])
        if 'field' in l[0]:
          f = l[0].replace('field_', '')
          field_list.append(f)
          total_field_list.append(f)
        elif 'meta' in l[0]:
          f = l[0].replace('meta_', '')
          meta_list.append(f)
          total_field_list.append(f)
    for prefix in scan_data:
      # Format export list
      for data in scan_data[prefix]:
        data_list = [prefix]
        for field in field_list:
          if field in data:
            data_list.append(data[field])
          else:
            data_list.append('no data')
        for meta in meta_list:
          if meta in data['metadata']:
            data_str = data['metadata'][meta].replace(',','*')
            data_list.append(data_str)
          else:
            data_list.append('no data')
        export_data.append(data_list)

    # Create temporary csv file
    with open('_temp.csv', 'wt', newline='') as f:
      writer = csv.writer(f, delimiter=',', quotechar='|')
      for row in export_data:
        writer.writerow(row)
    
    # Generate count report data
    offset = 1
    if 'url' in total_field_list:
      offset += 1
    if 'source' in total_field_list:
      offset += 1
    # Create report data structure
    report_data = {}
    for prefix in scan_data:
      if not prefix in report_data:
        report_data[prefix] = {}
      for i in range(len(total_field_list) - (offset)):
        if not total_field_list[i + offset] in report_data[prefix]:
          report_data[prefix][total_field_list[i + offset]] = {}
        for data in export_data:
          if not data[i + offset] in report_data[prefix][total_field_list[i + offset]]:
            report_data[prefix][total_field_list[i + offset]][data[i + offset]] = 1
          else:
            report_data[prefix][total_field_list[i + offset]][data[i + offset]] += 1
            
    # Convert data to a CSV-friendly format
    report_list = []
    for prefix in scan_data:
      report_list.append(['Data for: ' + prefix])
      for i in range(len(total_field_list) - (offset)):
        report_list.append(['****************************************'])
        report_list.append(['Data type: ' + total_field_list[i + offset]])
        for data in export_data:
          if  data[i + offset] in report_data[prefix][total_field_list[i + offset]]:
            report_list.append([data[i + offset], report_data[prefix][total_field_list[i + offset]][data[i + offset]]])
            del(report_data[prefix][total_field_list[i + offset]][data[i + offset]])
      report_list.append(['****************************************'])
          
    # Write to report file
    with open('field_count_report.csv', 'wt', newline='') as f:
      writer = csv.writer(f, delimiter=',', quotechar='|')
      for row in report_list:
        writer.writerow(row)
    
    # Delete temporary file
    os.remove('_temp.csv')

  def generate_image_metadata_report(self, data, field_settings, settings):
    # Sort if we were asked to sort
    if "sort_by_prefix" in settings:
      image_data = self.sort_data_by_prefix(data)
    else:
      image_data = self.list_data_as_global(data)
    # Add/format labels
    export_data = [['URL Prefix']]
    labels = [('field_url','Image Source'),
    ('field_source','URL Source'),
    ('meta_img_title','Meta: Image Title'),
    ('meta_img_alt','Meta: Image Alt')]
    # Add labels
    field_list = []
    meta_list = []
    for l in labels:
      if l[0] in field_settings:
        export_data[0].append(l[1])
        if 'field' in l[0]:
          f = l[0].replace('field_', '')
          field_list.append(f)
        elif 'meta' in l[0]:
          f = l[0].replace('meta_img_', '')
          meta_list.append(f)
    for prefix in image_data:
      # Format export list
      for data in image_data[prefix]:
        data_list = [prefix]
        for field in field_list:
          if field in data:
            data_list.append(data[field])
          else:
            data_list.append('no data')
        for meta in meta_list:
          if meta in data['metadata']:
            data_str = data['metadata'][meta].replace(',','*')
            data_list.append(data_str)
          else:
            data_list.append('no data')
        export_data.append(data_list)

    # Add to a csv file
    with open('image_meta_report.csv', 'wt', newline='') as f:
      writer = csv.writer(f, delimiter=',', quotechar='|')
      for row in export_data:
        writer.writerow(row)

  def update(self, dt):
    if self.thread_list:
      if self.idle:
        t = self.thread_list.pop(0)
        self.idle = False
        t.start()
    # If the scan is inactive, reset the scan button
    if self.idle:
      self.ids.runButton.text = "Start the Scan"
    # Get the active URL, and show it. Otherwise, show 'idle'
    if self.active_url:
      self.ids['active_url'].text = "Scanning: " + self.active_url
    else:
      self.ids['active_url'].text = "Scanner idle"
    
    # If there is data in the queue, add it to the totals and move data
    # to the 'complete' pile for export.
    if self.scan_data_queued:
      for data in self.scan_data_queued:
        self.scan_data_queued.remove(data)
        # I am not sure why, but this loop is required to prevent all 
        # metadata from being overwritten to the newest value
        data['metadata'] = {}
        for i in data['meta']:
          data['metadata'][i] = data['meta'][i]
        # Update aggregate data
        self.aggregate_data[data['prefix']]['total'] += 1
        self.aggregate_data[data['prefix']]['total_time'] += data['time']
        self.aggregate_data[data['prefix']]['speed'] = self.aggregate_data[data['prefix']]['total_time'] / self.aggregate_data[data['prefix']]['total']
        if data['cache'] == 'HIT':
          self.aggregate_data[data['prefix']]['cache']['HIT'] += 1
        else:
          self.aggregate_data[data['prefix']]['cache']['MISS'] += 1
        
        if data['status'] in self.aggregate_data[data['prefix']]['status']:
          self.aggregate_data[data['prefix']]['status'][data['status']] += 1
        else:
          self.aggregate_data[data['prefix']]['status'][data['status']] = 1
        # Move data from the queue to the finished pile once we are done with it.
        self.scan_data.update({data['url']: data})
    
    # If there is data in the image metadata queue, add it to the 
    # totals and move data to the 'complete' pile for export.
    if self.image_metadata_queued:
      for data in self.image_metadata_queued:
        self.image_metadata_queued.remove(data)
        # I am not sure why, but this loop is required to prevent all 
        # metadata from being overwritten to the newest value
        data['metadata'] = {}
        for i in data['meta']:
          data['metadata'][i] = data['meta'][i]
        # Move data from the queue to the finished pile once we are done with it.
        self.image_metadata.update({data['url']: data})
    
    # Update the live report
    for prefix in self.aggregate_data:
      # Status Codes
      stats = self.aggregate_data[prefix]['status']
      stat_str = ''
      count = 0
      for stat in stats:
        stat_str = stat_str + str(stat) + ': ' + str(stats[stat]) + ', '
        count += 1
        if count % 2 == 0 and count != 0:
          stat_str = stat_str + '\n'
      self.report_widgets[prefix+'status'].text = stat_str
      # Cache hits/misses
      hit = self.aggregate_data[prefix]['cache']['HIT']
      miss = self.aggregate_data[prefix]['cache']['MISS']
      self.report_widgets[prefix+'cache'].text = 'Hit: ' + str(hit) + '\n' + 'Miss: ' + str(miss)
      # Site Speed
      spd = self.aggregate_data[prefix]['speed']
      self.report_widgets[prefix+'speed'].text = "{0:.2f}".format(round(spd,2)) + ' sec'

      

# Define the app
class QAApp(App):
  def build(self):
    app = AppScreen()
    Clock.schedule_interval(app.update, 0.1)
    return app


if __name__ == '__main__':
    QAApp().run()
