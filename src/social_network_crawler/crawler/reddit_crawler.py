from praw import Reddit  # type: ignore
from typing import List

from src.social_network_crawler.crawler.api_crawler import ApiCrawler
from src.shared.models.collected_site import CollectedSite, SourceType
from src.shared.services.url_helper import UrlHelper
from src.shared.services.secret_manager_accessor import SecretManagerAccessor


class RedditCrawler(ApiCrawler):
    """
    This class is used to crawl Reddit content.
    """

    def __init__(self):
        super().__init__("reddit")
        self.__fetch_secrets()
        self.__client = self.__get_reddit_client()

    def __fetch_secrets(self) -> None:
        self.__REDDIT_APP_ID, self.__REDDIT_APP_SECRET = (
            SecretManagerAccessor.get_reddit_api_secrets()
        )

    def __get_reddit_client(self) -> Reddit:
        """
        Private function used to load a token to access the API.
        """
        return Reddit(
            client_id=self.__REDDIT_APP_ID,
            client_secret=self.__REDDIT_APP_SECRET,
            user_agent="phishing_detector by python script.",
        )

    def fetch_links(self) -> List[CollectedSite]:
        thread = self.__client.subreddit("all")
        urls = self.__fetch_urls_from_submissions(thread)
        print(f'found {urls} from reddit!')
        urls = self.__remove_duplicates(urls)
        urls = self.__remove_non_existent_urls(urls)

        return CollectedSite.from_urls(
            urls, SourceType.API, source_name=self.source_name
        )

    def __fetch_urls_from_submissions(self, thread) -> List[str]:
        collected = []
        for submission in thread.new(limit=100):
            collected += UrlHelper.extract(submission.selftext)
            collected += self.__fetch_urls_from_submission_comments(submission)

        return collected

    def __fetch_urls_from_submission_comments(self, submission) -> List[str]:
        collected = []
        submission.comments.replace_more(limit=None)
        for comment in submission.comments.list():
            collected += UrlHelper.extract(comment.body)

        return collected

    def __remove_duplicates(self, urls) -> List[str]:
        return list(dict.fromkeys(urls))

    def __remove_non_existent_urls(self, urls) -> List[str]:
        for url in urls:
            if not UrlHelper.exists(url):
                urls.remove(url)
        return urls
