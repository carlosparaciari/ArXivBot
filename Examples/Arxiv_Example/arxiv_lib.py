import requests
import feedparser
import urllib

# Advanced search the arxiv.
# As parameter, it takes the following parameters:
#
# au	Author
# ti	Title
# abs	Abstract
# co	Comment
# jr	Journal Reference
# cat	Subject Category
# rn	Report Number
# id	Id (use id_list instead)
# 
# which are set to Null by default.

def advanced_search(author, title, abstract, comment, jref, category, rnum, identity):

	# We create the string for the advanced search
	search_def = ''

	# Check we provide the correct fields and create the
	if isinstance(author, str):
		search_def += 'au:' + author + '+AND+'
	if isinstance(title, str):
		search_def += 'ti:' + title + '+AND+'
	if isinstance(abstract, str):
		search_def += 'abs:' + abstract + '+AND+'
	if isinstance(comment, str):
		search_def += 'co:' + comment + '+AND+'
	if isinstance(jref, str):
		search_def += 'jr:' + jref + '+AND+'
	if isinstance(category, str):
		search_def += 'cat:' + category + '+AND+'
	if isinstance(rnum, str):
		search_def += 'rn:' + rnum + '+AND+'
	if isinstance(identity, str):
		search_def += 'id:' + identity + '+AND+'

	# Check that search_def is not empty. In that case, return error
	if len(search_def) == 0:
		raise exception

	# Remove last and we put
	print(search_def) 
		
	response = requests.post('http://export.arxiv.org/api/query', data = {'search_query':'au:alhambra_a'}) 

advanced_search('autor', 'title', 'abstract', 'comment', 'jref', 'category', 'rnum', 'identity')
