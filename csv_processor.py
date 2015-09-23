#Import needed files
import csv_tools
import csv_stats

# How to compute category indexes:
# In the CSV file, start with column A. This is Index 0. As you count 
# to the right, add 1 per column.

# How to activate a function:
# Just remove the comment character, '#'

# Category Count Report:
# Put the CSV file into the same folder as this one. Then, enter the
# file name, then the destination file name, and finally the column 
# index we are counting in the source file.
print(csv_stats.csv_cat_count_report('call-log.csv', 'call-log-processed-1.csv', 4))

# Subcategory Count Report:
# This is similar to the category count report, but also permits adding 
# a second category. Enter the source file, destination file, first 
# and second (sub)category index.
#print(csv_stats.csv_subcat_count_report('call-log.csv', 'call-log-processed.csv', 4, 1))

# Category Average Report:
# This is similar to the category count report, but instead takes 
# numbers and computes an average. Enter the source file, destination 
# file, catagory index, and the index of the values columne you want to
# average.
#print(csv_stats.csv_cat_avg_report('call-log.csv', 'call-log-processed-1.csv', 0, 1))

# Category Sum Report:
# This is similar to the category average report, but instead computes 
# a sum per category.
#print(csv_stats.csv_cat_avg_report('call-log.csv', 'call-log-processed-1.csv', 0, 1))
