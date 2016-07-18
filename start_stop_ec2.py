# coding:utf-8

import requests
import json
import pytz
from datetime import date,datetime
import get_holiday
import boto3
import logging

KINTONE_URL = 'https://YOUR_DOMAIN.cybozu.com/k/v1/records.json?app=00'
HEADERS_KEY = 'X-Cybozu-API-Token'
HEADERS_VALUE = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

SQS_URL = 'https://sqs.ap-northeast-1.amazonaws.com/1234567890/start_stop_ec2_queue'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def getWeekDayStr(dt_arg):
    week_day_str = ''
    week_day = dt_arg.weekday()
    if week_day == 0:
        week_day_str = u'月'
    elif week_day == 1:
        week_day_str = u'火'
    elif week_day == 2:
        week_day_str = u'水'
    elif week_day == 3:
        week_day_str = u'木'
    elif week_day == 4:
        week_day_str = u'金'
    elif week_day == 5:
        week_day_str = u'土'
    elif week_day == 6:
        week_day_str = u'日'
    return week_day_str

def checkValidate(type_str,record):
    field_name = ''
    field_value = ''
    if type_str == 'start':
        field_name = 'c_start_check'
        field_value = u'開始'
    elif type_str == 'stop':
        field_name = 'c_stop_check'
        field_value = u'停止'
    check_item = record[field_name]['value']
    if len(check_item) > 0:
        if check_item[0] == field_value:
            return True
    return False

def checkDate(type_str,record,holidays,date_str,week_day_str):
    field_name = ''
    if type_str == 'start':
        field_name = 'c_start_week_day'
    elif type_str == 'stop':
        field_name = 'c_stop_week_day'
    week_day_array = record[field_name]['value']
    if len(week_day_array) > 0:
        if u'祝' in week_day_array and date_str in holidays:
            return True
        elif week_day_str in week_day_array:
            if u'祝' in week_day_array:
                return True
            else:
                if date_str not in holidays:
                    return True
    return False

def checkItem(type_str,record,time_str):
    field_name = ''
    if type_str == 'start':
        field_name = 't_start_time'
    elif type_str == 'stop':
        field_name = 't_stop_time'
    check_time = record[field_name]['value']
    if time_str[0:4] == check_time[0:4]:
        return True
    return False

def getQueueList():
    now = datetime.now(pytz.timezone('Asia/Tokyo'))
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime("%H:%M")
    week_day_str = getWeekDayStr(now)
    headers = {HEADERS_KEY:HEADERS_VALUE}
    response_record = requests.get(KINTONE_URL,headers=headers)
    record_data = json.loads(response_record.text)
    records=record_data['records']
    holidays = get_holiday.getHolidays()
    queue_list = []
    for record in records:
        ec2_name = record['s_ec2_name_tag']['value']
        for type_str in ['start','stop']:
            if checkValidate(type_str,record):
                if checkDate(type_str,record,holidays,date_str,week_day_str):
                    if checkItem(type_str,record,time_str):
                        queue_list.append({'type':type_str,'ec2_name':ec2_name,'datetime':date_str + ' ' + time_str})
    return queue_list

def set_enqueue(queue_list):
    try:
        sqs_client = boto3.client('sqs')
        for queue in queue_list:
            response = sqs_client.send_message(
                QueueUrl = SQS_URL,
                MessageBody = json.dumps(queue)
            )
    except Exception as e:
        logger.info(e)

def handler(event, context):
    try:
        queue_list = getQueueList()
        if len(queue_list) > 0:
            set_enqueue(queue_list)

    except Exception as e:
       logger.info(e)
       raise e
