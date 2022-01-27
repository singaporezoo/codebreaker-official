from lambda_function import lambda_handler

MLE = {
  "problemName": "helloworld",
  "submissionId": 33576,
  "testcaseNumber": 1,
  "customChecker": 0,
  "timeLimit": 1,
  "memoryLimit": 128
}

print(lambda_handler(MLE,{}))