from http import HTTPStatus
from io import BytesIO
from typing import Dict

from google.appengine.api import urlfetch
from requests import PreparedRequest, Response
from requests.adapters import BaseAdapter
from requests.cookies import extract_cookies_to_jar
from requests.utils import get_encoding_from_headers
from urllib3.response import HTTPResponse


class URLFetchAdapter(BaseAdapter):
    """
    A `requests` transport adapter that delegates to App Engine's urlfetch service
    """

    def send(
        self,
        request: PreparedRequest,
        stream,
        timeout=None,
        verify=True,
        cert=None,
        proxies=None,
    ) -> Response:
        """Sends PreparedRequest object. Returns Response object.

        :param request: The :class:`PreparedRequest <PreparedRequest>` being sent.
        :param stream: (optional) Whether to stream the request content.
        :param timeout: (optional) How long to wait for the server to send
            data before giving up, as a float, or a :ref:`(connect timeout,
            read timeout) <timeouts>` tuple.
        :type timeout: float or tuple
        :param verify: (optional) Either a boolean, in which case it controls whether we verify
            the server's TLS certificate, or a string, in which case it must be a path
            to a CA bundle to use
        :param cert: (optional) Any user-provided SSL certificate to be trusted.
        :param proxies: (optional) The proxies dictionary to apply to the request.
        """

        del request.headers["Accept-Encoding"]
        result = urlfetch.fetch(
            url=request.url,
            payload=request.body,
            method=request.method,
            headers=request.headers,
            deadline=timeout,
            validate_certificate=True,
        )
        return self._build_response(result, result)

    def close(self):
        """Cleans up adapter specific items."""
        pass

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
        self, req: PreparedRequest, resp: urlfetch._URLFetchResult
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

        # Add new cookies from the server.
        extract_cookies_to_jar(response.cookies, req, resp)

        # Give the Response some context.
        response.request = req

        return response
