from flask import render_template, session, request, redirect, flash
from forms import searchSubmissionForm
import awstools
import contestmode
from math import ceil
from pprint import pprint

def viewsubmissions(problemName):
    pageNo = request.args.get('page')
    problem = problemName
    userInfo = awstools.getCurrentUserInfo()
    problemInfo = awstools.getProblemInfo(problem)
    contest = contestmode.contest()

    if userInfo == None or ((userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin')):
        if userInfo == None:
            flash('Sorry, you are not logged in yet', 'warning')
            return redirect(f'/')
        else:
            flash('Sorry, this is an admin-only service', 'warning')
            return redirect(f'/')
            
    if contestmode.contest() and (userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers()):
        flash("You do not have access in contest mode", "warning")
        return redirect("/")

    if problemInfo['superhidden'] == True:
        if userInfo['username'] not in problemInfo['allowAccess'] and userInfo['role'] != 'superadmin':
            flash('Sorry, this is a private service', 'warning')
            return redirect(f'/')

    if pageNo == None:
        pageNo = 1
    pageNo = int(pageNo)
    
    submissionList = awstools.getSubmissionsList(pageNo, problem, None)
    maxSub = len(submissionList)
    
    subPerPage = awstools.subPerPage
    submissionList.sort(key = lambda x:x['subId'], reverse=True)
    submissionList = submissionList[(pageNo-1)*subPerPage : min(len(submissionList), pageNo*subPerPage)]
    maxPage = ceil(maxSub / subPerPage)
    pages = range(max(1, pageNo-1), min(maxPage+1, pageNo+3)) 
    linkname = f'{problem}?'
     
    return render_template('viewsubmissions.html', problem=problem, pageNo=pageNo, pages=pages, maxPage=maxPage, submissionList=submissionList, userinfo=userInfo, contest=contest, linkname=linkname, socket=contestmode.socket())

