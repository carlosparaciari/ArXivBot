import telepot
import requests
import datetime
import time
import sys
import random
import psycopg2
import arxiv_lib as al
import emoji_detect as emjd
from customised_exceptions import NoArgumentError, GetRequestError, UnknownError, NoCategoryError
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

## @package Library.arxiv_bot
#  A Telegram Bot for searching the arXiv and get RSS feeds.
#
#  In this library we define a class which receives queries from Telegram users
#  and makes searches on the arXiv.

## This class implements the ArXivBot.
#
#  This class inherits from the telepot.Bot class (https://github.com/nickoala/telepot).
#  The class is used to deal with the messages received by the bot on Telegram,
#  and to perform simple searches on the arXiv website.
class ArxivBot(telepot.Bot):

	## Class constructor
	def __init__(self, token, db_name, db_user, db_password):

		super(ArxivBot, self).__init__(token)

		## The API link for the arXiv
		self.arxiv_search_link = 'http://export.arxiv.org/api/query?search_query='

		## The RSS link for the arXiv
		self.arxiv_rss_link = 'http://arxiv.org/rss/'

		## The maximum number of results shown from an RSS feed
		self.max_rss_result_number = 50

		## The maximum number of results shown from a search using API
		self.max_api_result_number = 10

		## The maximum number of keywords used in a search
		self.max_number_keywords = 10

		## The maximum number of authors shown for each paper
		self.max_number_authors = 5

		## The maximum number of characters in a single Telegram message
		self.max_characters_chat = 4096

		## The number of seconds to wait after using the API (set by arXiv)
		self.arxiv_fair_time = 3

		## The name of the PostgreSQL database
		self.database_name = db_name

		## The user of the PostgreSQL database
		self.database_user = db_user

		## The password of the PostgreSQL database
		self.database_password = db_password

	## Class destructor
	def __del__(self):

		super(ArxivBot, self).__del__()

		self.close_connection_with_database()

	## This method allows for the injection of the email address for the feedbacks
	#
	#  @param self The object pointer
	#  @param email_address The string with the email address
	def set_email_feedback(self, email_address):

		## The email address for the feedbacks
		self.feedback_address = email_address

	## This method receives the message sent by the user and processes it depending on the different "flavour" associated to it.
	#
	#  **NOTE**: Most of the "flavours" are not implemented yet. Some might be implemented in the future.
	#
	#  @param self The object pointer
	#  @param msg The message received from the user
	def handle(self, msg):

		msg_flavor = telepot.flavor(msg)

		if msg_flavor == 'chat':
			self.handle_chat_message(msg)
		elif msg_flavor == 'callback_query':
			self.handle_callback_query(msg)
		elif msg_flavor == 'inline_query':
			self.handle_inline_query(msg)
		elif msg_flavor == 'chosen_inline_result':
			self.handle_chosen_inline_result(msg)
		else:
			raise telepot.BadFlavor(msg)

	## This method is called by the @ref handle method when the "flavour" of the message is 'chat'.
	#
	#  The user is allowed to send four different commands:
	#
	#  - `/search` : perform a simple search in the arXiv
	#  - `/today` : search the papers of the day in a given category of the arXiv
	#  - `/set` : set the category where to search for the new submission
	#  - `/feedback` : the user can use the command to send a feedback
	#  - `/help` : send an help message to the user
	#
	#  If another command is sent, the method suggest the user to use the `/help`.
	#  If the `/search` command is used, the @ref do_easy_search_chat method is called.
	#  If the `/today` command is used, the @ref do_today_search method is called.
	#
	#  After the search is done, the results are sent to the user and the task is finished.
	#
	#  @param self The object pointer
	#  @param msg The message received from the user
	def handle_chat_message(self, msg):

		content_type, chat_type, chat_id = telepot.glance(msg, 'chat')

		if content_type != 'text':
			self.sendMessage(chat_id, u'You can only send me text messages, sorry!')
			return None

		text_message = msg[content_type]

		try:
			self.save_message_log( chat_id, content_type, text_message )
		except:
			return None

		if emjd.detect_emoji(text_message):
			self.sendMessage(chat_id, u'You have used an invalid unicode character. Unacceptable! \U0001F624')
			return None

		text_message_list = text_message.split()
		command = text_message_list[0]

		if command == '/search':
			command_argument = text_message_list[1:]
			self.do_easy_search_chat( command_argument , chat_id )
		elif command == '/set' and len(text_message_list) == 2:
			command_argument = text_message_list[1]
			self.set_category( command_argument , chat_id )
		elif command == '/today' and len(text_message_list) == 1:
			self.do_today_search_with_set_preference( chat_id )
		elif command == '/today' and len(text_message_list) == 2:
			command_argument = text_message_list[1]
			self.do_today_search( command_argument , chat_id )
		elif command == '/feedback':
			command_argument = text_message_list[1:]
			self.give_feedback( command_argument, chat_id )
		elif command == '/help' and len(text_message_list) == 1:
			self.get_help( chat_id )
		else:
			self.sendMessage(chat_id, u'See the /help for information on this Bot!')

	## This method is called by the @ref handle method when the "flavour" of the message is 'callback_query'.
	#
	#  The message has a 'callback_query' flavour when the user uses the inline
	#  keyboard to search for new results of their search.
	#
	#  **NOTE**: at the moment, this bot will receive callback queries only when the
	#  user is looking at the results of a simple search, and want to move
	#  to other results (the previous or the next ones)
	#
	#  @param self The object pointer
	#  @param msg The message received from the user
	def handle_callback_query(self, msg):

		query_id, chat_id, query_data = telepot.glance(msg, 'callback_query')
		msg_id = telepot.origin_identifier(msg)
		content_type = 'callback'

		try:
			self.save_message_log( chat_id, content_type, query_data, query_id)
		except:
			return None

		try:
			function, command, new_start = query_data.split()
		except ValueError as VE:
			self.sendMessage(chat_id, u'We are experiencing some technical problems, sorry!')
			self.save_known_error_log(chat_id, VE)
			return None
		except:
			self.sendMessage(chat_id, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_id, 'arxiv_bot.handle_callback_query')
			return None

		if function == 'search':
			if command == 'close':
				self.editMessageReplyMarkup(msg_id, reply_markup=None)
				return None

			msg_content = msg['message']['text']
			left_key = 'Your search keywords are:\n'
			right_key = '\n\n'

			keywords = self.find_current_keywords(msg_content, left_key, right_key)
			new_start = int(new_start)

			self.do_easy_search_query( keywords, new_start, chat_id, query_id, msg_id )
		else:
			self.sendMessage(chat_id, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_id, 'arxiv_bot.handle_callback_query')

	## This method is used when the user calls the `/search` command.
	#
	#  This method composes the arXiv link to which the requests is sent, makes a requests to
	#  the website, parses the results, and sends them to the user.
	#
	#  **NOTE**: No more than 10 results are shown due to the limitations on the screen of mobile phones.
	#  The user can nevertheless view more results using the next button.
	#
	#  @param self The object pointer
	#  @param argument A list of Unicode strings which define the search
	#  @param chat_identity The identity number associated to the chat
	def do_easy_search_chat(self, argument, chat_identity):

		if len(argument) > self.max_number_keywords:
			message = 'Please use less than ' + str(self.max_number_keywords) + ' keywords for your search.'
			self.sendMessage(chat_identity, message)
			return None

		initial_result_number = 0

		try:
			easy_search_link = al.simple_search(argument, self.arxiv_search_link, initial_result_number, self.max_api_result_number)
		except NoArgumentError:
			self.sendMessage(chat_identity, u'Please provide some arguments for your arXiv search.')
			return None
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.simple_search')
			return None

		try:
			search_list, total_results = self.search_and_format_API( easy_search_link, chat_identity )
		except:
			return None

		message_result = self.prepare_message_api( argument, initial_result_number, search_list, total_results)

		if total_results <= self.max_api_result_number:
			self.send_message_safely( chat_identity, message_result )
		else:
			keyboard = self.search_prev_next_keyboard( initial_result_number, total_results, self.max_api_result_number )
			self.send_message_safely( chat_identity, message_result, markup = keyboard )

		time.sleep( self.arxiv_fair_time )

	## This method is used when the user clicks the next/previous buttons.
	#
	#  The method composes the arXiv link to which the requests is sent, makes a requests to
	#  the website, parses the results, and edit the previous message.
	#
	#  @param self The object pointer
	#  @param argument A list of Unicode strings which define the search
	#  @param start_number An integer specifying the number of the first shown result
	#  @param chat_identity The identity number associated to the chat
	#  @param query_identity The identity number associated to the query
	#  @param msg_identity The identity number associated to the message, so we can edit the message
	def do_easy_search_query(self, argument, start_number, chat_identity, query_identity, msg_identity):

		try:
			easy_search_link = al.simple_search(argument, self.arxiv_search_link, start_number, self.max_api_result_number)
		except NoArgumentError:
			self.sendMessage(chat_identity, u'Please provide some arguments for the search.')
			return None
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.simple_search')
			return None

		try:
			search_list, total_results = self.search_and_format_API( easy_search_link, chat_identity )
		except:
			return None

		message_result = self.prepare_message_api( argument, start_number, search_list, total_results)

		keyboard = self.search_prev_next_keyboard( start_number, total_results, self.max_api_result_number )
		self.edit_message_safely(message_result, query_identity, msg_identity, keyboard)

		time.sleep( self.arxiv_fair_time )

	## This method is used when the user calls the `/set` command.
	#
	#  This method saves the favourite category of the user, so that in the future the
	#  user can use the `/today` command without specifying the category
	#
	#  The method saves the preferred category in a file, together with the
	#  chat_id of the user. If another category was previously saved, the
	#  method overrides it with the new one.
	#
	#  @param self The object pointer
	#  @param arxiv_category The arXiv category we are interested in (ONLY one category)
	#  @param chat_identity The identity number associated to the chat
	def set_category(self, arxiv_category, chat_identity):

		if not al.category_exists( arxiv_category ):
			self.send_message_safely(chat_identity, u'Please use the arXiv subjects.\nSee http://arxitics.com/help/categories for further information.')
			return None

		if self.preference_exists( chat_identity ):
			self.overwrite_preference( chat_identity, arxiv_category )
			self.send_message_safely(chat_identity, u'Your preferred category has been updated!\nNow use /today to get the daily submissions to this category.')
		else:
			self.add_preference( chat_identity, arxiv_category )
			self.send_message_safely(chat_identity, u'Your preferred category has been recorded!\nNow use /today to get the daily submissions to this category.')

	## This method looks at the RSS feed of a category set by the user.
	#
	#  If the category is not set, the Bot will notify the user about the
	#  usage of the `/today` command.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	def do_today_search_with_set_preference(self, chat_identity):

		if self.preference_exists( chat_identity ):
			preferred_category = self.search_for_category( chat_identity )
			if preferred_category == None:
				self.sendMessage(chat_identity, u'An unknown error occurred while checking your preferences. \U0001F631')
				self.save_unknown_error_log(chat_identity, 'arxiv_bot.do_today_search_with_set_preference')
				return None
			self.do_today_search( preferred_category, chat_identity )
		else:
			message = (u"You have not /set your favourite arXiv category. "
					   u"Please set your favourite category with\n"
					   u"    <i>/set favourite_category</i>\n"
				   	   u"or specify the category you are interested in with\n"
				   	   u"    <i>/today arxiv_category</i>\n"
					  )
			self.send_message_safely( chat_identity, message )

	## This method is used when the user calls the `/today` command.
	#
	#  The method searches for the papers of the day in a given category of the arXiv.
	#
	#  The method composes the arXiv link to which the requests is sent, makes a requests to
	#  the website, parses the results, and sends them to the user.
	#
	#  **NOTE** : Only for this kind of search, we allow for a maximum of 50 results.
	#  If more results are presents, the user is notified.
	#
	#  @param self The object pointer
	#  @param arxiv_category The arXiv category we are interested in (ONLY one category for limiting the number of results)
	#  @param chat_identity The identity number associated to the chat
	def do_today_search(self, arxiv_category, chat_identity):

		try:
			today_search_link = al.search_day_submissions(arxiv_category, self.arxiv_rss_link)
		except NoCategoryError:
			self.send_message_safely(chat_identity, u'Please use the arXiv subjects.\nSee http://arxitics.com/help/categories for further information.')
			return None
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.search_day_submissions')
			return None

		try:
			search_list, feed_date = self.search_and_format_RSS( today_search_link, chat_identity )
		except:
			return None

		total_results = len(search_list)
		search_list = search_list[:self.max_rss_result_number]
		remaining_results = total_results - self.max_rss_result_number

		self.send_results_back_rss(chat_identity, search_list, remaining_results, arxiv_category, feed_date)

	## This method returns the email address where the user can submit a feedback, or saves the feedback received.
	#
	#  @param self The object pointer
	#  @param argument The string with the feedback
	#  @param chat_identity The identity number associated to the chat
	def give_feedback(self, argument, chat_identity):

		if len(argument) == 0:
			feedback_response = (u'We are always happy to hear your view! \U0001F4E3\n\n'
								 u'Use /feedback <i>your comment</i>\n'
								 u'or email us at ' + self.feedback_address
								)
		else:
			separator = ' '
			message = separator.join(argument)
			try:
				self.save_feedback(chat_identity, message)
			except:
				return None
			feedback_response = u'Thanks for your feedback! \U0001F604'

		self.send_message_safely( chat_identity, feedback_response )

	## This method provides some useful information about the Bot to the user.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	def get_help(self, chat_identity ):

		random_category = random.randint( 0, al.number_categories() - 1 )

		try:
			example_category = al.single_category(random_category)
		except TypeError as TE:
			self.sendMessage(chat_identity, u'We are experiencing some technical problems, sorry!')
			self.save_known_error_log(chat_identity, TE)
			return None
		except IndexError as IE:
			self.sendMessage(chat_identity, u'We are experiencing some technical problems, sorry!')
			self.save_known_error_log(chat_identity, IE)
			return None
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.single_category')
			return None

		message = (u"Search for papers on the arXiv with this bot. "
				   u"Search papers using some keywords, or check the new submissions to your favourite category, "
				   u"and share the results easily. With ArXivBot you can\n\n"
				   u"- make a /search using some keywords\n"
				   u"    <i>e.g. /search atom 2017</i>\n\n"
				   u"- look at what's going on /today in the arXiv\n"
				   u"    <i>e.g. /today " + example_category + u"</i>\n\n"
				   u"- /set your favourite arXiv category\n"
				   u"    <i>e.g. /set " + example_category + u"</i>\n"
				   u"           <i>/today</i>\n\n"
				   u"- send us your /feedback\n"
				   u"    <i>e.g. /feedback I like this bot!</i>\n\n"
				   u"Enjoy your search! \U0001F609"
				  )

		self.send_message_safely( chat_identity, message )

	## This method is used in the API search methods to send the request to the arXiv, parse the result, and format it accordingly.
	# 
	#  @param self The object pointer
	#  @param search_link The arXiv link for the request
	#  @param chat_identity The identity number associated to the chat
	def search_and_format_API(self, search_link, chat_identity):

		try:
			search_dictionary = self.send_and_parse_request(search_link, chat_identity)
		except:
			raise

		try:
			search_list = al.review_response( search_dictionary , self.max_number_authors , 'API' )
		except NoArgumentError:
			self.sendMessage(chat_identity, u'No result has been found for your search. Try again!')
			raise
		except TypeError as TE:
			self.sendMessage(chat_identity, u'The result of the search got corrupted.')
			self.save_known_error_log(chat_identity, TE)
			raise
		except ValueError as VE:
			self.sendMessage(chat_identity, u'We are experiencing some technical problems, sorry!')
			self.save_known_error_log(chat_identity, VE)
			raise
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.review_response')
			raise

		try:
			total_results = al.total_number_results( search_dictionary )
		except NoArgumentError as NAE:
			self.sendMessage(chat_identity, u'The result of the search got corrupted.')
			self.save_known_error_log(chat_identity, NAE)
			raise
		except TypeError as TE:
			self.sendMessage(chat_identity, u'The result of the search got corrupted.')
			self.save_known_error_log(chat_identity, TE)
			raise
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.total_number_results')
			raise

		return search_list, total_results

	## This method is used in the RSS feed methods to send the request to the arXiv, parse the result, and format it accordingly.
	# 
	#  @param self The object pointer
	#  @param search_link The arXiv link for the request
	#  @param chat_identity The identity number associated to the chat
	def search_and_format_RSS(self, search_link, chat_identity):

		try:
			search_dictionary = self.send_and_parse_request(search_link, chat_identity)
		except:
			raise

		try:
			search_list = al.review_response( search_dictionary , self.max_number_authors , 'RSS' )
		except NoArgumentError:
			self.sendMessage(chat_identity, u'There are no submissions to your favourite category today, try tomorrow!')
			raise
		except TypeError as TE:
			self.sendMessage(chat_identity, u'The result of the search got corrupted.')
			self.save_known_error_log(chat_identity, TE)
			raise
		except ValueError as VE:
			self.sendMessage(chat_identity, u'We are experiencing some technical problems, sorry!')
			self.save_known_error_log(chat_identity, VE)
			raise
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.review_response')
			raise

		try:
			feed_date = al.find_date_RSS( search_dictionary )
		except NoArgumentError as NAE:
			self.sendMessage(chat_identity, u'The result of the search got corrupted.')
			self.save_known_error_log(chat_identity, NAE)
			raise
		except TypeError as TE:
			self.sendMessage(chat_identity, u'The result of the search got corrupted.')
			self.save_known_error_log(chat_identity, TE)
			raise
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.find_date_RSS')
			raise

		return search_list, feed_date

	## This method sends the request to the arXiv and parse the response.
	# 
	#  This method is used in the search_and_format methods, both for API search and RSS feed.
	#
	#  @param self The object pointer
	#  @param search_link The arXiv link for the request
	#  @param chat_identity The identity number associated to the chat
	def send_and_parse_request(self, search_link, chat_identity):

		try:
			search_response = al.request_to_arxiv(search_link)
		except TypeError as TE:
			self.sendMessage(chat_identity, u'The url got corrupted. Try again!')
			self.save_known_error_log(chat_identity, TE)
			raise
		except GetRequestError as GRE:
			self.sendMessage(chat_identity, u'The search arguments are fine, but the search on the arXiv failed.')
			self.save_known_error_log(chat_identity, GRE)
			raise
		except requests.exceptions.HTTPError as HTTPE:
			self.sendMessage(chat_identity, u'We are currently experiencing connection problems, sorry!')
			self.save_known_error_log(chat_identity, HTTPE)
			raise
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.request_to_arxiv')
			raise

		try:
			search_dictionary = al.parse_response(search_response)
		except TypeError as TE:
			self.sendMessage(chat_identity, u'The result of the search got corrupted.')
			self.save_known_error_log(chat_identity, TE)
			raise
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.parse_response')
			raise

		return search_dictionary

	## This method formats the results of the search and prepares the message to be sent to the user.
	#
	#  The method prepares a message where all entries have a title, author's list, date (when the paper was published), and link.
	#  **NOTE**: Since only 10 results can be shown, we do not have to worry about exceeding the size limit for the message.
	#
	#  @param self The object pointer
	#  @param argument The keywords used in the search
	#  @param start_num The number of the first result shown
	#  @param search_list The unformatted list with all details about the results (prepared with the @ref search_and_format_API method)
	#  @param total_results The total number of results associated with the search
	def prepare_message_api(self, argument, start_num, search_list, total_results):

		result_counter = start_num + 1
		separator = ' '
		keywords = separator.join(argument)
		message_result = 'Your search keywords are:\n'+keywords+'\n\n'
		
		for result in search_list:
			new_item = '<b>' + str(result_counter) + '</b>. <em>' + result['title'] + '</em>\n' + result['authors'] + '\n<em>Submitted on ' + result['date'].strftime('%d %b %Y') + '</em>\n' + result['link'] + '\n\n'
			message_result += new_item
			result_counter += 1
		
		if total_results > self.max_api_result_number:
			total_number_info = 'There are ' + str(total_results) + ' results associated with this search.'
			message_result += total_number_info

		return message_result

	## This method formats the result of the today RSS feed and send it to the user.
	#
	#  **NOTE**: Telegram does not allow for sending messages bigger than 4096 characters,
	#  so the method cut the message into chucks if the total number of characters is bigger. 
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	#  @param search_list The unformatted list with all details about the results (prepared with the @ref search_and_format_RSS method)
	#  @param remaining_results The remaining results which have not been shown
	def send_results_back_rss(self, chat_identity, search_list, remaining_results, arxiv_category, feed_date):

		result_counter = 1
		today = feed_date + datetime.timedelta(days=1)
		message_result = 'List of submissions to <b>' + arxiv_category + '</b> for today ' + today.strftime("%a, %d %b %y") + '.\n\n'
		
		for result in search_list:
			new_item = '<b>' + str(result_counter) + '</b>. <em>' + result['title'] + '</em>\n' + result['authors'] + '\n'+result['link'] + '\n\n'
			try:
				message_result = self.check_size_and_split_message(message_result, new_item, chat_identity)
			except:
				return None
			result_counter += 1
		
		if remaining_results > 0:
			remaining_information = ('There are ' + str(remaining_results) + ' remaining submissions today.\n'
									 'Consider visiting the arXiv web-page to see them.'
									)
			try:
				message_result = self.check_size_and_split_message(message_result, remaining_information, chat_identity)
			except:
				return None

		self.send_message_safely( chat_identity, message_result )

	## This method checks the length of the message, and divides it if the maximum number of characters is exceeded.
	#
	#  The method is used in the @ref send_results_back_rss method.
	#
	#  @param self The object pointer
	#  @param message The message to check and possibly send
	#  @param new_item The new result to add to the message
	#  @param chat_identity The identity number associated to the chat
	def check_size_and_split_message(self, message, new_item, chat_identity):

		message_would_exceed = len(message) + len(new_item) >= self.max_characters_chat
		if message_would_exceed:
			try:
				self.sendMessage( chat_identity, message, parse_mode='HTML')
			except telepot.exception.TooManyRequestsError as TooE:
				self.sendMessage(chat_identity, u"You can only make 20 requests per minutes. Please try later!")
				raise
			except:
				self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
				self.save_unknown_error_log(chat_identity, 'arxiv_bot.check_size_and_split_message')
				raise
			message = ''
		message += new_item

		return message

	## This method sends the message safely.
	#
	#  The method provides the possibility of adding an inline keyboard at the bottom of the message.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	#  @param message The message to send
	#  @param markup The keyboard (optional, default is None)
	#  @param language The language in which the message is parsed (default is HTML)
	def send_message_safely(self, chat_identity, message, markup = None, language = 'HTML'):

		try:
			self.sendMessage(chat_identity, message, parse_mode=language, reply_markup=markup)
		except telepot.exception.TooManyRequestsError as TooE:
			self.sendMessage(chat_identity, u"You can only make 20 requests per minutes. Please try later!")
		except telepot.exception.TelegramError as TeleE:
			self.sendMessage(chat_identity, u"Telegram is messing around with the results, we'll have a look into this. Sorry!")
			self.save_known_error_log(chat_identity, TeleE)
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_bot.send_message_safely')

	## This method edits the message safely, with the possibility of adding an inline keyboard.
	#
	#  @param self The object pointer
	#  @param message The message to send
	#  @param query_identity The identifier for the query (needed to answer query and for exceptions handling)
	#  @param msg_identifier The identifier for the message to be edited
	#  @param keyboard The keyboard (optional, default is None)
	def edit_message_safely(self, message, query_identity, msg_identifier, keyboard = None):

		try:
			self.editMessageText(msg_identifier, message, parse_mode='HTML', reply_markup=keyboard)
		except telepot.exception.TooManyRequestsError as TooE:
			self.answer_robust_callback_query(query_identity, message=u"You can only make 20 requests per minutes. Please try later!")
			return None
		except telepot.exception.TelegramError as TeleE:
			self.answer_robust_callback_query(query_identity, message=u"You are probably clicking the buttons too quickly. Slow down! \U0001F422")
			self.save_known_error_log(query_identity, TeleE)
			return None
		except:
			self.editMessageText(msg_identifier, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(query_identity, 'arxiv_bot.edit_message_safely')
			return None

		self.answer_robust_callback_query(query_identity)

	## This method avoids the occurrence of errors when the ArXivBot cannot answer a callback call to the user.
	#
	#  @param self The object pointer
	#  @param query_identity The identifier for the query (needed to answer query and for exceptions handling)
	#  @param message The message to send (optional, default is None)
	def answer_robust_callback_query(self, query_identity, message = None):

		try:
			self.answerCallbackQuery(query_identity, text=message)
		except:
			self.save_unknown_error_log(query_identity, 'arxiv_bot.answer_robust_callback_query')

	## This method prepares a keyboard for getting the previous/next results of a search.
	#
	#  @param self The object pointer
	#  @param start_results_from The number of the first result shown
	#  @param total_results The number of total results to show
	#  @param number_results_shown The number of results shown so far
	def search_prev_next_keyboard(self, start_results_from, total_results, number_results_shown):

		new_start_prev = str(start_results_from - number_results_shown)
		new_start_next = str(start_results_from + number_results_shown)

		close_button = InlineKeyboardButton(text = 'Close', callback_data = 'search close None')
		prev_button = InlineKeyboardButton(text = 'Prev', callback_data = 'search previous ' + new_start_prev )
		next_button = InlineKeyboardButton(text = 'Next', callback_data = 'search next ' + new_start_next )

		results_to_be_shown = total_results - ( start_results_from + number_results_shown )

		if start_results_from == 0:
			keyboard = InlineKeyboardMarkup(inline_keyboard = [[close_button, next_button]])
		else:
			if results_to_be_shown > 0:
				keyboard = InlineKeyboardMarkup(inline_keyboard = [[close_button, prev_button, next_button]])
			else:
				keyboard = InlineKeyboardMarkup(inline_keyboard = [[close_button, prev_button]])

		return keyboard

	## This method searches in the preference database for the chat_identity of the user.
	#
	#  If the chat_identity is found, return True, otherwise return False.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	def preference_exists(self, chat_identity):

		try:
			self.open_connection_with_database()
			sql_command = "SELECT exists (SELECT 1 FROM preferences WHERE user_identity = %s LIMIT 1);"
			self.cursor_database.execute(sql_command, (chat_identity,))
			preference_tuple = self.cursor_database.fetchone()
			self.close_connection_with_database()
		except psycopg2.Error as PGE:
			self.sendMessage(chat_identity, u"We are experiencing some issues with our database. Sorry!")
			self.save_known_error_log(chat_identity, PGE)
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_bot.preference_exists')

		preference_bool = preference_tuple[0]

		return preference_bool

	## This method replaces the old preferred category associated with the chat_identity with the new category provided
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	#  @param category A category of the arXiv
	def overwrite_preference(self, chat_identity, category):

		try:
			self.open_connection_with_database()
			sql_command = "UPDATE preferences SET category = %s WHERE user_identity = %s;"
			self.cursor_database.execute(sql_command, (category, chat_identity))
			self.connection_database.commit()
			self.close_connection_with_database()
		except psycopg2.Error as PGE:
			self.sendMessage(chat_identity, u"We are experiencing some issues with our database. Sorry!")
			self.save_known_error_log(chat_identity, PGE)
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_bot.overwrite_preference')

	## This method adds the preference to the database.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	#  @param category A category of the arXiv
	def add_preference(self, chat_identity, category):

		try:
			self.open_connection_with_database()
			sql_command = "INSERT INTO preferences (user_identity, category) VALUES (%s, %s);"
			self.cursor_database.execute(sql_command, (chat_identity, category))
			self.connection_database.commit()
			self.close_connection_with_database()
		except psycopg2.Error as PGE:
			self.sendMessage(chat_identity, u"We are experiencing some issues with our database. Sorry!")
			self.save_known_error_log(chat_identity, PGE)
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_bot.add_preference')

	## This method searches into the preference database for the category associated with the chat_identity provided.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	def search_for_category(self, chat_identity):

		category = None

		try:
			self.open_connection_with_database()
			sql_command = "SELECT category FROM preferences WHERE user_identity = %s;"
			self.cursor_database.execute(sql_command, (chat_identity,))
			category_tuple = self.cursor_database.fetchone()
			self.close_connection_with_database()
		except psycopg2.Error as PGE:
			self.sendMessage(chat_identity, u"We are experiencing some issues with our database. Sorry!")
			self.save_known_error_log(chat_identity, PGE)
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_bot.search_for_category')

		if not category_tuple == None:
			category = category_tuple[0]

		return category

	## This method checks if a pattern is present in a string.
	#
	#  The method should probably not belong to the class, as it is pretty general.
	#  I might think of putting in an additional library.
	#
	#  @param self The object pointer
	#  @param string A string of text
	#  @param pattern A pattern to be found in the string
	def pattern_is_present(self, string, pattern):

		index = string.find(pattern)

		if index != -1:
			return True
		return False

	## This method searches for the keywords present in a message which shows the results of a given search.
	#
	#  @param self The object pointer
	#  @param message_content The text message
	#  @param left_key A pattern to be found at the left of the required information
	#  @param right_key A pattern to be found at the right of the required information
	def find_current_keywords(self, message_content, left_key, right_key):

		keywords_start = message_content.index( left_key ) + len( left_key )
		keywords_end = message_content.index( right_key, keywords_start )

		keywords = message_content[ keywords_start : keywords_end ]
		keywords = keywords.split()

		return keywords

	## This method saves the feedback message in a log file.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	#  @param argument String with the feedback to be saved
	def save_feedback(self, chat_identity, argument):

		message_time = datetime.datetime.utcnow()

		try:
			self.open_connection_with_database()
			sql_command = "INSERT INTO feedbacks (message_time, user_identity, comment) VALUES (%s, %s, %s);"
			self.cursor_database.execute(sql_command , (message_time, chat_identity, argument))
			self.connection_database.commit()
			self.close_connection_with_database()
		except psycopg2.Error as PGE:
			self.sendMessage(chat_identity, u"We are experiencing some issues with our database. Sorry!")
			self.save_known_error_log(chat_identity, PGE)
			raise
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_bot.save_feedback')
			raise

	## This method saves the details of the message (who, what) into the postgreSQL database 'chat' for statistical purposes.
	#
	#  **NOTE**: The chat identity is saved, but not other information such as the real name of the user.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	#  @param content_type The type of content sent by the user (text, picture, etc.)
	#  @param text_message The message sent by the user
	def save_message_log(self, chat_identity, content_type, text_message, query_identity = None):

		message_time = datetime.datetime.utcnow()

		try:
			self.open_connection_with_database()
			sql_command = "INSERT INTO chat (message_time, user_identity, content_type, content, query_identity) VALUES (%s, %s, %s, %s, %s);"
			self.cursor_database.execute(sql_command , (message_time, chat_identity, content_type, text_message, query_identity))
			self.connection_database.commit()
			self.close_connection_with_database()
		except psycopg2.Error as PGE:
			self.sendMessage(chat_identity, u"We are experiencing some issues with our database. Sorry!")
			self.save_known_error_log(chat_identity, PGE)
			raise
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_bot.save_message_log')
			raise

	## This method prepares the information about a unknown errors.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	#  @param in_function A string with information about where the error verified
	def save_unknown_error_log(self, chat_identity, in_function):

		error_time = datetime.datetime.utcnow()
		error_type = 'unknown'
		error_details = 'Error occurred in function ' + in_function

		self.save_error(error_time, chat_identity, error_type, error_details)

	## This method prepares the information about a known errors.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	#  @param raised_exception A string with information about the error verified
	def save_known_error_log(self, chat_identity, raised_exception):
		
		error_time = datetime.datetime.utcnow()
		error_type = 'known'
		error_details = type(raised_exception).__name__ + ' - ' + raised_exception.args[0]

		self.save_error(error_time, chat_identity, error_type, error_details)

	## This method saves the errors into the postgreSQL database 'errors' for bug-fixing purposes.
	#
	#  @param self The object pointer
	#  @param error_time The datetime object with the current date (GMT)
	#  @param chat_identity The identity number associated to the chat
	#  @param error_type The type of the error. Can be "known" or "unknown"
	#  @param error_details A string with information about the error
	def save_error(self, error_time, chat_identity, error_type, error_details):

		try:
			self.open_connection_with_database()
			sql_command = "INSERT INTO errors (error_time, user_identity, error_type, details) VALUES (%s, %s, %s, %s);"
			self.cursor_database.execute(sql_command , (error_time, chat_identity, error_type, error_details))
			self.connection_database.commit()
			self.close_connection_with_database()
		except:
			error_time_string = error_time.strftime("%d %b %Y %H:%M:%S")
			message_on_stdout = 'Error cannot be saved in database.\n' + error_time_string + ' - ' + str(chat_identity) + ' - ' + error_details
			print message_on_stdout

	## This method opens the connection with the database
	def open_connection_with_database(self):
			
		try:
			self.connection_database = psycopg2.connect(dbname = self.database_name,
														user = self.database_user,
														password = self.database_password)
			self.cursor_database = self.connection_database.cursor()
		except:
			error_time = datetime.datetime.utcnow()
			error_time_string = error_time.strftime("%d %b %Y %H:%M:%S")
			exception_type, exception_description, traceback = sys.exc_info()
			message_on_stdout = 'Error occurred during connection to database.\n' + error_time_string + ' - ' + exception_type.__name__ + ' - ' + str(exception_description)
			print message_on_stdout

	## This method closes the connection with the database
	def close_connection_with_database(self):

		connection_is_open = self.connection_database.closed == 0
		cursor_is_open = self.cursor_database.closed == False

		if cursor_is_open:
			self.cursor_database.close()
		if connection_is_open:
			self.connection_database.close()

	# --- TO BE IMPLEMENTED IN THE FUTURE (MAYBE?) ---

	def handle_inline_query(self, msg):

		message_id, from_id, message_query = telepot.glance(msg, 'inline_query')

	def handle_chosen_inline_result(self, msg):

		result_id, from_id, message_query = telepot.glance(msg, 'chosen_inline_result')
		
	## The method can be implemented but does not seem to fit into the design of the ArXivBot.
	def do_advanced_search(self):
		
		return None
