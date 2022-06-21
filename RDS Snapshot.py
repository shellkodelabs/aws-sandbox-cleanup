# Things to be done in this program
# 1. Enter the required regions in the regions list -> <'Region1'>,<'Region2'>,..
# 2. Enter the <sns region name>
# 3. Enter the <SNS Topic ARN>

import boto3
import json
import datetime
from dateutil.parser import parse
import logging

# client = boto3.client('ec2')
current_date = (datetime.datetime.now()).date()
regions = [<'Region1'>,<'Region2'>]

# SNS Notification
def notify(msg):
    sendclient = boto3.client('sns', region_name="<sns region name>")
    try:
        sendclient.publish(
            TopicArn="<SNS Topic ARN>",
            Message=(msg +"\nUnused rds snapshots more than 3 days will be Autoterminated!\n"),
            Subject="Unused RDS Snapshots will be AutoTerminated"
            )
    except ClientError as err:
        logging.info(err)
        return False

def lambda_handler(event, context):
   rds_snp = "" 
   for region in regions:
     rds_snp =delete_unused_rds_snapshots(region,rds_snp)
   if rds_snp:
     notify(rds_snp)   
      

def delete_unused_rds_snapshots(region,snp):
    client = boto3.client('rds', region_name=region)
    
    # Describing DB Snapshots
    snapshots = client.describe_db_snapshots(SnapshotType="manual")
    for snapshot in snapshots['DBSnapshots']:
        creation_time= snapshot['SnapshotCreateTime']
        creation_date=creation_time.date()
        days_launched=(current_date-creation_date).days
        if days_launched >= 3:
          logging.info(f"The snapshotID-{snapshot['DBSnapshotIdentifier']} have been deleted") 
          client.delete_db_snapshot(DBSnapshotIdentifier=snapshot['DBSnapshotIdentifier'])
        elif snp == "":
          snp = snp + "\nRDS Snapshots in SandBox account\n"       
          snp = snp + f"SnapshotId: {snapshot['DBSnapshotIdentifier']},Type: DBInstance, Region: {region}, Days_Launched: {days_launched} \n"
        else:
          snp = snp + f"SnapshotId: {snapshot['DBSnapshotIdentifier']}, Type: DBInstance, Region: {region}, Days_Launched: {days_launched} \n"
   
    # Describing DB Cluster Snapshots
    cluster_snapshot = client.describe_db_cluster_snapshots(SnapshotType="manual")
    for snapshot in cluster_snapshot['DBClusterSnapshots']:
        creation_time= snapshot['SnapshotCreateTime']
        creation_date=creation_time.date()
        days_launched=(current_date-creation_date).days
        if days_launched >= 3:
            logging.info(f"The snapshotID-{snapshot['DBClusterSnapshotIdentifier']} have been deleted")
            client.delete_db_cluster_snapshot(DBClusterSnapshotIdentifier=snapshot['DBClusterSnapshotIdentifier'])
        elif snp == "":
          snp = snp + "\nRDS Snapshots in SandBox account\n"       
          snp = snp + f"SnapshotId: {snapshot['DBClusterSnapshotIdentifier']}, Type: DBCluster, Region: {region}, Days_Launched: {days_launched} \n"
        else:
          snp = snp + f"SnapshotId: {snapshot['DBClusterSnapshotIdentifier']}, Type: DBCluster, Region: {region}, Days_Launched: {days_launched} \n"
    return snp 