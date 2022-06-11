import io
import time
from datetime import datetime
import subprocess
import contestmode
import awstools
from uuid import uuid4
MAX_ERROR_LENGTH = 500

def check(code, problem_info, userInfo):
    validated = problem_info["validated"]
    nowhitespace = code.replace(" ", "")

    if not validated:
        if (userInfo == None):
            return {"status":"warning","message":"Please log in."}
        elif (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin'):
            return {"status":"warning","message":"Sorry, this problem still has issues. Please contact the administrators."}
        else:
            return {"status":"danger","message":"Problem has 1 or more issues that require fixing"}

    if ("system" in nowhitespace and "system_" not in nowhitespace):
        return {"status":"danger", "message":"You have used some keywords in your code that we don't allow, please contact an admin if you believe there is an issue"}
    banned = [] #["fork", "popen", "popen2", "execv", "execl", "execlp", "execvpe", "execle"]

    for b in banned:
        if b in nowhitespace:
            return {"status":"danger", "message":"You have used some keywords in your code that we don't allow, please contact an admin if you believe there is an issue"}

    #print(len(code))
    if len(code) > 128000:
        time.sleep(0.75)
        return {"status":"danger", "message":":snuffle: your code is longer than shuffle! At most 128000 characters or you'll get poked!"}

    return {"status":"success", "message":""}

def compileCommunication(codeA, codeB, problem_info):

    timeLimit = problem_info['timeLimit']
    memoryLimit = problem_info['memoryLimit']
    subtaskMaxScores = problem_info['subtaskScores']
    subtaskNumber = len(subtaskMaxScores)
    subtaskDependency = problem_info['subtaskDependency']
    testcaseNumber = problem_info['testcaseCount']
    customChecker = problem_info['customChecker']
    source = problem_info['source']
    author = problem_info['author']
    title = problem_info['title']
    analysisVisible = problem_info['analysisVisible']
    problemType = problem_info['problem_type']
    validated = problem_info['validated']
    PROBLEM_NAME = problem_info['problemName']
    nameA = problem_info['nameA']
    nameB = problem_info['nameB']

    compileError=""

    if problemType == 'Communication':
        subuuid = str(uuid4())

        subprocess.run(f'mkdir tmp/submissions/{subuuid}', shell=True)

        sourceAName = f"tmp/submissions/{subuuid}/{nameA}.cpp"
        sourceBName = f"tmp/submissions/{subuuid}/{nameB}.cpp"
        headerAName = f"tmp/submissions/{subuuid}/{nameA}.h"
        headerBName = f"tmp/submissions/{subuuid}/{nameB}.h"
        graderName = f"tmp/submissions/{subuuid}/grader.cpp"
        compiledName = f"tmp/submissions/{subuuid}/{subuuid}"

        #Save the code
        with open(sourceAName,"w") as sourceFile:
            sourceFile.write(codeA)
            sourceFile.close()
        with open(sourceBName,"w") as sourceFile:
            sourceFile.write(codeB)
            sourceFile.close()

        try:
            # Bring from s3
            awstools.getGraderFile(f'{PROBLEM_NAME}/grader.cpp', graderName)
            awstools.getGraderFile(f'{PROBLEM_NAME}/{nameA}.h', headerAName)
            awstools.getGraderFile(f'{PROBLEM_NAME}/{nameB}.h', headerBName)

            #compile the code
            cmd=f"timeout 30s g++ -O2 -o {compiledName} {graderName} {sourceAName} {sourceBName} -m64 -static -std=gnu++17 -lm -s -w -Wall" 

            process = subprocess.run(cmd, shell=True, capture_output=True)
            process.check_returncode()
            
            subId = awstools.getNextSubmissionId()

            #Upload the compiled code to S3
            uploadTarget = f"compiled/{subId}"
            awstools.uploadCode(compiledName,uploadTarget)

            # Upload the source code to S3
            uploadTarget=f"source/{subId}A.cpp"
            awstools.uploadCode(sourceAName,uploadTarget)

            uploadTarget=f"source/{subId}B.cpp"
            awstools.uploadCode(sourceBName,uploadTarget)

            #delete the codes
            subprocess.run(f'sudo rm -rf tmp/submissions/{subuuid}', shell=True)

            username = awstools.getCurrentUserInfo()['username']

            awstools.gradeSubmission(PROBLEM_NAME,subId,username)
            #session["lastSubmission"] = time.time() 
            time.sleep(2)
            return {"status":"redirect","message":f"/submission/{subId}"}
        except subprocess.CalledProcessError as e:
            time.sleep(0.75)
            subprocess.run(f'sudo rm -rf tmp/submissions/{subuuid}', shell=True)
            compileError += process.stderr.decode('UTF-8')
            compileError = compileError.replace(f"tmp/submissions/{subuuid}", "ans")
            compileError = compileError.replace("<", "&lt;")
            compileError = compileError.replace(">", "&gt;")
            compileError = compileError[:MAX_ERROR_LENGTH]

            #delete the codes
            subprocess.run(f'sudo rm -rf tmp/submissions/{subuuid}', shell=True)

            return {"status":"compileError","message":compileError}
    else:
        return {'status': 'compileError', 'message': "problem isn't even communication"}

    return {"status":"success","message":""}

def compilesub(code, problem_info, language):

    timeLimit = problem_info['timeLimit']
    memoryLimit = problem_info['memoryLimit']
    subtaskMaxScores = problem_info['subtaskScores']
    subtaskNumber = len(subtaskMaxScores)
    subtaskDependency = problem_info['subtaskDependency']
    testcaseNumber = problem_info['testcaseCount']
    customChecker = problem_info['customChecker']
    source = problem_info['source']
    author = problem_info['author']
    title = problem_info['title']
    analysisVisible = problem_info['analysisVisible']
    problemType = problem_info['problem_type']
    validated = problem_info['validated']
    PROBLEM_NAME = problem_info['problemName']

    compileError=""

    if language == 'py':
        # Don't need to compile, just save
        # Save the code
        subuuid = str(uuid4())
        sourceName = f"tmp/submissions/{subuuid}.py"
        with open(sourceName,"w") as sourceFile:
            sourceFile.write(code)
            sourceFile.close()

        # Upload python code to source
        subId = awstools.getNextSubmissionId()
        uploadTarget=f"source/{subId}.py"
        awstools.uploadCode(sourceName,uploadTarget)

        #delete the codes
        subprocess.run(f'sudo rm {sourceName}', shell=True)

        username = awstools.getCurrentUserInfo()['username']

        awstools.gradeSubmission(PROBLEM_NAME,subId,username,language=language)

        time.sleep(1.5)
        return {"status":"redirect","message":f"/submission/{subId}"}

    if problemType == 'Batch':
        subuuid = str(uuid4())

        sourceName = f"tmp/submissions/{subuuid}.cpp"
        compiledName = f"tmp/submissions/{subuuid}"

        #Save the code
        with open(sourceName,"w") as sourceFile:
            sourceFile.write(code)
            sourceFile.close()

        try:
            #compile the code
            cmd=f"timeout 50s g++ -O2 -o {compiledName} {sourceName} -m64 -static -std=gnu++17 -lm -s -w -Wall -Wshadow -fmax-errors=512" 

            process = subprocess.run(cmd, shell=True, capture_output=True)
            process.check_returncode()

            #print(f"after compile: {datetime.now()}")

            subId = awstools.getNextSubmissionId()

            #Upload the compiled code to S3
            uploadTarget = f"compiled/{subId}"
            awstools.uploadCode(compiledName,uploadTarget)

            # Upload the source code to S3
            uploadTarget=f"source/{subId}.cpp"
            awstools.uploadCode(sourceName,uploadTarget)

            #delete the codes
            subprocess.run(f'sudo rm {sourceName}', shell=True)
            subprocess.run(f'sudo rm {compiledName}', shell=True)

            username = awstools.getCurrentUserInfo()['username']

            awstools.gradeSubmission(PROBLEM_NAME,subId,username)

            time.sleep(1.5)
            return {"status":"redirect","message":f"/submission/{subId}"}
        except subprocess.CalledProcessError:
            time.sleep(0.75)
            subprocess.run(f'sudo rm {sourceName}', shell=True)
            compileError += process.stderr.decode('UTF-8')
            #compileError = compileError.replace("\n", "<br>")
            compileError = compileError.replace(f"tmp/submissions/{subuuid}", "ans")
            compileError = compileError.replace("<", "&lt;")
            compileError = compileError.replace(">", "&gt;")
            compileError = compileError[:MAX_ERROR_LENGTH]

            if compileError == "":
                compileError = 'Compile timed out after 30s'

            return {"status":"compileError","message":compileError}
    elif problemType == 'Interactive':
        subuuid = str(uuid4())

        subprocess.run(f'mkdir tmp/submissions/{subuuid}', shell=True)

        sourceName = f"tmp/submissions/{subuuid}/{PROBLEM_NAME}.cpp"
        headerName = f"tmp/submissions/{subuuid}/{PROBLEM_NAME}.h"
        graderName = f"tmp/submissions/{subuuid}/grader.cpp"
        compiledName = f"tmp/submissions/{subuuid}/{subuuid}"

        #Save the code
        with open(sourceName,"w") as sourceFile:
            sourceFile.write(code)
            sourceFile.close()

        try:
            # Bring from s3
            awstools.getGraderFile(f'{PROBLEM_NAME}/grader.cpp', graderName)
            awstools.getGraderFile(f'{PROBLEM_NAME}/{PROBLEM_NAME}.h', headerName)

            #compile the code
            cmd=f"timeout 30s g++ -O2 -o {compiledName} {graderName} {sourceName} -m64 -static -std=gnu++17 -lm -s -w -Wall" 

            process = subprocess.run(cmd, shell=True, capture_output=True)
            process.check_returncode()
            
            subId = awstools.getNextSubmissionId()

            #Upload the compiled code to S3
            uploadTarget = f"compiled/{subId}"
            awstools.uploadCode(compiledName,uploadTarget)

            # Upload the source code to S3
            uploadTarget=f"source/{subId}.cpp"
            awstools.uploadCode(sourceName,uploadTarget)

            #delete the codes
            subprocess.run(f'sudo rm -rf tmp/submissions/{subuuid}', shell=True)

            username = awstools.getCurrentUserInfo()['username']

            awstools.gradeSubmission(PROBLEM_NAME,subId,username)
            #session["lastSubmission"] = time.time() 
            time.sleep(2)
            return {"status":"redirect","message":f"/submission/{subId}"}
        except subprocess.CalledProcessError as e:
            time.sleep(0.75)
            compileError += process.stderr.decode('UTF-8')
            compileError = compileError.replace(f"tmp/submissions/{subuuid}", "ans")
            compileError = compileError.replace("<", "&lt;")
            compileError = compileError.replace(">", "&gt;")
            compileError = compileError[:MAX_ERROR_LENGTH]

            #delete the codes
            subprocess.run(f'sudo rm -rf tmp/submissions/{subuuid}', shell=True)

            return {"status":"compileError","message":compileError}

    return {"status":"success","message":""}

def regradeCommunication(subId, regrade_type=0):
    subInfo = awstools.getSubmission(subId,False)
    if subInfo is None:
        return {'status':"warning",'message':"This submission doesn't exist"}
    problemName = subInfo['problemName']
    problem_info = awstools.getProblemInfo(problemName)
    if type(problem_info) is str:
        return {'status':"warning",'message':"This problem doesn't exist"}

    if regrade_type==1 and subInfo['totalScore'] == 0:
        return {'status':'warning','message':'Score is 0, skipped'}

    if regrade_type==2 and subInfo['totalScore'] != 100:
        return {'status':'warning','message':'Not AC, skipped'}

    timeLimit = problem_info['timeLimit']
    memoryLimit = problem_info['memoryLimit']
    subtaskMaxScores = problem_info['subtaskScores']
    subtaskNumber = len(subtaskMaxScores)
    subtaskDependency = problem_info['subtaskDependency']
    testcaseNumber = problem_info['testcaseCount']
    customChecker = problem_info['customChecker']
    source = problem_info['source']
    author = problem_info['author']
    title = problem_info['title']
    analysisVisible = problem_info['analysisVisible']
    problemType = problem_info['problem_type']
    validated = problem_info['validated']
    PROBLEM_NAME = problem_info['problemName']
    nameA = problem_info['nameA']
    nameB = problem_info['nameB']

    codeA = subInfo['codeA']
    codeB = subInfo['codeB']
    username = subInfo['username']
    submissionTime = subInfo['submissionTime']

    compileError=""

    if problemType == 'Communication':
        subuuid = str(uuid4())

        subprocess.run(f'mkdir tmp/submissions/{subuuid}', shell=True)

        sourceAName = f"tmp/submissions/{subuuid}/{nameA}.cpp"
        sourceBName = f"tmp/submissions/{subuuid}/{nameB}.cpp"
        headerAName = f"tmp/submissions/{subuuid}/{nameA}.h"
        headerBName = f"tmp/submissions/{subuuid}/{nameB}.h"
        graderName = f"tmp/submissions/{subuuid}/grader.cpp"
        compiledName = f"tmp/submissions/{subuuid}/{subuuid}"

        #Save the code
        with open(sourceAName,"w") as sourceFile:
            sourceFile.write(codeA)
            sourceFile.close()
        with open(sourceBName,"w") as sourceFile:
            sourceFile.write(codeB)
            sourceFile.close()

        try:
            # Bring from s3
            awstools.getGraderFile(f'{PROBLEM_NAME}/grader.cpp', graderName)
            awstools.getGraderFile(f'{PROBLEM_NAME}/{nameA}.h', headerAName)
            awstools.getGraderFile(f'{PROBLEM_NAME}/{nameB}.h', headerBName)

            #compile the code
            cmd=f"timeout 30s g++ -O2 -o {compiledName} {graderName} {sourceAName} {sourceBName} -m64 -static -std=gnu++17 -lm -s -w -Wall" 

            process = subprocess.run(cmd, shell=True, capture_output=True)
            process.check_returncode()

            #Upload the compiled code to S3
            uploadTarget = f"compiled/{subId}"
            awstools.uploadCode(compiledName,uploadTarget)

            # Upload the source code to S3
            uploadTarget=f"source/{subId}A.cpp"
            awstools.uploadCode(sourceAName,uploadTarget)

            uploadTarget=f"source/{subId}B.cpp"
            awstools.uploadCode(sourceBName,uploadTarget)

            #delete the codes
            subprocess.run(f'sudo rm -rf tmp/submissions/{subuuid}', shell=True)

            awstools.gradeSubmission(PROBLEM_NAME,subId,username,submissionTime,regradeall=True)
            #session["lastSubmission"] = time.time() 
            time.sleep(2)
            return {"status":"redirect","message":f"/submission/{subId}"}
        except subprocess.CalledProcessError as e:
            time.sleep(0.75)
            subprocess.run(f'sudo rm -rf tmp/submissions/{subuuid}', shell=True)
            compileError += process.stderr.decode('UTF-8')
            compileError = compileError.replace(f"tmp/submissions/{subuuid}", "ans")
            compileError = compileError.replace("<", "&lt;")
            compileError = compileError.replace(">", "&gt;")
            compileError = compileError[:MAX_ERROR_LENGTH]

            return {"status":"compileError","message":compileError}
    else:
        return {'status': 'compileError', 'message': "problem isn't even communication"}

    return {"status":"success","message":""}

def regradeSub(subId, regrade_type = 0, language = 'cpp'):
    subInfo = awstools.getSubmission(subId,False)
    if subInfo is None:
        return {'status':"warning",'message':"This submission doesn't exist"}
    problemName = subInfo['problemName']
    problem_info = awstools.getProblemInfo(problemName)
    if type(problem_info) is str:
        return {'status':"warning",'message':"This problem doesn't exist"}

    if problem_info['problem_type'] == 'Communication':
        return regradeCommunication(subId, regrade_type)

    if regrade_type==1 and subInfo['totalScore'] == 0:
        return {'status':'warning','message':'Score is 0, skipped'}

    if regrade_type==2 and subInfo['totalScore'] != 100:
        return {'status':'warning','message':'Not AC, skipped'}

    timeLimit = problem_info['timeLimit']
    memoryLimit = problem_info['memoryLimit']
    subtaskMaxScores = problem_info['subtaskScores']
    subtaskNumber = len(subtaskMaxScores)
    subtaskDependency = problem_info['subtaskDependency']
    testcaseNumber = problem_info['testcaseCount']
    customChecker = problem_info['customChecker']
    source = problem_info['source']
    author = problem_info['author']
    title = problem_info['title']
    analysisVisible = problem_info['analysisVisible']
    problemType = problem_info['problem_type']
    validated = problem_info['validated']
    PROBLEM_NAME = problem_info['problemName']

    code = subInfo['code']
    username = subInfo['username']
    submissionTime = subInfo['submissionTime']

    compileError=""

    if language == 'py':
        # Don't need to compile, just save
        # Save the code
        subuuid = str(uuid4())
        sourceName = f"tmp/submissions/{subuuid}.py"
        with open(sourceName,"w") as sourceFile:
            sourceFile.write(code)
            sourceFile.close()

        # Upload python code to source
        subId = awstools.getNextSubmissionId()
        uploadTarget=f"source/{subId}.py"
        awstools.uploadCode(sourceName,uploadTarget)

        #delete the codes
        subprocess.run(f'sudo rm {sourceName}', shell=True)

        username = awstools.getCurrentUserInfo()['username']

        awstools.gradeSubmission(PROBLEM_NAME,subId,username,language=language)

        time.sleep(1.5)
        return {"status":"redirect","message":f"/submission/{subId}"}

    if problemType == 'Batch':
        subuuid = str(uuid4())

        sourceName = f"tmp/submissions/{subuuid}.cpp"
        compiledName = f"tmp/submissions/{subuuid}"

        #Save the code
        with open(sourceName,"w") as sourceFile:
            sourceFile.write(code)
            sourceFile.close()

        try:
            #compile the code
            cmd=f"timeout 30s g++ -O2 -o {compiledName} {sourceName} -m64 -static -std=gnu++17 -lm -s -w -Wall -Wshadow -fmax-errors=512" 

            process = subprocess.run(cmd, shell=True, capture_output=True)
            process.check_returncode()

            #print(f"after compile: {datetime.now()}")

            #Upload the compiled code to S3
            uploadTarget = f"compiled/{subId}"
            awstools.uploadCode(compiledName,uploadTarget)

            #delete the codes
            subprocess.run(f'sudo rm {sourceName}', shell=True)
            subprocess.run(f'sudo rm {compiledName}', shell=True)
            
            awstools.gradeSubmission(PROBLEM_NAME,subId,username,submissionTime,regradeall=True)

            time.sleep(1.5)
            return {"status":"redirect","message":f"/submission/{subId}"}
        except subprocess.CalledProcessError:
            time.sleep(0.75)
            subprocess.run(f'sudo rm {sourceName}', shell=True)
            compileError += process.stderr.decode('UTF-8')
            #compileError = compileError.replace("\n", "<br>")
            compileError = compileError.replace(f"tmp/submissions/{subuuid}", "ans")
            compileError = compileError.replace("<", "&lt;")
            compileError = compileError.replace(">", "&gt;")
            compileError = compilerError[:MAX_ERROR_LENGTH]

            if compileError == "":
                compileError = 'Compile timed out after 30s'

            return {"status":"compileError","message":compileError}
    elif problemType == 'Interactive':
        subuuid = str(uuid4())

        subprocess.run(f'mkdir tmp/submissions/{subuuid}', shell=True)

        sourceName = f"tmp/submissions/{subuuid}/{PROBLEM_NAME}.cpp"
        headerName = f"tmp/submissions/{subuuid}/{PROBLEM_NAME}.h"
        graderName = f"tmp/submissions/{subuuid}/grader.cpp"
        compiledName = f"tmp/submissions/{subuuid}/{subuuid}"

        #Save the code
        with open(sourceName,"w") as sourceFile:
            sourceFile.write(code)
            sourceFile.close()

        try:
            # Bring from s3
            awstools.getGraderFile(f'{PROBLEM_NAME}/grader.cpp', graderName)
            awstools.getGraderFile(f'{PROBLEM_NAME}/{PROBLEM_NAME}.h', headerName)

            #compile the code
            cmd=f"timeout 30s g++ -O2 -o {compiledName} {graderName} {sourceName} -m64 -static -std=gnu++17 -lm -s -w -Wall" 

            process = subprocess.run(cmd, shell=True, capture_output=True)
            process.check_returncode()

            #Upload the compiled code to S3
            uploadTarget = f"compiled/{subId}"
            awstools.uploadCode(compiledName,uploadTarget)

            #delete the codes
            subprocess.run(f'sudo rm -rf tmp/submissions/{subuuid}', shell=True)

            awstools.gradeSubmission(PROBLEM_NAME,subId,username,submissionTime,regradeall=True)
            #session["lastSubmission"] = time.time() 
            time.sleep(2)
            return {"status":"redirect","message":f"/submission/{subId}"}
        except subprocess.CalledProcessError as e:
            time.sleep(0.75)
            compileError += process.stderr.decode('UTF-8')
            compileError = compileError.replace(f"tmp/submissions/{subuuid}", "ans")
            compileError = compileError.replace("<", "&lt;")
            compileError = compileError.replace(">", "&gt;")
            compileError = compileError[:MAX_ERROR_LENGTH]

            #delete the codes
            subprocess.run(f'sudo rm -rf tmp/submissions/{subuuid}', shell=True)

            return {"status":"compileError","message":"compileError"}

    return {"status":"success","message":""}

def regradeProblem(problemName, regrade_type = 0):
    #Please use your discretion (or if you want to donate to codebreaker :p)
    submissions = awstools.getSubmissionsToProblem(problemName)
    for i in submissions:
        regradeSub(int(i['subId']), regrade_type)

    awstools.updateScores(problemName)
