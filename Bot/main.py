#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'Library')))

import arxiv_bot as ab
import yaml

errors_log_file = os.path.join('LogFiles', 'errors.log')
chat_log_file = os.path.join('LogFiles', 'chat_recorder.log')
feedback_log_file = os.path.join('LogFiles', 'feedbacks.log')

with open(os.path.join('Data','bot_details.yaml'), 'r') as file_input:
	detail = yaml.load(file_input)

bot = ab.ArxivBot(detail['token'])
bot.set_log_files(errors_log_file, chat_log_file, feedback_log_file)
bot.message_loop(run_forever = True)