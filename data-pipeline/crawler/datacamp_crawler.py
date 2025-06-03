import requests
from bs4 import BeautifulSoup
import csv
import time
from urllib.parse import urljoin

# Base URL for the courses page
base_url = "https://www.datacamp.com"
# courses_url = f"https://www.datacamp.com/courses-all/page/1"

# Headers to mimic a browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Function to get course description from course page
def get_course_description(course_url):
    try:
        response = requests.get(course_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the course description section
        description_section = soup.find('div', class_='dc-course__description')
        if description_section:
            # Extract all text within the description section, cleaning up extra whitespace
            description = ' '.join(description_section.get_text(strip=True).split())
            return description
        return "Description not found"
    except requests.RequestException as e:
        print(f"Error fetching description for {course_url}: {e}")
        return "Error retrieving description"

# Function to crawl course data
def crawl_page(page_num):
    courses = []
    page_url = f"https://www.datacamp.com/courses-all/page/{page_num}"
    try:
        # Fetch the main courses page
        response = requests.get(page_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all course cards
        course_cards = soup.find_all('a', class_='ds-snowplow-navigation--all-courses-card')
        
        courses = []
        for card in course_cards:
            # Extract title
            title_elem = card.find('h3', class_='dc-card__title')
            title = title_elem.get_text(strip=True) if title_elem else "Title not found"
            
            # Extract URL
            relative_url = card.get('href', '')
            full_url = urljoin(base_url, relative_url)
            
            # Get detailed description from course page
            description = get_course_description(full_url)
            
            # Append course data
            courses.append({
                'title': title,
                'url': full_url,
                'description': description
            })
            
            # Respectful delay to avoid overwhelming the server
            time.sleep(1)
        
        print(f"Successfully crawled page {page_num}")
        return courses
    
    except requests.RequestException as e:
        print(f"Error fetching page {page_num}: {e}")
        return []
    except Exception as e:
        print(f"An error occurred on page {page_num}: {e}")
        return []

def crawl_courses(start_page, end_page):
    all_courses = []
    # Iterate through pages
    for page in range(start_page, end_page + 1):
        print(f"Crawling page {page}...")
        page_courses = crawl_page(page)
        all_courses.extend(page_courses)
        # Delay between pages
        time.sleep(2)
    
    # Write to CSV
    with open('datacamp_courses.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'url', 'description']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for course in all_courses:
            writer.writerow(course)
    
    print(f"Course data from pages {start_page} to {end_page} has been saved to datacamp_courses.csv")

# Run the crawler
if __name__ == "__main__":
    crawl_courses(1, 20)