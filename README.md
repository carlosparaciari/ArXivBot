![logo](https://user-images.githubusercontent.com/8984112/28944797-c5ede3fc-789b-11e7-962f-de8e6015a419.png)

This Bot for Telegram can be used to quickly search and share papers in the [arXiv web-site](https://arxiv.org/).
The user can search for papers using some keywords, and the Bot will return a list of results. Each result is presented with the paper's title, the authors, and the link to the arXiv website. Alternatively, the user can search for the daily submissions to a given category of the arXiv (such as, for example, quant-ph).

The Bot utilises [telepot](https://github.com/nickoala/telepot), a framework for the Telegram Bot API.

## Make your own ArXivBot
You do not need to clone this repository and run the Bot on your machine.
In fact, you can find the ArXivBot at the following [link](https://telegram.me/search_arxiv_bot), and you can use it straight away.

However, if you want a private Bot for searching on the arXiv, you can fork and clone the repository on your machine, and run the script `start_bot.sh`. For the ArXivBot to work, you first need to get a token form the [BotFather](https://telegram.me/BotFather), and save it in the yaml file in the directory `.\Bot\Data\` (change the name of the yaml file to `bot_details.yaml`).

### Improve this project
Every contribution to this project is more than welcome! If you find that the ArXivBot might be improved, by either adding new features or modifying existing ones, please modify the code of your local repository and commit it. Then, create a pull request to this project, and we will review your request.

## ArXiv Library
This project include a small library to communicate with the arXiv and parse the results, which can be re-used for other projects. As for the Bot itself, please feel free to improve the library, by either re-factoring it, or introducing other features. The library utilises the 3rd-party modules [Requests](http://docs.python-requests.org/en/master/) and [feedparser](https://github.com/kurtmckee/feedparser).
