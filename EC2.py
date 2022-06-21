# Things to be done in this program
# 1. Enter the required regions in the regions list
# 2. Enter the SNS region name
# 3. Enter the SNS topic ARN

import boto3
import logging
import re
from datetime import datetime,timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

date= datetime.now()
past_time = datetime.now() - timedelta(days=5)
regions = [<'Region1'>,<'Region2'>]

# Function for sns notification
def notify(msg):
    sendclient = boto3.client('sns', region_name="<sns region name>")
    try:
        sendclient.publish(
            TopicArn="<SNS Topic ARN>",
            Message=("AutoTermination Enabled Instances in your account \n" + msg +"These Stopped Instances will be AutoTerminated!"),
            Subject="Stopped Instances will be terminiated"
            )
    except ClientError as err:
        logging.info(err)
        return False

def lambda_handler(event, context):
    msg = ""
    for region in regions:
       msg = terminate_stopped_instance(region,msg)
    if msg:
      notify(msg)
        
def terminate_stopped_instance(region,msg):
    client = boto3.client("ec2", region_name=region)
    
    filters = [{
            'Name': 'tag:AutoTerminate',
            'Values': ['yes']
        },
        {
            'Name': 'instance-state-name', 
            'Values': ['stopped']
        }
    ]

    # fetch information about all the instances
    status = client.describe_instances(Filters=filters)
    for i in status["Reservations"]:
        instance_details = i["Instances"][0]
        #if instance_details["InstanceId"] in stopped_Instances:
        stopped_time = (re.findall("\((.*?) *\)", instance_details["StateTransitionReason"])[0]).replace(' GMT', '')
        stop_time = datetime.strptime(stopped_time, "%Y-%m-%d %H:%M:%S") + timedelta(hours=5,minutes=30)
        termination_date = (stop_time + timedelta(days=5)).date()
        
        # Checking for the user name
        tags=client.describe_tags( Filters=[
        {
            'Name': 'resource-id',
            'Values': [instance_details['InstanceId']],
        }])

        user = "None"
       
        # Getting the usename from the tags
        for tag in tags["Tags"]:
          if(tag.get("Key") =="CreatedBy"):
              user = tag.get("Value").split('@')[0]
                
        # Deletes the past instances over 5 days 
        if (past_time > stop_time):
            client.terminate_instances(InstanceIds = [instance_details["InstanceId"]])
        else:
            msg = msg + (f"User: {user}, Region: {region}, Instance_Id: {instance_details['InstanceId']}, Termination Date: {termination_date} \n")

    return msg      
