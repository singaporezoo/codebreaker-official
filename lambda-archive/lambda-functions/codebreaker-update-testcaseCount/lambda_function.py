import json
import boto3 # Amazon S3 client library
s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')
problems_table = dynamodb.Table('codebreaker-problems')
bucket = s3.Bucket('codebreaker-testdata')

def lambda_handler(event, context):
    problemName = event['problemName']
    testcaseCount = 0

    for obj in bucket.objects.filter(Prefix="{0}/".format(problemName)):
        testcaseCount += 1
    print(testcaseCount)

    problems_table.update_item(
        Key = {'problemName':problemName},
        UpdateExpression = f'set #b=:a',
        ExpressionAttributeValues={':a':int(testcaseCount/2)},
        ExpressionAttributeNames={'#b':'testcaseCount'}
    )
    
    return {
        'statusCode': 200,
        'testcaseCount':testcaseCount
    }
