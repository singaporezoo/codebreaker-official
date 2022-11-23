import io
import time
import random
import flask
import awstools
import contestmode
from forms import SubmitForm
from compilesub import check,compilesub,compileCommunication
from flask import Flask, render_template, request, url_for, redirect, flash, session, get_flashed_messages, make_response, send_file
from datetime import datetime, timedelta
from language import get_languages
languages = get_languages()

def setcookie(template):
    delay = 9
    if contestmode.contest():
        delay = int(awstools.getContestInfo(contestmode.contestId())['subDelay'])
    res = make_response(template)
    outlet = random.randint(0,14)
    curtime = time.time()
    res.set_cookie(f"lastSub{outlet}",value=f"{curtime}",secure=True,expires=curtime+delay+5)
    return res
    

def problem(PROBLEM_NAME):

    if contestmode.contest() and contestmode.contestId() != 'analysismirror' and PROBLEM_NAME not in contestmode.contestproblems():
        flash('Sorry, you cannot view that resource in contest mode', 'warning')
        return redirect(f'/contest/{contestmode.contestId()}')

    userInfo = awstools.getCurrentUserInfo()

    if contestmode.contest():
        if userInfo == None or (userInfo['username'] not in contestmode.allowedusers() and userInfo['role'] != 'superadmin'):
            contestinfo = awstools.getContestInfo(contestmode.contestId())
            start = datetime.strptime(contestinfo['startTime'], "%Y-%m-%d %X") 
            now = datetime.now() + timedelta(hours = 8)
    
            if now < start:
                flash("Sorry, the contest hasn't started yet", "warning")
                return redirect(f"/contests")

    scores = []
    verdicts = []
    returnCodes = []
    maxTime = []
    maxMemory = []
    t = 0
    t = time.time()
    form = SubmitForm()
    compileError = ""
    if "compileError" in session:
        compileError = session["compileError"]
        session.pop("compileError")

    form.language.choices = list(languages.keys())
        
    problem_info = awstools.getProblemInfo(PROBLEM_NAME)
    if (type(problem_info) is str):
        return 'Sorry, this problem does not exist'
    problem_info['testcaseCount'] = int(problem_info['testcaseCount'])
    timeLimit = problem_info['timeLimit']
    memoryLimit = problem_info['memoryLimit']
    subtaskMaxScores = problem_info['subtaskScores']
    subtaskNumber = len(subtaskMaxScores)
    subtaskDependency = problem_info['subtaskDependency']
    testcaseNumber = problem_info['testcaseCount']
    customChecker = problem_info['customChecker']
    source = problem_info['source']
    author = problem_info['author']
    problem_info["author"] = [x.replace(" ", "") for x in author.split(",")]
    title = problem_info['title']
    analysisVisible = problem_info['analysisVisible']
    problemType = problem_info['problem_type']
    validated = problem_info['validated']

    editorials = [i for i in problem_info['editorials'] if i != ""]

    if problem_info['problem_type'] == 'Communication':
        if 'nameA' not in problem_info.keys():
            problem_info['nameA'] = 'placeholderA'
        if 'nameB' not in problem_info.keys():
            problem_info['nameB'] = 'placeholderA'
    
    if not awstools.isAllowedAccess(problem_info,userInfo):
        return "Sorry, this problem does not exist"

    if not validated:
        if (userInfo == None or (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin')):
            flash("Sorry, this problem still has issues. Please contact the administrators.", 'warning')
            return redirect("/")
        else:
            canSubmit = False
            flash("Problem has 1 or more issues that require fixing",'danger')

    result = awstools.getProblemStatementHTML(PROBLEM_NAME, not problem_info['publicStatement'])
    if result['status'] == 200:
        statementHTML = result['response']
    else:
        flash("Statement is private", "warning")
        statementHTML = ""
    
    delay = 9
    if contestmode.contest():
        delay = int(awstools.getContestInfo(contestmode.contestId())['subDelay'])
    outlets = 15

    sublimit = awstools.getContestInfo(contestmode.contestId())['subLimit']
    if userInfo != None:
        numsubs = len(awstools.getSubmissionsList(None, PROBLEM_NAME, userInfo['username']))
    else:
        numsubs = sublimit

    if sublimit != -1:
        remsubs = max(0, sublimit - numsubs)
    else:
        remsubs = -1

    if form.is_submitted():
        result = request.form
        
        if 'form_name' in result and result['form_name'] == 'download_input':
            if userInfo == None or (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin'):
                flash('You do not have permission to access this resource!','warning')
                return redirect(f'/problem/{PROBLEM_NAME}')
            if contestmode.contest() and userInfo['username'] not in contestmode.allowedusers() and userInfo['role'] != 'superadmin':
                flash('You do not have permission to access this resource!', 'warning')
                return redirect(f'/problem{PROBLEM_NAME}')
            tcno = result['tcin']
            filename=f'{PROBLEM_NAME}/{tcno}.in'
            tcfile = awstools.getTestcase(filename)
            mem = io.BytesIO()
            mem.write(tcfile.encode('utf-8'))
            mem.seek(0)
            return send_file(mem,as_attachment=True,attachment_filename=filename)

        elif 'form_name' in result and result['form_name'] == 'download_output':
            if userInfo == None or (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin'):
                flash('You do not have permission to access this resource!','warning')
                return redirect(f'/problem/{PROBLEM_NAME}')
            if contestmode.contest() and userInfo['username'] not in contestmode.allowedusers() and userInfo['role'] != 'superadmin':
                flash('You do not have permission to access this resource!', 'warning')
                return redirect(f'/problem{PROBLEM_NAME}')
            tcno = result['tcout']
            filename=f'{PROBLEM_NAME}/{tcno}.out'
            tcfile = awstools.getTestcase(filename)
            mem = io.BytesIO()
            mem.write(tcfile.encode('utf-8'))
            mem.seek(0)
            return send_file(mem,as_attachment=True,attachment_filename=filename)

        language = 'C++ 17'
        if 'language' in result:
            language = result['language']
        if language not in languages.keys(): # Invalid language
            flash('Invalid language!', 'warning')
            return redirect(f'/problem/{PROBLEM_NAME}')
        language = languages[language]

        if userInfo == None or (userInfo['role'] not in ['member','admin','superadmin']):
            flash('You do not have permission to submit!','warning')
            return redirect(f'/problem/{PROBLEM_NAME}')

        if contestmode.contest() and sublimit != -1 and numsubs + 1 > sublimit:
            flash('You have reached the submission limit for this problem', 'warning')
            return redirect(f'/problem/{PROBLEM_NAME}')
        
        now = time.time() 
        #print(result)
        if "testCookie" not in request.cookies:
            flash("Please turn on cookies to submit", "danger")
            return redirect(f"/problem/{PROBLEM_NAME}")
        times = []
        for i in range(outlets):
            lastSub = request.cookies.get(f'lastSub{i}')
            
            if lastSub == None:
                continue
            else:
                lastSub = float(lastSub)

            if now - lastSub < delay and userInfo['role'] != 'superadmin':
                wait = round(delay - (now - lastSub), 2)
                times.append((wait, i))
                #flash(f"Please wait {wait} seconds before submitting again", "warning")
                #print((userInfo["username"] + " LOL GOT BLOCKED\n"))
                #return redirect(f"/problem/{PROBLEM_NAME}")
        
        times.sort(reverse = True)
        #print(times)

        if not contestmode.contest():
            if len(times) > 1 or (len(times) == 1 and times[0][0] < delay/2):
                #print(times)
                res = redirect(f"/problem/{PROBLEM_NAME}")
    
                flash(f"Please wait {delay+1} seconds before submitting again", "warning")
                #print((userInfo["username"] + " got blocked\n"))
                return res
        else:
            if (len(times) >= 1 and times[len(times)-1][0] > 0):
                #print(times)
                res = redirect(f"/problem/{PROBLEM_NAME}")
    
                flash(f"Please wait {times[len(times)-1][0]} seconds before submitting again", "warning")
                #print((userInfo["username"] + " got blocked\n"))
                return res


        if problem_info['problem_type'] == 'Communication':
            #print(result)        
            codeA = result['codeA']
            codeB = result['codeB']

            checkResult = check(codeA, problem_info, userInfo)
            if checkResult["status"] != "success":
                status = checkResult["status"]
                message = checkResult["message"]
                flash(message, status)

                if status == "danger":
                    return redirect(f"/problem/{PROBLEM_NAME}")
            
                if status == "warning":
                    return redirect("/")

            checkResult = check(codeB, problem_info, userInfo)
            if checkResult["status"] != "success":
                status = checkResult["status"]
                message = checkResult["message"]
                flash(message, status)

                if status == "danger":
                    return redirect(f"/problem/{PROBLEM_NAME}")
            
                if status == "warning":
                    return redirect("/")

            result = compileCommunication(codeA, codeB, problem_info)
            print(result)

        else:
            code = result['code']
            checkResult = check(code, problem_info, userInfo)

            if checkResult["status"] != "success":
                status = checkResult["status"]
                message = checkResult["message"]
                flash(message, status)

                if status == "danger":
                    return redirect(f"/problem/{PROBLEM_NAME}")
            
                if status == "warning":
                    return redirect("/")

            result = compilesub(code, problem_info, language)
        
        if result["status"] == "compileError":
            #print("CE")
            session["compileError"] = result["message"]
            return setcookie(redirect(f"/problem/{PROBLEM_NAME}"))

        elif result["status"] != "success":
            return setcookie(redirect(result["message"]))

    return render_template('problem.html', form=form, probleminfo=problem_info, userinfo = awstools.getCurrentUserInfo(), statementHTML = statementHTML, compileError=compileError, contest=contestmode.contest(), editorials = editorials, users=contestmode.allowedusers(), remsubs = remsubs, cppref=contestmode.cppref(), socket=contestmode.socket())
    
