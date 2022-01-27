from flask import flash, render_template, session, request, redirect, send_file
from forms import updateContestGroupForm
import io
import awstools, contestmode
import subprocess

def copyinfo(c_info):
    info = {}
    info['description'] = c_info['description']
    info['contests'] = c_info['contests']
    info['contestGroups'] = c_info['contestGroups']
    info['groupName'] = c_info['groupName']
    info['visible'] = c_info['visible']
    return info

def editcontestgroupcontests():
    contestGroupId = request.form['contestGroupId']
    contests = request.form['contests']
    awstools.updateContestGroupContests(contestGroupId, contests)
    return "Success!"

def editcontestgroupgroups():
    contestGroupId = request.form['contestGroupId']
    groups = request.form['contestGroups']
    awstools.updateContestGroupGroups(contestGroupId, groups)
    return "Success!"

def editcontestgroup(groupId):
    c_info = awstools.getContestGroupInfo(groupId)
    
    contest_ids = awstools.getAllContestIds()
    contests = []
    for i in range(len(contest_ids)):
        contests.append(contest_ids[i]["contestId"])
    contests.sort()

    group_ids = awstools.getAllContestGroupIds()
    groups = []
    for i in range(len(group_ids)):
        groups.append(group_ids[i]["groupId"])
    groups.sort()

    form = updateContestGroupForm()

    userInfo = awstools.getCurrentUserInfo()
    if userInfo == None or (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin'):
        flash("Abmenistratior access is required", "warning")
        return redirect("/")

    if contestmode.contest() and (userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers()):
        flash("You do not have access in contest mode", "warning")
        return redirect("/")
        
    if form.is_submitted():
        result = request.form

        if result['form_name'] == 'contest_group_info':
            info = {}
            info['description'] = result['contest_group_description']
            info['groupName'] = result['contest_group_name']
            info['visible'] = 'contest_group_visible' in result
            info['contests'] = c_info['contests']
            info['contestGroups'] = c_info['contestGroups']

            res = awstools.updateContestGroupInfo(groupId, info)
            return redirect(f'/admin/editgroup/{groupId}')
        
        elif result['form_name'] == 'add_contest':
            contest = result['contest']
            if contest == '':
                return redirect(f'/admin/editgroup/{groupId}')
            info = copyinfo(c_info)
            if contest in info["contests"]:
                flash("Contest already in group!", 'warning')
                return redirect(f'/admin/editgroup/{groupId}')
            if contest not in contests: 
                flash("Check your contest id :<", "warning")
                return redirect(f'/admin/editgroup/{groupId}')
            info['contests'].append(contest)
            awstools.updateContestGroupInfo(groupId, info)
            return redirect(f'/admin/editgroup/{groupId}')

        elif result['form_name'] == 'remove_contest':
            contest = result['contest']
            info = copyinfo(c_info)
            if contest not in info['contests']:
                return redirect(f'/admin/editgroup/{groupId}')

            info['contests'].remove(contest)
            awstools.updateContestGroupInfo(groupId, info)
            return redirect(f'/admin/editgroup/{groupId}')

        elif result['form_name'] == 'add_group':
            group = result['group']
            if group == '':
                return redirect(f'/admin/editgroup/{groupId}')
            info = copyinfo(c_info)
            if group in info["contestGroups"]:
                flash("Group already in group!", 'warning')
                return redirect(f'/admin/editgroup/{groupId}')
            if group not in groups: 
                flash("Check your group id :<", "warning")
                return redirect(f'/admin/editgroup/{groupId}')
            info['contestGroups'].append(group)
            awstools.updateContestGroupInfo(groupId, info)
            return redirect(f'/admin/editgroup/{groupId}')

        elif result['form_name'] == 'remove_group':
            group = result['group']
            info = copyinfo(c_info)
            if group not in info['contestGroups']:
                return redirect(f'/admin/editgroup/{groupId}')

            info['contestGroups'].remove(group)
            awstools.updateContestGroupInfo(groupId, info)
            return redirect(f'/admin/editgroup/{groupId}')

    return render_template('editcontestgroup.html', info=c_info, contest_ids=contests, form=form, userinfo=userInfo, group_ids = groups, socket=contestmode.socket())
