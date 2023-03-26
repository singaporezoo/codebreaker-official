from flask import render_template, session, flash, redirect, request
import re
import awstools, contestmode
from datetime import datetime, timedelta
from forms import addContestForm

def editcontestlist():
    contests = awstools.getAllContests()
    contestNames = [x['contestId'] for x in contests]
    groups = awstools.getAllGroupIds()
    groupNames = [x['groupId'] for x in groups]
    shownContests = []

    userInfo = awstools.getCurrentUserInfo()

    if userInfo == None or (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin'):
        flash("Admin access is required", "warning")
        return redirect("/")

    if contestmode.contest() and (userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers()):
        flash("You do not have access in contest mode", "warning")
        return redirect("/")

    username = userInfo["username"]
    
    ongoing = []; future = []; past = []; timedPractice = []; collections = [];
    for contestinfo in contests:
        endTime = contestinfo["endTime"]
        startTime = contestinfo["startTime"]
        duration = contestinfo["duration"]
        if endTime == "Unlimited":
            if duration == 0:
                collections.append(contestinfo)
            else:
                timedPractice.append(contestinfo)
        else:
            start = datetime.strptime(startTime, "%Y-%m-%d %X")
            end = datetime.strptime(endTime, "%Y-%m-%d %X")
            now = datetime.now() + timedelta(hours = 8)
            if now < start:
                future.append(contestinfo)
            elif now > end:
                past.append(contestinfo)
            else:
                ongoing.append(contestinfo)

    ongoing.sort(key = lambda x:x['endTime'])
    future.sort(key = lambda x:x['startTime'])
    past.sort(key = lambda x:x['endTime'], reverse=True)
    timedPractice.sort(key = lambda x:x['contestName'])
    collections.sort(key = lambda x:x['startTime'], reverse=True)

    def convert(s):
        if s == "Unlimited":
            return 
        s = datetime.strptime(s, "%Y-%m-%d %X").strftime("%d %b %Y %H:%M")
        return s
    for contestlist in [ongoing, future, past, timedPractice, collections]:
        for contest in contestlist:
            contest["startTime"] = convert(contest["startTime"]) 
            contest["endTime"] = convert(contest["endTime"]) 
    
    contestInfos = {}
    contestInfos['ongoing'] = ongoing
    contestInfos['future'] = future
    contestInfos['past'] = past
    contestInfos['timedPractice'] = timedPractice
    contestInfos['collections'] = collections

    contestGroupsInfo = awstools.getAllContestGroups()
    contestGroupsInfo.sort(key = lambda x:x['groupName'])

    form = addContestForm()

    if form.is_submitted():
        result = request.form
        if result['form_name'] == 'add_contest':
            if result['contest_id'] == '':
                flash('oopsies! did you accidentally click to add contest?', 'warning')
                return redirect('/admin/editcontests')
            if result['contest_id'] in contestNames:
                flash('oopsies! contest id already taken :(', 'warning')
                return redirect('/admin/editcontests')
            if not re.match(r'^[\w]*$', result['contest_id']):
                flash ('Invalid contest Id!', 'warning')
                return redirect('/admin/editcontests')
            awstools.createContestWithId(result['contest_id'])
            contest_id = result['contest_id']
            return redirect(f'/admin/editcontest/{contest_id}')
        elif result['form_name'] == 'add_group':
            if result['group_id'] == '':
                flash('oopsies! did you accidentally click to add group?', 'warning')
                return redirect('/admin/editcontests')
            if result['group_id'] in groupNames:
                flash('oopsies! group id already taken :(', 'warning')
                return redirect('/admin/editcontests')
            if not re.match(r'^[\w]*$', result['group_id']):
                flash ('Invalid contest group Id!', 'warning')
                return redirect('/admin/editcontests')
            awstools.createGroupWithId(result['group_id'])
            group_id = result['group_id']
            return redirect(f'/admin/editgroup/{group_id}')
                
    return render_template('editcontestlist.html', form=form, contestInfos = contestInfos, userinfo=userInfo, contestgroupsinfo=contestGroupsInfo, socket=contestmode.socket())
