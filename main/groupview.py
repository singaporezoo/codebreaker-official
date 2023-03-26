from flask import render_template, session, flash, redirect
import awstools
import contestmode
from datetime import datetime, timedelta
from forms import beginContestForm

def group(groupId):
    
    userInfo = awstools.getCurrentUserInfo()
    
    if userInfo != None:
        username = userInfo["username"]
    else:
        username = ""

    if contestmode.contest() and (userInfo == None or userInfo['role'] != 'superadmin'):
        flash('Sorry, you cannot view that resource in contest mode', 'warning')
        return redirect(f'/contest/{contestmode.contestId()}')

        
    contestgroupinfo = awstools.getContestGroupInfo(groupId)
    if type(contestgroupinfo) == str:
        flash("Invalid contest group ID!", "warning")
        return redirect(f'/contests')
    contestsinfo = []

    for contest in contestgroupinfo['contests']:
        contestinfo = awstools.getContestScore(contest,username)
        contestinfo['contestId'] = contest
        if contestinfo['public']:
            contestsinfo.append(contestinfo)

    groupsinfo = []

    for group in contestgroupinfo['contestGroups']:
        groupinfo = awstools.getContestGroupInfo(group)
        groupsinfo.append(groupinfo)

    return render_template('contestgroup.html', contestgroupinfo=contestgroupinfo, userinfo=userInfo, contestsinfo = contestsinfo, groupsinfo = groupsinfo, users=contestmode.allowedusers(), socket=contestmode.socket())
