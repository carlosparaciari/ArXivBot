# Excetion raised when no arguments are passed to the function
class NoArgumentError(Exception):
	pass

# Exception raised when get from arxiv fails
class GetRequestError(Exception):
	pass

# Exception raised when some generic error is raised
class UnknownError(Exception):
	pass

# Exception raised when a category does not belong to the arxiv
class NoCategoryError(Exception):
	pass