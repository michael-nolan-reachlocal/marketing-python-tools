#imports
import os
import csv
import csv_tools


""" 
Goals:

x Extract rows by category
- Perform statistics on rows/cols by category
  x Count
  x Sum
  - Average
  - Variance
  - St. Dev.
  - R^2
  - Mean/Median
  - ANOVA

- Generate reports for each stat type
  - Count
  - Sum
  - Average
  - Variance
  - St. Dev.
  - R^2
  - Mean/Median
  - ANOVA

- Generate Combination reports

"""

########################################################################
### CSV Categorization tools
########################################################################

## Get a list of categories
#
# Searches for all unique occurrences of a field, and returns a list.
#
# data: Data to iterate over
# index: List index with the categories

def cat_list(data, index = 0):
	c_list = data[int(index)]
	ret_list = []
	for i in c_list:
		if not i in ret_list:
			ret_list.append(i)

	return ret_list

## Get rows with category
# data: Data to search: a list of lists
# index: List Index to search
# val: Value to match

def cat_rows(data, index, val):
	ret_list = []
	for row in data:
		test_val = row[int(index)]
		if test_val == val:
			ret_list.append(row)
	
	return ret_list

## Get values from rows with a category
# data: data to search - a list of lists
# index: List index to search for rows
# val_indices: List of list indices to return
# val: Category value to match

def cat_vals(data, index, val_indices, val):
	rows = cat_rows(data, index, val)
	ret_list = []
	for row in rows:
		if len(val_indices) != 1:
			sub_row = []
			for val_index in val_indices:
				sub_row.append(row[val_index])
			ret_list.append(sub_row)
		else:
			ret_list.append(row[val_indices[0]])
		
	return ret_list

## Subcategory list
#
# Given a category list, find all subcategories. Returns a dictionary 
# of categories containing a list of subcategories
# data: data formatted as a list of lists
# c_list: List of categories
# index: List index of categories
# sub_index: List index for subcategory

def subcat_list(data, c_list, index, sub_index):
	ret_list = {}
	for c in c_list:
		rows = cat_vals(data, index, [index, sub_index], c)
		sub_list = []
		for row in rows:
			if not row[1] in sub_list:
				sub_list.append(row[1])
		ret_list[c] = sub_list
	return ret_list

########################################################################
### CSV Report Tools - Count
########################################################################

## Count instances of a category
#
# data: data formatted as a list of lists
# index: list index containing the category
# val: String to match

def cat_count_instance(data, index, val):
	rows = cat_rows(data, index, val)
	return len(rows)

## Generate counts report
# Returns a dictionary, with category name for key, and count
# as the value. Assumes data is stored as rows
# f: Data file for generating report
# index: row/column index containing the categories

def cat_count_report(f, index, debug = False):
	list_data = csv_tools.file_read_md(f, 'col', 'all', debug)
	c_list = cat_list(list_data, index)
	data = csv_tools.file_read_md(f, 'row', 'all', debug)
	ret_data = {}
	for c in c_list:
		ret_data[c] = cat_count_instance(data, index, c)
	return ret_data

## Write the counts report
#
#	Writes the count report to a destination file
# f: Path to data file
# dest: Path to destination file
# index: List index for categories

def csv_cat_count_report(f, dest, index, debug = False):
	report_data = cat_count_report(f, index, debug)
	with open(dest, 'wt', newline='') as fi:
		writer = csv.writer(fi, delimiter=',', quotechar='|')
		for item in report_data:
			row = [item, report_data[item]]
			writer.writerow(row)

## Generate counts report for sub-categories
# Returns a dictionary of categories, which in turn contains sub-categories and their counts
# f: Path to data file
# index: List index for categories
# sub_index: List index for subcategories

def subcat_count_report(f, index, sub_index, debug = False):
	list_data = csv_tools.file_read_md(f, 'col', 'all', debug)
	c_list = cat_list(list_data, index)
	data = csv_tools.file_read_md(f, 'row', 'all', debug)
	subc_list = subcat_list(data, c_list, index, sub_index)
	ret_data = {}
	for s in subc_list:
		rows = cat_vals(data, index, [index, sub_index], s)
		ret_data[s] = {}
		for i in subc_list[s]:
			ret_data[s][i] = cat_count_instance(rows, 1, i)
	return(ret_data)

## Write the subcategory counts report
#
#	Writes the subcat report to a destination file
# f: Path to data file
# dest: Path to destination file
# index: List index for categories
# sub_index: List index for subcategories

def csv_subcat_count_report(f, dest, index, sub_index, debug = False):
	report_data = subcat_count_report(f, index, sub_index)
	with open(dest, 'wt', newline='') as fi:
		writer = csv.writer(fi, delimiter=',', quotechar='|')
		n = 1
		for item in report_data:
			for i in report_data[item]:
				row = [item, i, report_data[item][i]]
				writer.writerow(row)
				n += 1
				if n % 100 == 0:
					print ('Wrote %s items' % (str(n)))


########################################################################
### CSV Report Tools - Sum
########################################################################

## Sum instances of a category
#
# data: data formatted as a list of lists
# index: list index containing the category
# val_index: list index containing the values to add
# val: String to match

def cat_sum_instance(data, index, val_index, val):
	rows = cat_rows(data, index, val)
	ret = 0.0
	for row in rows:
		ret += float(row[int(val_index)])
	return ret

## Generate sum report
# Returns a dictionary, with category name for key, and sum
# as the value. Assumes data is stored as rows
# f: Data file for generating report
# index: row/column index containing the categories
# val_index: row/column index containing the values to sum

def cat_sum_report(f, index = 0, val_index = 1, debug = False):
	list_data = csv_tools.file_read_md(f, 'col', 'all', debug)
	c_list = cat_list(list_data, index)
	data = csv_tools.file_read_md(f, 'row', 'all', debug)
	ret_data = {}
	for c in c_list:
		ret_data[c] = cat_sum_instance(data, index, val_index, c)
	return ret_data

## Write the counts report
#
#	Writes the count report to a destination file
# f: Path to data file
# dest: Path to destination file
# index: List index for categories

def csv_cat_sum_report(f, dest, index = 0, val_index = 1, debug = False):
	report_data = cat_sum_report(f, index, val_index, debug)
	with open(dest, 'wt', newline='') as fi:
		writer = csv.writer(fi, delimiter=',', quotechar='|')
		for item in report_data:
			row = [item, report_data[item]]
			writer.writerow(row)

########################################################################
### CSV Report Tools - Average
########################################################################

## Sum instances of a category
#
# data: data formatted as a list of lists
# index: list index containing the category
# val_index: list index containing the values to average
# val: String to match

def cat_avg_instance(data, index, val_index, val):
	count = cat_count_instance(data, index, val)
	s = cat_sum_instance(data, index, val_index, val)
	ret = s/count
	return ret

## Generate average report
# Returns a dictionary, with category name for key, and average
# as the value. Assumes data is stored as rows
# f: Data file for generating report
# index: row/column index containing the categories
# val_index: row/column containing the values to average

def cat_avg_report(f, index = 0, val_index = 1, debug = False):
	list_data = csv_tools.file_read_md(f, 'col', 'all', debug)
	c_list = cat_list(list_data, index)
	data = csv_tools.file_read_md(f, 'row', 'all', debug)
	ret_data = {}
	for c in c_list:
		ret_data[c] = cat_avg_instance(data, index, val_index, c)
	return ret_data

## Write the counts report
#
#	Writes the count report to a destination file
# f: Path to data file
# dest: Path to destination file
# index: List index for categories
# val_index: row/column containing the values to be averaged

def csv_cat_avg_report(f, dest, index = 0 , val_index = 1, debug = False):
	report_data = cat_avg_report(f, index, val_index, debug)
	with open(dest, 'wt', newline='') as fi:
		writer = csv.writer(fi, delimiter=',', quotechar='|')
		for item in report_data:
			row = [item, report_data[item]]
			writer.writerow(row)
