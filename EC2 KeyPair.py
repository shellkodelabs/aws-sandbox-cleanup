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
    kp = ""
    for region in regions:
        kp=delete_unused_keypair(region,kp)
    if kp:
      notify(kp)    

def delete_unused_keypair(region,kp):
    ec2 = boto3.client('ec2', region_name=region)
    all_key_pairs = []
    all_used_key_pairs = []
    all_unused_key_pairs = []
    unused_kp_tag = "No"
    all_key_pairs = list(map(lambda i: i['KeyName'], ec2.describe_key_pairs()['KeyPairs']))
    # Each EC2 reservation returns a group of instances.
    instance_groups = list(map(lambda i: i['Instances'], ec2.describe_instances()['Reservations']))
    
    # Create a list of all used key pairs in the account based on the running instances
    for group in instance_groups:
      for val in group:
        if 'KeyName' in val:
          if val['KeyName'] not in all_used_key_pairs:
            all_used_key_pairs.append(val['KeyName'])  
    
    all_unused_key_pairs = list(set(all_key_pairs) - set(all_used_key_pairs))  
    unusd_key_pairs =  ec2.describe_key_pairs(KeyNames=all_unused_key_pairs)['KeyPairs']
    usd_key_pairs = ec2.describe_key_pairs(KeyNames=all_used_key_pairs)['KeyPairs']
    
    # Removing the UnusedFDate in used keypairs if it presents.
    for values in usd_key_pairs:
      if values['Tags']:
        for keys in values['Tags']:
           if(keys.get('Key') == key):
                ec2.delete_tags(Resources=[values['KeyPairId'],], Tags=[{'Key': key, 'Value': value },])
                logging.info(f"Tag Deleted for the key_pair-{values['KeyPairId']}")
    
    for values in unusd_key_pairs:
      if values['Tags']:
        for keys in values['Tags']:
          if(keys.get('Key')==key):
            unused_kp_tag = "Yes"
            unused_fdate = keys.get("Value")
            kp_name = values['KeyName']
            termination_time = (datetime.strptime(unused_fdate, "%Y-%m-%d") + timedelta(days=5)).date()
            if current_time >= termination_time:
              ec2.delete_key_pair(KeyName=kp_name)
            elif kp == "":
              kp = kp + "\nUnused KeyPairs: \n"       
              kp = kp + f"Keypair Name: {kp_name}, Region: {region}, Termination Time: {termination_time} \n"
            else:
              kp = kp + f"Keypair Name: {kp_name}, Region: {region}, Termination Time: {termination_time} \n"

      if unused_kp_tag == "No":
        ec2.create_tags(Resources=[values['KeyPairId'],], Tags=[{'Key': key, 'Value': value },])
        logging.info(f"Tag created for the key_pair-{values['KeyPairId']}")
    return kp
