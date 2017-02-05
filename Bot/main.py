import yaml
import time
import os
import telepot

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    print(content_type, chat_type, chat_id)

    if content_type == 'text':
        bot.sendMessage(chat_id, msg['text'])

with open(os.path.join('Data','detail.yaml'), 'r') as file_input:
	detail = yaml.load(file_input)

bot = telepot.Bot(detail['token'])

bot.message_loop(handle)
print ('Listening ...')

# Keep the program running.
while 1:
    time.sleep(10)

# # ---- MY CLASS ----

# # We create a class since we want to create a method for handle, not a function
# class MyTestBot(telepot.Bot):

# 	def __init__(self, *args, **kwargs):
# 		super(MyTestBot, self).__init__(*args, **kwargs)

# 	# Basic handle function, it print the message
# 	def handle(self, msg):

# 		# Check the flavor. At the moment, we accept only normal messages.
# 		flavor = telepot.flavor(msg)

# 		if flavor == 'normal':
# 			# Use glance method to get the basic information
# 			content_type, chat_type, chat_id = telepot.glance(msg)
# 			print(msg)
		
# 			# Send back a text to say Hello
# 			time.sleep(1)
# 			self.sendMessage(chat_id, 'Hey mate!')
	
# 		else:
# 			raise telepot.BadFlavor(msg)

# # ---- MAIN ----

# # Open the detail file with token, name of the bot, etc..
# with open('detail.yaml', 'r') as fin:
# 	detail = yaml.load(fin)

# # Initialise the Bot
# bot = MyTestBot(detail['token'])

# # Use method notifyOnMessage, which take as agrument our function handle
# bot.notifyOnMessage()

# # while loop to run as deamon
# while 1:
# 	time.sleep(10)