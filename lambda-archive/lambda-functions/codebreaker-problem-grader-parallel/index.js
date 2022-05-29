var AWS = require("aws-sdk");
var lambda = new AWS.Lambda()

let grade = async (start,end, problemName, subId, TLE, MLE, customChecker, language) => {
    console.log(start,end)
    var payload = {
        "problemName": problemName,
        "submissionId": subId,
        "start":start,
        "end":end,
        "memoryLimit": MLE,
        "timeLimit": TLE,
        "customChecker": customChecker,
        "language": language
    }
    let funcName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:evenmorecringe'
    
    await new Promise((resolve,reject) => {
        const params = {
            FunctionName: funcName, // the lambda function we are going to invoke
            Payload: JSON.stringify(payload),
            InvocationType: 'Event'
        }
        lambda.invoke(params, (err,result) => {
            if(err)reject(err)
            else resolve(result.Payload)
        })
    })
}

exports.handler = async (event) => {
    let problemName = event["problemName"]
    let subId = event["submissionId"]
    let start = event['start']
    let end = event['end']
    let customChecker = event["customChecker"]
    let TLE = event["timeLimit"]
    let MLE = event["memoryLimit"]
    let language = event['language']
    
    if (start + 3000 >= end){
        for(let i=start;i<=end;i+=1){
            console.log(i)
            var payload = {
                'problemName':problemName,
                'submissionId':subId,
                'testcaseNumber':i,
                'customChecker':customChecker,
                'timeLimit':TLE,
                'memoryLimit':MLE,
                'language': language
            }
            let funcName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:codebreaker-testcase-grader'
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
    }else{
        let mid = (start+end)/2;
        let ranges = [[start,mid], [mid+1,end]];
        for (let i=0; i<2; i+=1){
            grade(ranges[i][0], ranges[i][1], problemName, subId, TLE, MLE, customChecker,language)
        }
    }   
}