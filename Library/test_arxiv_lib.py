from nose.tools import assert_raises, assert_equal
from arxiv_lib import request_to_arxiv, advanced_search
from customised_exceptions import NoArgumentError, GetRequestError
from subprocess import DEVNULL, STDOUT, check_call
import requests
import time

# When anything but a string is passed to the request_to_arxiv it needs to rise error (TypeError)
def test_request_to_arxiv_no_string():

	possible_arguments = [1, 1., [1, 'a'], False, {'a' : 1}]

	for arg in possible_arguments:
		with assert_raises(TypeError):
			request_to_arxiv(arg)

# When the link is not in the correct format (MissingSchema)
def test_request_to_arxiv_wrong_link_format():

	link = 'wrong_link_format'

	with assert_raises(requests.exceptions.MissingSchema):
		request_to_arxiv(link)

# When no arguments are passed, we need to raise error (NoArgumentError)
def test_advanced_search_no_arguments():

	link = 'http://export.arxiv.org/api/query?search_query='	

	with assert_raises(NoArgumentError):
		advanced_search(False, False, False, False, False, False, False, False, link)

# When the link is not in the correct format (InvalidSchema)
def test_advanced_search_wrong_link_format():

	link = 'wrong_link_format'

	with assert_raises(requests.exceptions.InvalidSchema):
		advanced_search('sparaciari_c', False, False, False, False, False, False, False, link)
		
# When there is not Internet Connection (GetRequestError):
def test_advanced_search_no_connection():
	
	link = 'http://export.arxiv.org/api/query?search_query='	

	# We simulate the absence of internet connection by turning off the wifi
	check_call(['networksetup', '-setairportpower', 'airport', 'off'], stdout=DEVNULL, stderr=STDOUT)

	with assert_raises(GetRequestError):
		advanced_search('sparaciari_c', False, False, False, False, False, False, False, link)

	# We turn it on stright after, waiting 15 seconds to be sure we are up and running
	check_call(['networksetup', '-setairportpower', 'airport', 'on'], stdout=DEVNULL, stderr=STDOUT)
	time.sleep(5)

# When the response from arxiv is wrong (HTTPError)
def test_advanced_search_status_code():

	link = 'http://export.arxiv.org/apii/query?search_query='	

	with assert_raises(requests.exceptions.HTTPError):
		advanced_search('sparaciari_c', False, False, False, False, False, False, False, link)

# When everything goes well.
def test_advanced_search_correct():

	link = 'http://export.arxiv.org/api/query?search_query='
	test_file = 'text_response_test_advanced_search.txt'

	response = advanced_search('sparaciari_c', 'kullback', False, False, False, False, False, False, link).text

	with open(test_file, 'r') as f:
		expected = f.read()

	# We remove the first few information, containing the current date.
	assert_equal(response[504:], expected[504:], "The obtained response is different from the expected one")
