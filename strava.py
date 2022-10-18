import time

import requests

import dynamo
auth_url = "https://www.strava.com/oauth/token"


def get_strava_api(user_id):
    """Getting info from strava api
    """
    # If access_token has expired then
    # use the refresh_token to get the new access_token
    expired = False
    athlete = dynamo.query_strava_token(user_id)
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
        dynamo.update_user_strava_token(new_strava_tokens)
    strava_tokens = dynamo.query_strava_token(user_id)
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
    print(new_strava_tokens)
    new_id = new_strava_tokens['athlete']['id']
    del new_strava_tokens['athlete']
    new_strava_tokens['id'] = new_id
    dynamo.insert_user(new_strava_tokens)
    return str(new_strava_tokens['id'])
