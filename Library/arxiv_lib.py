from customised_exceptions import NoArgumentError, GetRequestError, UnknownError, NoCategoryError
import requests
import feedparser
import sys, os
import cgi
import bs4

## @package Library.arxiv_lib
#  Small library for making requests to the arXiv and parsing the results.
#
#  This library provides some methods to send requests to the arXiv (using their API),
#  and to parse and format the results. The library includes methods to perform simple
#  searches on the arXiv, as well as to read the daily RSS feeds, and to parse and extract
#  the relevant information to be sent to the users.

## List of all the categories of the arXiv.
ALL_CATEGORIES = ['stat.AP', 'stat.CO', 'stat.ML', 'stat.ME', 'stat.OT', 'stat.TH', 'stat', 'q-fin.PR', 'q-fin.RM', 'q-fin.PM', 'q-fin.TR',
'q-fin.MF', 'q-fin.CP', 'q-fin.ST', 'q-fin.GN', 'q-fin.EC', 'q-fin', 'q-bio.BM', 'q-bio.GN', 'q-bio.MN', 'q-bio.SC', 'q-bio.CB', 'q-bio.NC',
'q-bio', 'q-bio.TO', 'q-bio.PE', 'q-bio.QM', 'q-bio.OT', 'cs.AI', 'cs.CL', 'cs.CC', 'cs.CE', 'cs.CG', 'cs.GT', 'cs.CV', 'cs.CY', 'cs.CR',
'cs.DS', 'cs.DB', 'cs.DL', 'cs.DM', 'cs.DC', 'cs.ET', 'cs.FL', 'cs.GL', 'cs.GR', 'cs.AR', 'cs.HC', 'cs.IR', 'cs.IT', 'cs.LG', 'cs.LO', 'cs.MS',
'cs.MA', 'cs.MM', 'cs.NI', 'cs.NE', 'cs.NA', 'cs.OS', 'cs.OH', 'cs.PF', 'cs.PL', 'cs.RO', 'cs.SI', 'cs.SE', 'cs.SD', 'cs.SC', 'cs.SY', 'cs',
'astro-ph.GA', 'astro-ph.CO', 'astro-ph.EP', 'astro-ph.HE', 'astro-ph.IM', 'astro-ph.SR', 'astro-ph', 'cond-mat.dis-nn', 'cond-mat.mtrl-sci',
'cond-mat.mes-hall', 'cond-mat.other', 'cond-mat.quant-gas', 'cond-mat.soft', 'cond-mat.stat-mech', 'cond-mat.str-el', 'cond-mat.supr-con',
'cond-mat', 'gr-qc', 'hep-ex', 'hep-lat', 'hep-ph', 'hep-th', 'math-ph', 'nlin.AO', 'nlin.CG', 'nlin.CD', 'nlin.SI', 'nlin.PS', 'nlin',
'nucl-ex', 'nucl-th', 'physics', 'physics.acc-ph', 'physics.app-ph', 'physics.ao-ph', 'physics.atom-ph', 'physics.atm-clus', 'physics.bio-ph',
'physics.chem-ph', 'physics.class-ph', 'physics.comp-ph', 'physics.data-an', 'physics.flu-dyn', 'physics.gen-ph', 'physics.geo-ph',
'physics.hist-ph', 'physics.ins-det', 'physics.med-ph', 'physics.optics', 'physics.ed-ph', 'physics.soc-ph', 'physics.plasm-ph',
'physics.pop-ph', 'physics.space-ph', 'econ', 'eess', 'quant-ph', 'math', 'math.AG', 'math.AT', 'math.AP', 'math.CT', 'math.CA', 'math.CO',
'math.AC', 'math.CV', 'math.DG', 'math.DS', 'math.FA', 'math.GM', 'math.GN', 'math.GT', 'math.GR', 'math.HO', 'math.IT', 'math.KT', 'math.LO',
'math.MP', 'math.MG', 'math.NT', 'math.NA', 'math.OA', 'math.OC', 'math.PR', 'math.QA', 'math.RT', 'math.RA', 'math.SP', 'math.ST', 'math.SG']

## This function returns the number of available arXiv categories.
def number_categories():

	return len( ALL_CATEGORIES )

## This function takes an integer \f$i\f$ and returns the \f$i\f$-th category in the list ALL_CATEGORY.
#
#  @param category_index Integer number
def single_category(category_index):

	if not isinstance(category_index, int):
		raise TypeError('The index is not an integer.')

	if category_index < len( ALL_CATEGORIES ) and category_index >= 0:
		return ALL_CATEGORIES[category_index]
	else:
		raise IndexError('The module-scope list ALL_CATEGORY has no element ' + str(category_index) + '.')

## This function reviews the dictionary obtained from parse_response and returns title, author and link for each entry.
#
#  Only title, author and link are passed since they will go to the Telegram Bot.
#  The output of this function is therefore a list of dictionary with these entries.
#  Two different behaviours are expected from this function, depending on the
#  value of feed_type, which can be API or RSS (the first is used for searches,
#  the second for new submissions)
#
#  @param dictionary This is the output of the function @ref parse_response
#  @param max_number_authors The maximum number of authors to be shown (then they are replaced by 'et al.')
#  @param feed_type The type of feed to review (can be API or RSS)
def review_response(dictionary, max_number_authors, feed_type):

	results_list = []

	if not isinstance(max_number_authors, int):
		raise TypeError('The number of authors has to be an integer.')

	if max_number_authors < 1:
		raise ValueError('The maximum number of authors has to be bigger than 1.')

	if not isinstance(dictionary, dict):
		raise TypeError('The argument passed is not a dictionary.')

	try:
		if not isinstance(dictionary['entries'], list):
			raise TypeError('The field entries is corrupted.')
	except KeyError:
		raise NoArgumentError('No entries have been found during the search.')

	for entry in dictionary['entries']:

		if not isinstance(entry, dict):
			raise TypeError('One of the entries is corrupted.')

		if feed_type == 'API':
			element = {'title' : prepare_title_field_API(entry),
				   	   'authors' : prepare_authors_field_API(entry, max_number_authors)}
		elif feed_type == 'RSS':
			if is_update( entry ) == True:
				continue
			element = {'title' : prepare_title_field_RSS(entry),
					   'authors' : prepare_authors_field_RSS(entry, max_number_authors)}
		else:
			raise ValueError('Wrong feed type. It can only be API or RSS.')
		
		element['link'] = is_field_there(entry, 'link')
		
		# Check whether all field in the element are None
		is_empty = element['title'] == None and element['authors'] == None and element['link'] == None

		if not is_empty:
			results_list.append(element)

	if len(results_list) == 0:
		raise NoArgumentError('No entries have been found during the search.')
	
	return results_list

## This function formats the title, and is needed for the review_response.
#
#  This function removes the newline symbols \n from the title, and escapes the
#  HTML symbols <, >, &, so that they are correctly interpreted by telepot.send_message().
#
#  @param dictionary This is the output of the function @ref parse_response
def prepare_title_field_API(dictionary):

	title = is_field_there(dictionary, 'title')

	if isinstance(title, unicode):
		title = title.replace(u'\n',u'')
		title = title.replace(u'  ',u' ')
		title = cgi.escape(title)
		return title
	else:
		return None

## This function formats the authors, and is needed for the review_response.
#
#  This function unifies the name of the authors in a single one, and returns a Unicode string (if there are some authors).
#  It also cuts the number of authors after max_number_authors, and replaces the remaining with 'et al.'
#
#  @param dictionary This is the output of the function @ref parse_response
#  @param max_number_authors The maximum number of authors to be shown (then they are replaced by 'et al.')
def prepare_authors_field_API(dictionary, max_number_authors):

	authors_list = is_field_there(dictionary, 'authors')
	authors_string = unicode( '' , "utf-8")
	authors_number = 1

	if isinstance(authors_list, list):
		for author in authors_list:
			author_name = is_field_there(author, 'name')
			if authors_number > max_number_authors:
				authors_string = authors_string + u'et al.**'
				break
			if isinstance(author_name, unicode) and authors_number <= max_number_authors:
				authors_number +=1
				authors_string = authors_string + author_name + unicode( ', ' , "utf-8")

	else:
		return None

	# Check if we have something in the authors string
	if len(authors_string) == 0:
		return None
	else:
		authors_string = authors_string[: -2]
		return authors_string

## This function prepares the title, and is needed for the review_response.
#
#  This function prepares the title field after receiving an entry from the RSS feed.
#  The main difference with the API search is the presence of the arXiv id, which is removed.
#
#  @param dictionary This is the output of the function @ref parse_response
def prepare_title_field_RSS(dictionary):

	title = prepare_title_field_API(dictionary)

	if title != None:
		index = title.find(' (arXiv:')
		title = title[:index-1]
	
	return title

## This function formats the authors, and is needed for the review_response.
#
#  This function prepares the authors field after receiving an entry from the RSS feed.
#  The function is different from the one used for standard search feeds as the authors
#  are given in a single line and hyper links are present. This function remove hyper links
#  and cut the number of authors if they are more than a maximum value
#
#  @param dictionary This is the output of the function @ref parse_response
#  @param max_number_authors The maximum number of authors to be shown (then they are replaced by 'et al.')
def prepare_authors_field_RSS(dictionary, max_number_authors):

	authors_string = is_field_there(dictionary, 'author')

	if isinstance(authors_string, unicode):
		end_string = authors_count_same_string(authors_string, max_number_authors)
		if end_string != -1:
			authors_string = authors_string[:end_string] + u', et al.'
		authors_string = remove_hyperlinks(authors_string)
		return authors_string
	else:
		return None

## This function removes hyper links, and is needed for the prepare_authors_field_RSS.
#
#  This function removes the hyper links (<a href = ***> ... </a>) from a string,
#  and return a unicode string.
#
#  @param string A string with hyper links inside
def remove_hyperlinks(string):

	bs_string = bs4.BeautifulSoup(string, 'html.parser')

	for hlink in bs_string.findAll('a'):
		hlink.replaceWithChildren()

	return unicode( str( bs_string ) , "utf-8")

## This function finds where to put 'et al.' in the author string, and is needed for the prepare_authors_field_RSS.
#
#  This function finds the position of the "max_number_authors"-th comma in the string,
#  and returns it. If this comma doesn't exist, return -1.
#
#  @param authors_string A string with all the authors
#  @param max_number_authors The maximum number of authors to be shown (then they are replaced by 'et al.')
def authors_count_same_string(authors_string, max_number_authors):

	index = -1

	for iteration in range( max_number_authors ):
		index = authors_string.find( ',' , index + 1 )
		if index == -1:
			break

	return index

## This function checks whether the entry is new or updated, and is needed for the @ref review_response function.
#
#  This function checks if the entry is an update of a previous version of the paper.
#  Return True if it is, and False if is not. If the title field is absent, returns True.
#
#  @param dictionary This is the output of the function @ref parse_response
def is_update( dictionary ):

	title = is_field_there(dictionary, 'title')

	if title != None:
		index = title.find('UPDATED')
		if index == -1:
			return False
				
	return True

## This function returns the total number of results in the search.
#
#  @param dictionary This is the output of the function @ref parse_response
def total_number_results(dictionary):

	if not isinstance(dictionary, dict):
		raise TypeError('The argument passed is not a dictionary.')

	feed_information = is_field_there(dictionary, 'feed')

	if feed_information == None:
		raise NoArgumentError('No feed have been returned by the search.')

	if not isinstance(feed_information, dict):
		raise TypeError('The field feed is corrupted.')

	total_results = is_field_there(feed_information, 'opensearch_totalresults')

	if total_results == None:
		raise NoArgumentError('The feed got corrupted.')

	return int(total_results)

## This function checks if a key is inside a dictionary, and is needed for the @ref review_response function.
#
#  This function checks that the dictionary has something associated to the key, and if not, it returns None.
#
#  @param dictionary This is the output of the function @ref parse_response
#  @param key This is a key which might be in the dictionary
def is_field_there(dictionary, key):

	try:
		return dictionary[key]
	except:
		return None

## This function finds the year of a given entry, and is needed for the @ref review_response function.
#
#  @param dictionary This is the output of the function @ref parse_response
def find_year(dictionary):

	date = is_field_there(dictionary, 'date')

	if isinstance(date, unicode) and len(date) > 3:
		date = date[0:4]
		return date
	else:
		return None

## This function parses the output of the @ref request_to_arxiv function.
#
#  This function modifies the response obtained by the request library, making it a raw data (string).
#  Then, it parses the raw data using FeedParser, and returns a dictionary.
#
#  @param response This is the output of the function @ref request_to_arxiv
def parse_response(response):
	
	if not isinstance(response, requests.models.Response):
		raise TypeError('The argument passed is not a Response object.')

	rawdata = response.text

	parsed_response = feedparser.parse(rawdata)

	return parsed_response

## This function communicates with the arXiv and download the information.
#
#  @param arxiv_search_link The link to the arXiv website
def request_to_arxiv(arxiv_search_link):

	if not ( isinstance(arxiv_search_link, unicode) or isinstance(arxiv_search_link, str) ):
		raise TypeError('The argument passed is not a string.')

	# Making a query to the arXiv
	try:
		response = requests.get( arxiv_search_link ) 
	except requests.exceptions.InvalidSchema as invalid_schema:
		raise invalid_schema
	except requests.exceptions.MissingSchema as missing_schema:
		raise missing_schema
	except:
		raise GetRequestError('Get from arXiv failed. Might be connection problem')

	# Check the status of the response
	try:
		response.raise_for_status()
	except requests.exceptions.HTTPError as connection_error:
		raise connection_error
	else:
		return response

## This function adds to the arXiv link an extra field, which specifies the number of results we want to obtain.
#
#  **NOTE**: This function is not used any more, since @ref simple_search now takes care of this.
#
#  @param arxiv_search_link The link to the arXiv website
#  @param number_of_results An integer number
def specify_number_of_results(arxiv_search_link, number_of_results):

	if number_of_results < 0:
		raise ValueError('The number of results you are interested in cannot be negative.')

	arxiv_search_link += '&max_results=' + str(number_of_results)

	return arxiv_search_link

## This function adds a specific category to the arXiv RSS link.
#
#  @param subject_category A category of the arXiv
#  @param arxiv_search_link The link to the arXiv website
def search_day_submissions(subject_category, arxiv_search_link):

	if not category_exists(subject_category):
		raise NoCategoryError('The passed category is not in the ArXiv')

	arxiv_search_link += subject_category

	return arxiv_search_link

## This function checks whether a category exists.
#
#  @param subject_category A (possible) category of the arXiv 
def category_exists(subject_category):

	return subject_category in ALL_CATEGORIES

## This function performs an advanced search the arXiv.
#
#  This function assembles the link for the request to arXiv, which will be passed
#  to the @ref request_to_arxiv function.
#  If a variable is not a string, it is not included in the function,
#  But no exception is raised. Exception is raised only is the search
#  is empty. After the query is done, the response is returned.
#
#  @param author The searched author(s)
#  @param title The searched title
#  @param abstract The searched abstract
#  @param comment The searched comment
#  @param jref The searched journal reference
#  @param category The searched category
#  @param rnum The searched report number
#  @param identity The searched identity number
#  @param arxiv_search_link The link to the arXiv website
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

## This function performs a simple search the arXiv.
#
#  This function assembles the link for the request to arXiv, which will be passed
#  to the @ref request_to_arxiv function.
#
#  @param words The keywords of the search
#  @param arxiv_search_link The link to the arXiv website
#  @param start_num The number of the initial result
#  @param max_num The maximum number of shown results
def simple_search(words, arxiv_search_link, start_num, max_num):

	# Initialising constant values for the search
	connector = '+AND+'
	length_check = len(arxiv_search_link)
	key = 'all:'
	start_opt = '&start='
	max_opt = '&max_results='

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

	# Remove last connector from the search
	arxiv_search_link = arxiv_search_link[: - len(connector) ]

	# Add the options defining which results to show
	arxiv_search_link += start_opt + str(start_num) + max_opt + str(max_num)

	return arxiv_search_link