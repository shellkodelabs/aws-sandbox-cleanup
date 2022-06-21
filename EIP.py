# Things to be done in this program
# 1. Enter the required regions in the regions list
# 2. Enter the SNS topic ARN

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
    sendclient = boto3.client('sns', region_name="us-east-1")
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
    eip = ""
    for region in regions:
        eip=elastic_ips_cleanup(region,eip)
    if eip:
      notify(eip)    

def elastic_ips_cleanup(region,eip):
    ec2 = boto3.client('ec2', region_name=region)
    addresses_dict = ec2.describe_addresses()
    unused_eip_tag = "No"
    for eip_dict in addresses_dict['Addresses']:
        if "InstanceId" and "NetworkInterfaceId" not in eip_dict:
              for tag in eip_dict['Tags']:
                if(tag.get("Key") ==key ):
                  unused_eip_tag = "Yes"
                  unused_fdate = tag.get("Value")
                  user = [tag.get("Value").split('@')[0] for tag in eip_dict['Tags'] if tag.get("Key") =="CreatedBy"]
                  termination_time = (datetime.strptime(unused_fdate, "%Y-%m-%d") + timedelta(days=5)).date()
                  if current_time >= termination_time:
                    try:
                      ec2.release_address(AllocationId=eip_dict['AllocationId'])
                    except Exception as e:
                      print(f"Unable to release eip {eip_dict['AllocationId']}" +str(e))
                  elif eip == "":
                    eip = eip + "\nUnused EIP: \n"       
                    eip = eip + f"User: {user[0]}, Region: {region}, EIP: {eip_dict['AllocationId']}, Termination Time: {termination_time} \n"
                  else:
                    eip = eip + f"User: {user[0]}, Region: {region}, EIP: {eip_dict['AllocationId']}, Termination Time: {termination_time} \n"
                  
              if unused_eip_tag == "No":
                ec2.create_tags(Resources=[eip_dict['AllocationId'],], Tags=[{'Key': key, 'Value': value },])
                logging.info(f"Tag created for the EIP-{eip_dict['AllocationId']}")
        else:
          if any(tag.get('Key') == key for tag in eip_dict['Tags']):
              ec2.delete_tags(Resources=[eip_dict['AllocationId'],], Tags=[{'Key': key, 'Value': value },])
    return eip