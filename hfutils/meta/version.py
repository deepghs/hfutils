"""
This module provides functionality to retrieve information about Hugging Face sites and their versions.

It contains utilities to identify whether a site is the official Hugging Face hub or a custom
deployment, along with version information when available.
"""

from dataclasses import dataclass
from typing import Optional

from huggingface_hub.constants import ENDPOINT
from huggingface_hub.utils import get_session, build_hf_headers, hf_raise_for_status


@dataclass
class HfSiteInfo:
    """
    Data class containing information about a Hugging Face site.

    This class holds metadata about a Hugging Face deployment, including
    the site identifier and version information.

    :param site: The site identifier (e.g., 'huggingface' for official hub)
    :type site: str
    :param version: The version of the site deployment, if available
    :type version: Optional[str]

    Example::

        >>> site_info = HfSiteInfo(site='huggingface')
        >>> print(site_info.site)
        huggingface
        >>> site_info = HfSiteInfo(site='custom-hub', version='1.2.3')
        >>> print(f"{site_info.site} v{site_info.version}")
        custom-hub v1.2.3
    """
    site: str
    version: Optional[str] = None


def hf_site_info(endpoint: Optional[str] = None, hf_token: Optional[str] = None) -> HfSiteInfo:
    """
    Retrieve information about a Hugging Face site deployment.

    This function queries the version API endpoint to determine if the target
    is the official Hugging Face hub or a custom deployment. For custom
    deployments, it also retrieves version information.

    :param endpoint: The API endpoint URL. If None, uses the default Hugging Face endpoint
    :type endpoint: Optional[str]
    :param hf_token: The Hugging Face authentication token for private endpoints
    :type hf_token: Optional[str]

    :return: Site information including site identifier and version
    :rtype: HfSiteInfo
    :raises requests.HTTPError: If the API request fails (except for 404 on official hub)

    Example::

        >>> # Query official Hugging Face hub
        >>> info = hf_site_info()
        >>> print(info.site)
        huggingface

        >>> # Query custom deployment
        >>> info = hf_site_info(endpoint='https://my-custom-hub.com')
        >>> print(f"{info.site} v{info.version}")
        my-custom-hub v2.1.0
    """
    r = get_session().post(
        f"{endpoint or ENDPOINT}/api/version",
        headers=build_hf_headers(token=hf_token),
    )
    if r.status_code == 404:
        # this is huggingface official site
        return HfSiteInfo(site='huggingface')
    else:
        hf_raise_for_status(r)
        meta_info = r.json()
        return HfSiteInfo(site=meta_info['site'], version=meta_info['version'])
