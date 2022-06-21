# Things to be done in this program
# 1. Enter the required regions in the regions list -> <'Region1'>,<'Region2'>,..
# 2. Enter the <sns region name>
# 3. Enter the <SNS Topic ARN>
import boto3
import logging
import re
from datetime import datetime,timedelta
from botocore.exceptions import ClientError

date= datetime.now()
past_time = (datetime.now() - timedelta(days=5)).date()
regions = [<'Region1'>,<'Region2'>]


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def notify(msg):
    sendclient = boto3.client('sns', region_name="<sns region name>")
    try:
        sendclient.publish(
            TopicArn="<SNS Topic ARN>",
            Message=("AutoTermination Enabled DBInstances & DBClusters in Sandbox account \n" + msg +"These Stopped DBInstances will be AutoTerminated and DBClusters have to be Terminated by the CreatedUser! \n"),
            Subject="Stopped DBInstances will be terminiated"
            )
    except ClientError as err:
        logging.info(err)
        return False

def clu_notify(clu_msg,user):
    sendclient = boto3.client('sns', region_name="us-east-1")
    try:
        sendclient.publish(
            TopicArn="arn:aws:sns:us-east-1:732041584766:SK-Sandbox-Bot",
            Message=("AutoTermination Enabled DBClusters in Sandbox account \n" + clu_msg +"Please Terminate the DBCluster if you no longer needed! \n"),
            Subject=f"{user} Terminate the Stopped DBCluster"
            )
    except ClientError as err:
        logging.info(err)
        return False        

def lambda_handler(event, context):
    msg = ""
    for region in regions:
      msg = terminate_stopped_db_instance(region,msg)
    if msg:
      notify(msg)
    
def terminate_stopped_db_instance(region,msg):
    key= "AutoTerminate"
    value="yes"
    client = boto3.client('rds', region_name=region)
    
    #Deletes if it's a  db instance
    response = client.describe_db_instances()
    v_readReplica=[]
    
    for i in response['DBInstances']:
        readReplica=i['ReadReplicaDBInstanceIdentifiers']
        v_readReplica.extend(readReplica)
    
    for i in response['DBInstances']:
        #The if condition below filters aurora clusters from single instance databases as boto3 commands defer to stop the aurora clusters.
        if i['Engine'] not in ['aurora-mysql','aurora-postgresql']:
        #The if condition below filters Read replicas.
            if i['DBInstanceIdentifier'] not in v_readReplica and len(i['ReadReplicaDBInstanceIdentifiers']) == 0:
                arn=i['DBInstanceArn']
                resp2=client.list_tags_for_resource(ResourceName=arn)
        #check if the RDS instance is part of the Auto-Stop group.
                if 0==len(resp2['TagList']):
                    logging.info('DB Instance {0} is not part of AutoTerminate'.format(i['DBInstanceIdentifier']))
                else:
                    for tag in resp2['TagList']:
                        #If the tags match, then stop the instances by validating the current status.
                        if tag['Key']==key and tag['Value']==value:
                            if i['DBInstanceStatus'] == 'stopped':
                                  respon = client.describe_db_instances(DBInstanceIdentifier=i['DBInstanceIdentifier'])                                            
                                  stopped_time=((respon['DBInstances'][0]['AutomaticRestartTime'])-timedelta(days=7)).date()
                                  termination_date= stopped_time + timedelta(days=5)
                                  user = [key.get("Value").split('@')[0] for key in resp2['TagList'] if key.get("Key") =="CreatedBy"]
                                  if past_time > stopped_time :
                                    client.delete_db_instance(DBInstanceIdentifier=i['DBInstanceIdentifier'],SkipFinalSnapshot=True)
                                  else:
                                    msg = msg + f"User: {user[0]}, Region: {region}, DBInstanceIdentifier: {i['DBInstanceIdentifier']}, Termination Date: {termination_date} \n" 
            elif i['DBInstanceIdentifier'] in v_readReplica:
                 logging.info('DB Instance {0} is a Read Replica. Cannot terminate a Read Replica instance'.format(i['DBInstanceIdentifier']))
            else:
                  logging.info('DB Instance {0} has a read replica. Cannot terminate a database with Read Replica'.format(i['DBInstanceIdentifier']))
    
    response=client.describe_db_clusters()
    for i in response['DBClusters']:
        clu_msg = ""
        cluarn=i['DBClusterArn']
        resp2=client.list_tags_for_resource(ResourceName=cluarn)
        if 0==len(resp2['TagList']):
              logging.info('DB Cluster {0} is not part of autostop'.format(i['DBClusterIdentifier']))
        else:
            for tag in resp2['TagList']:
                if tag['Key']==key and tag['Value']==value:
                     if i['Status'] == 'stopped':
                              respon = client.describe_db_clusters(DBClusterIdentifier=i['DBClusterIdentifier'])                                            
                              stopped_date=((respon['DBClusters'][0]['AutomaticRestartTime'])-timedelta(days=7)).date()
                              days_unused= (date.date() - stopped_date).days
                              user = [key.get("Value").split('@')[0] for key in resp2['TagList'] if key.get("Key") =="CreatedBy"]
                              if (int(days_unused) > 5):
                                clu_msg = clu_msg + f"User: {user[0]}, Region: {region}, DBClusterIdentifier: {i['DBClusterIdentifier']}, Days_Unused: {days_unused} \n" 
                                clu_notify(clu_msg,user[0])
                              else:
                                msg = msg + f"User: {user[0]}, Region: {region}, DBClusterIdentifier: {i['DBClusterIdentifier']}, Days_Unused: {days_unused}  \n" 

    return msg