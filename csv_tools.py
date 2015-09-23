#imports
import os
import csv


""" 
Goals:

x Read/skip headers if needed
x 1D reader, multi-D reader (Each row/column)
x Retrieve row + col info (height, width)
- Read/Edit a specific point, row, or column
x Retrieve a list of rows/columns
x Write rows/columns
x Transpose data
"""

########################################################################
### CSV File basic data
########################################################################

# Flip row/column
def flip_orient(orient):
	if orient == 'row':
		return 'col'
	else:
		return 'row'

# Gets the width of a CSV file, assuming the first row contains the max # of columns

def get_width(f):
	with open(f, 'rt') as fi:
		reader = csv.reader(fi, delimiter=',', quotechar='|')
		row = next(reader)
		return len(row)

# Gets the height of a CSV file

def get_height(f):
	with open(f, 'rt') as fi:
		reader = csv.reader(fi, delimiter=',', quotechar='|')
		i = 0
		for row in reader:
			i += 1
		return i

# Converts dictionaries to lists, in which the dictionary value is a 
# list aka a data dimension
def dim_to_list(dim):
	lst = []
	for key,value in dim.items():
		temp = [key]
		for i in value:
			temp.append(i)
		lst.append(temp)
	return lst[0]

########################################################################
### Row Readers and Editors
########################################################################

## Read 1 dimenision (row/col) from a file
# f: File, provide as filename
# header: Is the first item to be read a header?
# order: The row/column to read
# orient: read a row or column. Pass 'row' or 'col'
# return: either a list or dictionary containing the csv values

def file_read_1d(f, orient = 'row', order = 0, header = True, debug = False):
	with open(f, 'rt') as fi:
		reader = csv.reader(fi, delimiter=',', quotechar='|')
		
		# If entry data is invalid, return false
		if (header != True and header != False) \
		or (not isinstance(order, int)) \
		or (orient != 'row' and orient != 'col'):
			print('One of your entries was invalid.')
			print(" ".join(header, order, orient))
			return False
		
		ret = {}
		
		# Start with row/column orientation, then apply order, then header
		if orient == 'row':
			i = 0
			for row in reader:
				if i == order:
					if header:
						head = row[0]
						ret[head] = row[1:]
						break
					else:
						ret = row
						break
				i += 1
				if debug and i == order and order % 500 == 0:
						print("Read %s rows in %s." % (str(order), str(f)))
		
		#col orientation		
		elif orient == 'col':
			if header:
				head_row = next(reader)
				head = head_row[order]
				item_list = []
				i = 0
				for row in reader:
					item = row[order]
					item_list.append(item)
					i += 1
					if debug and i % 500 == 0:
						print("Read %s items in Column %s of %s." % (str(i), str(order), str(f)))
				
				ret[head] = item_list
			
			else:
				item_list = []
				i = 0
				for row in reader:
					item = row[order]
					item_list.append(item)
					i += 1
					if debug and i % 500 == 0:
						print("Read %s items in Column %s of %s." % (str(i), str(order), str(f)))
				
				ret = item_list
		
		return ret

## Read 1 dimenision (row/col) from a list of lists
# data:Data to read
# order: The row/column to read
# orient: read a row (list) or column (index in list). Pass 'row' or 'col'
# return: either a list or dictionary containing the csv values

def data_read_1d(data, orient = 'row', order = 0, debug = False):
		
	# If entry data is invalid, return false
	if (not isinstance(order, int)) \
	or (orient != 'row' and orient != 'col'):
		print('One of your entries was invalid.')
		print(" ".join(header, order, orient))
		return False
	
	ret = []
	
	# Row orientation
	if orient == 'row':
		ret = data[order]
	
	#col orientation		
	elif orient == 'col':
		item_list = []
		for row in data:
			item = row[order]
			item_list.append(item)
		
		ret = item_list
	
	return ret

## Multi-dimensional reading column class
# f: File, provide as filename
# headers: Is the first item to be read a header?
# order: A list of rows/columns to read, or 'all'
# orient: read a row or column to the end.
# return: a list of either lists or dictionary containing the csv values

def file_read_md(f, orient = 'row', order = 'all', debug = False):
	with open(f, 'rt') as fi:
		reader = csv.reader(fi, delimiter=',', quotechar='|')
		# If order == 'all', rewrite order list accordingly
		if order == 'all':
			height = get_height(f)
			width = get_width(f)
			if orient == 'row':
				order = range(0,height)
			elif orient == 'col':
				order = range(0,width)
		# Now that we've got the order list, run file_read_1d once per dimension
		ret_list = []
		data = []
		
		for i, row in enumerate(reader):
			data.append(row)
			if debug and i % 1000 == 0:
				print('Read %s items in %s' % (str(i), str(f)))
		if order == 'all':
			if orient == 'row':
				ret_list = data
			if orient == 'col':
				ret_list = data_transpose(data)
		else:
			for i in order:
				ret_list.append(data_read_1d(data, orient, i, debug))
		
		return ret_list

## Write multiple dimensions to a file
# f: File to write to
# data: List of entires to write; list based

def write_md(f, data, orient = 'row'):
	#set destination to temp if we need to transpose
	dest = f
	if orient == 'col':
		dest = '_tempfile.csv'
	#write rows
	with open(dest, 'wt', newline='') as fi:
		writer = csv.writer(fi, delimiter=',', quotechar='|')
		for row in data:
			writer.writerow(row)
	if orient == 'col':
		file_transpose('_tempfile.csv', f)
		os.remove('_tempfile.csv')
		

## Raw Merge: Merge two CSV files together without looking at data
# f1: Path of first input file
# f2: Path of second input file
# dest: Path of destination file
# orient: Read and merge by rows or columns

def merge_raw(f1, f2, dest, orient = 'row', debug = False):
	data1 = file_read_md(f1, orient, 'all', False, debug)
	data2 = file_read_md(f2, orient, 'all', False, debug)
	data = data1 + data2
	write_md(dest, data, orient)

## Find a row/column with property
# Reads a CSV file, and returns data with a matching field value as 
# a list. Searches a given index, not all values in a row/column
#
# f: File to search
# val: Value to match
# i: Row/column index to search
# orient: Search by row/column

def find_dim(f, val, i = 0, orient = 'row', debug = False):
	search = 'row'
	if orient == 'row':
		search = 'col'
	search_list = file_read_md(f, search, [i], False, debug)
	n = 0
	stop = False
	for x in search_list[0]:
		if str(x) == str(val):
			stop = True
		if not stop:
			n += 1
	if not stop:
		return False
	else:
		dim = file_read_md(f, orient, [n], False, debug)
		return dim[0]

## Merge by common property
# Iterates through a row or column on two tables, and if matched, adds
# the column/row from the first and second table to an output table.
#
# Example:
#
#	table1         table2
#	key1           key1, val1
#                key2, val2
# Yields:
#
# newtable
# key1, key1, val1
#
# f1: First CSV file, contains "keys" to search for
# f2: Second CSV file, contains potential matches
# dest: Destination file
# orient: Read/merge by rows or columns
# key: The key field from f1, given as a row/column index
# search: The search field from f2, given as a row/column index

def merge_by_field(f1, f2, dest, orient = 'row', key = 0, search = 0, f_reject = 'none', debug = False):
	compare_list = file_read_1d(f1, orient, key, False)
	base_orient = 'row'
	if orient == 'row':
		base_orient = 'col'
	if debug:
		print('Reading data...')
	dim_base = file_read_md(f1, base_orient, 'all', False, debug)
	data = []
	data_reject = []
	
	if debug:
		print('Commencing merge...')
	i = 0
	
	for item in dim_base:
		new_dim = find_dim(f2, item[int(key)], int(search), base_orient)
		if new_dim != False:
			data.append(item + new_dim)
		else:
			if f_reject != 'none':
				data_reject.append(item)
			else:
				data.append(item)
		if debug:
			i += 1
			if i % 100 == 0:
				print('Processed %s items' % (str(i)))
	
	if debug:
		print('Merge Complete, writing to file...')
	write_md(dest, data, base_orient)
	if f_reject != 'none':
		write_md(f_reject, data_reject, base_orient)

## Transpose items in one file by writing to a new file
# source: Source file
# dest: Destination file

def file_transpose(source, dest):
	if source == dest:
		print('Source cannot equal destination!')
	data = file_read_md(source, 'col', 'all', False, debug)
	write_md(dest, data)

## Transpose data
# data: Data to transpose

def data_transpose(data):
	length = len(data[0])
	r = range(0,length)
	new_data = []
	for i in r:
		print(i)
		new_row = data_read_1d(data,'col',i)
		new_data.append(new_row)
	return(new_data)


########################################################################
### Point Readers and Editors
########################################################################

## Point reader
# f: CSV file to read
# row: Row Index
# col: Column Index
# headers: Whether the data has a header row

def read_point(f, row, col, headers = True):
	width = get_width(f)
	height = get_height(f)
	if headers:
		height -= 1
	if row >= width or col >= height:
		print('Your coordinates are out of bounds!')
		print('Row: max ' + str(width) + ', yours was ' + str(row))
		print('Col: max ' + str(height) + ', yours was ' + str(col))
		return False
	else:
		column = file_read_1d(f, 'col', col, headers)
		lst = []
		if headers:
			lst = next(iter(column.values()))
		else:
			lst = column
		point = lst[row]
		return point

## Point Finder
# f: CSV file to read
# val: value to find

def find_point(f, val, headers = True, debug = False):
	ret = False
	coord = {}
	coord['row'] = -1
	coord['col'] = -1
	data = file_read_md(f, 'col', 'all', headers, debug)
	
	if headers:
		for col in data:
			pass
	else:
		pass
	
	if ret:
		return coord
	else:
		print('Value "' + str(val) + '" was not found!')
		return False

## Point Editor
# f: CSV file to read
# row:
# col:
# val: New Value for row/col index

