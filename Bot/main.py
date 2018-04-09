#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'Library')))
import arxiv_bot as ab
import yaml
import datetime
from telepot.loop import MessageLoop

with open(os.path.join('Data','bot_details.yaml'), 'r') as file_input:
	detail = yaml.load(file_input)

# Set up the ArXivBot

bot = ab.ArxivBot(detail['token'], detail['database_name'], detail['database_user'], detail['database_password'])
bot.set_email_feedback(detail['email'])

# Start running the service

try:
	MessageLoop(bot).run_forever()
except:
	error_time = datetime.datetime.utcnow()
	error_time_string = error_time.strftime("%d %b %Y %H:%M:%S")
	exception_type, exception_description, traceback = sys.exc_info()
	message_on_stdout = 'Error occurred during message_loop.\n' + error_time_string + ' - ' + exception_type.__name__ + ' - ' + str(exception_description)
	print message_on_stdout

del bot
