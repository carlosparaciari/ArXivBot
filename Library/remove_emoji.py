import re

# The remove_emoji_from_text function removes any emoji from the text,
# and returns a message without emoji.
# Function taken from Stackoverflow:
#
# http://stackoverflow.com/questions/26568722/remove-unicode-emoji-using-re-in-python
#
# Thanks to Martijn Pieters.

def remove_emoji_from_text(text_msg):

	try:
		# Wide UCS-4 build
		myre = re.compile(u'['
			u'\U0001F300-\U0001F64F'
			u'\U0001F680-\U0001F6FF'
			u'\u2600-\u26FF\u2700-\u27BF]+', 
			re.UNICODE)
	except re.error:
		# Narrow UCS-2 build
		myre = re.compile(u'('
			u'\ud83c[\udf00-\udfff]|'
			u'\ud83d[\udc00-\ude4f\ude80-\udeff]|'
			u'[\u2600-\u26FF\u2700-\u27BF])+', 
			re.UNICODE)

	# Remove the emoji from the string
	cleared_text = myre.sub('', text_msg)

	return cleared_text                          # <-------------------------- DOES NOT FILTER EMOJI SUCH AS THE HEART! :(