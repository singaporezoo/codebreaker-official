import time
import json
import awstools

def regradeProblem(problemName, regradeType = 'NORMAL',stitch=False):
    # Regrade type can be NORMAL, AC, NONZERO
    submissions = awstools.getSubmissionsToProblem(problemName)
    problemInfo = awstools.getProblemInfo(problemName)
    
    for i in submissions:
        subId = int(i['subId'])
        submissionInfo = awstools.getSubmission(subId)
        if regradeType == 'AC' and submissionInfo['totalScore'] != 100:
            continue
        if regradeType == 'NONZERO' and submissionInfo['totalScore'] == 0:
            continue
        print(f"REGRADE {subId}")
        
        awstools.gradeSubmission(
            problemName=problemName,
            submissionId=submissionInfo['subId'],
            username=submissionInfo['username'],
            submissionTime=submissionInfo['submissionTime'],
            regradeall=True,
            language=submissionInfo['language'],
            problemType=problemInfo['problem_type'],
            stitch=stitch
        )
        
    
def lambda_handler(event, context):
    problemName = event['problemName']
    regradeType = event['regradeType']
    
    stitch = event['stitch']
    regradeProblem(problemName=problemName,regradeType=regradeType,stitch=stitch)
    # GIVE TIME FOR ALL PROBLEMS TO GRADE
    time.sleep(30)
    
    
    if stitch:
        awstools.updateAllStitchedScores(problemName)
    else:
        awstools.updateAllScores(problemName)
''' 
TEST EVENT
{
  "problemName": "wheelofmisfortune",
  "type": "NORMAL",
  "stitch": false
}
'''