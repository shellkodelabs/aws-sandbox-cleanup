# Things to be done in this program
# 1. Enter the required regions in the regions list -> <'Region1'>,<'Region2'>,..
# 2. Enter the <sns region name>
# 3. Enter the <SNS Topic ARN>

import boto3
import json
import datetime
from dateutil.parser import parse

# client = boto3.client('ec2')
current_date = datetime.datetime.now()
regions = [<'Region1'>,<'Region2'>]

# SNS Notification
def notify(msg):
    sendclient = boto3.client('sns', region_name="<sns region name>")
    try:
        sendclient.publish(
            TopicArn="<SNS Topic ARN>",
            Message=(msg +"\nUnused resources more than 3 days will be Autoterminated!\n"),
            Subject="Unused Snapshots will be AutoTerminated"
            )
    except ClientError as err:
        logging.info(err)
        return False
   
def lambda_handler(event, context):
   ami_msg= ""
   for region in regions:
     ami_msg=delete_unused_ami(region,ami_msg)
   if ami_msg:
    notify(ami_msg)     
     
def delete_unused_ami(region,msg):       
   ec2 = boto3.client('ec2',region_name=region)
   amis = ec2.describe_images(Owners=['self'])  
   for ami in amis['Images']:
      creation_date = parse(ami['CreationDate'].split('T')[0])
      days_launched = (current_date-creation_date).days
      if(days_launched) > 3:
         ec2.deregister_image(ImageId=ami['ImageId'])
      elif msg == "":
         msg = msg + "\nAMI's in SandBox account\n"       
         msg = msg + f"Name: {ami['Name']}, Region: {region}, Days_Launched: {days_launched} \n"
      else:
          msg=msg + f"Name: {ami['Name']}, Region: {region}, Days_Launched: {days_launched} \n"
   return msg 

    
 
            
      
        
 