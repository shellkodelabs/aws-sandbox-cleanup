# Things to be done in this program
# 1. Enter the regions in the list
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
    sgp = ""
    for region in regions:
        sgp=delete_unused_security_group(region,sgp)
    if sgp:
      notify(sgp)    

def delete_unused_security_group(region,v_sgp):
    ec2 = boto3.resource('ec2', region_name=region)
    ec2_sgp = boto3.client('ec2', region_name=region)
    sgps = list(ec2.security_groups.all())
    insts = list(ec2.instances.all())
    eni = list(ec2.network_interfaces.all())
    unused_sgp_tag = "No"
    
    all_sgps = [sg.group_name for sg in sgps]
    used_sgps = [sg['GroupName'] for inst in insts for sg in inst.security_groups]
    eni_sgps = [sg['GroupName'] for nw in eni for sg in nw.groups]
    for sgp in eni_sgps:
      if sgp not in used_sgps:
        used_sgps.append(sgp)
    unused_sgps = list(set(all_sgps) - set(used_sgps))
    
  # Remove UnusedFDate tag from used security groups
    for sgp in sgps:
      if sgp.group_name in used_sgps and sgp.tags:
          for keys in sgp.tags:
            if(keys.get('Key') == key):
              ec2_sgp.delete_tags(Resources=[sgp.group_id,], Tags=[{'Key': key, 'Value': value },])
              logging.info(f"UnusedFDate Tag deleted for the security group {sgp.group_name}")
    # Adding or Getting the UnusedFDate from Unused security groups        
    for sgp in sgps:
      if sgp.group_name in unused_sgps:
        if sgp.tags == None:
          ec2_sgp.create_tags(Resources=[sgp.group_id,], Tags=[{'Key': key, 'Value': value },])
          logging.info(f"Tag created for the EIP-{sgp.group_name}")
        else:
          for keys in sgp.tags:
            if(keys.get('Key') == key):
                unused_sgp_tag = "Yes"
                unused_fdate = keys.get('Value')
                termination_time = (datetime.strptime(unused_fdate, "%Y-%m-%d") + timedelta(days=5)).date()
                if current_time >= termination_time:
                  if sgp.group_name != "default": 
                    try:
                      ec2_sgp.delete_security_group(GroupId=sgp.group_id)
                    except Exception as e:
                      logging.info(f"Unable to delete sgp-id {sgp.group_id}" + str(e))
                elif v_sgp == "":
                  v_sgp = v_sgp + "\nUnused Security Groups: \n"       
                  v_sgp = v_sgp + f"Security-Group Name: {sgp.group_name}, Region: {region}, Termination Time: {termination_time} \n"
                else:
                  v_sgp = v_sgp + f"Security-Group Name: {sgp.group_name}, Region: {region}, Termination Time: {termination_time} \n"
               
          if unused_sgp_tag == "No":
            ec2_sgp.create_tags(Resources=[sgp.group_id,], Tags=[{'Key': key, 'Value': value },])
            logging.info(f"UnusedFDate Tag created for the security group {sgp.group_name}")
    return v_sgp
