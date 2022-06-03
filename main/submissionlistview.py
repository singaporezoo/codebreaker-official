from flask import render_template, session, request, redirect, flash
from forms import searchSubmissionForm
import awstools
import contestmode
from math import ceil
from pprint import pprint

def submissionlist():
    pageNo = request.args.get('page')
    username = request.args.get('username')
    problem = request.args.get('problem')
    userInfo = awstools.getCurrentUserInfo()
    contest = contestmode.contest()

    if contest  and (userInfo == None or ((userInfo['username'] not in contestmode.allowedusers() and userInfo['role'] != 'superadmin'))):
        if userInfo == None:
            flash('Sorry, you are not logged in yet', 'warning')
            return redirect(f'/contest/{contestmode.contestId()}')
        if username != userInfo['username']:
            return redirect(f'/submissions?username={userInfo["username"]}&problem={problem if problem else ""}')
    
    if username == "":
        username = None
    if problem == "":
        problem = None

    if pageNo == None:
        pageNo = 1
    pageNo = int(pageNo)
    
    submissionList = []
    maxSub = 0
    
    if username == None and problem == None:
        submissionList = awstools.getSubmissionsList(pageNo, None, None)
        maxSub = int(awstools.getNumberOfSubmissions())
    else:
        submissionList = awstools.getSubmissionsList(pageNo, problem, username)
        maxSub = len(submissionList)
    
    subPerPage = awstools.subPerPage
    submissionList.sort(key = lambda x:x['subId'], reverse=True)
    if username != None or problem != None:
        submissionList = submissionList[(pageNo-1)*subPerPage : min(len(submissionList), pageNo*subPerPage)]
    maxPage = ceil(maxSub / subPerPage)
    pages = range(max(1, pageNo-1), min(maxPage+1, pageNo+3)) 
   
    if problem != None:
        probleminfo = awstools.getProblemInfo(problem)
    
    if userInfo == None or (userInfo['role'] != 'superadmin' and (problem == None or 'allowAccess' not in probleminfo or userInfo['username'] not in probleminfo['allowAccess'])):
        superhidden = awstools.getSuperhiddenProblems()
        submissionList = [s for s in submissionList if s['problemName'] not in superhidden]

    if contest and contestmode.contestId() != 'analysismirror':
        submissionList = [s for s in submissionList if s['problemName'] in contestmode.contestproblems()]

    fullfeedback = True
    if contest:
        fullfeedback = contestmode.fullfeedback()
    
    linkname = 'submissions?'
    if username != None:
        linkname += f'username={username}&'
    if problem != None:
        linkname += f'problem={problem}&'
    
    form = searchSubmissionForm()
    if form.is_submitted():
        result = request.form
        username = result['username']
        problem = result['problem']
        return redirect(f'/submissions?username={username}&problem={problem}')
    print(submissionlist)

    return render_template('submissionlist.html', form=form, username=username, problem=problem, pageNo=pageNo, pages=pages, maxPage=maxPage, submissionList=submissionList, linkname=linkname, userinfo=userInfo, contest=contest, users=contestmode.allowedusers(), fullfeedback=fullfeedback, hidetime=contestmode.hidetime(), cppref=contestmode.cppref(), socket=contestmode.socket())
