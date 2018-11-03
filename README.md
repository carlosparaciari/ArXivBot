![logo](https://user-images.githubusercontent.com/8984112/28944797-c5ede3fc-789b-11e7-962f-de8e6015a419.png)

This Bot for Telegram can be used to quickly search and share papers in the [arXiv web-site](https://arxiv.org/).
The user can search for papers using some keywords, and the Bot will return a list of results. Each result is presented with the paper's title, the authors, and the link to the arXiv website. Alternatively, the user can search for the daily submissions to a given category of the arXiv (such as, for example, quant-ph).

The Bot utilises [telepot](https://github.com/nickoala/telepot), a framework for the Telegram Bot API.

## Make your own ArXivBot
You do not need to clone this repository and run the Bot on your machine.
In fact, you can find the ArXivBot at the following [link](https://storebot.me/bot/search_arxiv_bot), and you can use it straight away.

However, if you want a private Bot for searching on the arXiv, you can fork and clone the repository on your machine, and run the script `start_bot.sh`. Notice that, for the ArXivBot to work, you first need to set up a few things on your local machine. First of all, you need to create the file `bot_details.yaml` in the `.\Bot\Data\` folder, and fill it with the relevant details. See the file `example_bot_details.yaml` in the same folder for a list of all the fields you need to provide. In particular, you will need to get a token form the [BotFather](https://telegram.me/BotFather), so that your bot can connect to Telegram.

 This bot uses [PostgreSQL](https://www.postgresql.org/) databases to store the chat records, the errors generated at runtime, the feedbacks received, and the preferences of each user. Therefore, you will need to have access to a postgres server, or preferably to have set up a local server on your own machine (see for instance this easy [guide](https://help.ubuntu.com/community/PostgreSQL) for Ubuntu). Once the local server is set up, you can use the script `postgres_script.py` to create a new postgres user (the one the bot will use to store the information), a new database, and the relevant tables. Notice that you will have to provide the script with the username and password of an existing postgres user, who should have the privilege to create a new user and a database (you can use, for example, the postgres superuser). If the script does not return any error, you can start using your bot.

 While we cannot provide any further assistance, we would like to receive a feedbacks from you if you have suggestions on how to improve this small guide (or if you find a bug in the scripts).

### Improve this project
Every contribution to this project is more than welcome! If you find that the ArXivBot might be improved, by either adding new features or modifying existing ones, please modify the code of your local repository and commit it. Then, create a pull request to this project, and we will review your request.

## ArXiv library

[![Build Status](https://travis-ci.org/carlosparaciari/ArXivBot.svg?branch=master)](https://travis-ci.org/carlosparaciari/ArXivBot)

This project include a small library to communicate with the arXiv and parse the results, which can be re-used for other projects. As for the Bot itself, please feel free to improve the library, by either re-factoring it, or introducing other features. The library utilises the 3rd-party modules [Requests](http://docs.python-requests.org/en/master/), [feedparser](https://github.com/kurtmckee/feedparser), and [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/).

## Acknowledgement
We thank Thomas Galley for the logo.
