# Excetion raised when no arguments are passed to the function
class NoArgumentError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

# Exception raised when get from arxiv fails
class GetRequestError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

# Exception raised when some generic error is raised
class UnknownError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

