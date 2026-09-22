from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


class HttpService:
    """
    A thin HTTP client with automatic retry logic.

    Authentication is entirely external: pass pre-generated headers as
    ``headers`` for authenticated requests, or omit them for unauthenticated
    ones (e.g. fetching schemas from GitHub).

    Use :class:`~sds_common.services.auth_header_provider.AuthHeaderProvider`
    to produce the headers, then inject them here via :class:`SdsCommon` or
    directly.
    """

    def __init__(
        self,
        session: requests.Session,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.session = session
        self.headers = headers

    def make_post_request(self, url: str, data: dict, params: dict | None = None) -> requests.Response:
        """
        Make a POST request to a specified URL.

        :param url: the URL to send the POST request to.
        :param data: the JSON data to send in the POST request.
        :param params: the query parameters to include in the POST request.
        :return: the response from the POST request.
        """
        return self.session.post(url, json=data, headers=self.headers, params=params)

    def make_get_request(self, url: str, params: dict | None = None) -> requests.Response:
        """
        Make a GET request to a specified URL.

        :param url: the URL to send the GET request to.
        :param params: the query parameters to include in the GET request.
        :return: the response from the GET request.
        """
        return self.session.get(url, headers=self.headers, params=params)

    @classmethod
    def create(cls, headers: dict[str, str] | None = None) -> 'HttpService':
        """
        Build an :class:`HttpService` with a pre-configured retry session.

        :param headers: Optional headers to attach to every request (e.g. IAP Bearer token).
                        Pass ``None`` for unauthenticated clients.
        :return: A ready-to-use :class:`HttpService` instance.
        """
        return cls(session=cls._build_session(), headers=headers)

    @staticmethod
    def _build_session() -> requests.Session:
        """
        Set up an http/s session with retry logic.

        :return: a configured :class:`requests.Session`.
        """
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
