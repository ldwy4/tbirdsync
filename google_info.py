import datetime
import os.path
import pickle
import time

import requests
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from googleapiclient.discovery import build

import dynamo

goog_url = 'https://www.googleapis.com/oauth2/v4/token'
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive.metadata.readonly']

def save_sheet_id(user_id, sheet_id):
    dynamo.insert_sheet_id(user_id, sheet_id)


def get_sheet_id(user_id):
    return dynamo.query_sheet_id(user_id)


def get_Goog_API(user_id):
    """Writing info to sheets api"""

    # Get token from DB
    creds = dynamo.query_user(user_id)
    expires = creds['google_expires_at']
    # If there are no (valid) credentials available, let the user log in.
    if creds['google_expires_at'] < time.time():
        res = requests.post(
            url=goog_url,
            data={
                'client_id': '882547647274-nfh6efs7c3q69r67fhtjkonm8o4b15ia.apps.googleusercontent.com',
                'client_secret': 'Rm4v_Gt1yTe9ZSpD5AX1VONS',
                'grant_type': 'refresh_token',
                'refresh_token': creds['refresh_token'],
                'access_type': 'offline',
                'prompt': 'consent'
            }
        )
        creds['token'] = res.json()['access_token']
        expires = datetime.datetime.fromtimestamp(time.time() + res.json()['expires_in'])
        dynamo.update_user_with_google_info(user_id, creds)

    creds['token_uri'] = "https://oauth2.googleapis.com/token"
    creds['client_id'] = '882547647274-nfh6efs7c3q69r67fhtjkonm8o4b15ia.apps.googleusercontent.com'
    creds['client_secret'] = 'Rm4v_Gt1yTe9ZSpD5AX1VONS'
    creds['scopes'] = SCOPES
    credentials = google.oauth2.credentials.Credentials(token=creds['token'],
                                                        refresh_token=creds['refresh_token'],
                                                        token_uri=creds['token_uri'],
                                                        client_id=creds['client_id'] ,
                                                        client_secret=creds['client_secret'],
                                                        scopes= SCOPES)
    service = build('sheets', 'v4', credentials=credentials)

    creds['expires_at'] = expires
    # Store credentials in DB again
    dynamo.update_user_with_google_info(user_id, creds)

    return service


def new_google_user(id, auth_res):
    """Writing info to sheets api"""
    # tokens = None
    flow = Flow.from_client_secrets_file(
        'credentials.json', SCOPES, redirect_uri="https://api.tbirdsync.com/google")
    flow.fetch_token(authorization_response=auth_res)
    credentials = flow.credentials
    print(credentials)
    creds = {'token': credentials.token,
             'refresh_token': credentials.refresh_token,
             'expires_at': time.time() + 3600
             }
    print(creds)
    dynamo.update_user_with_google_info(id, creds)
    return str(id)


def get_url():
    """Writing info to sheets api"""
    tokens = None
    flow = Flow.from_client_secrets_file(
        'credentials.json', SCOPES, redirect_uri="https://api.tbirdsync.com/google")
    return flow.authorization_url(access_type='offline', include_granted_scope='true', prompt='consent')[0]