import json
import boto3 
s3 = boto3.client('s3')
BUCKET_NAME = 'codebreaker-clarification-number'
        
def lambda_handler(event, context):
    id = s3.get_object(Bucket=BUCKET_NAME,Key=f'clarificationNumber.txt')['Body'].read().decode('utf-8')
    id = int(id)
    with open("/tmp/clarificationNumber.txt",'w') as f:
        f.write(str(id+1))
    s3.upload_file('/tmp/clarificationNumber.txt',BUCKET_NAME,'clarificationNumber.txt')
    return {
        'statusCode': 200,
        'clarificationId': id
    }