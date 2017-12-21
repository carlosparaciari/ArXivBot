import telepot
import requests
import time
import os
import random
import tempfile
import shutil
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
	def __init__(self, *args, **kwargs):

		super(ArxivBot, self).__init__(*args, **kwargs)

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

	## This method allows for the injection of the name of the files for the error, feedback, and chat logs.
	#
	#  @param self The object pointer
	#  @param errors_file_name The string with the path to the error logfile
	#  @param message_file_name The string with the path to the chat logfile
	#  @param feedback_file_name The string with the path to the feedback logfile
	def set_log_files(self, errors_file_name, message_file_name, feedback_file_name):

		## The path to the error logfile
		self.errors_log_file = errors_file_name

		## The path to the chat logfile
		self.message_log_file = message_file_name

		## The path to the feedback logfile
		self.feedback_log_file = feedback_file_name

	## This method allows for the injection of the email address for the feedbacks
	#
	#  @param self The object pointer
	#  @param email_address The string with the email address
	def set_email_feedback(self, email_address):

		## The email address for the feedbacks
		self.feedback_address = email_address

	## This method allows for the injection of the name of the files for storing the users' preferences
	#
	#  @param self The object pointer
	#  @param preference_file_name The string with the path to the preferences database
	def set_preference_database(self, preference_file_name):

		## The path to the preference database
		self.preference_file = preference_file_name

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
		self.save_message_details_log( chat_id, content_type )

		if content_type != 'text':
			self.sendMessage(chat_id, u'You can only send me text messages, sorry!')
			return None

		text_message = msg[content_type]
		self.save_message_content_log( text_message )

		if emjd.detect_emoji(text_message):
			self.sendMessage(chat_id, u'You have used an invalid unicode character. Unacceptable! \U0001F624')
			return None

		text_message_list = text_message.split()
		command = text_message_list[0]

		if command == '/search' and len(text_message_list) > 1:
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

		self.save_message_details_log( chat_id, query_id )
		self.save_message_content_log( query_data )

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
			self.sendMessage(chat_identity, u'Please provide some arguments for the search.')
			return None
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.simple_search')
			return None

		try:
			search_list, total_results = self.search_and_format( easy_search_link, chat_identity )
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
			search_list, total_results = self.search_and_format( easy_search_link, chat_identity )
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
				self.save_unknown_error_log(chat_identity, 'arxiv_lib.do_today_search_with_set_preference')
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
			search_list, total_results = self.search_and_format( today_search_link, chat_identity, feed_type = 'RSS' )
		except:
			return None

		total_results = len(search_list)
		search_list = search_list[:self.max_rss_result_number]
		remaining_results = total_results - self.max_rss_result_number

		self.send_results_back_rss(chat_identity, search_list, remaining_results)

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
			self.save_feedback(chat_identity, message)
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

	## This method is used in the other search methods to send the request to the arXiv, parse the result, and format it accordingly.
	# 
	#  @param self The object pointer
	#  @param search_link The arXiv link for the request
	#  @param chat_identity The identity number associated to the chat
	#  @param feed_type The type of feed the method has to process (can be either API or RSS). API is default
	def search_and_format(self, search_link, chat_identity, feed_type = 'API'):

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

		try:
			search_list = al.review_response( search_dictionary , self.max_number_authors , feed_type )
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
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.parse_response')
			raise

		total_results = None

		if feed_type == 'API':
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

	## This method formats the results of the search and prepares the message to be sent to the user.
	#
	#  **NOTE**: Since only 10 results can be shown, we do not have to worry about exceeding the size limit for the message.
	#
	#  @param self The object pointer
	#  @param argument The keywords used in the search
	#  @param start_num The number of the first result shown
	#  @param search_list The unformatted list with all details about the results (prepared with the @ref search_and_format method)
	#  @param total_results The total number of results associated with the search
	def prepare_message_api(self, argument, start_num, search_list, total_results):

		result_counter = start_num + 1
		separator = ' '
		keywords = separator.join(argument)
		message_result = 'Your search keywords are:\n'+keywords+'\n\n'
		
		for result in search_list:
			new_item = '<b>'+str(result_counter)+'</b>. <em>'+result['title']+'</em>\n'+result['authors']+'\n'+result['link']+'\n\n'
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
	#  @param search_list The unformatted list with all details about the results (prepared with the @ref search_and_format method)
	#  @param remaining_results The remaining results which have not been shown
	def send_results_back_rss(self, chat_identity, search_list, remaining_results):

		result_counter = 1
		message_result = ''
		
		for result in search_list:
			new_item = '<b>'+str(result_counter)+'</b>. <em>'+result['title']+'</em>\n'+result['authors']+'\n'+result['link']+'\n\n'
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

		preference_bool = False

		with open(self.preference_file, 'r') as database:
			for item in database:
				if self.pattern_is_present( item, str(chat_identity) ):
					preference_bool = True
					break

		return preference_bool

	## This method replaces the old preferred category associated with the chat_identity with the new category provided
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	#  @param category A category of the arXiv
	def overwrite_preference(self, chat_identity, category):

		temporary_file, absolute_path_file = tempfile.mkstemp()

		with os.fdopen(temporary_file, 'w') as new_database:
			with open(self.preference_file, 'r') as old_database:
				for item in old_database:
					if self.pattern_is_present( item, str(chat_identity) ):
						item = str(chat_identity) + ' ' + str(category) + '\n'
					new_database.write(item)

		os.remove(self.preference_file)
		shutil.move(absolute_path_file, self.preference_file)

	## This method adds the preference to the database.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	#  @param category A category of the arXiv
	def add_preference(self, chat_identity, category):

		preference_string = str(chat_identity) + ' ' + str(category) + '\n'

		with open(self.preference_file, 'a') as database:
			database.write(preference_string)

	## This method searches into the preference database for the category associated with the chat_identity provided.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	def search_for_category(self, chat_identity):

		category = None

		with open(self.preference_file, 'r') as database:
			for item in database:
				identity, preference = item.split()
				if identity == str(chat_identity):
					category = preference

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

		message_time = time.strftime("%d %b %Y %H:%M:%S", time.localtime())
		message_string = message_time + ' - ' + str(chat_identity) + ' - ' + argument + '\n'
		with open(self.feedback_log_file, 'a') as fblog:
			fblog.write(message_string)

	## This method saves the details of the message (who, what) in a log file for statistical purposes.
	#
	#  **NOTE**: The chat identity is saved, but not other information such as the real name of the user.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	#  @param content_type The type of content sent by the user (text, picture, etc.)
	def save_message_details_log(self, chat_identity, content_type):

		message_time = time.strftime("%d %b %Y %H:%M:%S", time.localtime())
		message_string = message_time + ' - ' + str(chat_identity) + ' - ' + content_type + '\n'
		with open(self.message_log_file, 'a') as msglog:
			msglog.write(message_string)

	## This method saves the content of the message in a log file for statistical purposes.
	#
	#  @param self The object pointer
	#  @param text_message The message sent by the user
	def save_message_content_log(self, text_message):

		message_string = text_message+u'\n'
		with open(self.message_log_file, 'a') as msglog:
			msglog.write(message_string.encode('utf8'))

	## This method saves the unknown errors in a log file for bug-fixing purposes.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	#  @param in_function A string with information about where the error verified
	def save_unknown_error_log(self, chat_identity, in_function):

		error_time = time.strftime("%d %b %Y %H:%M:%S", time.localtime())
		error_string = error_time + ' - ' + str(chat_identity) + ' - ' + 'Unknown error occurred while running ' + in_function + ' function.' + '\n'
		with open(self.errors_log_file, 'a') as errlog:
			errlog.write(error_string)

	## This method saves the known errors in a log file for bug-fixing purposes.
	#
	#  @param self The object pointer
	#  @param chat_identity The identity number associated to the chat
	#  @param raised_exception A string with information about the error verified
	def save_known_error_log(self, chat_identity, raised_exception):

		error_time = time.strftime("%d %b %Y %H:%M:%S", time.localtime())
		error_string = error_time + ' - ' + str(chat_identity) + ' - ' + type(raised_exception).__name__ + ' - ' + raised_exception.args[0] + '\n'
		with open(self.errors_log_file, 'a') as errlog:
			errlog.write(error_string)

	# --- TO BE IMPLEMENTED IN THE FUTURE (MAYBE?) ---

	def handle_inline_query(self, msg):

		message_id, from_id, message_query = telepot.glance(msg, 'inline_query')

	def handle_chosen_inline_result(self, msg):

		result_id, from_id, message_query = telepot.glance(msg, 'chosen_inline_result')
		
	## The method can be implemented but does not seem to fit into the design of the ArXivBot.
	def do_advanced_search(self):
		
		return None
