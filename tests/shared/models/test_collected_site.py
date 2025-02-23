import re
import pytest
from typing import List
from unittest import TestCase

from src.shared.models.collected_site import CollectedSite, SourceType


class TestCollectedSite(TestCase):
    def test_source_type_from_str(self):
        assert CollectedSite.source_type_from_string("API") == SourceType.API
        assert CollectedSite.source_type_from_string("CRAWLER") == SourceType.CRAWLER
        assert CollectedSite.source_type_from_string("HONEY_POT") == SourceType.HONEY_POT
        assert CollectedSite.source_type_from_string("MAIL") == SourceType.MAIL
        with pytest.raises(Exception):
            assert CollectedSite.source_type_from_string("other")

    def test_from_urls_without_source_name(self):
        urls_list = ["https://example.com", "http://test.com"]
        uuid_regexp = (
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        )
        date_regexp = r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])T([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$"

        collected_sites: List[CollectedSite] = CollectedSite.from_urls(
            urls_list, SourceType.MAIL
        )

        assert len(collected_sites) == len(urls_list)
        site1: CollectedSite = collected_sites[0]
        site2: CollectedSite = collected_sites[1]

        assert re.match(uuid_regexp, str(site1.id)) and re.match(
            uuid_regexp, str(site2.id)
        )
        assert re.match(date_regexp, site1.date) and re.match(date_regexp, site2.date)
        assert site1.source == SourceType.MAIL and site2.source == SourceType.MAIL
        assert site1.source_name is None and site2.source_name is None
        assert site1.url == "https://example.com" and site2.url == "http://test.com"
        assert site1.screenshot is None and site2.screenshot is None
        assert site1.is_safe is None and site2.is_safe is None

    def test_from_urls_with_source_name(self):
        urls_list = ["https://other.org"]
        collected_sites: List[CollectedSite] = CollectedSite.from_urls(
            urls_list, SourceType.HONEY_POT, "some_source"
        )
        uuid_regexp = (
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
        )
        date_regexp = r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])T([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$"

        assert len(collected_sites) == len(urls_list)
        site1: CollectedSite = collected_sites[0]

        assert re.match(uuid_regexp, str(site1.id))
        assert re.match(date_regexp, site1.date)
        assert site1.source == SourceType.HONEY_POT
        assert site1.source_name == "some_source"
        assert site1.url == "https://other.org"
        assert site1.screenshot is None
        assert site1.is_safe is None

    def test_to_dynamo_db_item_complete(self):
        collected_site = CollectedSite(
            "123",
            "YYYY-MM-DDThh:mm:ss",
            SourceType.API,
            "some_source",
            "http://website.com",
            "http://screnshot.png",
            False,
        )

        db_item = CollectedSite.to_dynamodb_item(collected_site)

        assert db_item == {
            "id": {"S": "123"},
            "date": {"S": "YYYY-MM-DDThh:mm:ss"},
            "source": {"S": "API"},
            "source_name": {"S": "some_source"},
            "url": {"S": "http://website.com"},
            "screenshot": {"S": "http://screnshot.png"},
            "is_safe": {"BOOL": False},
        }

    def test_to_dynamo_db_item_with_none(self):
        collected_site = CollectedSite(
            "456",
            "YYYY-MM-DDThh:mm:ss",
            SourceType.CRAWLER,
            None,
            "http://somewhere.com",
            None,
            None,
        )

        db_item = CollectedSite.to_dynamodb_item(collected_site)

        assert db_item == {
            "id": {"S": "456"},
            "date": {"S": "YYYY-MM-DDThh:mm:ss"},
            "source": {"S": "CRAWLER"},
            "url": {"S": "http://somewhere.com"},
        }

    def test_from_dynamodb_item(self):
        data = {
            "id": {"S": "456"},
            "date": {"S": "YYYY-MM-DDThh:mm:ss"},
            "source": {"S": "CRAWLER"},
            "url": {"S": "http://somewhere.com"},
        }

        expected = CollectedSite(
            "456",
            "YYYY-MM-DDThh:mm:ss",
            SourceType.CRAWLER,
            None,
            "http://somewhere.com",
            None,
            None
        )

        res = CollectedSite.from_dynamodb_item(data)

        assert res == expected

        data = {
            "id": {"S": "789"},
            "date": {"S": "YYYY-MM-DDThh:mm:ss"},
            "source": {"S": "API"},
            "source_name": {"S": "reddit"},
            "url": {"S": "https://other.com"},
            "screenshot": {"S": "https://somefile.png"},
            "is_safe": {"BOOL": True}
        }

        expected = CollectedSite(
            "789",
            "YYYY-MM-DDThh:mm:ss",
            SourceType.API,
            "reddit",
            "https://other.com",
            "https://somefile.png",
            True
        )

        res = CollectedSite.from_dynamodb_item(data)

        assert res == expected