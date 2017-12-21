from emoji import UNICODE_EMOJI

## @package Library.emoji_detect
#  Micro-library containing functions to filter emoji 

## This function searches a string searching for emoji
#
#  @param text_msg String with some text
def detect_emoji(text_msg):

    for emoji in UNICODE_EMOJI:
        if text_msg.find(emoji) != -1:
        	return True

    return False
