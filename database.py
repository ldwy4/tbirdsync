from __future__ import print_function

import mysql.connector
from mysql.connector import errorcode


def insert_status(id, status):
    id = id - 5100000000
    connection = mysql.connector.connect(
        user='admin', password='tjmwauki',
        host='default.cy5btlr16n7h.us-west-2.rds.amazonaws.com',
        database='main',
        buffered=True
    )
    cursor = connection.cursor()
    query = ("SELECT * from log_status "
             "WHERE id = " + str(id))
    cursor.execute(query)
    logged = False
    for (id, store_status) in cursor:
        if store_status == 'failed':
            logged = True
    if logged:
        print(status)
        template = ("UPDATE log_status "
                    "SET status = %s "
                    "WHERE id = %s")
        data = (status, id)
    else:
        template = ("INSERT INTO log_status "
                    "(id, status) "
                    "VALUES (%s, %s)")
        data = (id, status)
    cursor.execute(template, data)
    print(cursor.statement)
    connection.commit()
    cursor.close()
    connection.close()


def update_status(id, status):
    id = id - 5100000000
    connection = mysql.connector.connect(
        user='admin', password='tjmwauki',
        host='default.cy5btlr16n7h.us-west-2.rds.amazonaws.com',
        database='main',
    )
    cursor = connection.cursor()
    template = ("UPDATE log_status "
                "SET status = %s "
                "WHERE id = %s")
    data = (status, id)
    cursor.execute(template, data)
    print(cursor.statement)
    connection.commit()
    cursor.close()
    connection.close()


def check_status(id):
    id = id - 5100000000

    connection = mysql.connector.connect(
        user='admin', password='tjmwauki',
        host='default.cy5btlr16n7h.us-west-2.rds.amazonaws.com',
        database='main',
    )
    cursor = connection.cursor()
    query = ("SELECT * from log_status "
             "WHERE id = " + str(id))
    cursor.execute(query)
    logged = False
    for (id, status) in cursor:
        if status != 'failed':
            logged = True
    connection.commit()
    cursor.close()
    connection.close()
    print(logged)
    return logged


def insert_google_token(id, creds):
    connection = mysql.connector.connect(
        user='admin', password='tjmwauki',
        host='default.cy5btlr16n7h.us-west-2.rds.amazonaws.com',
        database='main',
    )
    cursor = connection.cursor()
    template = ("INSERT INTO google_token (id, token, refresh_token, expires_at) "
                "VALUES (%s, %s, %s, %s)")
    data = (id, creds['token'], creds['refresh_token'], creds['expires_at'])
    cursor.execute(template, data)
    connection.commit()
    cursor.close()
    connection.close()


def update_google_token(id, creds):
    connection = mysql.connector.connect(
        user='admin', password='tjmwauki',
        host='default.cy5btlr16n7h.us-west-2.rds.amazonaws.com',
        database='main',
    )
    cursor = connection.cursor()
    template = ("UPDATE google_token  "
                "SET token = %s, refresh_token = %s , expires_at = %s "
                "WHERE id = %s")
    data = (creds['token'], creds['refresh_token'], creds['expires_at'], id)
    cursor.execute(template, data)
    connection.commit()
    cursor.close()
    connection.close()


def query_google_token(id):
    connection = mysql.connector.connect(
        user='admin', password='tjmwauki',
        host='default.cy5btlr16n7h.us-west-2.rds.amazonaws.com',
        database='main',
    )
    cursor = connection.cursor()
    query = ("SELECT * from google_token "
             "WHERE id = " + str(id))
    ret = dict()
    cursor.execute(query)
    for (id, token, refresh_token, expires_at) in cursor:
        ret['token'] = token
        ret['refresh_token'] = refresh_token
        ret['expires_at'] = expires_at
    connection.commit()
    cursor.close()
    connection.close()
    return ret


def insert_strava_token(creds):
    connection = mysql.connector.connect(
        user='admin', password='tjmwauki',
        host='default.cy5btlr16n7h.us-west-2.rds.amazonaws.com',
        database='main',
    )
    cursor = connection.cursor()
    template = ("INSERT INTO strava_token (id, access_token, refresh_token, expire_at, expires_in) "
                "VALUES (%s, %s, %s, %s, %s)")
    data = (creds['id'], creds['access_token'], creds['refresh_token'], creds['expires_at'], creds['expires_in'])
    cursor.execute(template, data)
    connection.commit()
    cursor.close()
    connection.close()


def update_strava_token(creds):
    connection = mysql.connector.connect(
        user='admin', password='tjmwauki',
        host='default.cy5btlr16n7h.us-west-2.rds.amazonaws.com',
        database='main',
    )
    cursor = connection.cursor()
    template = ("UPDATE strava_token  "
                "SET access_token = %s, refresh_token = %s, expire_at = %s, expires_in = %s "
                "WHERE id = %s")
    data = (creds['access_token'], creds['refresh_token'], creds['expires_at'], creds['expires_in'], creds['id'])
    cursor.execute(template, data)
    connection.commit()
    cursor.close()
    connection.close()


def query_strava_token(id):
    connection = mysql.connector.connect(
        user='admin', password='tjmwauki',
        host='default.cy5btlr16n7h.us-west-2.rds.amazonaws.com',
        database='main',
    )
    cursor = connection.cursor()
    query = ("SELECT * from strava_token "
             "WHERE id = " + str(id))
    ret = dict()
    ret['token_type'] = 'Bearer'
    cursor.execute(query)
    for (id, access_token, refresh_token, expire_at, expires_in) in cursor:
        ret['expires_at'] = expire_at
        ret['expires_in'] = expires_in
        ret['refresh_token'] = refresh_token
        ret['access_token'] = access_token
    ret['id'] = id
    connection.commit()
    cursor.close()
    connection.close()
    return ret

def insert_sheet_id(id, sheet_id):
    connection = mysql.connector.connect(
        user='admin', password='tjmwauki',
        host='default.cy5btlr16n7h.us-west-2.rds.amazonaws.com',
        database='main',
    )
    cursor = connection.cursor()
    if not query_sheet_id(id):
        template = ("INSERT INTO sheet_id (id, sheet_id) "
                    "VALUES (%s, %s)")
        data = (id, sheet_id)
    else:
        template = ("UPDATE sheet_id set sheet_id=%s where id=%s")
        data = (sheet_id, id)
    cursor.execute(template, data)
    connection.commit()
    cursor.close()
    connection.close()


def query_sheet_id(id):
    connection = mysql.connector.connect(
        user='admin', password='tjmwauki',
        host='default.cy5btlr16n7h.us-west-2.rds.amazonaws.com',
        database='main',
    )
    cursor = connection.cursor()
    query = ("SELECT * from sheet_id "
             "WHERE id = " + str(id))
    ret = None
    cursor.execute(query)
    for (id, sheet_id) in cursor:
        ret = sheet_id
    connection.commit()
    cursor.close()
    connection.close()
    return ret


def test_ssh():
    connection = mysql.connector.connect(
        user='admin', password='tjmwauki',
        host='default.cy5btlr16n7h.us-west-2.rds.amazonaws.com',
        database='main',
    )
    status = 'success'
    id = 1
    cursor = connection.cursor()
    template = ("INSERT INTO log_status "
                "(id, status) "
                "VALUES (%s, %s)")
    data = (id, status)
    cursor.execute(template, data)
    print(cursor.statement)
    connection.commit()
    cursor.close()
    connection.close()


if __name__ == '__main__':
    creds = {"token_type": "Bearer", "expires_at": 1618295135, "expires_in": 21473, "refresh_token": "4b85be51979ba60b645de6d6de6ec0d09bdbf7c1", "access_token": "b573473f622e755988591db94ed11dfcdf68b2ab", "id": 65729793}
    print(query_strava_token(45934359))
