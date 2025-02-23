import re
import requests
from typing import List


class UrlHelper:
    @staticmethod
    def extract(string: str) -> List[str]:
        """
        Used to extract every URLs that are present in the provided string.
        """
        regexp = re.compile(r"(https?://\S+)")
        return regexp.findall(string)

    @staticmethod
    def exists(url: str) -> bool:
        """
        Returns `true` if the provided `url` exists.

        The `url` is considered as existing if a `GET` request leads to
        a status code in the range `200` to `299`.
        """
        try:
            response = requests.get(url, timeout=10)
            return 200 <= response.status_code < 300
        except Exception:
            return False
