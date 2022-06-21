# Things to be done in this program
# Enter the SNS region name
# Enter the SNS topic ARN

import json
import boto3
from datetime import datetime,timedelta
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

date= datetime.now() 
current_time = (datetime.now()).date()
past_time = (datetime.now() - timedelta(days=10)).date()
deletion_time = (datetime.now() - timedelta(days=15)).date()

# SNS Notification
def notify(msg):
    sendclient = boto3.client('sns', region_name="<sns region name>")
    try:
        sendclient.publish(
            TopicArn="<SNS Topic ARN>",
            Message=("Unused Resources in your account \n" + msg +"\n Unused Iam roles will be terminated after 30 days \n"),
            Subject="Unused IAM roles will be Autoterminiated"
            )
    except ClientError as err:
        logging.info(err)
        return False

def lambda_handler(event, context):
    rol = ""
    rol = delete_unused_role(rol)
    if rol:
     notify(rol)

def delete_unused_role(rol):
    iam = boto3.resource('iam')
    roles = iam.roles.all()
    client = boto3.client('iam')
    role = [client.get_role(RoleName=role.role_name) for role in roles] 
   
    for value in role:
      user = None
      usage = value['Role']['RoleLastUsed']
      role_name = value['Role']['RoleName']
      last_used = usage.get('LastUsedDate')
      tags = client.list_role_tags(RoleName=role_name)
      if tags['Tags']:
        user_name = [keys.get("Value") for keys in tags['Tags'] if keys.get("Key").lower()=="createdby" or keys.get("Key").lower()=="name"]
        if user_name:
           user = user_name[0].split('@')[0]
      region = usage.get('Region')
      if last_used != None:
        lst_usg = last_used.date()
        if ('awsservicerole' not in role_name.lower()):
            # Getting the unused roles for past 10 days
            if lst_usg < past_time:
                if rol == "":
                  rol = rol + "\nUnused IAM Roles: \n"       
                  rol = rol + f"User: {user}, Role Name: {role_name}, Region: {region}, Last_unused: {lst_usg} \n"
                else:   
                  rol = rol + f"User: {user}, Role Name: {role_name}, Region: {region}, Last_unused: {lst_usg} \n"
            
            # Deleting the unused roles for past 15 days
            if lst_usg < deletion_time:
                unused_role = iam.Role(role_name)
                response = client.list_instance_profiles_for_role(RoleName=role_name)
                if(response['InstanceProfiles']):
                    instance_profile_name = response['InstanceProfiles'][0]['InstanceProfileName']
                   # Removing roles from from the instance profile
                    if instance_profile_name != None:
                        try:
                          client.remove_role_from_instance_profile(
                              InstanceProfileName=instance_profile_name,
                              RoleName=role_name)
                        except Exception as e:
                          logging.info(f"Unable to delete profile" +str(e))
                
                
                # Detaching policies from the role  
                policies = unused_role.attached_policies.all()
                arns = [policy.arn for policy in policies]
                for arn in arns:
                  unused_role.detach_policy(PolicyArn=arn)
                  
                # Deleting the inline policies from the role
                response = client.list_role_policies(RoleName=role_name)
                for inl_pol in response['PolicyNames']:
                   client.delete_role_policy(RoleName=role_name, PolicyName=inl_pol)

               # Deleting the role
                try:
                  client.delete_role(RoleName=role_name)
                except Exception as e:
                  logging.info(f"Not able to Delete! {role_name}" +str(e))

        
    return rol