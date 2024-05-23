# app.py
import imaplib
import email
from email.header import decode_header
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import smtplib
from email.mime.text import MIMEText

# Email fetching function
def fetch_email():
    # Connect to the server
    mail = imaplib.IMAP4_SSL("imap.your-email-provider.com")
    mail.login("your-email@example.com", "your-password")

    # Select the mailbox you want to check
    mail.select("inbox")

    # Search for all emails
    status, messages = mail.search(None, "ALL")

    # Convert messages to a list of email IDs
    email_ids = messages[0].split()

    # Fetch the latest email
    status, msg_data = mail.fetch(email_ids[-1], "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    # Decode the email subject
    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding)

    # Decode email sender
    from_ = msg.get("From")

    # Extract email body
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = msg.get_payload(decode=True).decode()

    return subject, from_, body

# Web automation function
def spellcheck_text(text):
    # Set up headless browser
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    # Go to ChatGPT login page
    driver.get("https://chat.openai.com/")

    # Assume you are already logged in and the session is stored in cookies
    cookies = {
        # Add your session cookies here
    }

    for cookie in cookies:
        driver.add_cookie(cookie)

    # Go to the ChatGPT interface
    driver.get("https://chat.openai.com/chat")

    # Find the input field and enter the text
    input_field = driver.find_element_by_css_selector("input-selector")
    input_field.send_keys(text)
    input_field.send_keys(Keys.RETURN)

    # Wait for the response and retrieve it
    # Add your logic to wait and fetch the response here

    corrected_text = "Corrected text"  # Replace with actual logic to fetch corrected text

    # Close the browser
    driver.quit()

    return corrected_text

# Email sending function
def send_email(subject, from_, body):
    # Create a text/plain message
    msg = MIMEText(body)
    msg["Subject"] = "Corrected: " + subject
    msg["From"] = "your-email@example.com"
    msg["To"] = from_

    # Send the message via your SMTP server
    server = smtplib.SMTP_SSL("smtp.your-email-provider.com", 465)
    server.login("your-email@example.com", "your-password")
    server.sendmail("your-email@example.com", [from_], msg.as_string())
    server.quit()

if __name__ == "__main__":
    subject, from_, body = fetch_email()
    corrected_body = spellcheck_text(body)
    send_email(subject, from_, corrected_body)
