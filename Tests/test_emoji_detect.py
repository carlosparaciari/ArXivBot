import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'Library')))

from nose.tools import assert_raises, assert_equal
import emoji_detect as emjd

def test_emoji_detect_failure():

	message = u'I am happy without emoji!'
	assert_equal(emjd.detect_emoji(message), False, "The function detects false emoji.")

def test_emoji_detect_succedes():

	message = u'I am sad! \U0001f61e'
	assert_equal(emjd.detect_emoji(message), True, "The function does not detect emoji.")