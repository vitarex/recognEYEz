from flask import Request, Response
from typing import Tuple, List
from Library.errors import InvalidUsage

def parse(request: Request, argument_name: str, raise_if_none: bool = False):
    """Parse the request arguments or form for the given argument

    Arguments:
        request {request} -- Request to parse
        argument_name {str} -- Argument to find

    Returns:
        Object -- The parsed argument or None if the argument could not be found
    """
    if argument_name in request.args.keys():
        return request.args.get(argument_name)
    if argument_name in request.form.keys():
        return request.form[argument_name]
    if raise_if_none:
        raise InvalidUsage("The request argument {} could not be found".format(argument_name))
    return None

def parse_list(request: Request, arguments_list: List[str], raise_if_none: bool = False) -> Tuple:
    """Parse a list of arguments from a request

    Arguments:
        request {request} -- Request to parse
        arguments_list {List[str]} -- List of argument names
        raise_if_none {bool} -- Raise an exception if one of the arguments was not found

    Returns:
        Tuple -- The tuple of parsed arguments
    """
    argument_tuple = tuple()
    for argument in arguments_list:
        argument_tuple = argument_tuple + (parse(request, argument, raise_if_none),)
    return argument_tuple

class OKResponse(Response):
    def __init__(self,
                 response='',
                 status=200,
                 headers=None,
                 mimetype=None,
                 content_type=None,
                 direct_passthrough=False,
                 ):
        return super().__init__(response,
                                status,
                                headers,
                                mimetype,
                                content_type,
                                direct_passthrough)
