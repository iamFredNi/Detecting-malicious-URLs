import os
from moto import mock_aws
from boto3 import client
from unittest import TestCase
from src.shared.models.collected_site import CollectedSite, SourceType
from src.shared.services.dynamodb_accessor import (
    DynamoDbAccessor,
)  # Assure-toi que le chemin est correct


@mock_aws
class TestDynamoDBAccessor(TestCase):
    def setUp(self):
        self.db = client("dynamodb")
        self.db.create_table(
            TableName=os.environ["TABLE_NAME"],
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
                {"AttributeName": "date", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},
                {"AttributeName": "date", "KeyType": "RANGE"},
            ],
        )

    def test_write_collected_site(self):
        accessor = DynamoDbAccessor()
        collected_site = CollectedSite(
            id="123",
            date="YYYY-MM-DDThh:mm:ss",
            source=SourceType.API,
            source_name="reddit",
            url="http://example.com",
            screenshot=None,
            is_safe=None,
        )

        accessor.write(collected_site)

    def test_read_collected_site(self):
        accessor = DynamoDbAccessor()

        collected_site = CollectedSite(
            id="123",
            date="YYYY-MM-DDThh:mm:ss",
            source=SourceType.API,
            source_name="reddit",
            url="http://example.com",
            screenshot=None,
            is_safe=None,
        )
        accessor.write(collected_site)


        result = accessor.read_collected_site("123")

        assert collected_site == result
