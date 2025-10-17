from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

import os
import mimetypes

# Google drive setup
SCOPES = ['https://www.googleapis.com/auth/drive']
creds = None

def authenticate_google_drive():
    """Authenticates with the Google Drive API and returns a service object."""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    # It's created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This will open a browser window for you to log in and authorize the app.
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    try:
        service = build('drive', 'v3', credentials=creds)
        print("✅ Google Drive API Authentication Successful!")
        return service
    except HttpError as error:
        print(f"An error occurred during authentication: {error}")
        return None

def upload_folder_to_drive(service, local_folder_path, parent_folder_id=None):
    """Uploads a local folder and its contents to Google Drive."""
    folder_name = os.path.basename(local_folder_path)
    print(f"\nUploading folder '{folder_name}' to Google Drive...")
    
    # 1. Create the folder on Google Drive
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]
        
    try:
        gdrive_folder = service.files().create(body=file_metadata, fields='id').execute()
        gdrive_folder_id = gdrive_folder.get('id')
        print(f"  - Created Google Drive folder with ID: {gdrive_folder_id}")

        # 2. Upload files into the created folder
        for item in os.listdir(local_folder_path):
            item_path = os.path.join(local_folder_path, item)
            if os.path.isfile(item_path):
                # Guess the MIME type of the file
                mimetype, _ = mimetypes.guess_type(item_path)
                file_metadata = {
                    'name': item,
                    'parents': [gdrive_folder_id]
                }
                media = MediaFileUpload(item_path, mimetype=mimetype)
                service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                print(f"    - Uploaded file: {item}")
        
        return gdrive_folder_id
    except HttpError as error:
        print(f"An error occurred uploading the folder: {error}")
        return None

def get_shareable_link(service, folder_id):
    """Makes a folder public and returns its shareable link."""
    try:
        # Create a permission for anyone with the link to view
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        service.permissions().create(fileId=folder_id, body=permission).execute()
        
        # Get the webViewLink from the file's metadata
        result = service.files().get(fileId=folder_id, fields='webViewLink').execute()
        link = result.get('webViewLink')
        print(f"  - Generated shareable link: {link}")
        return link
    except HttpError as error:
        print(f"An error occurred while getting the shareable link: {error}")
        return None

