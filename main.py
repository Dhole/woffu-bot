#!/usr/bin/env python3

import json
import random
import requests
import datetime
import sys
import time
import base64

AUTHORITY = 'REDACTED.woffu.com'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36'
START_HOUR = 10
END_HOUR = 14
NO_WORK_DAYS = ['Friday', 'Saturday', 'Sunday']

START_OFFSET_MEAN = 5
START_OFFSET_VAR = 4

END_OFFSET_MEAN = 10
END_OFFSET_VAR = 8

HEADERS_BASE = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/json',
        }

def new_headers(jwt=None):
    headers = HEADERS_BASE.copy()
    if jwt:
        headers['authorization'] = f'Bearer {jwt}'
        headers['cookie'] = f'woffu.token={jwt}'
    headers['Authority'] = AUTHORITY
    return headers

def login(username, password):
    headers = new_headers()
    url = f'https://{AUTHORITY}/token'
    data = f'grant_type=password&username={username}&password={password}'
    r = requests.post(url, headers=headers, data=data)
    return r.json()

def signs(jwt):
    headers = new_headers(jwt)
    url = f'https://{AUTHORITY}/api/signs'
    r = requests.get(url, headers=headers)
    return r.json()

def check_in_out(jwt):
    headers = new_headers(jwt)
    headers['Content-Type'] = 'application/json;charset=UTF-8'
    url = f'https://{AUTHORITY}/api/svc/signs/signs'
    date = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    user_id = parse_jwt(jwt)['UserId']
    data = f'{{"UserId":{user_id},"TimezoneOffset":-120,"StartDate":"{date}","EndDate":"{date}","DeviceId":"WebApp"}}'
    r = requests.post(url, headers=headers, data=data)
    return r.json()

def rand_minute_start():
    return random.randrange(START_OFFSET_MEAN - START_OFFSET_VAR, START_OFFSET_MEAN + START_OFFSET_VAR)

def rand_minute_end():
    return random.randrange(END_OFFSET_MEAN - END_OFFSET_VAR, END_OFFSET_MEAN + END_OFFSET_VAR)

def parse_jwt(jwt):
    s = jwt.split('.')[1]
    jwt_json = base64.b64decode(s + '=' * (-len(s) % 4))
    return json.loads(jwt_json)

def run(username, password):
    auth = login(username, password)
    jwt = auth['access_token']
    rand_min_start = rand_minute_start()
    rand_min_end = rand_minute_end()
    # print('Next check out at {:02d}:{:02d}'.format(END_HOUR, rand_min_end))
    # print('Next check in at {:02d}:{:02d}'.format(START_HOUR, rand_min_start))
    last_day = None
    new_day = False
    while True:
        with open('holidays.txt') as f:
            holidays = f.readlines()
        holidays = [x.strip() for x in holidays]

        ts = datetime.datetime.now()
        h, m = ts.hour, ts.minute

        if last_day != ts.day:
            last_day = ts.day
            new_day = True
            print(f'=== {datetime.datetime.now()} ===')
        else:
            new_day = False

        start_hour = START_HOUR
        end_hour = END_HOUR
        if ts.strftime("%A") == 'Monday':
            start_hour = 9
            end_hour = 18

        if ts.strftime("%A") in NO_WORK_DAYS:
            if new_day:
                print(f'Today is a non-working day at {datetime.datetime.now()}')
            pass
        elif ts.strftime("%Y-%m-%d") in holidays:
            if new_day:
                print(f'Yay!  Today is holiday! at {datetime.datetime.now()}')
            pass
        elif (h * 60 + m) >= (start_hour * 60 + rand_min_start) and (h * 60 + m) < (end_hour * 60 + rand_min_end):
            s = signs(jwt)
            if len(s) == 0 or not s[-1]['SignIn']:
                print(f'Checking in at {datetime.datetime.now()}...')
                rand_min_end = rand_minute_end()
                check_in_out(jwt)
                print('Next check out at {:02d}:{:02d}'.format(end_hour, rand_min_end))
        else:
            s = signs(jwt)
            if len(s) == 0:
                pass
            elif s[-1]['SignIn']:
                print(f'Checking out at {datetime.datetime.now()}...')
                rand_min_start = rand_minute_start()
                check_in_out(jwt)
                print('Next check in at {:02d}:{:02d}'.format(start_hour, rand_min_start))
        time.sleep(60)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} username password")
        sys.exit(1)
    username, password = sys.argv[1], sys.argv[2]
    run(username, password)
