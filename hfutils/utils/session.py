"""
This module provides functionality for creating and managing HTTP sessions with customizable retry logic,
timeout settings, and user-agent rotation using random user-agent generation. It is designed to help with
robust web scraping and API consumption by handling common HTTP errors and timeouts gracefully.

Main Features:

- Automatic retries on specified HTTP response status codes.
- Configurable request timeout.
- Rotating user-agent for each session to mimic different browsers and operating systems.
- Optional SSL verification.
"""

from functools import lru_cache
from typing import Optional, Dict

import requests
from random_user_agent.params import SoftwareName, OperatingSystem
from random_user_agent.user_agent import UserAgent
from requests.adapters import HTTPAdapter, Retry

DEFAULT_TIMEOUT = 15  # seconds


class TimeoutHTTPAdapter(HTTPAdapter):
    """
    A custom HTTPAdapter that enforces a default timeout on all requests.

    :param args: Variable length argument list for HTTPAdapter.
    :param kwargs: Arbitrary keyword arguments. 'timeout' can be specified to set a custom timeout.
    """

    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        """
        Sends the Request object, applying the timeout setting.

        :param request: The Request object to send.
        :type request: requests.PreparedRequest
        :param kwargs: Keyword arguments that may contain 'timeout'.
        :return: The response to the request.
        """
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


def get_requests_session(max_retries: int = 5, timeout: int = DEFAULT_TIMEOUT, verify: bool = True,
                         headers: Optional[Dict[str, str]] = None, session: Optional[requests.Session] = None) \
        -> requests.Session:
    """
    Creates a requests session with retry logic, timeout settings, and random user-agent headers.

    :param max_retries: Maximum number of retries on failed requests.
    :type max_retries: int
    :param timeout: Request timeout in seconds.
    :type timeout: int
    :param verify: Whether to verify SSL certificates.
    :type verify: bool
    :param headers: Additional headers to include in the requests.
    :type headers: Optional[Dict[str, str]]
    :param session: An existing requests.Session instance to use.
    :type session: Optional[requests.Session]
    :return: A configured requests.Session object.
    :rtype: requests.Session
    """
    session = session or requests.session()
    retries = Retry(
        total=max_retries, backoff_factor=1,
        status_forcelist=[408, 429, 500, 501, 502, 503, 504, 505, 506, 507, 509, 510, 511],
        allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
    )
    adapter = TimeoutHTTPAdapter(max_retries=retries, timeout=timeout, pool_connections=32, pool_maxsize=32)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        "User-Agent": get_random_ua(),
        **dict(headers or {}),
    })
    if not verify:
        session.verify = False

    return session


@lru_cache()
def _ua_pool():
    """
    Creates and caches a UserAgent rotator instance with a specified number of user agents.

    :return: A UserAgent rotator instance.
    :rtype: UserAgent
    """
    software_names = [SoftwareName.CHROME.value, SoftwareName.FIREFOX.value, SoftwareName.EDGE.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.MACOS.value]

    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=1000)
    return user_agent_rotator


def get_random_ua():
    """
    Retrieves a random user agent string from the cached UserAgent rotator.

    :return: A random user agent string.
    :rtype: str
    """
    return _ua_pool().get_random_user_agent()
