# Things to be done in this program
# 1. Enter the required regions in the regions list -> <'Region1'>,<'Region2'>,..
# 2. Enter the <sns region name>
# 3. Enter the <SNS Topic ARN>
# 4. Enter the <account_id> 

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
   snp = ""
   for region in regions:
     snp=delete_unused_snapshots(region,snp)
  if snp:
    notify(snp)     
     

def delete_unused_snapshots(region,snp):   
    client = boto3.client('ec2',region_name=region)
    snapshots = client.describe_snapshots(OwnerIds=['<account_id>'])
    for snapshot in snapshots['Snapshots']:
        creation_time= snapshot['StartTime']
        creation_date=creation_time.date()
        current_date=datetime.datetime.now().date()
        days_launched=(current_date-creation_date).days
        if days_launched > 3:
          client.delete_snapshot(SnapshotId=snapshot['SnapshotId'])
        elif snp == "":
          snp = snp + "\nSnapshots in SandBox account\n"       
          snp = snp + f"SnapshotId: {snapshot['SnapshotId']}, Region: {region}, Days_Launched: {days_launched} \n"
        else:
          snp= snp + f"SnapshotId: {snapshot['SnapshotId']}, Region: {region}, Days_Launched: {days_launched} \n"
    return snp 
            
      
        
 