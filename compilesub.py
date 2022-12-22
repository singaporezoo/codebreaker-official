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
