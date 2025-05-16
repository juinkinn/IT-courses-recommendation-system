from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import csv
from tqdm import tqdm
import urllib.parse

# Base URL
base_url = "https://www.edx.org/search?subject=Computer+Science&tab=course&page={}"

# Set up Selenium WebDriver
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no browser window)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
    
    service = Service()  
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Function to crawl a single page
def crawl_page(page_num, csv_writer, output_file, driver):
    url = base_url.format(page_num)
    print(f"\nCrawling page {page_num}: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)  
    except Exception as e:
        print(f"Failed to load page {page_num}: {e}")
        return False

    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Find the div with class="overflow-x-auto"
    course_container = soup.find('div', class_='overflow-x-auto')
    if not course_container:
        print(f"No course container found on page {page_num}. Stopping.")
        return False

    # Find all course items (assuming each course is in an <a> tag with href)
    course_links = course_container.find_all('a', href=True)
    if not course_links:
        print(f"No courses found on page {page_num}. Stopping.")
        return False

    # Initialize progress bar
    print(f"Found {len(course_links)} courses on page {page_num}")
    progress_bar = tqdm(course_links, desc=f"Page {page_num} Progress", unit="course")

    # Process each course
    for course in progress_bar:
        # Get course name from <span>
        course_name_tag = course.find('span')
        course_name = course_name_tag.get_text(strip=True) if course_name_tag else "Unknown Course"
        progress_bar.set_postfix({"Course": course_name[:30] + "..." if len(course_name) > 30 else course_name})
        
        # Get the course URL
        course_url = course['href']
        if not course_url.startswith('http'):
            course_url = urllib.parse.urljoin("https://www.edx.org", course_url)

        # Crawl the course details page
        course_description = crawl_course_details(course_url, driver)
        
        # Combine paragraphs
        description_text = " | ".join(course_description)
        
        # Print data to console
        print(f"\nCourse: {course_name}")
        print("About this course:")
        for paragraph in course_description:
            print(f"- {paragraph}")
        print("-" * 50)

        # Write to CSV
        csv_writer.writerow([course_name, description_text])

        # Short delay to avoid overwhelming the server
        time.sleep(1)

    progress_bar.close()
    return True

# Function to crawl course details page
def crawl_course_details(course_url, driver):
    try:
        driver.get(course_url)
        time.sleep(3)  # Wait for page to load
    except Exception as e:
        print(f"Failed to load course page {course_url}: {e}")
        return ["Error: Could not retrieve course description"]

    # Parse the course page
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Find the div with class="mx-auto bg-inherit max-w-full"
    about_section = soup.find('div', class_='mx-auto bg-inherit max-w-full')
    if not about_section:
        print(f"No 'About this course' section found for {course_url}")
        return ["No description available"]

    # Extract all <p> tags
    paragraphs = about_section.find_all('p')
    if not paragraphs:
        print(f"No <p> tags found in 'About this course' section for {course_url}")
        return ["No description available"]

    return [p.get_text(strip=True) for p in paragraphs]

# Main function
def main():
    output_file = "edx_courses.csv"
    page_num = 1
    max_pages = 42  

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(["Course Name", "About This Course"])

    driver = setup_driver()
    try:
        # Crawl pages
        while page_num <= max_pages:
            with open(output_file, 'a', encoding='utf-8', newline='') as f:
                csv_writer = csv.writer(f)
                success = crawl_page(page_num, csv_writer, output_file, driver)
            if not success:
                print(f"Finished crawling after page {page_num}")
                break
            page_num += 1
            time.sleep(2)
    finally:
        driver.quit()

    print(f"\nCrawling complete. Results saved to {output_file}")

if __name__ == "__main__":
    main()