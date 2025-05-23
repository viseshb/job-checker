import smtplib
import json
import time
import sys
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# === Email Configuration ===
GMAIL_USER = "visesh66@gmail.com"
GMAIL_PASS = "vdovcubqlesknzlo"  # Use Gmail App Password
TO_EMAIL = "visesh66@gmail.com"

# === Job Site URL ===
URL = "https://tamus.wd1.myworkdayjobs.com/en-US/TAMUSA_External?workerSubType=0e1cd8ed350201da3af87057e74b7c04"
JOB_CACHE_FILE = "seen_jobs.json"

# === Send Email ===
def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        print("✅ Email sent successfully!")
    except Exception as e:
        print("❌ Failed to send email:", str(e))

# === Fetch Job Listings with Selenium ===
def fetch_jobs():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(URL)
    time.sleep(5)  # Allow JS to load jobs

    jobs = []
    links = driver.find_elements(By.XPATH, '//a[contains(@href, "/en-US/TAMUSA_External/job/")]')

    for link in links:
        title = link.text.strip()
        href = link.get_attribute("href")
        if title and (title, href) not in jobs:
            jobs.append((title, href))

    driver.quit()
    return jobs

# === Load Previous Jobs from File ===
def load_previous_jobs():
    try:
        with open(JOB_CACHE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# === Save Current Jobs to File ===
def save_jobs(jobs):
    with open(JOB_CACHE_FILE, "w") as f:
        json.dump(jobs, f)

# === Print All Jobs ===
def print_all_jobs():
    jobs = fetch_jobs()
    print(f"📋 Found {len(jobs)} current job(s):\n")
    for i, (title, link) in enumerate(jobs, 1):
        print(f"{i}. {title}\n   {link}\n")

# === Monitor and Alert New Jobs ===
def monitor_jobs():
    current_jobs = fetch_jobs()
    print(f"\n🧾 CURRENT JOB LISTINGS ({len(current_jobs)}):")
    for title, link in current_jobs:
        print(f"- {title}\n  {link}\n")

    current_titles = [title for title, _ in current_jobs]
    seen_titles = load_previous_jobs()

    new_jobs = [(title, link) for title, link in current_jobs if title not in seen_titles]

    if new_jobs:
        print(f"🔔 {len(new_jobs)} new job(s) found!")
        message_body = "\n\n".join(f"{title}\n{link}" for title, link in new_jobs)
        send_email("📢 New Job Posted at TAMUSA!", message_body)
        save_jobs(current_titles)
    else:
        print("No new jobs yet.")

# === Entry Point ===
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--print":
        print_all_jobs()
    else:
        while True:
            monitor_jobs()
            time.sleep(300)  # every 5 minutes
