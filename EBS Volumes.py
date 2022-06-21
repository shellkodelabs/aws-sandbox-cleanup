# Things to be done in this program
# 1. Enter the required regions in the regions list
# 2. Enter the SNS region name
# 3. Enter the SNS topic ARN

import boto3
import logging
from datetime import datetime,timedelta
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
date= datetime.now() 
current_time = (datetime.now()).date()

# Regions to find the unused resources
regions = [<'Region1'>,<'Region2'>]

# key and value for Unused Date
key="Unused_date"
value= str(date.date())

# SNS Notification
def notify(msg):
    sendclient = boto3.client('sns', region_name="<sns region name>")
    try:
        sendclient.publish(
            TopicArn="<SNS Topic ARN>",
            Message=("Unused Resources in your account \n" + msg +"\nThese Unused resources will be AutoTerminated! \n"),
            Subject="Unused Resources will be Autoterminiated"
            )
    except ClientError as err:
        logging.info(err)
        return False
        
def lambda_handler(event, context):
    vol = ""
    for region in regions:
        vol=delete_unused_volume(region,vol)
    if vol:
      notify(vol)    

def delete_unused_volume(region,vol):
    # To add, describe and delete the tags
    ec2_v = boto3.client('ec2', region_name=region)
    unused_ebs_tag = "No"
    # To describe and delete the volume
    ec2 = boto3.resource('ec2', region_name=region)
    volumes = ec2.volumes.all()
  
    # Volumes to be terminated are added in in the list
    to_terminate=[]
    for volume in volumes:
       # Checks for the volume attachments
        if len(volume.attachments) == 0:
            to_terminate.append(volume)
        else:
            ec2_v.delete_tags(Resources=[volume.id],Tags=[{"Key": key}])
            
    if to_terminate:
        for volume in to_terminate:
            tags=ec2_v.describe_tags( Filters=[
                {
                    'Name': 'resource-id',
                    'Values': [volume.id],
                }])            
            for tag in tags['Tags']:
                if(tag.get("Key") ==key ):
                  unused_ebs_tag = "Yes"
                  unused_fdate = tag.get("Value")
                  user = [tag.get("Value").split('@')[0] for tag in tags['Tags'] if tag.get("Key") =="CreatedBy"]
                  termination_time = (datetime.strptime(unused_fdate, "%Y-%m-%d") + timedelta(days=5)).date()
                  if current_time >= termination_time:
                    volume.delete()                 
                  elif vol == "":
                    vol = vol + "\nUnused Volumes: \n"       
                    vol = vol + f"User: {user[0]}, Region: {region}, Volume: {volume.id}, Termination Time: {termination_time} \n"
                  else:
                    vol = vol + f"User: {user[0]}, Region: {region}, Volume: {volume.id}, Termination Time: {termination_time} \n"
                  
            if unused_ebs_tag == "No":
              volume.create_tags(DryRun=False,Tags=[{'Key': key,'Value': value},])
              logging.info(f"Tag created for the volume-{volume.id}")
                  
    return vol              
