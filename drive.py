from __future__ import print_function
import requests
import time
import datetime
from googleapiclient.discovery import build
import dynamo
import google.oauth2.credentials
from google.oauth2.credentials import Credentials
import quickstart as api
goog_url = 'https://www.googleapis.com/oauth2/v4/token'

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive.metadata.readonly']


def main(user_id):
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = dynamo.query_google_token(user_id)
    print(creds)
    expires = creds['google_expires_at']
    # If there are no (valid) credentials available, let the user log in.
    if creds['google_expires_at'] < time.time():
        res = requests.post(
            url=goog_url,
            data={
                'client_id': '882547647274-nfh6efs7c3q69r67fhtjkonm8o4b15ia.apps.googleusercontent.com',
                'client_secret': 'Rm4v_Gt1yTe9ZSpD5AX1VONS',
                'grant_type': 'refresh_token',
                'refresh_token': creds['google_refresh_token'],
                'access_type': 'offline',
                'prompt': 'consent'
            }
        )
        creds['google_access_token'] = res.json()['access_token']
        expires = datetime.datetime.fromtimestamp(time.time() + res.json()['expires_in'])
        dynamo.update_user_with_google_info(user_id, creds)

    creds['token_uri'] = "https://oauth2.googleapis.com/token"
    creds['client_id'] = '882547647274-nfh6efs7c3q69r67fhtjkonm8o4b15ia.apps.googleusercontent.com'
    creds['client_secret'] = 'Rm4v_Gt1yTe9ZSpD5AX1VONS'
    creds['scopes'] = SCOPES
    credentials = google.oauth2.credentials.Credentials(token=creds['google_access_token'],
                                                        refresh_token=creds['google_refresh_token'],
                                                        token_uri=creds['token_uri'],
                                                        client_id=creds['client_id'],
                                                        client_secret=creds['client_secret'],
                                                        scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)
    creds['expires_at'] = expires

    # Store credentials in DB again
    dynamo.update_user_with_google_info(user_id, creds)

    # Call the Drive v3 API
    results = service.files().list(
        q="mimeType='application/vnd.google-apps.spreadsheet'",
        pageSize=15, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        files = []
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))
            files.append([item['name'], item['id']])
    return files


def create_log(user_id):
    SPREADSHEET_ID = '1AQkyIl87SFQ2ItJIBuBBH-npsmR9fPHcuBPngLvQ_Lk'
    creds = dynamo.query_google_token(user_id)
    expires = creds['google_expires_at']
    # If there are no (valid) credentials available, let the user log in.
    if creds['google_expires_at'] < time.time():
        res = requests.post(
            url=goog_url,
            data={
                'client_id': '882547647274-nfh6efs7c3q69r67fhtjkonm8o4b15ia.apps.googleusercontent.com',
                'client_secret': 'Rm4v_Gt1yTe9ZSpD5AX1VONS',
                'grant_type': 'refresh_token',
                'refresh_token': creds['google_refresh_token'],
                'access_type': 'offline',
                'prompt': 'consent'
            }
        )
        creds['google_access_token'] = res.json()['access_token']
        expires = time.time() + res.json()['expires_in']
        dynamo.update_user_with_google_info(user_id, creds)

    creds['token_uri'] = "https://oauth2.googleapis.com/token"
    creds['client_id'] = '882547647274-nfh6efs7c3q69r67fhtjkonm8o4b15ia.apps.googleusercontent.com'
    creds['client_secret'] = 'Rm4v_Gt1yTe9ZSpD5AX1VONS'
    creds['scopes'] = SCOPES
    credentials = google.oauth2.credentials.Credentials(token=creds['google_access_token'],
                                                        refresh_token=creds['google_refresh_token'],
                                                        token_uri=creds['token_uri'],
                                                        client_id=creds['client_id'],
                                                        client_secret=creds['client_secret'],
                                                        scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    creds['expires_at'] = expires
    spreadsheet = {
        'properties': {
            'title': '2021/2022 Training Log',
            'locale': 'en_GB'
        }
    }
    request = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
    newSheetId = request.get('spreadsheetId')
    sheet_metadata = service.spreadsheets().get(spreadsheetId=newSheetId, ranges=[]).execute()
    deleteSheet = sheet_metadata.get('sheets', '')[0].get("properties", {}).get("sheetId", {})
    sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, ranges=[]).execute()
    sheets = sheet_metadata.get('sheets', '')

    copy_sheet_to_another_spreadsheet_request_body = {
        # The ID of the spreadsheet to copy the sheet to.
        'destination_spreadsheet_id': newSheetId,
    }

    title_body = None
    for sheet in sheets:
        sheetId = sheet.get("properties", {}).get("sheetId", {})

        results = service.spreadsheets().sheets().copyTo(
            spreadsheetId=SPREADSHEET_ID, sheetId=sheetId, body=copy_sheet_to_another_spreadsheet_request_body).execute()
        newId = results.get("sheetId", {})
        title = results.get("title", {}).replace("Copy of ", '')
        if title_body is None:
            title_body = {
                'requests': [
                    {
                        'updateSheetProperties': {
                            'properties': {'sheetId': newId,
                                           'title': title},
                            'fields': 'title',
                        }
                    },
                    {
                        "deleteSheet": {
                            "sheetId": deleteSheet
                        }
                    }
                ]
            }
        else:
            title_body['requests'].append(
                {
                    'updateSheetProperties': {
                        'properties': {'sheetId': newId,
                                       'title': title},
                        'fields': 'title',
                     }
                })
    update = service.spreadsheets().batchUpdate(spreadsheetId=newSheetId, body=title_body).execute()

    # Store credentials in DB again
    dynamo.update_user_with_google_info(user_id, creds)
    dynamo.save_sheet_id(user_id, newSheetId)
    # api.upload_old_activities(user_id)

if __name__ == '__main__':
    main(45934359)