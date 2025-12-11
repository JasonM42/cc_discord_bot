import os.path

from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SERVICE_ACCOUNT_FILE = "google-service-credentials.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]
FILE_ID = "1xVfyq3cHMN65bWkSEddWLdiokEuvPppH"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, 'data', 'grdn_data.pkl')


def download_pickle():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive"]
    )

    service = build("drive", "v3", credentials=creds)

    request = service.files().get_media(fileId=FILE_ID)
    fh = open(OUTPUT_PATH, "wb")

    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    fh.close()
    print("Downloaded:", OUTPUT_PATH)


def upload_pickle():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive"]
    )

    service = build("drive", "v3", credentials=creds)
    print("Uploading: ", OUTPUT_PATH)
    if os.path.exists(OUTPUT_PATH):
        print("Path exists")
        print("Size: ", os.path.getsize(OUTPUT_PATH))
        media = MediaFileUpload(OUTPUT_PATH, mimetype="application/octet-stream")

    updated = service.files().update(
        fileId=FILE_ID,
        media_body=media
    ).execute()

    print("Updated remote file:", updated["id"])
