class PreprocessingError(Exception):
    """
    Custom Error to avpoid raising too generic ValueErrors
    """
    pass


class NoDataFoundError(PreprocessingError):
    """"""
    pass


