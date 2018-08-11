import traceback
import requests
from requests import RequestException
from ristomele.logger import Logger
from ristomele.gui.error import ErrorMessage

DESCRIPTION = """
Controllare che il cellulare sia collegato alla rete WIFI corretta
"""

class SmartRequests(object):
    """
    Like requests, but it always print a traceback on exception and raises on
    400s and 500s status codes
    """

    def do_smart_request(self, method, *args, **kwargs):
        error_message = kwargs.pop('error', '')
        meth = getattr(requests, method)
        try:
            resp = meth(*args, **kwargs)
            resp.raise_for_status()
            return resp
        except RequestException as e:
            Logger.exception('SmartRequests exception')
            raise ErrorMessage(error_message, DESCRIPTION)

    def get(self, *args, **kwargs):
        return self.do_smart_request('get', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.do_smart_request('put', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.do_smart_request('post', *args, **kwargs)
