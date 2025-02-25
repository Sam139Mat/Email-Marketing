import os
import requests
from bs4 import BeautifulSoup
import re
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Email credentials from .env file (Security Fix)
SENDER_EMAIL = os.getenv("EMAIL_ADDRESS")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Google Search API Key (SerpAPI)
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# Apollo.io API Key for Job Title Extraction
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")

def google_search(query, num_results=10):
    """Fetches Google search results using SerpAPI."""
    search_url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "num": num_results,
        "hl": "en",
        "gl": "ke",
        "api_key": SERPAPI_KEY
    }
    response = requests.get(search_url, params=params)
    return response.json() if response.status_code == 200 else None

def get_job_title(email):
    """Fetches job title from Apollo.io API."""
    url = "https://api.apollo.io/v1/people/match"  # Correct endpoint
    headers = {"Content-Type": "application/json", "X-Api-Key": APOLLO_API_KEY}
    payload = {"email": email}
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("person", {}).get("title", " ")  # Handle missing title properly
    
    return " "

def extract_linkedin_profiles(results):
    """Extracts LinkedIn profile links, emails, names, and job titles."""
    extracted_data = []
    for result in results.get("organic_results", []):
        link = result.get("link", "")
        snippet = result.get("snippet", "")
        
        # Extract email from snippet
        email_match = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', snippet)
        email = email_match[0] if email_match else None

        # Extract name (if available in LinkedIn URL)
        name_match = re.search(r'/in/([\w-]+)', link)
        name = name_match.group(1).replace('-', ' ').title() if name_match else " "
        
        # Get job title using Apollo.io
        job_title = get_job_title(email) if email else " "

        if email:
            extracted_data.append((name, email, job_title, link))
    
    return extracted_data

def save_to_csv(data, filename='linkedin_contacts.csv'):
    """Saves extracted contacts to a CSV file."""
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'Email', 'Job Title', 'LinkedIn Profile'])
        writer.writerows(data)

def send_email(recipient_email, recipient_name, job_title, success_emails, failed_emails):
    """Sends a personalized email to each contact."""
    subject = "Revolutionizing Your Marketing"
    body = f"""
    Hi {recipient_name}, 
    {job_title} 
   
    We are a team of passionate Gen Z innovators ready to revolutionize the way you market yourself, your brand, or your organization. 
    In today’s digital world, storytelling is everything, and we specialize in bringing your story to life through:

     Compelling Branding & Storytelling – We craft narratives that truly connect.
     Stunning Websites & Powerful Apps – Designed to captivate and convert.
     Social Media Management – Growing and engaging your audience effortlessly.
    
    We believe you can benefit from our services in building your online presence. Let’s collaborate and take your brand to the next level!
    
    Looking forward to discussing how we can help.
    
    Regards,  
    Digitall Marketing Solutions  
    https://digitallke.net
    """

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        print(f"Email sent to {recipient_name} at {recipient_email}")
        success_emails.append((recipient_name, recipient_email))
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")
        failed_emails.append((recipient_name, recipient_email))

def save_emails_to_txt(success_emails, failed_emails):
    """Save successfully sent and failed emails to .txt files."""
    # Save successful emails
    with open('success_emails.txt', 'w') as success_file:
        for name, email in success_emails:
            success_file.write(f"{name}: {email}\n")

    # Save failed emails
    with open('failed_emails.txt', 'w') as failed_file:
        for name, email in failed_emails:
            failed_file.write(f"{name}: {email}\n")

if __name__ == "__main__":
    search_query = 'site:instagram.com "@gmail.com" OR "@hotmail.com" OR "@outlook.com" OR "@yahoo.com"'
    search_results = google_search(search_query)

    # print("Raw Search Results:", search_results)  # Debugging step

    if search_results:
        linkedin_profiles = extract_linkedin_profiles(search_results)

        print("Extracted LinkedIn Profiles:", linkedin_profiles)  # Debugging step

        save_to_csv(linkedin_profiles)  # Save data to CSV

        # Lists to track success and failure
        success_emails = []
        failed_emails = []

        # Sending emails to extracted contacts
        for name, email, job_title, _ in linkedin_profiles:
            send_email(email, name, job_title, success_emails, failed_emails)

        # After attempting to send emails, display the results
        print("\nEmails sent successfully:")
        for name, email in success_emails:
            print(f"{name}: {email}")

        print("\nEmails that failed to send:")
        for name, email in failed_emails:
            print(f"{name}: {email}")

        # Save the lists to text files
        save_emails_to_txt(success_emails, failed_emails)
