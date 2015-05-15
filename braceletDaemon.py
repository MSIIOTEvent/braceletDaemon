#!/usr/bin/env python

###################################################################
#  To use:
#   * On the web:
#       * Go to https://dashboard.us.enableiot.com
#       * Register - be sure to click the "Sign Up Here" link. Do not use
#       * any of the OAuth options, or you will not be able to use the API.#
#       * Verify your email address
#       * Enter a name for your account
#   * Below line 39 in this file:
#       * Update your username, password and account_name
#       * Update the proxy address if required
#       * Update the device id below. The device id MUST be unique or
#         the step to create the device will fail
#   * Install the python "requests" library. You can use Python 
#     virtual environments, or install it globally:
#       $ pip install requests
#   * Run the program
#       $ python braceletDeamon.py
#

import sys
import requests
import json
import uuid
import time
import random
import datetime

#####################################
# Set these values first
#####################################
host = "dashboard.us.enableiot.com"

proxies = {
    # "https": "http://proxy.example.com:8080"
}

username = "xxxxxxxxxxxx"
password = "yyyyyyyyyyyy"
account_name = "nnnnnnnn"

#this will create a device with this id - error if it already exists
device_id = "zzzzzzzzzzz"






verify = True # whether to verify certs
#####################################

api_root = "/v1/api"
base_url = "https://{0}{1}".format(host, api_root)
device_name = "Device-{0}".format(device_id)

g_user_token = ""
g_device_token = ""


def main():
    global g_user_token, g_device_token

    # get an authentication token for use in the following API calls.
    # It will be put in every header by get_user_headers()
    g_user_token = get_token(username, password)

    # get my user_id (uid) within the Intel IoT Analytics Platform
    uid = get_user_id()
    print "UserId: {0}".format(uid)

    # for all the accounts I have access to, find the first account 
    # with the name {account_name} and return the account_id (aid)
    aid = get_account_id(uid, account_name)
    print "AccountId: {0}".format(aid)

    # heartb1
    cid = "27779c56-d019-4aa7-ac35-d7ad10807b0a"
    print "ComponentID (cid): {0}".format(cid)
    file1 = "/home/root/remoteDevHBRec.inf"
    # emot1
    cid2 = "d353c82d-fd53-4a25-823a-1d0da77c6da2"
    print "ComponentID (cid2): {0}".format(cid2)
    file2 = "/home/root/remoteDevEMORec.inf"

    # Something about the UTC
    #now = datetime.datetime.utcnow()
    #print now
    #epochMilli = unix_time_millis(now)
    #epochMilli = unix_time(now)
    #epochMilli = epochMilli * 1000 - 80000
    #print epochMilli
    
    # for while-loop test
    epochMilli = -8
    while True:
        o = get_observations_from_datetime(aid, device_id, cid, epochMilli)
        print_observation_to_file(o, file1)
        o = get_observations_from_datetime(aid, device_id, cid2, epochMilli)
        print_observation_to_file(o, file2)
        time.sleep(5)

def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()

def unix_time_millis(dt):
    return unix_time(dt) * 1000.0


def get_user_headers():
    headers = {
        'Authorization': 'Bearer ' + g_user_token,
        'content-type': 'application/json'
    }
    #print "Headers = " + str(headers)
    return headers


def get_device_headers():
    headers = {
        'Authorization': 'Bearer ' + g_device_token,
        'content-type': 'application/json'
    }
    #print "Headers = " + str(headers)
    return headers


def check(resp, code):
    if resp.status_code != code:
        print "Expected {0}. Got {1} {2}".format(code, resp.status_code, resp.text)
        sys.exit(1)


# Given a username and password, get the user token
def get_token(username, password):
    url = "{0}/auth/token".format(base_url)
    headers = {'content-type': 'application/json'}
    payload = {"username": username, "password": password}
    data = json.dumps(payload)
    print "data = " + data
    resp = requests.post(url, data=data, headers=headers, proxies=proxies, verify=verify)
    check(resp, 200)
    js = resp.json()
    token = js['token']
    return token


# given a user token, get the user_id
def get_user_id():
    url = "{0}/auth/tokenInfo".format(base_url)
    resp = requests.get(url, headers=get_user_headers(), proxies=proxies, verify=verify)
    check(resp, 200)
    js = resp.json()
    #print js
    user_id = js["payload"]["sub"]
    return user_id


# given a user_id, get the account_id of the associated account with account_name
# if there are multiple accounts with the same name, return one of them
def get_account_id(user_id, account_name):
    url = "{0}/users/{1}".format(base_url, user_id)
    resp = requests.get(url, headers=get_user_headers(), proxies=proxies, verify=verify)
    check(resp, 200)
    js = resp.json()
    if 'accounts' in js:
        accounts = js["accounts"]
        for k, v in accounts.iteritems():
            if 'name' in v and v["name"] == account_name:
                return k
    print "Account name {0} not found.".format(account_name)
    print "Available accounts are: {0}".format([v["name"] for k, v in accounts.iteritems()])
    return None

#get_observations
def get_observations_from_datetime(account_id, device_id, component_id, epoch_ts):
    url = "{0}/accounts/{1}/data/search".format(base_url, account_id)
    #epoch_string = "{0}".format(epoch_ts)
    epoch_string = -8
    print epoch_string
    search = {
        "from": epoch_string,
        "targetFilter": {
            "deviceList": [device_id]
        },
        "metrics": [
            {
                "id": component_id
            }
        ]
        # This will include lat, lon and alt keys
        #,"queryMeasureLocation": True
    }
    data = json.dumps(search)
    resp = requests.post(url, data=data, headers=get_user_headers(), proxies=proxies, verify=verify)
    check(resp, 200)
    js = resp.json()
    return js



def print_observation_to_file(js, fileName):  # js is result of /accounts/{account}/data/search
    fo = open(fileName, "wb")
    if 'series' in js:
        series = js["series"]
        series = sorted(series, key=lambda v: v["deviceName"])
        for v in series:
            print "FName: {2} Device: {0} Count: {1}".format(v["deviceName"], len(v["points"]), fileName)
            #print "points= {0}".format(v["points"]);
            points = v["points"]
            for pv in points:
                outStr =  "timestamp: {0} value: {1}".format(pv["ts"], pv["value"])
                fo.write(outStr + "\n");               
                #print outStr

    fo.close()        



if __name__ == "__main__":
    main()
