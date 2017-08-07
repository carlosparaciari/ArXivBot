import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'Library')))

from nose.tools import assert_raises, assert_equal
import arxiv_lib as al
from customised_exceptions import NoArgumentError, GetRequestError,NoCategoryError
from subprocess import check_call
import requests
import time
import cgi

# NOTICE : A few tests make a request to the arXiv.
# 		   In order to satisfy the arXiv regulation, a 3-second delay is used every time the test
#		   makes a request to the arXiv (ONLY 3 tests at the moment)

# ---------------------------------- ADVANCED SEARCH TESTS ----------------------------------

# when no arguments are passed, we need to raise error (NoArgumentError)
def test_advanced_search_no_arguments():

	link = 'http://export.arxiv.org/api/query?search_query='	

	with assert_raises(NoArgumentError):
		al.advanced_search(False, False, False, False, False, False, False, False, link)

# when the response from arXiv is wrong (HTTPError)
def test_advanced_search_status_code():

	link = 'http://export.arxiv.org/apii/query?search_query=au:sparaciari_c'	

	with assert_raises(requests.exceptions.HTTPError):
		al.request_to_arxiv(link)

# when the request to arXiv goes well
def test_advanced_search_correct():

	link = 'http://export.arxiv.org/api/query?search_query='
	test_file = os.path.join('Data', 'text_response_test_advanced_search.txt')

	search_link = al.advanced_search('sparaciari_c', 'kullback', False, False, False, False, False, False, link)
	response = al.request_to_arxiv(search_link).text
	time.sleep(3)

	with open(test_file, 'r') as f:
		expected = f.read()

	# We remove the first few information, containing the current date.
	assert_equal(response[504:], expected[504:], "The obtained response is different from the expected one")

# ---------------------------------- SIMPLE SEARCH TESTS ----------------------------------

# when no arguments are passed, we need to raise error
def test_simple_search_no_arguments():

	link = 'http://export.arxiv.org/api/query?search_query='	

	with assert_raises(NoArgumentError):
		al.simple_search(False, link)

# when the simple search returns the correct link for a string argument
def test_simple_search_correctness_str():

	link = 'http://export.arxiv.org/api/query?search_query='
	correct_link = 'http://export.arxiv.org/api/query?search_query=all:electron'

	obtained_link = al.simple_search('electron', link)

	assert_equal(obtained_link, correct_link, "The obtained link is different from the expected one")

# when the simple search returns the correct link for a Unicode argument
def test_simple_search_correctness_unicode():

	link = 'http://export.arxiv.org/api/query?search_query='
	correct_link = 'http://export.arxiv.org/api/query?search_query=all:electron'

	obtained_link = al.simple_search(u'electron', link)

	assert_equal(obtained_link, correct_link, "The obtained link is different from the expected one")

# when the simple search returns the correct link for a string list argument
def test_simple_search_correctness_str_list():

	link = 'http://export.arxiv.org/api/query?search_query='
	correct_link = 'http://export.arxiv.org/api/query?search_query=all:electron+AND+all:proton'

	obtained_link = al.simple_search(['electron', 'proton'], link)

	assert_equal(obtained_link, correct_link, "The obtained link is different from the expected one")

# when the simple search returns the correct link for a Unicode list argument
def test_simple_search_correctness_unicode_list():

	link = 'http://export.arxiv.org/api/query?search_query='
	correct_link = 'http://export.arxiv.org/api/query?search_query=all:electron+AND+all:proton'

	obtained_link = al.simple_search([u'electron', u'proton'], link)

	assert_equal(obtained_link, correct_link, "The obtained link is different from the expected one")

# ---------------------------------- SINGLE CATEGORY TEST ----------------------------------

# test that the function single_category raises an exception when it does not receive an integer
def test_single_category_not_integer():

	wrong_argument = 'this is a string'

	with assert_raises(TypeError):
		al.single_category(wrong_argument)

# test that the function single_category raises an exception when the argument is not between 0 and len(ALL_CATEGORIES)
def test_single_category_wrong_index():

	wrong_index_neg = -1
	wrong_index_pos = al.number_categories()

	with assert_raises(IndexError):
		al.single_category(wrong_index_neg)

	with assert_raises(IndexError):
		al.single_category(wrong_index_pos)

# test that the function single_category works correctly
def test_single_category_correct():

	correct_indices = [0, 3, al.number_categories() - 1]
	expected_results = ['stat.AP', 'stat.ME', 'quant-ph']

	for ind, expected_result in zip(correct_indices, expected_results):
		obtained_result = al.single_category(ind)
		assert_equal(obtained_result, expected_result, "The obtained result is different from the expected one")

# ---------------------------------- COSTUMISED NUMBER OF RESULTS TEST ----------------------------------

# test that the function specify_number_of_results raises a ValueError when a negative number of results is passed
def test_specify_number_of_results_negative():

	link = 'http://export.arxiv.org/api/query?search_query=all:electron'
	number_of_results = -1

	with assert_raises(ValueError):
		al.specify_number_of_results(link, number_of_results)

# test that the function specify_number_of_results raises a ValueError when a negative number of results is passed
def test_specify_number_of_results_correct():

	link = 'http://export.arxiv.org/api/query?search_query=all:electron'
	correct_link = 'http://export.arxiv.org/api/query?search_query=all:electron&max_results=15'
	number_of_results = 15

	obtained_link = al.specify_number_of_results(link, number_of_results)

	assert_equal(obtained_link, correct_link, "The obtained link is different from the expected one")

# ---------------------------------- TODAY'S SUBMISSIONS TEST ----------------------------------

# test that the time range we use is the same of the arXiv (checked at https://arxiv.org/help/submit#availability)
def test_time_range_for_today_search():

	time_information = [time.strptime('Wed 19 Jul 2017 12:15:31', '%a %d %b %Y %H:%M:%S'),
						time.strptime('Thu 20 Jul 2017 12:15:31', '%a %d %b %Y %H:%M:%S'),
						time.strptime('Fri 21 Jul 2017 12:15:31', '%a %d %b %Y %H:%M:%S'),
						time.strptime('Sat 22 Jul 2017 12:15:31', '%a %d %b %Y %H:%M:%S'),
						time.strptime('Sun 23 Jul 2017 12:15:31', '%a %d %b %Y %H:%M:%S'),
						time.strptime('Mon 24 Jul 2017 12:15:31', '%a %d %b %Y %H:%M:%S'),
						time.strptime('Tue 25 Jul 2017 12:15:31', '%a %d %b %Y %H:%M:%S')
						]
	expected_results = ['submittedDate:[201707171800+TO+201707181800]',
					    'submittedDate:[201707181800+TO+201707191800]',
					    'submittedDate:[201707191800+TO+201707201800]',
					    'submittedDate:[201707191800+TO+201707201800]',
					    'submittedDate:[201707191800+TO+201707201800]',
					    'submittedDate:[201707201800+TO+201707211800]',
					    'submittedDate:[201707211800+TO+201707241800]'
					    ]

	for time_info, expected_result in zip(time_information, expected_results):

		obtained_result = al.time_range_for_today_search(time_info)
		assert_equal(obtained_result, expected_result, "The obtained time range is different from the expected one")

# test on the function category_exists
def test_category_exists_correct():

	existing_category = 'cs.GT'
	non_existing_category = 'not.cat'

	assert_equal( al.category_exists( existing_category ), True, "The obtained boolean is different from the expected one")
	assert_equal( al.category_exists( non_existing_category ), False, "The obtained boolean is different from the expected one")

# test if search_day_submissions raises error for wrong category
def test_search_day_submissions_wrong_category():

	link = 'http://export.arxiv.org/api/query?search_query=all:electron'
	time_information = time.strptime('Wed 19 Jul 2017 12:15:31', '%a %d %b %Y %H:%M:%S')
	non_existing_category = 'not.cat'

	with assert_raises(NoCategoryError):
		al.search_day_submissions(time_information, non_existing_category, link)

# test if search_day_submissions returns the expected link for the search
def test_search_day_submissions_correct():

	link = 'http://export.arxiv.org/api/query?search_query='
	time_information = time.strptime('Wed 19 Jul 2017 12:15:31', '%a %d %b %Y %H:%M:%S')
	arxiv_category = 'math.DS'

	expected_result = 'http://export.arxiv.org/api/query?search_query=cat:math.DS+AND+submittedDate:[201707171800+TO+201707181800]'
	obtained_result = al.search_day_submissions(time_information, arxiv_category, link)

	assert_equal( obtained_result, expected_result, "The obtained link is different from the expected one")

# ---------------------------------- REQUEST TO ARXIV TESTS ----------------------------------

# when anything but a string is passed to the al.request_to_arxiv it needs to rise error (TypeError)
def test_request_to_arxiv_no_string():

	possible_arguments = [1, 1., [1, 'a'], False, {'a' : 1}]

	for arg in possible_arguments:
		with assert_raises(TypeError):
			al.request_to_arxiv(arg)

# when the link is not in the correct format (MissingSchema)
def test_request_to_arxiv_wrong_link_format():

	link = 'wrong_link_format'

	with assert_raises(requests.exceptions.MissingSchema):
		al.request_to_arxiv(link)

# when there is not Internet Connection (GetRequestError) - Need administrator privileges to work:
# def test_request_to_arxiv_no_connection():
	
# 	link = 'http://export.arxiv.org/api/query?search_query=au:sparaciari_c'	

# 	# We simulate the absence of internet connection by turning off the wifi
# 	# For Windows use : netsh interface set interface "Wi-Fi" disabled
# 	check_call('netsh interface set interface "Wi-Fi" disabled',shell=True)

# 	with assert_raises(GetRequestError):
# 		al.request_to_arxiv(link)

# 	# We turn it on straight after, waiting 15 seconds to be sure we are up and running
# 	# For Windows use : netsh interface set interface "Wi-Fi" enabled
# 	check_call('netsh interface set interface "Wi-Fi" enabled',shell=True)
# 	time.sleep(10)

# ---------------------------------- PARSE RESPONSE TESTS ----------------------------------

# when the argument of parse response is not a requests.Response, need to return error
def test_parse_response_wrong_argument():

	possible_arguments = [1, 1., [1, 'a'], False, {'a' : 1}]

	for arg in possible_arguments:
		with assert_raises(TypeError):
			al.parse_response(arg)

# when the parse response work fine
def test_parse_response_correct():

	link = 'http://export.arxiv.org/api/query?search_query=all:electron+AND+all:proton'
	test_file = os.path.join('Data', 'text_parsing_test.txt')

	response = al.request_to_arxiv(link)
	time.sleep(3)
	parsed_response = al.parse_response(response)

	# We select the abstract of the first paper downloaded
	abstract_obtained = parsed_response['entries'][0]['summary_detail']['value']

	with open(test_file, 'r') as f:
		expected_abstract = unicode( f.read() , "utf-8")
	
	assert_equal(abstract_obtained, expected_abstract, "The obtained response is different from the expected one")

	return 0

# ---------------------------------- REVIEW FEED TESTS ----------------------------------

# tests that the method total_number_results raises error if it does not receive a dictionary
def test_total_number_results_wrong_argument():

	not_dictionary = 'This is a string'

	with assert_raises(TypeError):
			al.total_number_results(not_dictionary)
	
# tests that the method total_number_results raises error if dictionary has no key 'feed'
def test_total_number_results_no_feed():

	dictionary = {'key1' : 1 , 'key2' : 'hello'}

	with assert_raises(NoArgumentError):
			al.total_number_results(dictionary)

# tests that the method total_number_results raises error if dictionary has the key 'feed', but it is not a dictionary
def test_total_number_results_wrong_feed():

	dictionary = {'key1' : 1 , 'key2' : 'hello', 'feed' : 'this is a string'}

	with assert_raises(TypeError):
			al.total_number_results(dictionary)

# tests that the method total_number_results raises error if dictionary does not has the key 'totalresults'
def test_total_number_results_no_totalresults():

	dictionary = {'key1' : 1 , 'key2' : 'hello', 'feed' : {'key3' : True}}

	with assert_raises(NoArgumentError):
			al.total_number_results(dictionary)

# tests that the method total_number_results returns the correct value
def test_total_number_results_correct():

	dictionary = {'key1' : 1 , 'key2' : 'hello', 'feed' : {'opensearch_totalresults' : u'13'}}

	obtained_result = al.total_number_results(dictionary)
	expected_result = 13

	assert_equal(obtained_result, expected_result, "The obtained number is different from the expected one")

# ---------------------------------- REVIEW RESPONSE TESTS ----------------------------------

# when the maximum number of authors of review response is not an int, needs to return error
def test_review_response_wrong_number_type():

	dictionary = {'a' : 1, 'entries' : [{ 'key1' : 1, 'key2' : 2}, { 'key3' : 3, 'key4' : 4}]}
	max_number = 'this is a string'

	with assert_raises(TypeError):
		al.review_response(dictionary, max_number)

# when the maximum number of authors of review response is not bigger or equal to 1, needs to return error
def test_review_response_wrong_number_type():

	dictionary = {'a' : 1, 'entries' : [{ 'key1' : 1, 'key2' : 2}, { 'key3' : 3, 'key4' : 4}]}
	max_numbers = [-1, 0]

	for max_number in max_numbers:
		with assert_raises(ValueError):
			al.review_response(dictionary, max_number)

# when the argument of review response is not a dictionary, needs to return error
def test_review_response_wrong_argument():

	possible_arguments = [1, 1., [1, 'a'], False]

	for arg in possible_arguments:
		with assert_raises(TypeError):
			al.review_response(arg, 100)

# when the dictionary does not have the field 'entries'
def test_review_response_no_entries():

	dictionary = {'a' : 1 , 'b' : 'hi'}

	with assert_raises(NoArgumentError):
		al.review_response(dictionary, 100)

# when the dictionary has the field 'entries', but is not a list
def test_review_response_entries_no_list():

	dictionary = {'a' : 1 , 'b' : 'hi' , 'entries' : 'this is not a list'}

	with assert_raises(TypeError):
		al.review_response(dictionary, 100)

# when the dictionary has the field 'entries', it is a list, but not a list of dictionaries
def test_review_response_entries__list_no_dictionary():

	dictionary = {'a' : 1 , 'b' : 'hi' , 'entries' : [1,2,3]}

	with assert_raises(TypeError):
		al.review_response(dictionary, 100)

# when the dictionary has the field 'entries', and is a list of dictionaries, and one entry is correct
def test_review_response_correct():

	dictionary = {'a' : 1 , 'b' : 'hi' ,
				  'entries' : [{'noise' : True,
				  				'title' : u'Nice Title',
				  				'animal' : 'Dog',
				  				'authors' : [{'name' : u'Carlo'}],
				  				'date' : u'1992-05-12',
				  				'link' : 'www.hi.com'},
				  			   {'noise' : False,
				  			   	'animal' : 'Frog'}
				  			  ]}

	result_list = al.review_response(dictionary, 100)

	expected_list = [{'title' : u'Nice Title', 'authors' : u'Carlo', 'year' : u'1992', 'link' : 'www.hi.com'}]

	assert_equal(result_list, expected_list, "The obtained response is different from the expected one")

# general test, from the link to the result list given by review_response
def test_review_response_correct_from_link():

	link = 'http://export.arxiv.org/api/query?search_query=au:sparaciari_c+AND+ti:kullback'

	response = al.request_to_arxiv(link)
	time.sleep(3)
	parsed_response = al.parse_response(response)

	result_list = al.review_response(parsed_response, 100)

	expected_list = {'link': u'http://arxiv.org/abs/1311.6008v2',
					 'authors': u"Carlo Sparaciari, Stefano Olivares, Francesco Ticozzi, Matteo G. A. Paris",
					 'year': u'2014',
					 'title': u'Exact and approximate solutions for the quantum minimum-Kullback-entropy estimation problem'}

	assert_equal(result_list[0], expected_list, "The obtained response is different from the expected one")

# ---------------------------------- IS FIELD THERE TESTS ----------------------------------

# when the filed is not there, al.is_field_there should give None
def test_is_field_there_no():

	dictionary = {'a' : 1 , 'b' : 'hi'}

	element = al.is_field_there(dictionary,'c')

	assert_equal(element, None, "The obtained response is different from the expected one")
	
# when the filed is there, al.is_field_there should give a value
def test_is_field_there_no():

	dictionary = {'a' : 1 , 'b' : 'hi'}

	element = al.is_field_there(dictionary,'a')

	assert_equal(element, 1, "The obtained response is different from the expected one")

# ---------------------------------- ONE LINE TITLE TESTS ----------------------------------

# when the title field is not there, one_line_title should give None
def test_one_line_title_no_entry():

	dictionary = {'a' : 1 , 'b' : 'hi'}

	element = al.one_line_title(dictionary)

	assert_equal(element, None, "The obtained response is different from the expected one")

# when the title field is there, but it is not a string
def test_one_line_title_wrong_entry():

	dictionary = {'a' : 1 , 'b' : 'hi', 'title' : 1}

	element = al.one_line_title(dictionary)

	assert_equal(element, None, "The obtained response is different from the expected one")

# when the title field is there, and there is a string with no \n
def test_one_line_title_no_newline():

	title_string = u'Once upon a time'
	dictionary = {'a' : 1 , 'b' : 'hi', 'title' : title_string}

	element = al.one_line_title(dictionary)

	assert_equal(element, title_string, "The obtained response is different from the expected one")

# when the title field is there, and there is a string with \n
def test_one_line_title_newline():

	title_string = u'Once upon\n a time'
	expected_string = u'Once upon a time'

	dictionary = {'a' : 1 , 'b' : 'hi', 'title' : title_string}

	element = al.one_line_title(dictionary)

	assert_equal(element, expected_string, "The obtained response is different from the expected one")

# when the title field has a symbol as <, >, or &, we replace with the HTML symbol.
def test_one_line_title_escape():

	title_string = u'4 > 3 & 5 < 6'
	expected_string = u'4 &gt; 3 &amp; 5 &lt; 6'

	dictionary = {'a' : 1 , 'b' : 'hi', 'title' : title_string}

	element = al.one_line_title(dictionary)

	assert_equal(element, expected_string, "The obtained response is different from the expected one")

# ---------------------------------- COMPATC AUTHORS TESTS ----------------------------------

# when the author field is not there, compact_authors should give None
def test_compact_authors_no_entry():

	dictionary = {'a' : 1 , 'b' : 'hi'}

	element = al.compact_authors(dictionary, 100)

	assert_equal(element, None, "The obtained response is different from the expected one")

# when the author field is not a list, compact_authors should give None
def test_compact_authors_no_list():

	dictionary = {'a' : 1 , 'b' : 'hi', 'authors' : 2}

	element = al.compact_authors(dictionary, 100)

	assert_equal(element, None, "The obtained response is different from the expected one")

# when the author field is a list of authors, but they do not have the field 'name'
def test_compact_authors_no_name():

	dictionary = {'a' : 1 , 'b' : 'hi', 'authors' : [{'c' : 1},{'d' : False}] }

	element = al.compact_authors(dictionary, 100)

	assert_equal(element, None, "The obtained response is different from the expected one")

# when the author field is a list of authors, each of them with 'name', but they are not strings
def test_compact_authors_no_strings():

	dictionary = {'a' : 1 , 'b' : 'hi', 'authors' : [{'name' : 1},{'name' : False}] }

	element = al.compact_authors(dictionary, 100)

	assert_equal(element, None, "The obtained response is different from the expected one")

# when the author field is a list of authors, each of them with 'name', and a Unicode string associated to it
def test_compact_authors_correct():

	dictionary = {'a' : 1 , 'b' : 'hi',
			      'authors' : [{'name' : unicode('Carlo Sparaciari', "utf-8")},
			      			   {'name' : 2},
			      			   {'title' : False},
							   {'name' : unicode('Thomas Galley', "utf-8")},
							   {'name' : 3}
							  ]
			     }

	element = al.compact_authors(dictionary, 100)

	expected_element = unicode('Carlo Sparaciari, Thomas Galley' , "utf-8")

	assert_equal(element, expected_element, "The obtained response is different from the expected one")

# when the authors are more than expected, cut the list and replace with 'et al.'
def test_compact_authors_cut_number():

	dictionary = {'a' : 1 , 'b' : 'hi', 'authors' : [{'name' : unicode('Carlo Sparaciari', "utf-8")},
							   						 {'name' : unicode('Thomas Galley', "utf-8")},
							  						 {'name' : unicode('Cameron Deans', "utf-8")}
							  						]
			      }

	expected_strings = [unicode('Carlo Sparaciari, et al.' , "utf-8"),
						unicode('Carlo Sparaciari, Thomas Galley, et al.' , "utf-8"),
						unicode('Carlo Sparaciari, Thomas Galley, Cameron Deans' , "utf-8")
					   ]

	max_number_authors = range(1,4)
	for expected_string, max_number in zip(expected_strings, max_number_authors):
		obtained_string = al.compact_authors(dictionary, max_number)
		assert_equal(expected_string, obtained_string, "The obtained string is different from the expected one")

# ---------------------------------- FIND YEAR TESTS ----------------------------------

# when the date field is not there, find_year should give None
def test_find_year_no_entry():

	dictionary = {'a' : 1 , 'b' : 'hi'}

	element = al.find_year(dictionary)

	assert_equal(element, None, "The obtained response is different from the expected one")

# when the date field is there, but it is not associated with a string
def test_find_year_wrong_entry():

	dictionary = {'a' : 1 , 'b' : 'hi', 'date' : 3}

	element = al.find_year(dictionary)

	assert_equal(element, None, "The obtained response is different from the expected one")

# when the date field is there, but it is not associated with a string
def test_find_year_wrong_length():

	dictionary = {'a' : 1 , 'b' : 'hi', 'date' : u'123'}

	element = al.find_year(dictionary)

	assert_equal(element, None, "The obtained response is different from the expected one")

# when find year works fine
def test_find_year_correct():

	dictionary = {'a' : 1 , 'b' : 'hi', 'date' : u'1234567'}

	element = al.find_year(dictionary)

	assert_equal(element, u'1234', "The obtained response is different from the expected one")