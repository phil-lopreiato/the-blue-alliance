from io import BytesIO
from http import HTTPStatus
from typing import Dict

from google.appengine.api import urlfetch
from google.appengine.api.apiproxy_stub_map import UserRPC
from requests import PreparedRequest, Response, Session
from requests.cookies import extract_cookies_to_jar
from requests.utils import get_encoding_from_headers
from urllib3.response import HTTPResponse


from backend.common.futures import AwaitableRPC
from backend.common.http.urlfetch_adapter import URLFetchAdapter


class AwaitableResponse(AwaitableRPC):

    def _transform_response(self, resp):
        return self._build_response(resp)

    def _decode_content(self, data: bytes, headers: Dict[str, str]) -> bytes:
        content_encoding = headers.get("content-encoding", "").lower()
        decoder = None
        if content_encoding in HTTPResponse.CONTENT_DECODERS:
            decoder = HTTPResponse._get_decoder(content_encoding)
        elif "," in content_encoding:
            encodings = [
                e.strip()
                for e in content_encoding.split(",")
                if e.strip() in HTTPResponse.CONTENT_DECODERS
            ]
            if len(encodings):
                decoder = HTTPResponse._get_decoder(content_encoding)
        if not decoder:
            return data
        return decoder.decompress(data)

    def _build_response(
        self, resp: urlfetch._URLFetchResult
    ) -> Response:
        """Builds a :class:`Response <requests.Response>` object from a urllib3
        response. This should not be called from user code, and is only exposed
        for use when subclassing the
        :class:`HTTPAdapter <requests.adapters.HTTPAdapter>`

        :param req: The :class:`PreparedRequest <PreparedRequest>` used to generate the response.
        :param resp: The appengine response object.
        :rtype: requests.Response
        """
        response = Response()

        response.status_code = resp.status_code
        response.headers = resp.headers

        # Set encoding.
        response.encoding = get_encoding_from_headers(response.headers)
        response.raw = BytesIO(self._decode_content(resp.content, resp.headers))
        response.reason = HTTPStatus(resp.status_code).phrase

        response.url = resp.final_url

        return response


class URLFetchSession(Session):
    """
    A `requests` compatible Session that is backed by GAE urlfetch service
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.adapter = URLFetchAdapter()
        self.mount("http://", self.adapter)
        self.mount("https://", self.adapter)

    def request(self, method, url, **kwargs):
        rpc = urlfetch.create_rpc()
        headers = kwargs.pop("headers", {})
        future = urlfetch.make_fetch_call(rpc, url=url, method=method, headers=headers, payload=kwargs.get("data"))
        return AwaitableResponse(future)
