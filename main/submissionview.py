from flask import render_template, redirect, flash, request, session, make_response
import datetime
import time
import random

import awstools
import contestmode
from compilesub import check
from forms import ResubmitForm

#BEGIN: SUBMISSION -----------------------------------------------------------------------------------------------------------------------------------------------------
'''
Here, we view the results of a submission.
'''

def fixFloat(x):
    if type(x) == str: x = int(x)
    x = round(x,2)
    if x == round(x):
        x = round(x)
    return x

def setcookie(template):
    delay = 9
    if contestmode.contest():
        delay = int(awstools.getContestInfo(contestmode.contestId())['subDelay'])
    res = make_response(template)
    outlet = random.randint(0,14)
    curtime = time.time()
    res.set_cookie(f"lastSub{outlet}",value=f"{curtime}",secure=True,expires=curtime+delay+5)
    return res

def submission(subId):
    userInfo = awstools.getCurrentUserInfo()
    if not subId.isdigit():
        return "Sorry, the submission you're looking for doesn't exist"

    subDetails = awstools.getSubmission(int(subId))
    if subDetails == None:
        return "Sorry, the submission you're looking for doesn't exist. Refresh the page if you just made a submission." 

    subtaskScores = [fixFloat(i) for i in subDetails['subtaskScores']]
    scores = [fixFloat(i) for i in subDetails["score"]]
    returnCodes = [fixFloat(i) for i in subDetails["returnCodes"]]
    language = subDetails['language']

    problemName = subDetails['problemName']
    username = subDetails['username']
    problem_info = awstools.getProblemInfo(problemName)
    if type(problem_info) == str:
        return "Sorry, this problem doesn't exist"
    totalScore = 0
    verdicts = subDetails['verdicts']
    times = [round(x,2) for x in subDetails['times']]
    memories = [round(x) for x in subDetails['memories']]
    maxTime = round( max(max(subDetails['times']), float(subDetails['maxTime'])), 3);
    maxMemory = round( max(max(subDetails['memories']), float(subDetails['maxMemory'])), 2);
    submissionTime = subDetails['submissionTime']
    gradingTime = subDetails['gradingTime']
    
    code = None
    codeA = None
    codeB = None

    if 'code' in subDetails.keys():
        code= subDetails['code']
    else:
        codeA = subDetails['codeA']
        codeB = subDetails['codeB']

    if 'compileErrorMessage' in subDetails.keys():
        subDetails['maxTime'] = 'N/A'
        subDetails['maxMemory'] = 'N/A'
    else:
        subDetails['compileErrorMessage'] = ''
        subDetails['maxTime'] = f'{subDetails["maxTime"]} seconds'
        subDetails['maxMemory'] = f'{subDetails["maxMemory"]} MB'

    if problem_info['problem_type'] == 'Communication' and code != None:
        flash('This submission was made before the problem type was converted to communication', 'warning')
    
    if not awstools.isAllowedAccess(problem_info,userInfo):
        flash("Sorry, you are not authorized to view this resource!", 'warning')
        return redirect("/")

    subtaskMaxScores = problem_info['subtaskScores']
    subtaskNumber = len(subtaskMaxScores)
    subtaskDependency = problem_info['subtaskDependency']
    testcaseNumber = problem_info['testcaseCount']
    fullFeedback = problem_info['fullFeedback']

    contest = contestmode.contest()

    if contest and userInfo and userInfo['username'] not in contestmode.allowedusers() and userInfo['role'] != 'superadmin':
        if (problemName not in contestmode.contestproblems() and contestmode.contestId() != 'analysismirror') or username != userInfo['username']:
            flash('Sorry this submission cannot be viewed', 'warning')
            return redirect(f'/contest/{contestmode.contestId()}')
        contests = contestmode.contestIds()
        blocktime = datetime.datetime.now() + datetime.timedelta(seconds=1)
        for i in contests:
            contestinfo = awstools.getContestInfo(i)
            starttime = datetime.datetime.strptime(contestinfo['startTime'],"%Y-%m-%d %X")-datetime.timedelta(hours=8)
            blocktime = min(blocktime, starttime)
        subtime = datetime.datetime.strptime(gradingTime,"%Y-%m-%d %X")-datetime.timedelta(hours=8)
        if blocktime < datetime.datetime.now() and subtime < blocktime: #if earliest contest has started and the submission is before then
            flash('Sorry this submission cannot be viewed', 'warning')
            return redirect(f'/contest/{contestmode.contestId()}')

    if contest and userInfo == None: 
        flash("Sorry, you are not authorized to view this resource!", 'warning')
        return redirect("/")

    if contest and not contestmode.fullfeedback() and userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers():
        fullFeedback = False

    toRefresh = False
    subtaskDetails = []

    changed = False
    changedSubtask = (len(subtaskMaxScores) != len(subtaskScores))
    
    for i in range(subtaskNumber):
        maxScore = subtaskMaxScores[i]
        yourScore = 0
        if i < len(subtaskScores):
            yourScore = subtaskScores[i]

        yourScore = fixFloat(maxScore*yourScore/100)
        detail = {'number' : i, 'maxScore': maxScore, 'yourScore': yourScore, 'verdict': 'AC', 'testcases' : [], 'done' : True}
        stopVerdict = 0
        
        minScore = 100 #recalculate here cause of updating issues
        dep = subtaskDependency[i].split(',')
        nonAC = False
        for t in dep:
            x = t.split('-')
            
            TC = []
            if(len(x) == 1):
                ind = int(x[0])
                TC.append(ind)
            else:
                st = int(x[0])
                en = int(x[1])
                for j in range(st,en+1):
                    TC.append(j)
            for ind in TC:
                if len(scores) <= ind:
                    detail['testcases'].append({'score' : '-', 'verdict' :'UG', 'time': 'N/A', 'memory': 'N/A'})
                    changed = True
                    continue
                elif not fullFeedback and nonAC:
                    detail['testcases'].append({'score' : '-', 'verdict' :'N/A', 'time': 'N/A', 'memory': 'N/A'})
                else:
                    if verdicts[ind] == "RTE":
                        verdicts[ind] = f"RTE({returnCodes[ind]})"
                    if scores[ind] == 0:
                        nonAC = True # Still continue to show feedback for partial scoring
                    detail['testcases'].append({'score' : scores[ind], 'verdict' : verdicts[ind], 'time': times[ind], 'memory': memories[ind]})
                if verdicts[ind] == ":(":
                    detail['done'] = False
                    toRefresh = True
                if scores[ind] == 0 and verdicts[ind] != "AC" and verdicts[ind] != "PS":
                    detail['verdict'] = 'WA'
                    stopVerdict = 1
                if scores[ind] != 100 and verdicts[ind] == "PS" and detail['verdict'] != 'WA':
                    detail['verdict'] = 'PS'
                minScore = min(minScore, scores[ind])
        detail['yourScore'] = max(detail['yourScore'], maxScore * minScore / 100)
        detail['yourScore'] = fixFloat(detail['yourScore'])
        totalScore += detail['yourScore']

        diffInTime = (datetime.datetime.now() + datetime.timedelta(hours=8) - datetime.datetime.strptime(gradingTime, '%Y-%m-%d %H:%M:%S')).total_seconds()

        subtaskDetails.append(detail)
    
    if diffInTime > 60 or subDetails['compileErrorMessage'] != '':
        toRefresh = False
    if changed:
        flash("If you see the 'UG' verdict, it means that testcases were added after this submission was graded", "warning")
    if changedSubtask:
        flash("Some subtasks were added or removed from this question after this submission was graded", "warning")

    '''RESUBMISSION'''
    form = ResubmitForm()

    if form.is_submitted():

        result = request.form
        ''' REGRADE '''
        if 'form_name' in result and result['form_name'] == 'regrade':
            if userInfo == None or (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin'):
                flash('You do not have permission to regrade!','warning')
                return redirect(f'/problem/{problemName}')
            if contest and (userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers()):
                flash('You cannot regrade in contest mode!', 'warning')
                return redirect(f'/submission/{subId}')

            # For regrade, the code is already there so we just call grade 
            awstools.gradeSubmission(
                problemName = problemName,
                submissionId = subId,
                username = subDetails['username'], 
                submissionTime = subDetails['submissionTime'],
                regradeall=False,
                language = language,
                problemType = problem_info['problem_type']
            )

            time.sleep(2)
            return redirect(f"/submission/{subId}")
        
        else:
            ''' RESUBMIT '''
            if userInfo == None or (userInfo['role'] not in ['member','admin','superadmin']):
                flash('You do not have permission to submit!','warning')
                return redirect(f'/problem/{problemName}')
            
            now = time.time() 
            ''' DETERMINE IF SUBMISSION IS VALID: CHECK IF IT VIOLATES SUBMISSION DELAY OR SUBMISSION LIMIT ''' 
            delay = 9
            if contestmode.contest():
                delay = int(awstools.getContestInfo(contestmode.contestId())['subDelay']) - 1
            outlets = 15

            sublimit = awstools.getContestInfo(contestmode.contestId())['subLimit']
            numsubs = len(awstools.getSubmissionsList(None, problemName, awstools.getCurrentUserInfo()['username']))

            if contestmode.contest() and sublimit != -1 and numsubs + 1 > sublimit:
                flash("You have reached the submission limit for this problem", "warning")
                return redirect(f"/submission/{subId}")


            if "testCookie" not in request.cookies:
                flash("Please turn on cookies to submit", "danger")
                return redirect(f"/submission/{subId}")
            times = []
            for i in range(outlets):
                lastSub = request.cookies.get(f'lastSub{i}')
                
                if lastSub == None:
                    continue
                else:
                    lastSub = float(lastSub)
                
                if now - lastSub < delay and userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers():
                    wait = round(delay - (now - lastSub), 2)
                    times.append((wait, i))
            
            times.sort(reverse = True)

            if not contestmode.contest():
                if len(times) > 1 or (len(times) == 1 and times[0][0] < delay/2):
                    res = redirect(f"/submission/{subId}")
        
                    flash(f"Please wait {delay+1} seconds before submitting again", "warning")
                    return res
            else:
                if (len(times) >= 1 and times[len(times)-1][0] > 0):
                    res = redirect(f"/submission/{subId}")
        
                    flash(f"Please wait {times[len(times)-1][0]} seconds before submitting again", "warning")
                    return res
            ''' END SUBMISSION VERIFICATION '''

            result = request.form 

            code = None
            codeA = None
            codeB = None

            if 'code' in result:
                code = result['code']

                checkResult = check(code, problem_info,userInfo)
                if checkResult["status"] != "success":
                    status = checkResult["status"]
                    message = checkResult["message"]
                    flash(message, status)
    
                    if status == "danger":
                        return redirect(f"/submission/{subId}")
                    
                    if status == "warning":
                        return redirect("/")

            else:
                codeA = result['codeA']
                codeB = result['codeB']

                checkResult = check(codeA, problem_info,userInfo)
                if checkResult["status"] != "success":
                    status = checkResult["status"]
                    message = checkResult["message"]
                    flash(message, status)
    
                    if status == "danger":
                        return redirect(f"/submission/{subId}")
                    
                    if status == "warning":
                        return redirect("/")

                checkResult = check(codeB, problem_info,userInfo)
                if checkResult["status"] != "success":
                    status = checkResult["status"]
                    message = checkResult["message"]
                    flash(message, status)
    
                    if status == "danger":
                        return redirect(f"/submission/{subId}")
                    
                    if status == "warning":
                        return redirect("/")
            
            # Assign new submission index
            newSubId = awstools.getNextSubmissionId()

            if problem_info['problem_type'] == 'Communication':
                # Upload code file to S3
                s3pathA = f'source/{newSubId}A.{language}'
                s3pathB = f'source/{newSubId}B.{language}'
                awstools.uploadSubmission(code = codeA, s3path = s3pathA)
                awstools.uploadSubmission(code = codeB, s3path = s3pathB)
            else:
                # Upload code file to S3
                s3path = f'source/{newSubId}.{language}'
                awstools.uploadSubmission(code = code, s3path = s3path)

            awstools.gradeSubmission(
                problemName = problemName,
                submissionId = newSubId,
                username = subDetails['username'], 
                submissionTime = None,
                regradeall=False,
                language = language,
                problemType = problem_info['problem_type']
            )

            time.sleep(2)
            return redirect(f"/submission/{newSubId}")

    '''END RESUBMISSION'''

    return render_template('submission.html', message="",subDetails=subDetails,probleminfo=problem_info, userinfo=userInfo,toRefresh=toRefresh,contest=contest,form=form,code=code,codeA=codeA,codeB=codeB,users=contestmode.allowedusers(), hidetime=contestmode.hidetime(), cppref=contestmode.cppref(), socket=contestmode.socket(), subtaskDetails=subtaskDetails)

#END: SUBMISSION -----------------------------------------------------------------------------------------------------------------------------------------------------


