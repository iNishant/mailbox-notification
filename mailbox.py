from __future__ import print_function

import json
from urlparse import urlparse, parse_qs
from botocore.vendored import requests

GOOGLE_SHEETS_API_KEY = "CHANGE"
GOOGLE_SHEET_ID = "CHANGE"
SENDGRID_API_KEY = "CHANGE"
SENDGRID_TEMPLATE_ID = "CHANGE"
MAX_ROOMS_PER_MESSAGE = 5


def getSheetDataForRange(range):
    # eg Sheet1!A1:D5
    url = (
        "https://sheets.googleapis.com/v4/spreadsheets/" +
        GOOGLE_SHEET_ID +
        "/values/" + range + "?key=" + GOOGLE_SHEETS_API_KEY
    )
    res = requests.get(url)
    jsonData = res.json()
    if 'values' in jsonData:
        return jsonData['values']
    return []


def getQueryJSON(requestQuery):
    # request query will be of form 'number=919790464014&message=312+Speed+Post&keyword=gangahostel&receiveTime=2018-12-12 02:00:04&circle=AIRTEL Tamil Nadu'
    url = 'https://google.com/?' + requestQuery
    # makes a dummy url
    parsed_url = urlparse(url)
    data = parse_qs(parsed_url.query)
    # but each value is in array so get index 0
    newDict = {}
    for key in data:
        newDict[key] = data[key][0]
    return newDict


def isSecurityGuard(number):
    # check in google sheets
    print("Checking if sender:" + number + " is security guard...")
    rows = getSheetDataForRange('Sheet1!C2:C6')
    allowedNumbers = [r[0] for r in rows]
    if number in allowedNumbers:
        return True
    return False


def getRooms(body):
    # check if message contains rooms or not
    # return array
    parts = body.replace(" ", "").split(",")
    rooms = []
    for r in parts:
        try:
            roomNo = int(r)
            # checks int to validate but returns string
            rooms.append(str(roomNo))
        except ValueError:
            continue
    return rooms


def getEmailsFromRooms(rooms):
    # check sheets and get room no, returns status and email
    print("Getting emails for rooms...")
    rows = getSheetDataForRange('Sheet1!A2:B500')
    emails = []  # 2d array
    allRooms = [row[0] for row in rows]
    allRollNos = [row[1] for row in rows]
    for r in rooms:
        emailsForRoom = []
        for i in range(len(allRooms)):
            if allRooms[i] == r:
                emailsForRoom.append(
                    allRollNos[i].lower() + '@smail.iitm.ac.in'
                )
        emails.append(emailsForRoom)
    return emails


def sendEmail(email, room):
    # send email using sendgrid
    print("Sending email...")
    jsonData = {
      "personalizations": [
        {
          "to": [
            {
              "email": email
            }
          ],
          "dynamic_template_data": {
            "roomNo": room,
          }
        }
      ],
      "from": {
        "email": "gangahostel59@gmail.com",
        "name": "Ganga Hostel Mailbox"
      },
      "template_id": SENDGRID_TEMPLATE_ID
    }
    payload = json.dumps(jsonData)
    authHeader = "Bearer " + SENDGRID_API_KEY
    headers = {
        'content-type': "application/json",
        'authorization': authHeader,
    }

    url = "https://api.sendgrid.com/v3/mail/send"
    response = requests.request("POST", url, data=payload, headers=headers)
    print(response.text)


def respond():
    return {
        'statusCode': '200',
        'body': json.dumps({'status': 'Success'}),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    requestBody = event['body']
    jsonParams = getQueryJSON(requestBody)
    # json params will have number (91....), message(room no .....)
    numberOfSender = jsonParams['number'][2:]
    if not isSecurityGuard(numberOfSender):
        print("Unauthorized! Not a security guard number")
        return respond()
    rooms = getRooms(jsonParams['message'])
    print("Got rooms: ", rooms)
    nRooms = len(rooms)
    if nRooms > MAX_ROOMS_PER_MESSAGE:
        print("Rooms more than limit of: " + str(MAX_ROOMS_PER_MESSAGE))
        return respond()
    initDataDict = {}
    # each key is room no, value is array of emails of inhabitants
    for r in rooms:
        initDataDict[r] = []
    emails2DArray = getEmailsFromRooms(rooms)
    print("Got emails: ", emails2DArray)
    for i in range(nRooms):
        room = rooms[i]
        emailArray = emails2DArray[i]
        for e in emailArray:
            sendEmail(e, room)
    return respond()
