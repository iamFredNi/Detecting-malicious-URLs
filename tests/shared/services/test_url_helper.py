from src.shared.services.url_helper import UrlHelper
from unittest import TestCase


class TestUrlHelper(TestCase):
    def test_extract(self):
        data = "some random text"
        assert UrlHelper.extract(data) == []

        data = "http://some-site.com"
        assert UrlHelper.extract(data) == ["http://some-site.com"]

        data = "https://some-other.com"
        assert UrlHelper.extract(data) == ["https://some-other.com"]

        data = "https://site1.com Here's a comment with http://lol.fr multiple links https://hello-world.tk"
        assert UrlHelper.extract(data) == [
            "https://site1.com",
            "http://lol.fr",
            "https://hello-world.tk",
        ]

        data = "http://get-method.net?query=some-data"
        assert UrlHelper.extract(data) == ["http://get-method.net?query=some-data"]

    def test_exists(self):
        url = "https://www.google.com"
        assert UrlHelper.exists(url)

        url = "https://www.n0n-3x1st1ng-we6s1te999.net"
        assert not UrlHelper.exists(url)
