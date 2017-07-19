from customised_exceptions import NoArgumentError, GetRequestError, UnknownError
import requests
import feedparser

# Review response, it will review the dictionary obtained from parse_response
# and pass the following information for each entries:
#
# - title
# - authors
# - year
# - link
#
# Only these information are passed since they will go to the telegram app.
# The return argument is a list of dictionary with these entries

def review_response(dictionary):

	results_list = []

	if not isinstance(dictionary, dict):
		raise TypeError('The argument passed is not a dictionary.')

	try:
		if not isinstance(dictionary['entries'], list):
			raise TypeError('The field entries is corrupted.')
	except KeyError:
		raise NoArgumentError('No entries have been found during the search.')

	for entry in dictionary['entries']:

		if not isinstance(entry,dict):
			raise TypeError('One of the entries is corrupted.')

		# Only write the important data in the dictionary
		element = {'title' : one_line_title(entry),
				   'authors' : compact_authors(entry),
				   'year' : find_year(entry),
				   'link' : is_field_there(entry, 'link')}
		
		# Check whether all field in the element are None
		is_empty = element['title'] == None and element['authors'] == None and element['year'] == None and element['link'] == None

		if not is_empty:
			results_list.append(element)

	if len(results_list) == 0:
		raise NoArgumentError('No entries have been found during the search.')
	
	return results_list

# This function is needed for the review_response.
# It checks that the dictionary has something associated to the key, and if not, it returns None
def is_field_there(dictionary, key):

	try:
		return dictionary[key]
	except:
		return None

# This function is needed for the review_response.
# It modifies the title so that any \n is absent
def one_line_title(dictionary):

	title = is_field_there(dictionary, 'title')

	if isinstance(title, unicode):
		title = title.replace(u'\n',u'')
		return title
	else:
		return None

# This function is needed for the review_response.
# It unifies the name of the authors in a single one, and return a unicode string (if there are some authors)
def compact_authors(dictionary):

	authors_list = is_field_there(dictionary, 'authors')
	authors_string = unicode( '' , "utf-8")

	if isinstance(authors_list, list):
		for author in authors_list:
			author_name = is_field_there(author, 'name')
			if isinstance(author_name, unicode):
				authors_string = authors_string + author_name + unicode( ', ' , "utf-8")
	else:
		return None

	# Check if we have something in the authors string
	if len(authors_string) == 0:
		return None
	else:
		authors_string = authors_string[: -2]
		return authors_string

# This function is needed for the review_response.
# For a given date, it returns the year.
def find_year(dictionary):

	date = is_field_there(dictionary, 'date')

	if isinstance(date, unicode) and len(date) > 3:
		date = date[0:4]
		return date
	else:
		return None

# Parse the response. It modifies the response obtained by the request library
# making it a rawdata (string). Then, it parse it using parsefeed. It returns
# a dictionary.

def parse_response(response):
	
	if not isinstance(response, requests.models.Response):
		raise TypeError('The argument passed is not a Response object.')

	rawdata = response.text

	parsed_response = feedparser.parse(rawdata)

	return parsed_response

# Request function to comunicate with the arxiv and download the informations
# It takes a string (the link) as argument
# Check for the main connection errors.
# Return the response

def request_to_arxiv(arxiv_search_link):

	if not ( isinstance(arxiv_search_link, unicode) or isinstance(arxiv_search_link, str) ):
		raise TypeError('The argument passed is not a string.')

	# Making a query to the arxiv
	try:
		response = requests.get( arxiv_search_link ) 
	except requests.exceptions.InvalidSchema as invalid_schema:
		raise invalid_schema
	except requests.exceptions.MissingSchema as missing_schema:
		raise missing_schema
	except:
		raise GetRequestError('Get from arxiv failed. Might be connection problem')

	# Check the status of the response
	try:
		response.raise_for_status()
	except requests.exceptions.HTTPError as connection_error:
		raise connection_error
	else:
		return response

# Advanced search the arxiv.
#
# As parameter, it takes the following parameters:
#
# au			Author
# ti			Title
# abs			Abstract
# co			Comment
# jr			Journal Reference
# cat			Subject Category
# rn			Report Number
# id			Id
# arxiv_search_link	The arxiv link where making the query
# 
# And it make the link for the request to arxiv, which will be passed
# to the request to arxiv.
# 
# If a variable is not a string, it is not included in the function,
# But no exception is raised. Exception is raised only is the search
# is empty. After the query is done, the response is returned.

def advanced_search(author, title, abstract, comment, jref, category, rnum, identity, arxiv_search_link):

	# Initialising constant values for the search
	connector = '+AND+'
	length_check = len(arxiv_search_link)

	# Creating the dictionary for the search
	parameters = {
	 'au:' : author ,
	 'ti:' : title ,
	 'abs:' : abstract ,
	 'co:' : comment ,
	 'jr:' : jref ,
	 'cat:' : category ,
	 'rm:' : rnum ,
	 'id:' : identity
	 }

	# Creating the search string, adding each term iff it is a string
	for key in parameters:
		if isinstance(parameters[key], str):
			arxiv_search_link += key + parameters[key] + connector

	# Check that search_def is not empty. In that case, return error
	if len(arxiv_search_link) == length_check:
		raise NoArgumentError('No arguments have been provided to the search.')

	# Remove last connector fromt the search
	arxiv_search_link = arxiv_search_link[: - len(connector) ]

	return arxiv_search_link

# The simple search on the arxiv.
# 
# It takes the argument of the search, which is searched in the all fields,
# such as title, author, etc. The argument of this function has to be a string,
# or a list of strings. If nothing is passed, the search is not perfomed.
# Retruns the link for the call to arxiv

def simple_search(words, arxiv_search_link):

	# Initialising constant values for the search
	connector = '+AND+'
	length_check = len(arxiv_search_link)
	key = 'all:'

	# If the argument is a list of words, iterate over it
	if isinstance(words, list):
		for word in words:
			if isinstance(word, str) or isinstance(word, unicode):
				arxiv_search_link += key + word + connector

	# If it is a single string, add it without iterations
	elif isinstance(words, str) or isinstance(words, unicode):
		arxiv_search_link += key + words + connector

	# Check that search_def is not empty. In that case, return error
	if len(arxiv_search_link) == length_check:
		raise NoArgumentError('No arguments have been provided to the search.')

	# Remove last connector fromt the search
	arxiv_search_link = arxiv_search_link[: - len(connector) ]

	return arxiv_search_link