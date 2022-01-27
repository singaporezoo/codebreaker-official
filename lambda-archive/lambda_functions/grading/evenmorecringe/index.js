var AWS = require("aws-sdk");
var lambda = new AWS.Lambda()

exports.handler = async (event) => {
     let problemName = event["problemName"]
    let subId = event["submissionId"]
    let testcaseNumber = event["testcaseNumber"]
    let customChecker = event["customChecker"]
    let TLE = event["timeLimit"]
    let MLE = event["memoryLimit"]
    let lambdaML = event["lambdaML"]
    
    for(let i=1;i<=testcaseNumber;i+=1){
        var payload = {
            'problemName':problemName,
            'submissionId':subId,
            'testcaseNumber':i,
            'customChecker':customChecker,
            'timeLimit':TLE,
            'memoryLimit':MLE
        }
        let funcName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:codebreaker-testcase-grader'
        //funcName = funcName.concat(String(lambdaML))
        await new Promise((resolve,reject) => {
            const params = {
                FunctionName: funcName, // the lambda function we are going to invoke
                Payload: JSON.stringify(payload),
                InvocationType: 'Event'
            }
            // console.log(payload)
            lambda.invoke(params, (err,result) => {
                if(err)reject(err)
                else resolve(result.Payload)
            })
        })
    }
}