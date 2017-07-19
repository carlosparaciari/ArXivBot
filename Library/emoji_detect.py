from emoji import UNICODE_EMOJI

# The function detect_emoji search the string text_msg and return True if
# the string contains an emoji, False otherwhise.

def detect_emoji(text_msg):

    for emoji in UNICODE_EMOJI:
        if text_msg.find(emoji) != -1:
        	return True

    return False