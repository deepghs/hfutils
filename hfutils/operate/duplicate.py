"""
This module provides functionality for duplicating repositories on the Hugging Face Hub.

It includes a function to duplicate a repository, allowing users to create a copy of an existing
repository with a new name and optional privacy settings. This module interacts with the Hugging Face
API to perform the duplication process.

.. note::
    Inspired by `huggingface-projects/repo_duplicator <https://huggingface.co/spaces/huggingface-projects/repo_duplicator/blob/main/app.py>`_
    provided by huggingface official team.
"""

from typing import Optional

from huggingface_hub.constants import ENDPOINT
from huggingface_hub.utils import get_session, build_hf_headers, hf_raise_for_status

from .base import RepoTypeTyping


def hf_repo_duplicate(src_repo_id: str, dst_repo_id: str, repo_type: RepoTypeTyping,
                      private: bool = False, endpoint: Optional[str] = None, hf_token: Optional[str] = None):
    """
    Duplicate a repository on the Hugging Face Hub.

    This function creates a copy of an existing repository with a new name. It allows
    you to specify whether the new repository should be private or public.

    :param src_repo_id: The ID of the source repository to duplicate.
    :type src_repo_id: str
    :param dst_repo_id: The ID for the new (destination) repository.
    :type dst_repo_id: str
    :param repo_type: The type of the repository (e.g., 'model', 'dataset', 'space').
    :type repo_type: RepoTypeTyping
    :param private: Whether the new repository should be private. Defaults to False.
    :type private: bool, optional
    :param endpoint: The API endpoint to use. If None, the default endpoint will be used.
    :type endpoint: str, optional
    :param hf_token: The Hugging Face authentication token. If None, the default token will be used.
    :type hf_token: str, optional

    :return: The JSON response from the API containing information about the duplicated repository.
    :rtype: dict

    :raises: Raises an exception if the API request fails.

    Usage:
        >>> result = hf_repo_duplicate("original-repo", "new-repo", "model", private=True)
        >>> print(result)  # Prints information about the newly created repository
    """
    r = get_session().post(
        f"{endpoint or ENDPOINT}/api/{repo_type}s/{src_repo_id}/duplicate",
        headers=build_hf_headers(token=hf_token),
        json={"repository": dst_repo_id, "private": private},
    )
    hf_raise_for_status(r)
    return r.json()
