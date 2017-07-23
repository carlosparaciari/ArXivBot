import telepot
import requests
import time
import os
import random
import arxiv_lib as al
import emoji_detect as emjd
from customised_exceptions import NoArgumentError, GetRequestError, UnknownError, NoCategoryError

# Class ArxivBot inherits from the telepot.Bot class.
# The calss is used to deal with the messaged recived by the bot on Telegram,
# and to perform simple or advanced searches on the Arxiv website.

class ArxivBot(telepot.Bot):

	# Class constructor

	def __init__(self, *args, **kwargs):

		super(ArxivBot, self).__init__(*args, **kwargs)
		self.arxiv_search_link = 'http://export.arxiv.org/api/query?search_query='
		self.max_result_number = 50
		self.max_number_authors = 5
		self.max_characters_chat = 4096
		self.arxiv_fair_time = 3

	# The method allows for the injection of the filenames of the error and chat logs

	def set_log_files(self, errors_file_name, message_file_name, feedback_file_name):

		self.errors_log_file = errors_file_name
		self.message_log_file = message_file_name
		self.feedback_log_file = feedback_file_name

	# The handle method receives the message sent by the user and processes it depending
	# on the different "flavor" associated to it.

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

	# The handle_chat_message method is called by the handle method when the "flavor" of the
	# message is 'chat'. The user is allowed to send three different commands:
	#
	# - /search = perform a simple serch on all fields in the Arxiv
	# - /advsearch = perform an advanced search within different fields in the Arxiv
	# - /help = send an help message to the user
	#
	# If another command is sent, the method suggest the user to use the /help.
	# If the /search command is used, the do_easy_search method is called.
	# If the /advsearch command is used, the do_advanced_search is called.
	# If the /help command is used, a message with the description of the commands is sent.
	#
	# After the search is done, the results are sent to the user and the task is finished.

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
			self.do_easy_search( command_argument , chat_id )
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

	# The do_easy_search method is used when the user calls the /search command.
	# The methods takes as input
	#
	# - The argument of the search, a list of unicode strings (text) which define the search
	# - The identity of the chat, so as to be able to answer the call
	#
	# The method composes the arxiv link to which the requests is sent, makes a requests to
	# the website, parses the results, and sends them to the user.
	#
	# NOTICE : No more than 10 results are shown due to the limitations on the screen of mobilephones.
	# 		   The user is nevertheless advised to refine the search if more than 10 results are obtained.

	def do_easy_search(self, argument, chat_identity):

		try:
			easy_search_link = al.simple_search(argument, self.arxiv_search_link)
		except NoArgumentError:
			self.sendMessage(chat_identity, u'Please provide some arguments for the search.')
			return None
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.single_search')
			return None

		self.search_and_reply( easy_search_link, chat_identity )

		return None

	# The do_today_search method is used when the user calls the /today command.
	# It search for the papers of the day in a given category of the arxiv.
	# The methods takes as input
	#
	# - The arxiv category we are interested in (ONLY one category for limiting the number of results)
	# - The identity of the chat, so as to be able to answer the call
	#
	# The method composes the arxiv link to which the requests is sent, makes a requests to
	# the website, parses the results, and sends them to the user.
	#
	# NOTICE : Only for this kind of search, we allow for a maximum of 50 results.
	# 		   If more results are presents, the user is notified.

	def do_today_search(self, arxiv_category, chat_identity):

		today_time_GMT = time.gmtime()

		try:
			today_search_link = al.search_day_submissions(today_time_GMT, arxiv_category, self.arxiv_search_link)
		except NoCategoryError:
			self.sendMessage(chat_identity, u'Please use the arXiv subjects.\nSee https://arxiv.org/help/api/user-manual for further information.')
			return None
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.search_day_submissions')
			return None

		self.search_and_reply( today_search_link, chat_identity, self.max_result_number )

		return None

	# This method return the email address where the user can submit a feedback

	def give_feedback(self, argument, chat_identity):

		if len(argument) == 0:
			feedback_response = u"We are always happy to hear your view! \U0001F4E3\n\nUse /feedback <i>your comment</i>\nor email us at carlo.sparaciari@gmail.com"
		else:
			separator = ' '
			message = separator.join(argument)
			self.save_feedback(chat_identity, message)
			feedback_response = u'Thanks for your feedback! \U0001F604'

		self.sendMessage(chat_identity, feedback_response, parse_mode='HTML')

		return None

	# The method get_help provide some useful information about the Bot to the user

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
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.specify_number_of_results')
			return None

		message = u"Search for papers on the arXiv with this bot. Search papers using some keywords, or check the new submissions to your favourite category, and share the results easily. With ArXivBot you can\n\n- make a /search using some keywords\n    <i>e.g. /search atom 2017</i>\n\n- look at what's going on /today in the arXiv\n    <i>e.g. /today " + example_category + u"</i>\n\n- send us your /feedback\n    <i>e.g. /feedback I like this bot!</i>\n\nEnjoy your search! \U0001F609"
		self.sendMessage(chat_identity, message, parse_mode='HTML')

		return None

	# The search_and_reply method is used in the other search methods to
	# send the request to the arxiv, parse the result, and send it to the
	# user.
	# The methods takes as input
	#
	# - The arxiv link for the request
	# - The identity of the chat, so as to be able to answer the call
	# - The maximum number of result to be displayed (by default this is 10)

	def search_and_reply(self, search_link, chat_identity, max_number = 10):

		try:
			search_link = al.specify_number_of_results(search_link, max_number)
		except ValueError as VE:
			self.sendMessage(chat_identity, u'The number of shown results cannot be negative.')
			self.save_known_error_log(chat_identity, VE)
			return None
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.specify_number_of_results')
			return None

		try:
			search_response = al.request_to_arxiv(search_link)
		except TypeError as TE:
			self.sendMessage(chat_identity, u'The url got corrupted. Try again!')
			self.save_known_error_log(chat_identity, TE)
			return None
		except GetRequestError as GRE:
			self.sendMessage(chat_identity, u'The search arguments are fine, but the search on the arXiv failed.')
			self.save_known_error_log(chat_identity, GRE)
			return None
		except requests.exceptions.HTTPError as HTTPE:
			self.sendMessage(chat_identity, u'We are currently experiencing connection problems, sorry!')
			self.save_known_error_log(chat_identity, HTTPE)
			return None
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.request_to_arxiv')
			return None

		try:
			search_dictionary = al.parse_response(search_response)
		except TypeError as TE:
			self.sendMessage(chat_identity, u'The result of the search got corrupted.')
			self.save_known_error_log(chat_identity, TE)
			return None
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.parse_response')
			return None

		try:
			search_list = al.review_response( search_dictionary , self.max_number_authors )
		except NoArgumentError:
			self.sendMessage(chat_identity, u'No result has been found for your search. Try again!')
			return None
		except TypeError as TE:
			self.sendMessage(chat_identity, u'The result of the search got corrupted.')
			self.save_known_error_log(chat_identity, TE)
			return None
		except ValueError as VE:
			self.sendMessage(chat_identity, u'We are experiencing some technical problems, sorry!')
			self.save_known_error_log(chat_identity, VE)
			return None
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.parse_response')
			return None

		try:
			total_results = al.total_number_results( search_dictionary )
			remaining_results = total_results - max_number
		except NoArgumentError as NAE:
			self.sendMessage(chat_identity, u'The result of the search got corrupted.')
			self.save_known_error_log(chat_identity, NAE)
			return None
		except TypeError as TE:
			self.sendMessage(chat_identity, u'The result of the search got corrupted.')
			self.save_known_error_log(chat_identity, TE)
			return None
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.total_number_results')
			return None

		self.send_results_back(chat_identity, search_list, remaining_results)

		time.sleep( self.arxiv_fair_time ) 

		return None

	# The method send_results_back format the result of the searh and send it to the user.
	#
	# NOTICE: Telegram does not allow for sending messages bigger than 4096 characters,
	#         so the method cut the message into chucks if the total number of characters is bigger. 

	def send_results_back(self, chat_identity, search_list, remaining_results):

		result_counter = 1
		message_result = ''

		for result in search_list:
			new_item = '<b>'+str(result_counter)+'</b>. <em>'+result['title']+'</em>\n'+result['authors']+'\n'+result['link']+'\n\n'
			message_result = self.check_size_and_split_message(message_result, new_item, chat_identity)
			result_counter += 1
		
		if remaining_results > 0:
			remaining_information = 'There are ' + str(remaining_results) + ' unshown results.\nConsider refining your search, or visit the Arxiv webpage.'
			message_result = self.check_size_and_split_message(message_result, remaining_information, chat_identity)

		self.send_message_safely( message_result, chat_identity )

	# The methods checks the lenght of the message and divides it if the max number of characters is exceeded.

	def check_size_and_split_message(self, message, new_item, chat_identity):

		message_would_exceed = len(message) + len(new_item) >= self.max_characters_chat
		if message_would_exceed:
			self.send_message_safely( message, chat_identity )
			message = ''
		message += new_item

		return message

	# Send message safely

	def send_message_safely(self, message, chat_identity):

		try:
			self.sendMessage(chat_identity, message, parse_mode='HTML')
		except TelegramError as TeleE:
			self.sendMessage(chat_identity, u"Telegram is messing around with the results, we'll have a look into this. Sorry!")
			self.save_known_error_log(chat_identity, TeleE)
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.total_number_results')

	# Saves the feedback message in a log file

	def save_feedback(self, chat_identity, argument):

		message_time = time.strftime("%d %b %Y %H:%M:%S", time.localtime())
		message_string = message_time + ' - ' + str(chat_identity) + ' - ' + argument + '\n'
		with open(self.feedback_log_file, 'a') as fblog:
			fblog.write(message_string)


	# Saves the details of the message (who, what) in a log file for statistical purposes

	def save_message_details_log(self, chat_identity, content_type):

		message_time = time.strftime("%d %b %Y %H:%M:%S", time.localtime())
		message_string = message_time + ' - ' + str(chat_identity) + ' - ' + content_type + '\n'
		with open(self.message_log_file, 'a') as msglog:
			msglog.write(message_string)

	# Saves the content of the message in a log file for statistical purposes

	def save_message_content_log( self, text_message ):

		message_string = text_message+u'\n'
		with open(self.message_log_file, 'a') as msglog:
			msglog.write(message_string.encode('utf8'))

	# Saves the unknown errors in a log file for bug fixing purposes

	def save_unknown_error_log(self, chat_identity, in_function):

		error_time = time.strftime("%d %b %Y %H:%M:%S", time.localtime())
		error_string = error_time + ' - ' + str(chat_identity) + ' - ' + 'Unknown error occurred while running ' + in_function + ' function.' + '\n'
		with open(self.errors_log_file, 'a') as errlog:
			errlog.write(error_string)

	# Saves the known errors in a log file for bug fixing purposes

	def save_known_error_log(self, chat_identity, raised_exception):

		error_time = time.strftime("%d %b %Y %H:%M:%S", time.localtime())
		error_string = error_time + ' - ' + str(chat_identity) + ' - ' + type(raised_exception).__name__ + ' - ' + raised_exception.args[0] + '\n'
		with open(self.errors_log_file, 'a') as errlog:
			errlog.write(error_string)

	# --- TO BE IMPLEMENTED IN THE FUTURE (MAYBE) ---

	def handle_callback_query(self, msg):

		message_id, from_id, message_data = telepot.glance(msg, 'callback_query')

	def handle_inline_query(self, msg):

		message_id, from_id, message_query = telepot.glance(msg, 'inline_query')

	def handle_chosen_inline_result(self, msg):

		result_id, from_id, message_query = telepot.glance(msg, 'chosen_inline_result')
		
	# Advanced search (the method can be implemented but does not seem to fit into the design of the Bot)

	def do_advanced_search(self):
		
		return None