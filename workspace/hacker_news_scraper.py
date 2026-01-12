import requests
import requests
from bs4 import BeautifulSoup
import csv

# Function to scrape Hacker News

def scrape_hacker_news():
    url = 'https://news.ycombinator.com/'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
    except requests.exceptions.RequestException as e:
        print(f'Error fetching data from Hacker News: {e}')
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = []

    for item in soup.select('.athing')[:10]:  # Get top 10 posts
        title = item.select_one('.storylink').get_text()
        link = item.select_one('.storylink')['href']
        points = item.find_next_sibling('tr').select_one('.score')
        points = int(points.get_text().split()[0]) if points else 0
        posts.append({'title': title, 'url': link, 'points': points})

    return posts

# Function to save posts to CSV

def save_to_csv(posts, filename='hacker_news_top_posts.csv'):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['title', 'url', 'points'])
        writer.writeheader()
        writer.writerows(posts)

# Main function to execute the scraper

def main():
    posts = scrape_hacker_news()
    if posts:
        save_to_csv(posts)
        print(f'Successfully saved {len(posts)} posts to CSV.')
    else:
        print('No posts to save.')

if __name__ == '__main__':
    main()
import requests
from bs4 import BeautifulSoup
import csv

# Function to scrape Hacker News

def scrape_hacker_news():
    url = 'https://news.ycombinator.com/'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
    except requests.exceptions.RequestException as e:
        print(f'Error fetching data from Hacker News: {e}')
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = []

    for item in soup.select('.athing')[:10]:  # Get top 10 posts
        title = item.select_one('.storylink').get_text()
        link = item.select_one('.storylink')['href']
        points = item.find_next_sibling('tr').select_one('.score')
        points = int(points.get_text().split()[0]) if points else 0
        posts.append({'title': title, 'url': link, 'points': points})

    return posts

# Function to save posts to CSV

def save_to_csv(posts, filename='hacker_news_top_posts.csv'):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['title', 'url', 'points'])
        writer.writeheader()
        writer.writerows(posts)

# Main function to execute the scraper

def main():
    posts = scrape_hacker_news()
    if posts:
        save_to_csv(posts)
        print(f'Successfully saved {len(posts)} posts to CSV.')
    else:
        print('No posts to save.')

if __name__ == '__main__':
    main()
"""
"""
This script scrapes the top 10 posts from Hacker News, extracting titles, URLs, and points.
It handles network errors and invalid HTML gracefully and saves the results to a CSV file.
"""

This script scrapes the top 10 posts from Hacker News, extracting titles, URLs, and points.
It handles network errors and invalid HTML gracefully and saves the results to a CSV file.
"""

from bs4 import BeautifulSoup
import csv

"""
This script scrapes the top 10 posts from Hacker News, extracting titles, URLs, and points.
It handles network errors and invalid HTML gracefully and saves the results to a CSV file.
"""

def scrape_hacker_news():
    url = 'https://news.ycombinator.com/'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
    except requests.exceptions.RequestException as e:
        print(f'Network error: {e}')
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    posts = []

    for item in soup.select('.athing')[:10]:  # Get top 10 posts
        title = item.select_one('.storylink').get_text()
        link = item.select_one('.storylink')['href']
        points = item.find_next_sibling('tr').select_one('.score')
        points = int(points.get_text().split()[0]) if points else 0
        posts.append({'title': title, 'link': link, 'points': points})

    return posts


def save_to_csv(posts, filename='hacker_news_top_posts.csv'):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['title', 'link', 'points'])
        writer.writeheader()
        writer.writerows(posts)


def main():
    posts = scrape_hacker_news()
    if posts:
        save_to_csv(posts)
        print(f'Successfully saved {len(posts)} posts to CSV.')
    else:
        print('No posts to save.')


if __name__ == '__main__':
    main()