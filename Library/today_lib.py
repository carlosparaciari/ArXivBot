import time
import datetime

# The function which_weekday takes as argument a GMT time stamp,
# and returns a string with the weekday (Sun, Mon, Tue, Wed, Thu, Fri, Sat)

def which_weekday(time_information):

	return time.strftime("%a", time_information)

# The function what_time takes as argument a GMT time stamp,
# and returns an int composed by hour of the day (0-24) and minutes (0-60).
#
# For example, if the time is 17:23, the function returns 1723

def what_time(time_information):

	return int( time.strftime("%H%M", time_information) )

# The function move_current_date takes as argument a GMT time stamp,
# and returns a string with the date ( year, month, day without
# commas or spaces) moved by the int number_of_days.

def move_current_date(number_of_days, time_information):

	current_date = time.strftime("%m/%d/%y", time_information)
	input_date = datetime.datetime.strptime(current_date, "%m/%d/%y")
 	output_date = input_date + datetime.timedelta( days = number_of_days )

 	return datetime.datetime.strftime(output_date, "20%y%m%d")