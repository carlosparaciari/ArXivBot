import telepot
import arxiv_lib as al
from customised_exceptions import NoArgumentError, GetRequestError, UnknownError, EasySearchError

import remove_emoji as remj

# Class ArxivBot inherits from the telepot.Bot class.
# The calss is used to deal with the messaged recived by the bot on Telegram,
# and to perform simple or advanced searches on the Arxiv website.

class ArxivBot(telepot.Bot):

	# Class constructor

	def __init__(self, *args, **kwargs):

		super(ArxivBot, self).__init__(*args, **kwargs)
		self.arxiv_search_link = 'http://export.arxiv.org/api/query?search_query='

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

		if content_type != 'text':
			self.sendMessage(chat_id, 'You can only send me text messages, sorry!')
			return None

		self.sendMessage(chat_id, 'Thanks for your text!') # <-------------------------------------- Remove this after!

		text_message = remj.remove_emoji_from_text(msg[content_type])

		text_message_list = text_message.split()
		command = text_message_list[0]

		if command == '/search' and len(text_message_list) > 1:
			command_argument = text_message_list[1:]
			print( command_argument )   # <-------------------------------------- Remove this after!
			self.do_easy_search( command_argument ) # <----------------------------------------------------PUT try/except here!!!
		elif command == '/advsearch' and len(text_message_list) == 1:
			self.do_advanced_search()
		elif command == '/help' and len(text_message_list) == 1:
			self.get_help()
		else:
			self.sendMessage(chat_id, 'See the /help for information on this Bot!')

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

	def do_easy_search(self, argument):

		try:
			easy_search_link = al.simple_search(argument, self.arxiv_search_link)
		except NoArgumentError:
			self.sendMessage(chat_id, 'Please provide the arguments for the search.')
			raise EasySearchError('The easy search failed.')
		except:
			self.sendMessage(chat_id, 'An unknown error occurred.')
			raise EasySearchError('The easy search failed.')

		print( easy_search_link )

		# Complete here!

		return None

	def do_advanced_search(self):

		return None

	def get_help(self):

		return None