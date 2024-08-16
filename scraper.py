from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import csv
import concurrent.futures

# Function to initialize WebDriver
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("########REDACTED########")
    return driver

# Function to search and collect emails
def search_and_collect_emails(query, driver):
    email_entries = []
    
    try:

        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "name"))
        )
        
        search_box.clear()
        search_box.send_keys(query + Keys.RETURN)
        
        # Wait for results table to load and collect email entries
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//tbody/tr"))
        )
        
        rows = driver.find_elements(By.XPATH, "//tbody/tr")
        
        for row in rows:
            name = row.find_element(By.XPATH, ".//td[1]").text
            email = row.find_element(By.XPATH, ".//td[5]/a").text
            if email:
                email_entries.append([name, email])
    
    except TimeoutException:
        print(f"Timeout occurred for query: {query}. Skipping to the next.")
    
    return email_entries

# Function to handle processing of letter combinations with autosave and percent done
def process_letter_combinations(letters, total_combinations, start_combination=0):
    driver = init_driver()
    collected_emails = []
    count = 0
    
    for i, letter1 in enumerate(letters[0]):
        for j, letter2 in enumerate(letters[1]):
            for k, letter3 in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
                query = f"{letter1}{letter2}{letter3}"
                collected_emails.extend(search_and_collect_emails(query, driver))
                count += 1
                
                # Periodic autosave every 100 runs
                if count % 100 == 0:
                    with open("email_list_autosave.csv", "a", newline="") as file:
                        writer = csv.writer(file)
                        writer.writerows(collected_emails)
                    collected_emails = []  # Clear the list after saving

                percent_done = ((start_combination + count) / total_combinations) * 100
                print(f"Progress: {percent_done:.2f}%")
    
    driver.quit()
    
    return collected_emails

# Calculate the total number of combinations
total_combinations = 26 * 26 * 26 

# Split alphabet into two halves for parallel processing
first_half = ("ABCDEFGHIJKLM", "NOPQRSTUVWXYZ")
second_half = ("NOPQRSTUVWXYZ", "ABCDEFGHIJKLM")

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    futures = [
        executor.submit(process_letter_combinations, first_half, total_combinations, start_combination=0),
        executor.submit(process_letter_combinations, second_half, total_combinations, start_combination=total_combinations//2)
    ]
    
    all_emails = []
    for future in concurrent.futures.as_completed(futures):
        all_emails.extend(future.result())

# save to the CSV file
with open("email_list.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Name", "Email"])
    writer.writerows(all_emails)

