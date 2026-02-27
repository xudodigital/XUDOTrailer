import os
import json
import requests
from google.oauth2 import service_account
import google.auth.transport.requests

# File name where we will store the list of new URLs daily
URL_FILE = "new_urls.txt"

def get_access_token():
    json_creds = os.environ.get("GOOGLE_INDEXING_JSON")
    if not json_creds:
        print("❌ GOOGLE_INDEXING_JSON key not found in environment variables/GitHub Secrets!")
        return None
    
    # Convert the JSON text back into a machine-readable format
    creds_dict = json.loads(json_creds)
    scopes = ["https://www.googleapis.com/auth/indexing"]
    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
    
    request = google.auth.transport.requests.Request()
    creds.refresh(request)
    return creds.token

def notify_google(token, url):
    endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "url": url,
        "type": "URL_UPDATED"
    }
    response = requests.post(endpoint, json=data, headers=headers)
    if response.status_code == 200:
        print(f"✅ Indexing Success: {url}")
    else:
        print(f"❌ Failed ({response.status_code}): {url}")
        print(response.json())

if __name__ == "__main__":
    print("🤖 Starting Google Instant Indexing process...")
    
    if not os.path.exists(URL_FILE):
        print(f"ℹ️ {URL_FILE} not found today. Skipping indexing process.")
        exit()

    # Read the list of URLs from the text file
    with open(URL_FILE, "r") as f:
        urls = [line.strip() for line in f.readlines() if line.strip()]

    if not urls:
        print("ℹ️ new_urls.txt is empty. Nothing to index.")
        exit()

    # Limit to a maximum of 200 URLs per day to avoid hitting Google's quota
    urls_to_index = urls[:200]
    print(f"🚀 Found {len(urls_to_index)} new URLs. Contacting Google...")
    
    token = get_access_token()
    if token:
        for url in urls_to_index:
            notify_google(token, url)
        
        # Clean up the file after successful submission, so it won't be resent tomorrow
        os.remove(URL_FILE)
        print("🗑️ new_urls.txt has been cleaned up for tomorrow's task.")
