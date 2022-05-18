from flask import render_template, session, flash, request, redirect
import tags
import awstools
import contestmode

def home():
    if contestmode.contest():
        return redirect(f'/contest/{contestmode.contestId()}')

    userinfo = awstools.getCurrentUserInfo()
    if userinfo != None:
        userSubmissionList = awstools.getSubmissionsList(1, None, userinfo.username)
    else:
        userSubmissionList = None
    globalSubmissionList = awstools.getSubmissionsList(1, None, None)
    
    return render_template('home.html',
                           userinfo=userinfo,
                           globalSubmissionList=globalSubmissionList,
                           userSubmissionList=userSubmissionList,
                           statistics=awstools.credits_page(),
                           socket=contestmode.socket())
