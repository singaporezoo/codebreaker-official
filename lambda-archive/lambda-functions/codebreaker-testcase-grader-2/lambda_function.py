import os
import sys
import json
import boto3
import resource
import subprocess
from random import randrange

import wrapper
from weird import Funny
from decimal import *
from time import time
from uuid import uuid4
from math import ceil
from cmscmp import white_diff_step
s3 = boto3.resource('s3')

def limit_memory(maxsize): 
    soft, hard = resource.getrlimit(resource.RLIMIT_AS) 
    resource.setrlimit(resource.RLIMIT_AS, (maxsize, maxsize)) 
    
def getMem():
    X = resource.getrusage(resource.RUSAGE_CHILDREN)
    res =  X.ru_maxrss
    return res/1024
    
def lambda_handler(event, context):
    
    problemName = event["problemName"]
    subId = event["submissionId"]
    subHash = str(uuid4())
    testcaseNumber = event["testcaseNumber"]
    language = event["language"]
    customChecker = event["customChecker"]
    TLE = float(event["timeLimit"])
    MLE = float(event["memoryLimit"])

    os.chdir('/tmp')
    INPUT_FILE = f"{subHash}.in"
    OUTPUT_FILE = f"{subHash}.out"
    if language == 'cpp':
        CODE_FILE = "code"

        binaryPath = f"compiled/{subId}"
        s3.Bucket("codebreaker-submissions").download_file(binaryPath,CODE_FILE)
    elif language == 'py':
        CODE_FILE = "code.py"
        codePath = f"source/{subId}.py"
        s3.Bucket("codebreaker-submissions").download_file(codePath,CODE_FILE)
    
    inputPath = problemName + '/' + str(testcaseNumber) + '.in'
    s3.Bucket("codebreaker-testdata").download_file(inputPath,INPUT_FILE)
    subprocess.run(f"chmod +x {CODE_FILE}", shell=True)

    info = resource.getrusage(resource.RUSAGE_CHILDREN)
    originalTime = info.ru_utime
    allocatedTime = ceil(TLE+0.5)
    allocatedMemory = MLE
    cmd = "cd"
    
    try:
        process = subprocess.run(cmd,preexec_fn=(lambda: wrapper.grade(allocatedTime, allocatedMemory, INPUT_FILE, CODE_FILE, language)),capture_output=True)
    except Exception as e:
        result = {
            "verdict": "RTE(9)",
            "score": 0,
            "runtime": TLE, # runtime/s
            "memory": MLE, #memory limit/mb
            "returnCode": 69, #change this in the future
            # "stdout": "",
            # "stderr": str(typeof(e))
        }
        
        result = Funny(result,problemName,TLE)
        
        subprocess.run("rm -rf /tmp/*",shell=True)
        
        return result
    
    # print(process.stdout)
    dum = process.stdout.split()
    returnCode = int(dum[0])
    userTime = float(dum[1])
    userMem = float(dum[2])
    
    if returnCode >= 128:
        returnCode -= 128
        
    result = {
        "verdict": "AC",
        "score":0,
        "runtime": userTime , # runtime/s
        "memory": userMem, #memory limit/mb
        "returnCode":returnCode,
    }

    if userTime > TLE:
        result["verdict"] = "TLE"
    elif returnCode != 0:
        result["verdict"] = f"RTE({returnCode})"
    elif userMem > MLE:
        result['verdict'] = 'MLE'
    else:
        outputPath = problemName + '/' + str(testcaseNumber) + '.out'
        s3.Bucket("codebreaker-testdata").download_file(outputPath,OUTPUT_FILE)

        if customChecker == 0:
            res = white_diff_step("comparison_file",OUTPUT_FILE)
            result['score']=res
            if result['score'] == 100:
                result['verdict'] = 'AC'
            elif result['score'] == 0:
                result['verdict'] = 'WA'
            else:
                result['verdict'] = 'PS'
        else:
            s3.Bucket("codebreaker-checkers").download_file(f"compiled/{problemName}","checker")
            subprocess.run("chmod +x checker", shell=True)
            cmd = cmd= f"ulimit -s unlimited; ./checker {INPUT_FILE} comparison_file {OUTPUT_FILE}" # run cpp file 
            try:
                def setLimit():
                    resource.setrlimit(resource.RLIMIT_CPU, (allocatedTime, allocatedTime))
                    resource.setrlimit(resource.RLIMIT_CORE, (allocatedMemory,allocatedMemory))
                    # resource.setrlimit(resource.RLIMIT_NPROC, (20,20))
                    resource.setrlimit(resource.RLIMIT_FSIZE, (128000000,128000000))
                process = subprocess.run(cmd,shell=True,preexec_fn=setLimit, capture_output=True)
                out = process.stdout.decode('utf-8')
                err = process.stderr.decode('utf-8')
                s = ""
                for i in out:
                    if i in [str(t) for t in range(10)]:
                        s += i
                    elif i == '\n':
                        break
                    elif i == '.':
                        s += '.'
                
                # Strips away all characters
                
                if s == "" and err == "":
                    result = {
                        "verdict": "Checker Fault",
                        "score": 0,
                        "runtime": 0 , # runtime/s
                        "memory": 0, #memory limit/mb
                        "returnCode": 67, #change this in the future
                    }
                elif s == "" and err != "":
                    result = {
                        "verdict": "WA",
                        "score": 0,
                        "runtime": 0 , # runtime/s
                        "memory": 0, #memory limit/mb
                        "returnCode": 67, #change this in the future
                    }
                    if len(err) >= 2 and err[0] == 'o' and err[1] == 'k':
                        result['verdict'] = 'AC'
                        result["score"] = 100
                elif float(s) > 1:
                    result = {
                        "verdict": "Checker Fault",
                        "score": 0,
                        "runtime": 0 , # runtime/s
                        "memory": 0, #memory limit/mb
                        "returnCode": 67, #change this in the future
                    }
                else:
                    result['score'] = Decimal(s)*100
                    result['score'] = round(result['score'], 2)
                    if result['score'] == 100:
                        result['verdict'] = 'AC'
                    elif result['score'] == 0:
                        result['verdict'] = 'WA'
                    else:
                        result['verdict'] = 'PS'
            except Exception as e:
                result = {
                    "verdict": "Grader Fault",
                    "score": 0,
                    "runtime": 0 , # runtime/s
                    "memory": MLE, #memory limit/mb
                    "returnCode": 67, #change this in the future
                }
            
    result['runtime'] = round(result['runtime'],3)
    result['memory'] = round(result['memory'],1)
    subprocess.run("rm -rf /tmp/*",shell=True)
    
    result = Funny(result,problemName,TLE)

    return result