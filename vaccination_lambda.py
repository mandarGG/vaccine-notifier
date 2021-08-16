import requests
import json
import os
import datetime
from dotenv import load_dotenv

load_dotenv()
mode = os.environ['mode']
CHAT_ID = os.environ['CHAT_ID']
TELE_TOKEN = os.environ['TELE_TOKEN']



def send_telegram_message(text):
    URL = "https://api.telegram.org/bot{}/".format(TELE_TOKEN)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, CHAT_ID)
    requests.get(url)


def get_availability_by_district(district_id, date, pincodes=[]):
    headers = {
        'Accept':'application/json',
        'Host': 'cdn-api.co-vin.in',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0'
    }
    #API to get planned vaccination sessions for 7 days from a specific date in a given district.
    district_url = 'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={dist}&date={dt}'.format(
        dist=district_id, dt=date)

    print("Request Log", district_url, headers)
    print("\n")
    response = requests.get(district_url, headers=headers, timeout=3)

    full_message = ""
    if response.status_code == 200:
        response = response.json()
        #Testing
        if mode == 'dev':
            response['centers'].append(
                {
                    "center_id": 123456,
                    "name": "Test1 Covaxin-1 18 To 44",
                    "address": "Test1 Addr Covaxin-1 18 To 44",
                    "state_name": "Maharashtra",
                    "district_name": "Nanded",
                    "block_name": "Nanded",
                    "pincode": 431604,
                    "lat": 19,
                    "long": 77,
                    "from": "09:30:00",
                    "to": "17:30:00",
                    "fee_type": "Free",
                    "sessions": [
                        {
                            "session_id": "d47a5a2e-eda0-45fa-8bd3-19abb8ced5bc",
                            "date": "23-05-2021",
                            "available_capacity": 1,
                            "min_age_limit": 18,
                            "vaccine": "COVAXIN",
                            "slots": [
                                "09:30AM-11:30AM",
                                "11:30AM-01:30PM",
                                "01:30PM-03:30PM",
                                "03:30PM-05:30PM"
                            ]
                        }
                    ]
                }
            )
            response['centers'].append({
                    "center_id": 123457,
                    "name": "Test2 Covaxin-1 18 To 44",
                    "address": "Test2 Addr Covaxin-1 18 To 44",
                    "state_name": "Maharashtra",
                    "district_name": "Nanded",
                    "block_name": "Nanded",
                    "pincode": 431605,
                    "lat": 19,
                    "long": 77,
                    "from": "09:30:00",
                    "to": "17:30:00",
                    "fee_type": "Free",
                    "sessions": [
                        {
                            "session_id": "d47a5a2e-eda0-45fa-8bd3-19abb8ced5bc",
                            "date": "23-05-2021",
                            "available_capacity": 2,
                            "min_age_limit": 45,
                            "vaccine": "COVISHIELD",
                            "slots": [
                                "09:30AM-11:30AM",
                                "11:30AM-01:30PM",
                                "01:30PM-03:30PM",
                                "03:30PM-05:30PM"
                            ]
                        }
                    ]
                })
        centers = response['centers']
        for each_center in centers:
            # for nanded, filter by centers in city only
            if each_center["block_name"] == "Nanded":
                sessions = each_center['sessions']
                for each_session in sessions:
                    #each date wise
                    if (((each_session['min_age_limit']==45) & (each_session['vaccine']=='COVISHIELD')) or ((
                        each_session['min_age_limit']==18) & (each_session['vaccine']=='COVAXIN'))) and each_session['available_capacity']:
                            #vaccine avl at this center
                            #send date, slots, age group, vaccine timing
                            this_center_message = """
                            'Date': {slot_date}
                            'Pincode' : {pincode}
                            'Center Name' : {name}
                            'Address' : {address}
                            'Slots Available': {slots}
                            'Min Age Limit': {age}
                            'Vaccine': {vaccine}
                            """.format(name=each_center['name'], address=each_center['address'],
                                slots=each_session['available_capacity'], pincode=each_center['pincode'],
                                age=each_session['min_age_limit'], vaccine=each_session['vaccine'], slot_date=each_session['date'])

                            full_message = full_message + this_center_message
        return full_message
    else:
        print("Status Code",  response.status_code)
        error_response = """
        Error Code: {code} 
        Error Message : {error_message}
        """.format(code=response.status_code, error_message=str(response.content.decode('utf-8')))
        print("Response",error_response )
        # send_telegram_message(error_response)


def lambda_handler(event, context):
    TODAY_DATE_OBJ = datetime.datetime.today()
    CURRENT_HOUR = TODAY_DATE_OBJ.hour
    CURRENT_DAY = TODAY_DATE_OBJ.day
    TOMORROW_DATE = (TODAY_DATE_OBJ + datetime.timedelta(days=1)).strftime('%d-%m-%Y')
    # #dont run code for today 8 PM IST to tomorrow 11:50 AM IST
    # if (14<=CURRENT_HOUR) and (CURRENT_HOUR<=11 and CURRENT_DAY):
    #     print("Time between 8PM to 11AM, code wont run")
    #     return {"message": "Skipped program run as per schedule"}
    #for nanded
    full_message = get_availability_by_district(382, TOMORROW_DATE)
    if full_message:
        print("Slots found, sending message")
        print(full_message)
        send_telegram_message(full_message)
    else:
        print("No slots available for Nanded!!!")


lambda_handler(None,None)
