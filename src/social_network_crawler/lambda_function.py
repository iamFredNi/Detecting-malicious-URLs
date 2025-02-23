from typing import List

from src.social_network_crawler.crawler.api_crawler import ApiCrawler
from src.social_network_crawler.crawler.reddit_crawler import RedditCrawler
from src.shared.services.dynamodb_accessor import DynamoDbAccessor


api_crawlers: List[ApiCrawler] = [RedditCrawler()]

db_accessor = DynamoDbAccessor()


def lambda_handler(event, context):
    for crawler in api_crawlers:
        print(f'Fetching data from {crawler}...')
        results = crawler.fetch_links()
        for result in results:
            db_accessor.write(result)

if __name__ == "__main__":
    lambda_handler(0, 0)