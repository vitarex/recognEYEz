from typing import Dict

class InvalidUsage(Exception):
    """Raised when there are missing arguments in a request"""
    status_code = 400

    def __init__(self, message: str, status_code: int = None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self) -> Dict:
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv
