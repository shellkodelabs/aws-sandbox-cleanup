# Things to be done in this program
# 1. Enter the SNS region name
# 2. Enter the SNS topic ARN

import json
import boto3
from datetime import datetime,timedelta
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

date = datetime.now()
current_time = date.date()

# key and value for Unused Date
key="Unused_date"
value= str(date.date())

# SNS Notification
def notify(msg):
    sendclient = boto3.client('sns', region_name="<sns region name>")
    try:
        sendclient.publish(
            TopicArn="<SNS Topic ARN>",
            Message=("Unused Resources in your account \n" + msg +"\n Unused Iam roles will be terminated after 30 days \n"),
            Subject="Unused IAM and Lambda will be Autoterminiated"
            )
    except ClientError as err:
        logging.info(err)
        return False

def lambda_handler(event, context):
    poli=""
    poli = delete_unused_policy(poli)
    if poli:
     notify(poli)

def delete_unused_policy(poli):
    iam = boto3.client("iam")
    response = iam.list_policies(Scope='Local')
    for policy in response['Policies']:
        if policy['AttachmentCount'] ==0 :
            tags = iam.list_policy_tags(PolicyArn=policy['Arn'])
            for tag in tags['Tags']:
                if(tag.get("Key") ==key ):
                  unused_fdate = tag.get("Value")
                  user = [tag.get("Value").split('@')[0] for tag in tags['Tags'] if tag.get("Key") =="CreatedBy"]
                  if user:
                    user_name = user[0]
                  else:
                    user_name = None
                  termination_time = (datetime.strptime(unused_fdate, "%Y-%m-%d") + timedelta(days=5)).date()
                  if current_time >= termination_time:
                    try:
                      response = iam.list_policy_versions(PolicyArn=policy['Arn'])
                      for version in response['Versions']:
                        if version['IsDefaultVersion'] != True:
                          iam.delete_policy_version(PolicyArn=policy['Arn'],VersionId=version['VersionId'])
                      iam.delete_policy(PolicyArn=policy['Arn'])
                    except Exception as e:
                      logging.info(f"Unable to delete policy {policy['Arn']}" +str(e))
                  elif poli == "":
                    poli = poli + "\nUnused policy: \n"       
                    poli = poli + f"User: {user_name}, policy name: {policy['PolicyName']}, Termination Date: {termination_time} \n"
                  else:
                    poli = poli + f"User: {user_name}, policy name: {policy['PolicyName']}, Termination Da: {termination_time} \n"
 
            if not any(tag.get('Key') == key for tag in tags['Tags']):
              iam.tag_policy(PolicyArn=policy['Arn'] , Tags=[{'Key': key, 'Value': value} ])
              logging.info(f"Tag created for the policy-{policy['PolicyName']}")
        else :
            tags = iam.list_policy_tags(PolicyArn=policy['Arn'])
            if(tag.get("Key") ==key for tag in tags['Tags']):
              iam.untag_policy(PolicyArn=policy['Arn'],TagKeys=[key])
    return poli              
