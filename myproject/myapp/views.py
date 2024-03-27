from django.views.generic import View
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings  # For accessing settings
from google.oauth2 import service_account
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import os
from datetime import datetime
# myapp/views.py
from channels.layers import get_channel_layer

async def my_async_view(request):
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "your_group",
        {"type": "some_message", "data": "some_data"}
    )
    # ... other view logic

# If you're using class-based views:
from asgiref.sync import async_to_sync 

class MyAsyncView(View):
    async def get(self, request, *args, **kwargs):
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            "your_group",
            {"type": "some_message", "data": "some_data"}
        )

# To handle web requests you'll likely still need a non-async view.
# You can call your async function from within it:
def my_view(request):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
         "your_group",
         {"type": "some_message", "data": "some_data"}
    ) 
    # ... other view logic

def index(request):
    if request.method == 'POST':
        # Handle file upload, Google Sheets writing, etc. (see below)
        return redirect('index')  # Redirect after successful upload
    else:
        context = {}  # Add any context variables if needed
        return render(request, 'myapp/index.html', context) 

def upload_file_to_drive(file, name, mobile):
    credentials_path = os.path.join("KEYS", "sheets_drive_credentials.json")
    credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=['https://www.googleapis.com/auth/drive'])
    drive_service = build('drive', 'v3', credentials=credentials)

    timestamp = datetime.now().strftime('%d%m%y%H%M%S')

    file_metadata = {
        'name': f'{timestamp}',
        'parents': ['1XxGH39acwUjG80nvvn2Lh4NeKX2C5Ehq'],
    }

    media = MediaIoBaseUpload(io.BytesIO(file.read()), mimetype=file.content_type, resumable=True)
    request = drive_service.files().create(body=file_metadata, media_body=media, fields='webViewLink')

    response = None
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                # Emit progress to the client
                socketio.emit('progress', progress)
        except Exception as e:
            print(f"Error during upload: {str(e)}")
            break

    return response.get('webViewLink'), file_metadata['name']

def write_to_google_sheets(name, mobile, image_name, file_url):
    credentials_path = os.path.join("KEYS", "sheets_drive_credentials.json")
    credentials = service_account.Credentials.from_service_account_file(credentials_path, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    sheets_service = build('sheets', 'v4', credentials=credentials)

    spreadsheet_id = '150goQbrvEI_5T5YmSlJ5hLvrvR4yF0BKIZLY1JGA3qI'
    range_ = 'RAW DATA!A:D'

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    values = [[timestamp, image_name, name, mobile, file_url]]

    sheets_service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_,
        body={'values': values},
        valueInputOption='RAW',
    ).execute()
