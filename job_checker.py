import smtplib
import json
import time
import sys
import logging
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# === Configuration ===
GMAIL_USER = "visesh66@gmail.com"
GMAIL_PASS = "add your password"  # Gmail App Password
TO_EMAIL = "visesh66@gmail.com"
URL = "https://tamus.wd1.myworkdayjobs.com/en-US/TAMUSA_External?workerSubType=0e1cd8ed350201da3af87057e74b7c04"
JOB_CACHE_FILE = "seen_jobs.json"

# === Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# === Email Alert ===
def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        logging.info("✅ Email sent successfully!")
    except Exception as e:
        logging.error("❌ Failed to send email: %s", str(e))

# === Job Scraper ===
def fetch_jobs():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(URL)
    time.sleep(5)

    jobs = []
    links = driver.find_elements(By.XPATH, '//a[contains(@href, "/en-US/TAMUSA_External/job/")]')

    for link in links:
        title = link.text.strip()
        href = link.get_attribute("href")  # ✅ correct method
        if title and href and (title, href) not in jobs:
            jobs.append((title, href))

    driver.quit()
    return jobs

# === Persistence ===
def load_previous_jobs():
    try:
        with open(JOB_CACHE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_jobs(jobs):
    with open(JOB_CACHE_FILE, "w") as f:
        json.dump([{"title": title, "url": url} for title, url in jobs], f)

# === Manual View Mode ===
def print_all_jobs():
    jobs = fetch_jobs()
    for i, (title, link) in enumerate(jobs, 1):
        print(f"{i}. {title}\n   {link}\n")

# === Monitoring + Notification ===
def monitor_jobs():
    logging.info("�� Checking for jobs...")
    current_jobs = fetch_jobs()

    seen = load_previous_jobs()
    seen_titles = {job["title"] for job in seen}  # ✅ fixed

    new_jobs = [(title, link) for title, link in current_jobs if title not in seen_titles]

    if new_jobs:
        logging.info("🔔 %d new job(s) found!", len(new_jobs))
        body = "\n\n".join(f"{title}\n{link}" for title, link in new_jobs)
        send_email("📢 New TAMUSA Job(s) Posted", body)
        save_jobs(current_jobs)  # ✅ store new state
    else:
        logging.info("No new jobs.")

# === Entry Point ===
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--print":
        print_all_jobs()
    else:
        logging.info("🚀 Job Checker Service started.")
        try:
            while True:
                monitor_jobs()
                time.sleep(300)  # every 5 minutes
        except KeyboardInterrupt:
            logging.info("🛑 Job Checker stopped by user.")
        except Exception as e:
            logging.exception("❌ Uncaught error occurred:")
