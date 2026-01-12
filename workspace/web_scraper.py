import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from urllib.parse import urlparse

class WebScraper:
    def __init__(self, url):
        self.url = url
        self.validate_url()

    def validate_url(self):
        # Validate the URL format using urlparse
        parsed_url = urlparse(self.url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise ValueError('Invalid URL format')

    def fetch_title(self):
        try:
            response = requests.get(self.url, timeout=5)
            response.raise_for_status()  # Raise an error for bad responses
            # Extract title from HTML
            start = response.text.find('<title>') + len('<title>')
            end = response.text.find('</title>', start)
            title = response.text[start:end]
            if not title:
                return 'Title not found'
            return title.strip()  # Return the title without leading/trailing whitespace
        except Timeout:
            return 'Request timed out'
        except ConnectionError:
            return 'Connection error occurred'
        except RequestException as e:
            return f'Error fetching title: {e}'
        except Exception as e:
            return f'An unexpected error occurred: {e}'

# Unit tests
if __name__ == '__main__':
    scraper = WebScraper('https://example.com')
    print(scraper.fetch_title())

    # Basic unit tests
    def test_fetch_title():
        test_scraper = WebScraper('https://example.com')
        assert test_scraper.fetch_title() == 'Example Domain', 'Test failed: Title does not match'

    test_fetch_title()  # Run the test
    print('All tests passed!')