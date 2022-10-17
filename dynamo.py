import json

import boto3

TABLE_NAME = "tbirdSync"


# get table object containing user data for TbirdSync
def get_table():
    # Get the service resource.
    dynamodb = boto3.resource('dynamodb')

    # Create the DynamoDB table.
    table = dynamodb.Table(TABLE_NAME)
    return table


# insert new user into db
def insert_user(creds):
    table = get_table()
    print(creds)
    table.put_item(Item=creds)


def update_user_strava_token(creds):
    table = get_table()
    table.update_item(
        Key={
            'id': creds['id']
        },
        UpdateExpression='SET access_token = :val1, refresh_token = :val2, expires_at = :val3, expires_in = :val4',
        ExpressionAttributeValues={
            ':val1': creds['access_token'],
            ':val2': creds['refresh_token'],
            ':val3': creds['expires_at'],
            ':val4': creds['expires_in'],
        }
    )


def update_user_with_google_info(id_num, creds):
    table = get_table()
    table.update_item(
        Key={
            'id': id_num,
        },
        UpdateExpression='SET google_token = :val1, google_refresh_token = :val2, google_expires_at = :val3',
        ExpressionAttributeValues={
            ':val1': creds['token'],
            ':val2': creds['refresh_token'],
            ':val3': creds['expires_at']
        }
    )


def query_user(id_num):
    table = get_table()
    user = table.get_item(Key={'id': id_num})
    return user


# TODO: implement
def save_sheet_id(user_id, sheet_id):
    print("todo")


# TODO: implement
def get_sheet_id(user_id):
    return "nice"


if __name__ == '__main__':
    update_user_strava_token({'id': 45934359, 'expires_in': 11329,
                              'expires_at': 2,
                              'refresh_token': 'e5007d7287312259291900b8402c7907d4df2939',
                              'access_token': 'dbbd9c82ced6bbe4f707d5f2d74be575d5f56823'})
    creds = {
        'access_token': 'ya29.a0Aa4xrXNrK2lb05PV-looyu0DTqdilih6Q_FCUa0hFYx1ZU5AfE-SmCsd6wT54ibrcbFpGrwvj--QMW9burRe7c-qWZWVgWiuxFf5jBmofSTX3Uyu6DlVz8Tea9qYIGCOVRWtQ0SnwURvmetvmmMxLLW5ZVx1aCgYKATASARASFQEjDvL9-U26rV9JR4DVtSXLI-1Ufg0163',
        'expires_in': 3599,
        'refresh_token': '1//06T_DcL7EzT5zCgYIARAAGAYSNwF-L9IrOZDnVndV4IqHfxKO_TUM41JwczRXzWALNet6d85LhA0m9APJSfQWPfqj7te0zsXIu4s',
        'scope': ['https://www.googleapis.com/auth/drive.metadata.readonly',
                  'https://www.googleapis.com/auth/spreadsheets'], 'token_type': 'Bearer',
        'expires_at': 1666041780.8730166}

    # print(query_user(45934359))
    # update_user_with_google_info()
    # cred = {'id': 45934359, 'expires_in': 11329,
    #         'refresh_token': 'e5007d7287312259291900b8402c7907d4df2939',
    #         'access_token': 'dbbd9c82ced6bbe4f707d5f2d74be575d5f56823'}
    # insert_user(cred)
