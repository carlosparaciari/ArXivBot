from nose.tools import assert_raises, assert_equal
import arxiv_lib as al
from customised_exceptions import NoArgumentError, GetRequestError
from subprocess import check_call
import requests
import time

# ADVANCED SEARCH TESTS

# When no arguments are passed, we need to raise error (NoArgumentError)
def test_advanced_search_no_arguments():

	link = 'http://export.arxiv.org/api/query?search_query='	

	with assert_raises(NoArgumentError):
		al.advanced_search(False, False, False, False, False, False, False, False, link)

# When the response from arxiv is wrong (HTTPError)
def test_advanced_search_status_code():

	link = 'http://export.arxiv.org/apii/query?search_query=au:sparaciari_c'	

	with assert_raises(requests.exceptions.HTTPError):
		al.request_to_arxiv(link)

# When the request to arxiv goes well
def test_advanced_search_correct():

	link = 'http://export.arxiv.org/api/query?search_query='
	test_file = 'text_response_test_advanced_search.txt'

	search_link = al.advanced_search('sparaciari_c', 'kullback', False, False, False, False, False, False, link)
	response = al.request_to_arxiv(search_link).text

	with open(test_file, 'r') as f:
		expected = f.read()

	# We remove the first few information, containing the current date.
	assert_equal(response[504:], expected[504:], "The obtained response is different from the expected one")

# SIMPLE SEARCH TESTS

# When no arguments are passed, we need to raise error
def test_simple_search_no_arguments():

	link = 'http://export.arxiv.org/api/query?search_query='	

	with assert_raises(NoArgumentError):
		al.simple_search(False, link)

# When the simple search returns the correct link for a string argument
def test_simple_search_correctness_str():

	link = 'http://export.arxiv.org/api/query?search_query='
	correct_link = 'http://export.arxiv.org/api/query?search_query=all:electron'

	obtained_link = al.simple_search('electron', link)

	assert_equal(obtained_link, correct_link, "The obtained link is different from the expected one")

# When the simple search returns the correct link for a list argument
def test_simple_search_correctness_list():

	link = 'http://export.arxiv.org/api/query?search_query='
	correct_link = 'http://export.arxiv.org/api/query?search_query=all:electron+AND+all:proton'

	obtained_link = al.simple_search(['electron', 'proton'], link)

	assert_equal(obtained_link, correct_link, "The obtained link is different from the expected one")

# REQUEST TO ARXIV TESTS

# When anything but a string is passed to the al.request_to_arxiv it needs to rise error (TypeError)
def test_request_to_arxiv_no_string():

	possible_arguments = [1, 1., [1, 'a'], False, {'a' : 1}]

	for arg in possible_arguments:
		with assert_raises(TypeError):
			al.request_to_arxiv(arg)

# When the link is not in the correct format (MissingSchema)
def test_request_to_arxiv_wrong_link_format():

	link = 'wrong_link_format'

	with assert_raises(requests.exceptions.MissingSchema):
		al.request_to_arxiv(link)

# When there is not Internet Connection (GetRequestError) - Need administrator privileges to work:
# def test_request_to_arxiv_no_connection():
	
# 	link = 'http://export.arxiv.org/api/query?search_query=au:sparaciari_c'	

# 	# We simulate the absence of internet connection by turning off the wifi
# 	# For Windows use : netsh interface set interface "Wi-Fi" disabled
# 	check_call('netsh interface set interface "Wi-Fi" disabled',shell=True)

# 	with assert_raises(GetRequestError):
# 		al.request_to_arxiv(link)

# 	# We turn it on stright after, waiting 15 seconds to be sure we are up and running
# 	# For Windows use : netsh interface set interface "Wi-Fi" enabled
# 	check_call('netsh interface set interface "Wi-Fi" enabled',shell=True)
# 	time.sleep(10)

# PARSE RESPONSE TESTS

# when the argument of parse response is not a requests.Respones, need to return error
def test_parse_response_wrong_argument():

	possible_arguments = [1, 1., [1, 'a'], False, {'a' : 1}]

	for arg in possible_arguments:
		with assert_raises(TypeError):
			al.parse_response(arg)

# when the parse response work fine
def test_parse_response_correct():

	link = 'http://export.arxiv.org/api/query?search_query=all:electron+AND+all:proton'
	test_file = 'text_parsing_test.txt'

	response = al.request_to_arxiv(link)
	parsed_response = al.parse_response(response)

	# We select the abstract of the first paper downloaded
	abstract_obtained = parsed_response['entries'][0]['summary_detail']['value']

	with open(test_file, 'r') as f:
		expected_abstract = unicode( f.read() , "utf-8")
	
	assert_equal(abstract_obtained, expected_abstract, "The obtained response is different from the expected one")

	return 0

# REVIEW RESPONSE TESTS

# when the argument of review response is not a dictionary, need to return error
def test_review_response_wrong_argument():

	possible_arguments = [1, 1., [1, 'a'], False]

	for arg in possible_arguments:
		with assert_raises(TypeError):
			al.review_response(arg)

# when the dictionary does not have the field 'entries'
def test_review_response_no_entries():

	dictionary = {'a' : 1 , 'b' : 'hi'}

	with assert_raises(NoArgumentError):
		al.review_response(dictionary)

# when the dictionary has the field 'entries', but is not a list
def test_review_response_entries_no_list():

	dictionary = {'a' : 1 , 'b' : 'hi' , 'entries' : 'this is not a list'}

	with assert_raises(TypeError):
		al.review_response(dictionary)

# when the dictionary has the field 'entries', it is a list, but not a list of dictionaries
def test_review_response_entries__list_no_dictionary():

	dictionary = {'a' : 1 , 'b' : 'hi' , 'entries' : [1,2,3]}

	with assert_raises(TypeError):
		al.review_response(dictionary)

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

	result_list = al.review_response(dictionary)

	expected_list = [{'title' : u'Nice Title', 'authors' : u'Carlo', 'year' : u'1992', 'link' : 'www.hi.com'}]

	assert_equal(result_list, expected_list, "The obtained response is different from the expected one")

# general test, from the link to the result list given by review_response
def test_review_response_correct_from_link():

	link = 'http://export.arxiv.org/api/query?search_query=all:electron+AND+all:proton'
	test_file = 'text_parsing_test.txt'

	response = al.request_to_arxiv(link)
	parsed_response = al.parse_response(response)

	result_list = al.review_response(parsed_response)

	expected_list = {'link': u'http://arxiv.org/abs/0806.3233v1',
					 'authors': u"Anatoly Yu. Smirnov, Sergey E. Savel'ev, Franco Nori",
					 'year': u'2008',
					 'title': u'Shuttle-mediated proton pumping across the inner mitochondrial membrane'}

	assert_equal(result_list[4], expected_list, "The obtained response is different from the expected one")

# IS FIELD THERE TESTS

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

# ONE LINE TITLE TESTS

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

# COMPATC AUTHORS TESTS

# when the author field is not there, compact_authors should give None
def test_compact_authors_no_entry():

	dictionary = {'a' : 1 , 'b' : 'hi'}

	element = al.compact_authors(dictionary)

	assert_equal(element, None, "The obtained response is different from the expected one")

# when the author field is not a list, compact_authors should give None
def test_compact_authors_no_list():

	dictionary = {'a' : 1 , 'b' : 'hi', 'authors' : 2}

	element = al.compact_authors(dictionary)

	assert_equal(element, None, "The obtained response is different from the expected one")

# when the author field is a list of auhtors, but they do not have the field 'name'
def test_compact_authors_no_name():

	dictionary = {'a' : 1 , 'b' : 'hi', 'authors' : [{'c' : 1},{'d' : False}] }

	element = al.compact_authors(dictionary)

	assert_equal(element, None, "The obtained response is different from the expected one")

# when the author field is a list of auhtors, each of them with 'name', but they are not strings
def test_compact_authors_no_strings():

	dictionary = {'a' : 1 , 'b' : 'hi', 'authors' : [{'name' : 1},{'name' : False}] }

	element = al.compact_authors(dictionary)

	assert_equal(element, None, "The obtained response is different from the expected one")

# when the author field is a list of auhtors, each of them with 'name', and a unicode string associated to it
def test_compact_authors_correct():

	dictionary = {'a' : 1 , 'b' : 'hi',
			      'authors' : [{'name' : unicode('Carlo Sparaciari', "utf-8")},
			      			   {'name' : 2},
			      			   {'title' : False},
							   {'name' : unicode('Thomas Galley', "utf-8")},
							   {'name' : 3}
							  ]
			     }

	element = al.compact_authors(dictionary)

	expected_element = unicode('Carlo Sparaciari, Thomas Galley' , "utf-8")

	assert_equal(element, expected_element, "The obtained response is different from the expected one")

# FIND YEAR TESTS

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