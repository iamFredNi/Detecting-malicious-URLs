from typing import List

from src.shared.models.collected_site import CollectedSite


class ApiCrawler:
    """
    This class represents an interface to be implemented in any API crawler.
    """

    def __init__(self, source_name: str):
        self.source_name = source_name

    def fetch_links(self) -> List[CollectedSite]:
        """
        This method uses the API of the social network to fetch links from contents,
        using one API call.
        """
        pass
