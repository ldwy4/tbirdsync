import json
from flask import request
from flask import Flask, redirect, session, send_from_directory
from flask_cors import CORS
from flask import jsonify
import quickstart as api
import pprint
import time
import requests
import drive
import sys
from google_auth_oauthlib.flow import Flow

app = Flask(__name__)
CORS(app, support_credentials=True)

@app.route('/', methods=['GET'])
def api_root():
    # response = request.args
    # if response.get('code') != '':
    #     print(response.get('code'), file=sys.stderr)
    #     if api.new_strava_user(response.get('code')):
    #         return 'Success'
    return "Please work"


@app.route('/activity', methods=['POST'])
def api_post():
    print('Webhook Event received!', file=sys.stderr)
    if request.headers['Content-Type'] == 'application/json':
        if request.json['aspect_type'] == 'create':
            print('It is working!', file=sys.stderr)
            info = json.dumps(request.json)
            print(request.json['object_id'], file=sys.stderr)
            logged = api.fill_slot(request.json['object_id'], request.json['owner_id'])
            if not logged:
                time.sleep(90)
                api.fill_slot(request.json['object_id'], request.json['owner_id'])
            return info
        # elif request.json['aspect_type'] == 'update':
        #     print('Update!', file=sys.stderr)
        #     info = json.dumps(request.json)
        #     print(request.json['object_id'], file=sys.stderr)
        #     api.fill_slot(request.json['object_id'])
        #     return info
    return "Uh oh"

@app.route('/activity', methods=['Get'])
def api_sub_webhook():
    VERIFY_TOKEN = "STRAVA"
    response = request.args
    print(request.json)
    if response.get('hub.mode') == 'subscribe' and response.get('hub.verify_token') == VERIFY_TOKEN:
        url = 'https://api.strava.com/api/v3/push_subscriptions'
        payload = {
            'hub.challenge': response['hub.challenge'],
            'hub.mode': 'subscribe',
        }
        jsonpayload = json.dumps(payload, indent=2)
        # r = requests.get(url, data=jsonpayload)
        return jsonpayload
    else:
        return 'NOT OK'

@app.route('/strava', methods=['PUT'])
def api_update_activity():
    print('Activity updated')
    return 'update'

@app.route('/sheet', methods=['POST'])
def api_save_sheet():
    print(api_get_cookie())
    user_id = int(request.args.get('uid'))
    info = request.args.get('code')
    api.save_sheet_id(user_id, info)
    print(info)
    return "Saved sheet, you may now close tab :)"

@app.route('/cookie', methods=['POST', 'GET'])
def api_get_cookie():
    print(request.host)
    print(request.cookies)
    return request.cookies.get('token')

@app.route('/subscribe', methods=['GET'])
def api_subscribe():
    VERIFY_TOKEN = "STRAVA"
    response = request.args
    print(request.json)
    if response.get('hub.mode') == 'subscribe' and response.get('hub.verify_token') == VERIFY_TOKEN:
        url = 'https://api.strava.com/api/v3/push_subscriptions'
        payload = {
            'hub.challenge': response['hub.challenge'],
            'hub.mode': 'subscribe',
        }
        jsonpayload = json.dumps(payload, indent=2)
        # r = requests.get(url, data=jsonpayload)
        return jsonpayload
    else:
        return 'HELLO WORLD TEST'

@app.route('/url')
def api_get_url():
    return redirect(api.get_url())

@app.route('/strava', methods=['GET'])
def api_strava():
    code = request.args.get('code')
    response = redirect('http://www.tbirdsync.com/#/sign-in')
    token = api.new_strava_user(code)
    response.set_cookie('id', token, domain='tbirdsync.com')
    return response

@app.route('/google', methods=['GET'])
def api_google():
    token = request.cookies.get('id').replace("'",'"')
    code = int(token)
    auth_url = request.url
    print(api.new_google_user(code, auth_url))
    return redirect('http://www.tbirdsync.com/#/drive')

@app.route('/drive', methods=['GET', 'POST'])
def api_drive():
    user_id = int(request.args.get('code'))
    print(user_id)
    response = jsonify(drive.main(user_id))
    return response


@app.route('/create', methods=['GET','POST'])
def api_create_log():
    print(api_get_cookie())
    user_id = int(request.args.get('uid'))
    drive.create_log(user_id)
    return "Created sheet, you may now close tab :)"


@app.route('/test', methods=['GET'])
def api_print():
    user_id = request.cookies.get('id').replace("'",'"')
    return jsonify(api.get_unfinished(user_id))

@app.route('/test', methods=['POST'])
def api_recieve_update():
    print('Webhook Event received!', file=sys.stderr)
    print(request.cookies.get('token'))
    user_id = json.loads(request.cookies.get('token').replace("'",'"'))['id']
    if request.headers['Content-Type'] == 'application/json':
        print('It is working!', file=sys.stderr)
        info = json.dumps(request.json)
        api.update_log(user_id,request.json)
        return info
    return "Not working"

@app.route('/login', methods=['GET'])
def api_register():
    print('New User!', file=sys.stderr)
    if request.headers['Content-Type'] == 'application/json':
        info = json.dumps(request.json)
        return info
    return "New User Found!"

@app.after_request
def middleware_for_response(response):
    # Allowing the credentials in the response.
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/login', methods=['POST'])
def api_other():
    print('New User!', file=sys.stderr)
    return "Done"

if __name__ == '__main__':
    app.secret_key = 'A/2NDOFISNSD,?2!'
    app.run(debug=True)
