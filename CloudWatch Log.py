# Things to be done in this program
# 1. Enter the required regions name in the regions list

import json
import boto3
from datetime import datetime,timedelta
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
current_date= datetime.now()

regions = [<'Region1'>,<'Region2'>]

def lambda_handler(event, context):
   for region in regions:
     delete_unused_logs(region)

def delete_unused_logs(region):
 
  client = boto3.client('logs',region_name=region)
  response = client.describe_log_groups()
  for logs in response['logGroups']:
    quit = False
    ms=logs['creationTime']/1000
    group_name = logs['logGroupName']
    created_date=datetime.fromtimestamp(ms)
    created_days = (current_date - created_date).days
    if created_days > 15:
      event_response=client.describe_log_streams(logGroupName=group_name, orderBy='LastEventTime', descending=True)
      events = event_response['logStreams']
      for index,event in enumerate(events):
        if 'lastEventTimestamp' in event:
          if((current_date-datetime.fromtimestamp(event['lastEventTimestamp']/1000)).days > 15):
            if index == 0:
              client.delete_log_group(logGroupName=group_name)
              logging.info(f"Deleted Log group {group_name}")
              quit = True
            else:
              client.delete_log_stream(logGroupName=group_name,logStreamName=event['logStreamName'])
              logging.info(f"Deleted Log stream{event['logStreamName']}")
              
        else:
          # If single log stream with no events
          if index == 0:
            client.delete_log_group(logGroupName=group_name)
            quit = True
            logging.info(f"Deleted Log group {group_name}")
          else:
            client.delete_log_stream(logGroupName=group_name,logStreamName=event['logStreamName'])
            logging.info(f"Deleted Log stream{event['logStreamName']}")
        if quit == True:
          break
                          
 
  