import telepot
import requests
import time
import os
import arxiv_lib as al
import emoji_detect as emjd
from customised_exceptions import NoArgumentError, GetRequestError, UnknownError, EasySearchError

# Class ArxivBot inherits from the telepot.Bot class.
# The calss is used to deal with the messaged recived by the bot on Telegram,
# and to perform simple or advanced searches on the Arxiv website.

class ArxivBot(telepot.Bot):

	# Class constructor

	def __init__(self, *args, **kwargs):

		super(ArxivBot, self).__init__(*args, **kwargs)
		self.arxiv_search_link = 'http://export.arxiv.org/api/query?search_query='
		self.errors_log_file = os.path.join('LogFiles', 'errors.log')
		self.message_log_file = os.path.join('LogFiles', 'chat_recorder.log')

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
			self.do_easy_search( command_argument , chat_id)
		elif command == '/advsearch' and len(text_message_list) == 1:
			self.do_advanced_search()
		elif command == '/help' and len(text_message_list) == 1:
			self.get_help()
		else:
			self.sendMessage(chat_id, u'See the /help for information on this Bot!')

		# COULD PUT THIS IN FILE, as a LOG!

		print( content_type, chat_type, chat_id )   # <-------------------------------------- Remove this after!
		print( text_message )   # <-------------------------------------- Remove this after!
		print( text_message_list )   # <-------------------------------------- Remove this after!
		print( command )   # <-------------------------------------- Remove this after!

		# UNTIL HERE!

		# Complete here!

	# --- TO BE IMPLEMENTED ---

	def handle_callback_query(self, msg):

		message_id, from_id, message_data = telepot.glance(msg, 'callback_query')

	def handle_inline_query(self, msg):

		message_id, from_id, message_query = telepot.glance(msg, 'inline_query')

	def handle_chosen_inline_result(self, msg):

		result_id, from_id, message_query = telepot.glance(msg, 'chosen_inline_result')

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

		try:
			easy_search_response = al.request_to_arxiv(easy_search_link)
		except TypeError as TE:
			self.sendMessage(chat_identity, u'The url got corrupted. Try again!')
			self.save_known_error_log(chat_identity, TE)
			return None
		except GetRequestError as GRE:
			self.sendMessage(chat_identity, u'The search arguments are fine, but the search on the ArXiv failed.')
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
			easy_search_dictionary = al.parse_response(easy_search_response)
		except TypeError as TE:
			self.sendMessage(chat_identity, u'The result of the search got corrupted.')
			self.save_known_error_log(chat_identity, TE)
			return None
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.parse_response')
			return None

		try:
			easy_search_list = al.review_response( easy_search_dictionary )
		except NoArgumentError:
			self.sendMessage(chat_identity, u'No result has been found for your search. Try again!')
			return None
		except TypeError as TE:
			self.sendMessage(chat_identity, u'The result of the search got corrupted.')
			self.save_known_error_log(chat_identity, TE)
			return None
		except:
			self.sendMessage(chat_identity, u'An unknown error occurred. \U0001F631')
			self.save_unknown_error_log(chat_identity, 'arxiv_lib.parse_response')
			return None

		self.send_results_back(chat_identity, easy_search_list)

		return None

	def do_advanced_search(self):

		return None

	def get_help(self):

		return None

	def send_results_back(self, chat_identity, search_list):

		result_counter = 1
		message_result = ''

		for result in search_list:
			message_result += '<b>'+str(result_counter)+u'</b>. <em>'+result['title']+u'</em>\n'+result['authors']+u'\n\n'+result['link']+u'\n\n'
			result_counter += 1

		self.sendMessage(chat_identity, message_result, parse_mode='HTML')

	def save_message_details_log(self, chat_identity, content_type):

		message_time = time.strftime("%d %b %Y %H:%M:%S", time.localtime())
		message_string = message_time+' - '+str(chat_identity)+' - '+content_type+'\n'
		with open(self.message_log_file, 'a') as msglog:
			msglog.write(message_string)

	def save_message_content_log( self, text_message ):

		message_string = text_message+u'\n'
		with open(self.message_log_file, 'a') as msglog:
			msglog.write(message_string.encode('utf8'))

	def save_unknown_error_log(self, chat_identity, in_function):

		error_time = time.strftime("%d %b %Y %H:%M:%S", time.localtime())
		error_string = error_time+' - '+str(chat_identity)+' - '+'Unknown error occurred while running '+in_function+' function.'+'\n'
		with open(self.errors_log_file, 'a') as errlog:
			errlog.write(error_string)

	def save_known_error_log(self, chat_identity, raised_exception):

		error_time = time.strftime("%d %b %Y %H:%M:%S", time.localtime())
		error_string = error_time+' - '+str(chat_identity)+' - '+str(type(raised_exception))+' - '+str(raised_exception.args)+'\n'
		with open(self.errors_log_file, 'a') as errlog:
			errlog.write(error_string)
		