# Exception raised when no arguments are passed to the function

class NoArgumentError(Exception):
	pass

# Exception raised when get from arXiv fails

class GetRequestError(Exception):
	pass

# Exception raised when some generic error is raised

class UnknownError(Exception):
	pass

# Exception raised when a category does not belong to the arXiv

class NoCategoryError(Exception):
	pass