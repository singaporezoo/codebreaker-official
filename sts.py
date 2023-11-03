import boto3
import json
from uuid import uuid4
from botocore.exceptions import ClientError

iam_client = boto3.client('iam')
sts_client = boto3.client('sts')

def createRole(problemName):

	roleName = f'codebreaker-testdata-{problemName}-role'

	policyDocument = {
		'Version':'2012-10-17', 
		'Statement': [{ 
			'Sid': 'AllowAllS3ActionsInUserFolder', 
			'Effect': 'Allow', 
			'Action': ['s3:*'], 
			'Resource': [f'arn:aws:s3:::codebreaker-testdata/{problemName}/*'] 
	   }] 
	}

	assumeRolePolicyDocument = {
		"Version": "2012-10-17",
		"Statement": [
			{
				"Effect": "Allow",
				"Principal": {
					"AWS": [
						"arn:aws:iam::354145626860:role/ec2main",
						"arn:aws:iam::354145626860:root"
					]
				},
				"Action": "sts:AssumeRole",
				"Condition": {}
			}
		]
	}

	try:
		resp = iam_client.create_role(
			RoleName = roleName,
			AssumeRolePolicyDocument = json.dumps(assumeRolePolicyDocument),
			Description = f"Role that grants admins permission to upload testdata to {problemName}",
			MaxSessionDuration = 3600
		)

                sleep(5)

		arn = resp['Role']['Arn']

		iam_client.put_role_policy(
			RoleName=roleName,
			PolicyName='S3AccessPolicy',
			PolicyDocument=json.dumps(policyDocument)
		)

                iam_client.put_role_permissions_boundary(
			RoleName=roleName,
			PermissionsBoundary="arn:aws:iam::aws:policy/AmazonS3FullAccess"
		)

		return arn

	except ClientError as e:
		print(e)
		if e.response['Error']['Code'] == 'EntityAlreadyExists':
			resp = iam_client.get_role(RoleName=roleName)
			arn = resp['Role']['Arn']
			return arn
		else:
			return ''

def getTokens(problemName):
	arn = createRole(problemName)
	
	resp = sts_client.assume_role(RoleArn=arn,RoleSessionName="Testing",DurationSeconds=1800)
	accessKey = resp['Credentials']['AccessKeyId']
	secretAccessKey = resp['Credentials']['SecretAccessKey']
	sessionToken = resp['Credentials']['SessionToken']

	return {
		'accessKeyId': accessKey,
		'secretAccessKey': secretAccessKey,
		'sessionToken': sessionToken
	}

