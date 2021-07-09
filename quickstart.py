from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google_auth_oauthlib.flow import InstalledAppFlow
import google.oauth2.credentials
from google.auth.transport.requests import Request
from pprint import pprint
import database as db
import urllib3
import json
import requests
import time
import calendar
import math
import datetime
import pandas as pd

# create an instance of the API class

athlete_url = " https://www.strava.com/api/v3/athlete"
auth_url = "https://www.strava.com/oauth/token"
authorize_url = "https://www.strava.com/oauth/authorize"
goog_url = 'https://www.googleapis.com/oauth2/v4/token'

payload = {
    'client_id': "51156",
    'client_secret': "f5b3cb6c2ff9412a7928d3c36e4a11139d351885",
    'refresh_token': '64f39c7bc8df13baf5b7e8057e80b10e216e6753',
    'grant_type': 'refresh_token',
    'f': "json"
}

other_payload = {
    'client_id': "51156",
    'client_secret': "f5b3cb6c2ff9412a7928d3c36e4a11139d351885",
    'code': '9820d42d339c7870d1293bfe11b885c8d5591aa4',
    'grant_type': 'authorization_code',
    'f': "json"
}

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive.metadata.readonly']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '11I6tlT0e2M0ld11-MEUzRG7bdnRps-pDldmo6-5FgnY'
SAMPLE_RANGE_NAME = 'July!B2:Z30'


# Fills training log with activity with search_id
def fill_slot(search_id, user_id):
    print('search id:')
    print(search_id)
    if db.check_status(search_id):
        print('already logged')
        return True
    strava_tokens = get_strava_api(user_id)
    access_token = strava_tokens['access_token']
    header = {'Authorization': 'Bearer ' + access_token}
    # athlete_info = requests.get(athlete_url, headers=header).json()
    activities_url = "https://www.strava.com/api/v3/activities/" + str(search_id)
    activitie_info = requests.get(activities_url, headers=header).json()

    db.insert_status(search_id, 'pending')

    if 'id' not in activitie_info:
        print('failed to log')
        db.update_status(search_id, 'failed')
        return False

    service = get_Goog_API(user_id)

    global SPREADSHEET_ID
    SPREADSHEET_ID = get_sheet_id(user_id)
    time.sleep(5)
    if not has_sheet(service):
        create_sheet(service)

    value_input_option = 'USER_ENTERED'
    body = {'majorDimension': 'ROWS'}
    timeUpdate = {'majorDimension': 'ROWS'}
    body['range'] = 'LOOKUP_SHEET!A1'
    print(activitie_info)
    length = round(activitie_info['moving_time'] / 60.0, 1)
    distance = round(activitie_info['distance'] / 1000, 1)
    date = activitie_info['start_date_local']
    print(date)
    if (date[8] == '0'):
        day = date[9]
    else:
        day = date[8:10]
    if (date[5] == '0'):
        mon = date[6]
    else:
        mon = date[5:7]
    year = date[0:4]
    month, value = get_row(body, date, day, mon, year, service, value_input_option)

    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                                 range=month + '!A1:Z36').execute()
    values = result.get('values', [])

    # convert values into dataframe
    df = pd.DataFrame(values, columns=values[0])

    df = df.drop(0)

    df = df.replace([''], ['Empty'])
    df = df.replace([None], ['Empty'])
    row = df.loc[df['Date'] == day + "/" + mon + "/" + year]
    # For Rhys Kramer's template
    if "Time 1" not in df.columns:
        pace_req = {'majorDimension': 'ROWS'}
        if activitie_info['type'] == 'Run':
            time_col = chr(df.columns.get_loc('Min Running') + 65)
            prev_time = row.iloc[0, df.columns.get_loc('Min Running')]
            row = df.loc[df['Date'] == day + "/" + mon + "/" + year]
            run = row.iloc[0, df.columns.get_loc('Run 1')]
            placement = chr(df.columns.get_loc('Run 1') + 65)
            if (run != 'Empty'):
                print('Run 1 is filled already')
                run = row.iloc[0, df.columns.get_loc('Run 2')]
                placement = chr(df.columns.get_loc('Run 2') + 65)
                if (run != 'Empty'):
                    run = row.iloc[0, df.columns.get_loc('Run 3')]
                    placement = chr(df.columns.get_loc('Run 3') + 65)
                    if (run != 'Empty'):
                        placement = chr(df.columns.get_loc('Run 4') + 65)
            body['range'] = month + "!" + placement + value
            body['values'] = [[distance]]
            timeUpdate['range'] = month + "!" + time_col + value
            if prev_time != 'Empty':
                length += float(prev_time)
            timeUpdate['values'] = [[length]]
            request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID,
                                                             range=timeUpdate['range'],
                                                             valueInputOption=value_input_option,
                                                             body=timeUpdate)
            response = request.execute()
            km_total = row.iloc[0, df.columns.get_loc('Km Running')]
            km_total = float(km_total) + distance
            pace = str(math.trunc(length / km_total)) + ':' + str(
                math.trunc(((length / km_total) % 1) * 60)).zfill(2)
            pace_req['range'] = month + "!" + chr(df.columns.get_loc('Pace') + 65) + value
            pace_req['values'] = [[pace]]
            request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID,
                                                             range=pace_req['range'],
                                                             valueInputOption=value_input_option, body=pace_req)
            response = request.execute()
        else:
            time_placement = chr(df.columns.get_loc('Min X-Train') + 65)
            run_placement = chr(df.columns.get_loc('X-Train Km Equiv') + 66)
            body['values'] = [[length, round(length / 13.5, 1)]]
            body['range'] = month + '!' + time_placement + value + ":" + run_placement + value
            print("Activity has been logged")
    else:
        # For Personal Training log
        if (activitie_info['type'] == 'Run'):
            row = df.loc[df['Date'] == day + "/" + mon + "/" + year]
            run = row.iloc[0, df.columns.get_loc('Run 1')]
            run_number = 'Run 1'
            if (run != 'Empty'):
                print('Run 1 is filled already')
                run = row.iloc[0, df.columns.get_loc('Run 2')]
                run_number = 'Run 2'
                if (run != 'Empty'):
                    run_number = 'Run 3'
                    run = row.iloc[0, df.columns.get_loc('Run 3')]
                    extra_time = row.iloc[0, df.columns.get_loc('time 3')]
                    if run != 'Empty':
                        length = length + float(extra_time)
                        distance = distance + float(run)
            run_placement = chr(df.columns.get_loc(run_number) + 64)
            time_placement = chr(df.columns.get_loc(run_number) + 65)
            body['range'] = month + "!" + run_placement + value + ":" + time_placement + value
            body['values'] = [[length, distance]]
        else:
            body['values'] = [[length, round(length / 13.5, 1)]]
            body['range'] = month + "!R" + value + ":S" + value
            print("Activity has been logged")
    request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=body['range'],
                                                     valueInputOption=value_input_option, body=body)
    response = request.execute()
    print("Run has been logged")
    db.update_status(search_id, 'success')
    return True


def create_sheet(service):
    requests = []
    requests.append({
        "addSheet": {
            "properties": {
                "title": "LOOKUP_SHEET",
                "hidden": True,
                "gridProperties": {
                    "rowCount": 20,
                    "columnCount": 12
                },
                "tabColor": {
                    "red": 1.0,
                    "green": 0.3,
                    "blue": 0.4
                }
            }
        }
    })
    body = {'requests': requests}
    response = service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
    print("done")


def has_sheet(service):
    sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, ranges=[]).execute()
    sheets = sheet_metadata.get('sheets', '')
    title = None
    for sheet in sheets:
        if sheet.get("properties", {}).get("title", {}) == 'LOOKUP_SHEET':
            title = sheet.get("properties", {}).get("title", {})
    return title != None


def get_strava_api(user_id):
    """Getting info from strava api
    """
    # If access_token has expired then
    # use the refresh_token to get the new access_token
    expired = False
    athlete = db.query_strava_token(user_id)
    if athlete['expires_at'] < time.time():
        # Make Strava auth API call with current refresh token
        res = requests.post(
            url=auth_url,
            data={
                'client_id': '51156',
                'client_secret': 'f5b3cb6c2ff9412a7928d3c36e4a11139d351885',
                'grant_type': 'refresh_token',
                'refresh_token': athlete['refresh_token']
            }
        )
        # Save response as json in new variable
        new_strava_tokens = res.json()
        new_strava_tokens["id"] = user_id
        expired = True
    # if recieved new token
    if expired:
        db.update_strava_token(new_strava_tokens)
    strava_tokens = db.query_strava_token(user_id)
    return strava_tokens


def new_strava_user(code):
    """Getting info from strava api
    """
    res = requests.post(
        url=auth_url,
        data={
            'client_id': '51156',
            'client_secret': 'f5b3cb6c2ff9412a7928d3c36e4a11139d351885',
            'code': code,
            'grant_type': 'authorization_code',
        }
    )
    new_strava_tokens = res.json()
    id = new_strava_tokens['athlete']['id']
    del new_strava_tokens['athlete']
    new_strava_tokens['id'] = id
    db.insert_strava_token(new_strava_tokens)
    return str(new_strava_tokens['id'])


def save_sheet_id(user_id, sheet_id):
    db.insert_sheet_id(user_id, sheet_id)


def get_sheet_id(user_id):
    return db.query_sheet_id(user_id)


def get_Goog_API(user_id):
    """Writing info to sheets api"""

    # Get token from DB
    creds = db.query_google_token(user_id)
    expires = creds['expires_at']
    # If there are no (valid) credentials available, let the user log in.
    if creds['expires_at'].timestamp() < time.time():
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
        db.update_google_token(user_id, creds)

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
    pprint(creds)
    # Store credentials in DB again
    db.update_google_token(user_id, creds)

    return service


def new_google_user_local(id):
    """Writing info to sheets api"""
    tokens = None
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    creds = flow.run_local_server(port=8080)
    if os.path.exists('/tmp/goog.pickle'):
        with open('/tmp/goog.pickle', 'rb') as token:
            tokens = pickle.load(token)
            tokens[id] = creds
    with open('/tmp/goog.pickle', 'wb') as token:
        if not tokens:
            tokens = {id: creds}
        pickle.dump(tokens, token)


def new_google_user(id, auth_res):
    """Writing info to sheets api"""
    # tokens = None
    flow = Flow.from_client_secrets_file(
        'credentials.json', SCOPES, redirect_uri="https://api.tbirdsync.com/google")
    flow.fetch_token(authorization_response=auth_res)
    credentials = flow.credentials
    creds = {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'expires_at': datetime.datetime.fromtimestamp(time.time() + 3600)}
    db.insert_google_token(id, creds)
    return str(id)


def get_url():
    """Writing info to sheets api"""
    tokens = None
    flow = Flow.from_client_secrets_file(
        'credentials.json', SCOPES, redirect_uri="https://api.tbirdsync.com/google")
    return flow.authorization_url(access_type='offline', include_granted_scope='true', prompt='consent')[0]


def unpickle_pickle():
    if os.path.exists('tmp/goog.pickle'):
        with open('tmp/goog.pickle', 'rb') as token:
            tokens = pickle.load(token)
        for t in tokens:
            print(t)
            print(tokens[t])


def view_runs():
    with open('/tmp/goog.pickle', 'rb') as token:
        tokens = pickle.load(token)
        print(tokens)


# Prints runs in SAMPLE_RANGE_NAME
def print_runs():
    # Call APIs
    service = get_Goog_API()
    strava_tokens = get_strava_api()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])
    dict_ = {}
    if not values:
        print('No data found.')
    else:
        print('Displaying runs..')
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            dict_[row[1]] = (row[4])
        return dict_


# returns list of training log entries which are incomplete
def get_unfinished(user_id):
    unfinished = []
    # Call API

    service = get_Goog_API(user_id)
    sheet = service.spreadsheets()
    global SPREADSHEET_ID
    SPREADSHEET_ID = get_sheet_id(user_id)

    for i in range(3):

        # TODO: fix so that whole range is always taken even with empty cells

        month = calendar.month_name[int(datetime.datetime.now().strftime("%m")) - i]
        range_ = month + '!A1:Z30'
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=range_).execute()
        values = result.get('values', [])

        # convert values into dataframe
        df = pd.DataFrame(values, columns=values[0])

        # replace all non trailing blank values created by Google Sheets API
        # with null values

        df_replace = df.replace([''], ['Empty'])
        df_replace = df_replace.replace([None], ['Empty'])

        # finds training log entries that are unfinished
        for index, row in df_replace.iterrows():
            if 'Empty' not in (row['Run 1'] and row['Time 1']) and 'Empty' in (
                    row['Hours Slept'] or row['Fatigue(0-10)'] or row['Stress (0-5)']):
                print(row['Date'] + " is not complete!")
                unfinished.append([row['Date'], row['Run 1'], row['Time 1']])
    print(unfinished)
    return unfinished


def update_log(user_id, info):
    service = get_Goog_API(user_id)
    sheet = service.spreadsheets()

    value_input_option = 'USER_ENTERED'
    body = {'majorDimension': 'ROWS'}
    body['range'] = 'LOOKUP_SHEET!A1'
    date = info['date']
    if (date[1] == '/'):
        day = date[0]
        mon = date[2]
        year = date[4:8]
    else:
        day = date[0:2]
        mon = date[3]
        year = date[5:9]
    month, value = get_row(body, date, day, mon, year, service, value_input_option)
    range_ = month + '!A1:Z2'
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=range_).execute()
    values = result.get('values', [])

    # convert values into dataframe
    df = pd.DataFrame(values, columns=values[0])
    print(df)
    sleep = chr(df.columns.get_loc("Hours Slept") + 65)
    fatigue = chr(df.columns.get_loc("Fatigue(0-10)") + 65)
    stress = chr(df.columns.get_loc("Stress (0-5)") + 65)
    comment = chr(df.columns.get_loc("Comments/Knocks") + 65)
    batch_data = {
        'value_input_option': value_input_option,
        'data': [
            {
                'range': month + "!" + sleep + value,
                'values': [[info['sleep']]]
            },
            {
                'range': month + "!" + fatigue + value,
                'values': [[info['fatigue']]]
            },
            {
                'range': month + "!" + stress + value,
                'values': [[info['stress']]]
            },
            {
                'range': month + '!' + comment + value,
                'values': [[info['comment']]]
            }
        ]
    }
    # body['values'] = [[info['fatigue'], info['stress'], info['sleep'], info['comment']]]
    # body['range'] = month + "!R" + value + ":S" + value
    print("Log has been Updated!")

    request = sheet.values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=batch_data)
    response = request.execute()


def get_row(body, date, day, mon, year, service, value_input_option):
    month = calendar.month_name[int(mon)]
    body['values'] = [['=MATCH(--\"' + day + "/" + mon + "/" + year + '\", ' + month + '!B:B, 0)']]
    request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=body['range'],
                                                     valueInputOption=value_input_option, body=body)
    response = request.execute()
    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                                 range=body['range']).execute()
    value = result.get('values', [])[0][0]
    # TODO: rework these if statements
    if value == '#N/A':
        if int(mon) == 1:
            month = calendar.month_name[12]
        else:
            month = calendar.month_name[int(mon) - 1]
        body['values'] = [
            ['=MATCH(--\"' + day + "/" + mon + "/" + year + '\", ' + month + '!B:B, 0)']]
        pprint(body['values'])
        request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=body['range'],
                                                         valueInputOption=value_input_option, body=body)
        response = request.execute()
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                                     range=body['range']).execute()
        value = result.get('values', [])[0][0]
    if value == '#N/A':
        month = calendar.month_name[int(mon) + 1]
        body['values'] = [
            ['=MATCH(--\"' + day + "/" + mon + "/" + year + '\", ' + month + '!B:B, 0)']]
        pprint(body['values'])
        request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=body['range'],
                                                         valueInputOption=value_input_option, body=body)
        response = request.execute()
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID,
                                                     range=body['range']).execute()
        value = result.get('values', [])[0][0]
    return month, value


def credentials_to_dict(credentials):
    return {'token': credentials.token['token'],
            'refresh_token': credentials.token['refresh_token'],
            'token_uri': credentials.token['token_uri'],
            'client_id': credentials.token['client_id'],
            'client_secret': credentials.token['client_secret'],
            'expires_at': credentials.token['expires_at'],
            'scopes': credentials.token['scopes']}


if __name__ == '__main__':
    # payload = {
    #     'fatigue': 7.5,
    #     'stress': 2,
    #     'sleep': 8,
    #     'comment': 'Testing this out',
    #     'date': '31/8/2020',
    # };

    # fill_slot(5319925332, 34199943)
    print(has_sheet(get_Goog_API(45934359)))
    # new_google_user(2, "4/0AY0e-g6QCmEaX6odh250fRhGqm8XEi4pqeDcr9hTbfEEhXmIPvH8mTF_lZ5qUgNi7kBkPw")
    # print(get_url())
    # print(get_Goog_API(34199943))
    # unpickle_pickle()
    # create_sheet(get_Goog_API(45934359), '1K9_3xLrmKyoCVkwjh8GYi6zKAKjXWLy7MwQ2guYLCt8')
    # save_sheet_id(45934359, '11I6tlT0e2M0ld11-MEUzRG7bdnRps-pDldmo6-5FgnY')
    # get_sheet_id(45934359)
    # get_Goog_API(1)
    # save_sheet_id(2, 'yolo')

    # view_runs()
    # update_log(payload)
    # get_unfinished()

"""Random stuff I might need"""

# Call the Sheets API
# sheet = service.spreadsheets()
# result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
#                             range=SAMPLE_RANGE_NAME).execute()
# values = result.get('values', [])
# value_input_option = 'RAW'
# distance = round((activities_info[0]['distance'] + activities_info[1]['distance'] + 2100)/1000,2)
# body = {}
# body['values'] = [[distance]]
# body['majorDimension'] = 'ROWS'
# range_ = 'July!E10'
# body['range'] = range_
# request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=range_,
#                                                  valueInputOption=value_input_option, body=body)
# response = request.execute()

# searches sheet for value and returns row
# def search_row():
#     value_input_option = 'USER_ENTERED'
#     body = {'majorDimension': 'ROWS'}
#     for i in range(25):
#         body['range'] = 'LOOKUP_SHEET!A1'
#         act = activities_info[i]
#         time = round(act['moving_time'] / 60.0, 1)
#         distance = round(act['distance'] / 1000, 1)
#         date = act['start_date_local']
#         month = calendar.month_name[int(date[6])]
#         body['values'] = [['=MATCH(--\"'+date[8:10]+"/"+date[6]+"/"+date[0:4]+'\", '+month+'!B:B, 0)']]
#         request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=body['range'],
#                                                          valueInputOption=value_input_option, body=body)
#         response = request.execute()
#         result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
#                                     range=body['range']).execute()
#         value = result.get('values', [])[0][0]
#         # TODO: rework these if statements
#         if value == '#N/A':
#             month = calendar.month_name[int(date[6])-1]
#             body['values'] = [
#                 ['=MATCH(--\"' + date[8:10] + "/" + date[6] + "/" + date[0:4] + '\", ' + month + '!B:B, 0)']]
#             pprint(body['values'])
#             request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=body['range'],
#                                                              valueInputOption=value_input_option, body=body)
#             response = request.execute()
#             result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
#                                         range=body['range']).execute()
#             value = result.get('values', [])[0][0]
#         if value == '#N/A':
#             month = calendar.month_name[int(date[6]) + 1]
#             body['values'] = [
#                 ['=MATCH(--\"' + date[8:10] + "/" + date[6] + "/" + date[0:4] + '\", ' + month + '!B:B, 0)']]
#             pprint(body['values'])
#             request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=body['range'],
#                                                              valueInputOption=value_input_option, body=body)
#             response = request.execute()
#             result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
#                                         range=body['range']).execute()
#             value = result.get('values', [])[0][0]
#         body['values'] = [[time, distance]]
#         body['range'] = month + "!D" + value + ":E" + value
#         request = service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range=body['range'],
#                                                          valueInputOption=value_input_option, body=body)
#         response = request.execute()

# requests.append({
#     "addSheet": {
#         "properties": {
#             "hidden": True,
#             "title": "LOOKUP_SHEET"
#         }
#     }
# })
# body = {
#     'requests': request
# }
#
# response = service.spreadsheets().batchUpdate(
#     spreadsheetId=SPREADSHEET_ID,
#     body=body).execute()
# search_row()
# def print_runs():
#     if not values:
#         print('No data found.')
#     else:
#         print('Day, Distance:')
#         for row in values:
#             # Print columns A and E, which correspond to indices 0 and 4.
#             print('%s, %skm' % (row[1], row[4]))
