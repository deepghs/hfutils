"""
This module provides functionality to retrieve information about Hugging Face sites and their versions.

It contains utilities to identify whether a site is the official Hugging Face hub, a Hugging Face
enterprise deployment, or a custom self-hosted deployment that maintains API compatibility with
Hugging Face. The module distinguishes between:

- Official Hugging Face (huggingface.co): The main public hub
- Hugging Face Enterprise: Custom deployments supported by Hugging Face but not the official site
- Self-hosted compatible projects: Open source projects that implement HF-compatible APIs

The identification mechanism works by checking the /api/version endpoint. Official huggingface.co
returns 404 for this endpoint, while enterprise and self-hosted deployments return site metadata.
"""

from dataclasses import dataclass
from typing import Optional

from huggingface_hub.constants import ENDPOINT
from huggingface_hub.utils import get_session, build_hf_headers, hf_raise_for_status
from urlobject import URLObject


@dataclass
class HfSiteInfo:
    """
    Data class containing information about a Hugging Face site.

    This class holds metadata about a Hugging Face deployment, including
    the site identifier and version information. It can represent:

    - Official Hugging Face hub (site='huggingface', version='official')
    - Hugging Face enterprise deployments (site='huggingface', version='custom')
    - Self-hosted compatible projects (site=custom_name, version=custom_version)

    :param site: The site identifier (e.g., 'huggingface' for official hub or enterprise)
    :type site: str
    :param version: The version of the site deployment ('official', 'custom', or specific version)
    :type version: str

    Example::

        >>> # Official Hugging Face hub
        >>> site_info = HfSiteInfo(site='huggingface', version='official')
        >>> print(f"{site_info.site} ({site_info.version})")
        huggingface (official)

        >>> # Self-hosted project
        >>> site_info = HfSiteInfo(site='custom-hub', version='1.2.3')
        >>> print(f"{site_info.site} v{site_info.version}")
        custom-hub v1.2.3
    """
    site: str
    version: str


def hf_site_info(endpoint: Optional[str] = None, hf_token: Optional[str] = None) -> HfSiteInfo:
    """
    Retrieve information about a Hugging Face site deployment.

    This function queries the /api/version endpoint to determine the type of deployment:

    1. Official Hugging Face (huggingface.co): Returns 404 for /api/version, identified as 'official'
    2. Hugging Face Enterprise: Returns site metadata with site='huggingface' but version='custom'
    3. Self-hosted compatible projects: Returns custom site name and version information

    The identification mechanism relies on the fact that the official huggingface.co does not
    expose a /api/version endpoint (returns 404), while enterprise deployments and self-hosted
    projects that maintain API compatibility do provide this endpoint with site metadata.

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
        >>> print(f"{info.site} ({info.version})")
        huggingface (official)

        >>> # Query Hugging Face enterprise deployment
        >>> info = hf_site_info(endpoint='https://company.huggingface.co')
        >>> print(f"{info.site} ({info.version})")
        huggingface (custom)

        >>> # Query self-hosted compatible project
        >>> info = hf_site_info(endpoint='https://my-custom-hub.com')
        >>> print(f"{info.site} v{info.version}")
        my-custom-hub v2.1.0
    """
    endpoint = endpoint or ENDPOINT
    is_huggingface_official = URLObject(endpoint).hostname == 'huggingface.co'
    r = get_session().post(
        f"{endpoint or ENDPOINT}/api/version",
        headers=build_hf_headers(token=hf_token),
    )
    if r.status_code == 404:
        # this is huggingface official site
        return HfSiteInfo(site='huggingface', version='official' if is_huggingface_official else 'custom')
    else:
        hf_raise_for_status(r)
        meta_info = r.json()
        return HfSiteInfo(site=meta_info['site'], version=meta_info['version'])
