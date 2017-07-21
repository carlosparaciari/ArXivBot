import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'Library')))

import time
from nose.tools import assert_raises, assert_equal
import today_lib as tl

# The test shows how the function which_weekday works
def test_which_weekday_passes():

	time_information = time.strptime('Thu 20 Jul 2017 12:15:31', '%a %d %b %Y %H:%M:%S')
	obtained_result = tl.which_weekday(time_information)
	expected_result = 'Thu'

	assert_equal(obtained_result, expected_result, "The obtained weekday is different from the expected one")

# The test shows how the function what_time works
def test_what_time_passes():

	time_information = time.strptime('Thu 20 Jul 2017 12:15:31', '%a %d %b %Y %H:%M:%S')
	obtained_result = tl.what_time(time_information)
	expected_result = 1215

	assert_equal(obtained_result, expected_result, "The obtained weekday is different from the expected one")

# The test shows how the function move_current_date works for future days
def test_move_current_date_future():

	time_information = time.strptime('Thu 20 Jul 2017 12:15:31', '%a %d %b %Y %H:%M:%S')
	number_of_days = 2

	obtained_result = tl.move_current_date(number_of_days, time_information)
	expected_result = '20170722'

	assert_equal(obtained_result, expected_result, "The obtained weekday is different from the expected one")

# The test shows how the function move_current_date works for past days
def test_move_current_date_past():

	time_information = time.strptime('Thu 20 Jul 2017 12:15:31', '%a %d %b %Y %H:%M:%S')
	number_of_days = -2

	obtained_result = tl.move_current_date(number_of_days, time_information)
	expected_result = '20170718'

	assert_equal(obtained_result, expected_result, "The obtained weekday is different from the expected one")

# Test of move_current_date function for funny days of the year
def test_move_current_date_special_days():

	time_information = [time.strptime('Sun 2 Jul 2017 12:15:31', '%a %d %b %Y %H:%M:%S'),
						time.strptime('Mon 27 Feb 2017 12:15:31', '%a %d %b %Y %H:%M:%S'),
						time.strptime('Tue 1 Mar 2016 12:15:31', '%a %d %b %Y %H:%M:%S'),
						time.strptime('Wed 30 Dec 2015 12:15:31', '%a %d %b %Y %H:%M:%S'),
						time.strptime('Tue 3 Jan 2017 12:15:31', '%a %d %b %Y %H:%M:%S')
						]
	number_of_days = [-3, 4, -2, 2, -5]
	expected_results = ['20170629', '20170303', '20160228', '20160101', '20161229']

	for time_info, days, expected_result in zip(time_information, number_of_days, expected_results):

		obtained_result = tl.move_current_date(days, time_info)
		assert_equal(obtained_result, expected_result, "The obtained weekday is different from the expected one")