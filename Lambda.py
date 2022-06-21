# Things to be done in this program
# 1. Enter the required regions in the regions list -> <'Region1'>,<'Region2'>,..
# 2. Enter the <sns region name>
# 3. Enter the <SNS Topic ARN>

import json
import boto3
from datetime import datetime,timedelta
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

date= datetime.now() 
current_time = (datetime.now()).date()

# Regions to find the unused resources
regions = [<'Region1'>,<'Region2'>]

# key and value for Unused Find Date
key="Unused_date"
value= str(date.date())

# SNS Notification
def notify(msg):
    sendclient = boto3.client('sns', region_name="<sns region name>")
    try:
        sendclient.publish(
            TopicArn="<SNS Topic ARN>",
            Message=("Unused Resources in our Sandbox account \n" + msg +"\n Inactive Lambda will be terminated after 5 days \n"),
            Subject="Inactive Lambda will be Autoterminiated"
            )
    except ClientError as err:
        logging.info(err)
        return False

def lambda_handler(event, context):
    lam=""
    for region in regions:
      lam=delete_unused_lambda_function(region,lam)
    if lam: 
     notify(lam)

    
def delete_unused_lambda_function(region,lam):
    lamb =  boto3.client('lambda', region_name=region)
    response = lamb.list_functions(MaxItems=123)
    for lambd in response['Functions']:
        respo = lamb.get_function(FunctionName=lambd['FunctionName'])
        tags = lamb.list_tags(Resource=lambd['FunctionArn'],)
        if respo['Configuration']['State'] == 'Inactive':
            for tag in tags['Tags']:
                if(tag.get("Key") ==key ):
                  unused_fdate = tag.get("Value")
                  termination_time = (datetime.strptime(unused_fdate, "%Y-%m-%d") + timedelta(days=5)).date()
                  if current_time >= termination_time:
                    try:
                      lamb.delete_function(FunctionName=lambd['FunctionName'])
                    except Exception as e:
                      logging.info(f"Unable to delete the function {lambd['FunctionName']}" +str(e))
                  if lam == "":
                    lam = lam + "\nUnused lambda function: \n"       
                    lam = lam + f"lambda function name: {lambd['FunctionName']}, Region: {region}, Termination Date: {termination_time} \n"
                  else:
                    lam = lam + f"lambda function name: {lambd['FunctionName']}, Region: {region}, Termination Date: {termination_time} \n"
            if not any(tag.get('Key') == key for tag in tags['Tags']):
              lamb.tag_resource(Resource=lambd['FunctionArn'], Tags={key:value})
              print(f"state:{respo['Configuration']['State']} region:{region} name:{lambd['FunctionName']}")
              logging.info(f"Tag created for the lambda function-{lambd['FunctionName']}")
        else :
            lamb.untag_resource(Resource=lambd['FunctionArn'],TagKeys=[key]) 
            logging.info(f"state:{respo['Configuration']['State']} region:{region} name:{lambd['FunctionName']}")
    return lam        
       
