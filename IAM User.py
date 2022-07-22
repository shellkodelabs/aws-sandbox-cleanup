# Things to be done in this program
# 1. Enter the SNS region name
# 2. Enter the SNS topic ARN

import json
import boto3
from datetime import datetime,timedelta
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
date= datetime.now().date()


# SNS Notification
def notify(msg):
    sendclient = boto3.client('sns', region_name="<sns region name>")
    try:
        sendclient.publish(
            TopicArn="<SNS Topic ARN>",
            Message=( msg +"\n⏳These unused IAM users for more than 7️⃣ days will be AutoTerminated⏰\n"),
            Subject="Unused IAM Users will be Autoterminiated"
            )
    except ClientError as err:
        logging.info(err)
        return False

def lambda_handler(event, context):
    msg= ""
    msg=delete_unused_user(msg)
    if msg:
      notify(msg)
        

def delete_unused_user(msg):
  client = boto3.client("iam")
  iam = boto3.resource("iam") 
  users = iam.users.all()
  for user in users:
      created_days = (date-(user.create_date).date()).days
      key_last_days = None
      pass_last_date = user.password_last_used
      if pass_last_date:
        pass_last_days = (date-(pass_last_date).date()).days
        if msg == "":
           msg = msg + "\n Unused IAM Users \n"  
      else:   
        pass_last_days = None
        
      access_response = client.list_access_keys(UserName=user.name)
      
      # Having both Console and CLI Access
      if access_response['AccessKeyMetadata']:
        if msg == "":
           msg = msg + "\n Unused IAM Users \n" 
        access_key_creation_date = access_response['AccessKeyMetadata'][0]['CreateDate'].date()
        access_key_id = access_response['AccessKeyMetadata'][0]['AccessKeyId']
        cli_response=client.get_access_key_last_used(AccessKeyId= access_key_id) 
        
        # Getting Keys age
        if(cli_response['AccessKeyLastUsed'].get('LastUsedDate')):
          key_last_date =(cli_response['AccessKeyLastUsed']['LastUsedDate']).date()
          key_last_days = (date - key_last_date).days
        else:
          key_last_days = None
       
        if pass_last_days == None and key_last_days == None:
          msg = msg + f"Username: {user.name}, Days_launched: {created_days}, AccessKey_Unused_days: {key_last_days}, Password_Unused_Days: {pass_last_days} \n"
          if created_days > 7:
            delete_user(user.name,access_key_id)
        elif  pass_last_days == None and key_last_days != None:
          msg = msg + f"Username: {user.name}, Days_launched: {created_days}, AccessKey_Unused_days: {key_last_days}, Password_Unused_Days: {pass_last_days} \n" 
          if key_last_days > 7:
            delete_user(user.name,access_key_id)
        elif  pass_last_days != None and key_last_days == None:
          msg = msg + f"Username: {user.name}, Days_launched: {created_days}, AccessKey_Unused_days: {key_last_days}, Password_Unused_Days: {pass_last_days} \n" 
          if pass_last_days > 7:
            delete_user(user.name,access_key_id)
        else:
          msg = msg + f"Username: {user.name}, Days_launched: {created_days}, AccessKey_Unused_days: {key_last_days}, Password_Unused_Days: {pass_last_days} \n" 
          if pass_last_days > 7 and key_last_days > 7:
              delete_user(user.name,access_key_id)
      else:
        # Having only Console access
        msg = msg + f"Username: {user.name}, Days_launched: {created_days}, AccessKey_Unused_days: {key_last_days}, Password_Unused_Days: {pass_last_days} \n"
        if pass_last_days == None:
          if created_days > 7:
            delete_user(user.name,access_key_id=None)
            
        elif pass_last_days > 7:
              delete_user(user.name,access_key_id=None)
        
  
  return msg
  
def delete_user(user_name, access_key_id):
  client = boto3.client("iam")
  
  #Condition 1
  try:
    client.delete_login_profile(UserName=user_name)
  except:
    logging.info(f"No login profile for the user {user_name}")
  
  #Condition 2
  if access_key_id != None:
    client.delete_access_key(UserName=user_name, AccessKeyId=access_key_id)
  
  #Condition 3
  response = client.list_signing_certificates(UserName=user_name)
  if response['Certificates']:
    cert_id = response['Certificates'][0]['CertificateId']
    client.delete_signing_certificate(CertificateId=cert_id)

  #Condition 4
  response = client.list_ssh_public_keys(UserName=user_name)
  if response['SSHPublicKeys']:
    ssh_key = response['SSHPublicKeys'][0]['SSHPublicKeyId']
    client.delete_ssh_public_key(UserName=user_name, SSHPublicKeyId=ssh_key)
    
  #Condition 5
  response = client.list_service_specific_credentials(UserName=user_name)
  if response['ServiceSpecificCredentials']:
    service_id = response['ServiceSpecificCredentials'][0]['ServiceSpecificCredentialId']
    client.delete_service_specific_credential(UserName=user_name, ServiceSpecificCredentialId=service_id)
    
  #Condition 6
  response = client.list_mfa_devices(UserName=user_name)
  if response['MFADevices']:
    serial_no = response['MFADevices'][0]['SerialNumber']
    client.deactivate_mfa_device(UserName=user_name, SerialNumber=serial_no)
    client.delete_virtual_mfa_device(SerialNumber=serial_no)
  
  #Condition 7
  response = client.list_user_policies(UserName=user_name)
  if response['PolicyNames']:
    policy_names = response['PolicyNames']
    for policy in policy_names:
      client.delete_user_policy(UserName=user_name, PolicyName=policy)
    
  # Condition 8
  response=client.list_attached_user_policies(UserName=user_name)
  if response['AttachedPolicies']:
    policy_arns = response['AttachedPolicies']
    for policy in policy_arns:
     policy_arn = policy['PolicyArn']
     client.detach_user_policy(UserName=user_name, PolicyArn=policy_arn)
    
  #Condition 9
  response = client.list_groups_for_user(UserName=user_name)
  if response['Groups']:
    group_name = response['Groups'][0]['GroupName']
    client.remove_user_from_group(GroupName=group_name, UserName=user_name)
    
  #Condition 10
  response=client.delete_user(UserName=user_name)
