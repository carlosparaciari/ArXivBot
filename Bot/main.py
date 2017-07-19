# -*- coding: utf-8 -*-

import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'Library')))

import arxiv_bot as ab
import yaml

with open(os.path.join('Data','bot_details.yaml'), 'r') as file_input:
	detail = yaml.load(file_input)

bot = ab.ArxivBot(detail['token'])

bot.message_loop(run_forever = True)