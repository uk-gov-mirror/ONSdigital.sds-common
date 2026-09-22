from __future__ import annotations

import json
import logging
from pathlib import Path

import requests

from sds_common.models.schema_publish_errors import FilepathError, SchemaFetchError, SchemaJSONDecodeError
from sds_common.services.http_service import HttpService

logger = logging.getLogger(__name__)


def split_filename(path: str) -> str | None:
    """
    Splits a filename without extension from the path.

    :param path: the path to the file.
    :return: the filename.
    :raises FilepathError: if the filename cannot be split from the path.
    """
    try:
        return Path(path).stem
    except TypeError as error:
        raise FilepathError(path) from error


def decode_json_response(response: requests.Response, filepath: str = 'N/A') -> dict | None:
    """
    Decode the JSON response from a requests.Response object.

    :param response: the response object to decode.
    :param filepath: the schema filepath, used in the error if decoding fails.
    :return: the decoded JSON response.
    :raises SchemaJSONDecodeError: if the response cannot be decoded.
    """
    try:
        return response.json()
    except json.JSONDecodeError as error:
        raise SchemaJSONDecodeError(filepath) from error


def fetch_raw_schema_from_github(path: str, http_service: HttpService, github_schema_url: str) -> dict:
    """
    Fetches the schema from the ONSdigital GitHub repository.

    :param path: the path to the schema JSON.
    :return dict: the schema JSON.
    :raises SchemaFetchError: if the schema cannot be fetched.
    """
    url = github_schema_url + path
    logger.info('Fetching schema from %s', url)
    response = http_service.make_get_request(url)

    if response.status_code != 200:
        raise SchemaFetchError(path, response.status_code, url)
    schema = decode_json_response(response, filepath=path)
    return schema
