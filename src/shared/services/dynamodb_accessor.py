from boto3 import client
from os import environ
from src.shared.models.collected_site import CollectedSite
from typing import List

class DynamoDbAccessor:
    """
    The purpose of this class is to interact easly with AWS DynamoDB.
    """

    def __init__(self):
        self.client = client("dynamodb")
        self.__TABLE_NAME = environ["TABLE_NAME"]

    def read_collected_site(self, id: str) -> CollectedSite:
        """
        Reads the CollectedSite object with the specified id from the database.
        """
        response = self.client.get_item(
            TableName=self.__TABLE_NAME, Key={"id": {"S": id}, "date": {"S": "YYYY-MM-DDThh:mm:ss"}}
        )
        return CollectedSite.from_dynamodb_item(response['Item'])

    def write(self, collected_site: CollectedSite) -> None:
        """
        Creates or updates an item from the provided CollectedSite object in the database.
        """
        self.client.put_item(
            TableName=self.__TABLE_NAME,
            Item=CollectedSite.to_dynamodb_item(collected_site),
        )

    def write_all(self, collected_sites: list[CollectedSite]) -> None:
        """
        Creates or updates multiple items from the provided list of CollectedSite objects in the database
        using a single batch_write_item request.
        """

        items = [
            {
                "PutRequest": {
                    "Item": CollectedSite.to_dynamodb_item(collected_site)
                }
            }
            for collected_site in collected_sites
        ]

        self.client.batch_write_item(
            RequestItems={
                self.__TABLE_NAME : items
            }
        )

    def get_all_collected_sites(self) -> List[CollectedSite]:
        response = self.client.scan(TableName=self.__TABLE_NAME)
        items = response.get('Items', [])

        while 'LastEvaluatedKey' in response:
            response = self.client.scan(
                TableName=self.__TABLE_NAME,
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))

        collected_sites = CollectedSite.from_dynamodb_items(items)

        return collected_sites
    
    def update_collected_site(self, site: CollectedSite) -> None:
        self.update_collected_site_safety(site)
        self.update_collected_site_screenshot(site)

    def update_collected_site_safety(self, site: CollectedSite) -> None:
        if site.is_safe is None:
            return
        self.client.update_item(
            TableName=self.__TABLE_NAME,
            Key={
                'id': { 'S': site.id },
                'date': { 'S': site.date }
            },
            UpdateExpression="SET is_safe = :is_safe",
            ExpressionAttributeValues={
                ':is_safe': {'BOOL': site.is_safe}
            },
        )

    def update_collected_site_screenshot(self, site: CollectedSite) -> None:
        if site.screenshot is None:
            return
        self.client.update_item(
            TableName=self.__TABLE_NAME,
            Key={
                'id': { 'S': site.id },
                'date': { 'S': site.date }
            },
            UpdateExpression="SET screenshot = :screenshot",
            ExpressionAttributeValues={
                ':screenshot': {'S': site.screenshot}
            },
        )

if __name__ == "__main__":
    db = DynamoDbAccessor()
    data = db.get_all_collected_sites()
    print(data)
    print(len(data))