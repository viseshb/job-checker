import json
import time
import smtplib
from email.mime.text import MIMEText
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import os

# === Config from Render Environment Variables ===
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_PASS = os.environ["GMAIL_PASS"]
TO_EMAIL = os.environ["TO_EMAIL"]

URL = "https://tamus.wd1.myworkdayjobs.com/en-US/TAMUSA_External?workerSubType=0e1cd8ed350201da3af87057e74b7c04"
JOB_CACHE_FILE = "seen_jobs.json"

# === Send Gmail ===
def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        print("✅ Email sent!")
    except Exception as e:
        print("❌ Email failed:", str(e))

# === Scrape jobs using headless Chrome ===
def fetch_jobs():
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    driver = uc.Chrome(options=options)
    driver.get(URL)
    time.sleep(5)

    jobs = []
    links = driver.find_elements(By.XPATH, '//a[contains(@href, "/en-US/TAMUSA_External/job/")]')
    for link in links:
        title = link.text.strip()
        href = link.get_attribute("href")
        if title and (title, href) not in jobs:
            jobs.append((title, href))

    driver.quit()
    return jobs

# === Load/save jobs ===
def load_previous_jobs():
    try:
        with open(JOB_CACHE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_jobs(jobs):
    with open(JOB_CACHE_FILE, "w") as f:
        json.dump(jobs, f)

# === Main monitor ===
def monitor_jobs():
    current_jobs = fetch_jobs()
    print(f"🧾 Found {len(current_jobs)} jobs")

    current_titles = [title for title, _ in current_jobs]
    seen_titles = load_previous_jobs()

    new_jobs = [(title, link) for title, link in current_jobs if title not in seen_titles]

    if new_jobs:
        print(f"🔔 New jobs found: {len(new_jobs)}")
        message = "\n\n".join(f"{title}\n{link}" for title, link in new_jobs)
        send_email("📢 New TAMUSA Job Posted", message)
        save_jobs(current_titles)
    else:
        print("No new jobs.")

if __name__ == "__main__":
    while True:
        monitor_jobs()
        time.sleep(300)  # every 5 minutes
