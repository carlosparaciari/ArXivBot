from customised_exceptions import NoArgumentError, GetRequestError, UnknownError
import requests
import feedparser
import urllib

# Request function to comunicate with the arxiv and download the informations
# It takes a string (the link) as argument
# Check for the main connection errors.

def request_to_arxiv(arxiv_search_link):

	if not isinstance(arxiv_search_link, str):
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
# And it make a query to the arxive to search for these parameters.
# One do not need to specifies all the variables.
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

	# Make the request
	try:
		response = request_to_arxiv(arxiv_search_link)
	except requests.exceptions.InvalidSchema as invalid_schema:
		raise invalid_schema
	except requests.exceptions.MissingSchema as missing_schema:
		raise missing_schema
	except GetRequestError:
		raise GetRequestError('Get from arxiv failed. Might be connection problem')
	except requests.exceptions.HTTPError as connection_error:
		raise connection_error
	except TypeError:
		raise TypeError('The argument passed is not a string.')
	except:
		raise UnknownError('During the request to Arxiv something went wrong.')
	else:
		return response

# The simple search on the arxiv.
# It takes the argument of the search, which is searched in the all fields,
# such as title, author, etc. The argument of this function has to be a string.
# If nothing is passed, the search is not perfomed.

def simple_search(word):

	return 0	
