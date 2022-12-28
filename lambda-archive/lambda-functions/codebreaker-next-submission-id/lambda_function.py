import os
import json
import boto3 

s3 = boto3.client('s3')
judgeName = os.environ['judgeName']
BUCKET_NAME = f'{judgeName}-submission-number'
        
def lambda_handler(event, context):
    subId = s3.get_object(Bucket=BUCKET_NAME,Key=f'submissionNumber.txt')['Body'].read().decode('utf-8')
    subId = int(subId)
    with open("/tmp/submissionNumber.txt",'w') as f:
        f.write(str(subId+1))
    s3.upload_file('/tmp/submissionNumber.txt',BUCKET_NAME,'submissionNumber.txt')
    return {
        'statusCode': 200,
        'submissionId': subId
    }