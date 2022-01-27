from flask import flash, render_template, session, request, redirect, send_file
from forms import updateContestForm
import io
import awstools, contestmode
import subprocess

def copyinfo(c_info):
    info = {}
    info['contestName'] = c_info['contestName']
    info['duration'] = c_info['duration']
    info['startTime'] = c_info['startTime']
    info['endTime'] = c_info['endTime']
    info['problems'] = c_info['problems']
    info['public'] = c_info['public']
    info['publicScoreboard'] = c_info['publicScoreboard']
    info['users'] = c_info['users']
    info['scores'] = c_info['scores']
    info['description'] = c_info['description']
    info['editorial'] = c_info['editorial']
    info['editorialVisible'] = c_info['editorialVisible']
    info['subDelay'] = c_info['subDelay']
    info['subLimit'] = c_info['subLimit']
    return info

def editcontestproblems():
    contestId = request.form['contestId']
    problems = request.form['problems']
    awstools.updateContestProblems(contestId,problems)
    return "Success!"

def editcontest(contestId):
    c_info = awstools.getContestInfo(contestId)
    if c_info == None:
        flash("This contest does not exist!", "warning")
        return redirect('/admin/editcontests')
    problem_names = awstools.getAllProblemNames()
    names = []
    for i in range(len(problem_names)):
        names.append(problem_names[i]["problemName"])
    names.sort()
    raw_usernames = awstools.getAllUsernames()
    usernames = []
    for i in range(len(raw_usernames)):
        usernames.append(raw_usernames[i]["username"])
    usernames.sort()
    form = updateContestForm()
    userInfo = awstools.getCurrentUserInfo()

    if userInfo == None or (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin'):
        flash("Abmenistratior access is required", "warning")
        return redirect("/")

    if contestmode.contest() and (userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers()):
        flash("You do not have access in contest mode", "warning")
        return redirect("/")

    if contestId in contestmode.contestIds() and userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers():
        flash("You cannot edit this contest!", "warning")
        return redirect("/")

    scoreboard = awstools.checkScoreboard(contestId)

    if form.is_submitted():
        result = request.form

        if result['form_name'] == 'contest_info':
            info = {}
            info['public'] = 'contest_public' in result
            info['publicScoreboard'] = 'contest_scoreboardpublic' in result
            info['editorialVisible'] = 'editorial_visible' in result
            info['contestName'] = result['contest_name']
            info['duration'] = int(result['contest_duration'])
            info['startTime'] = result['contest_start']
            info['endTime'] = result['contest_end']
            info['editorial'] = result['editorial']
            info['problems'] = c_info['problems']
            info['users'] = c_info['users']
            info['scores'] = c_info['scores']
            info['description'] = result['contest_description']
            info['subDelay'] = int(result['contest_sub_delay'])
            info['subLimit'] = int(result['contest_sub_limit'])
            if info['subDelay'] < 5:
                flash("Submission delay must be at least 5s", "warning")
                return redirect(f'/admin/editcontest/{contestId}')
            if info['subLimit'] != -1 and info['subLimit'] < 0:
                flash("Submission limit must be -1 (no limit) or a positive integer", "warning")
                return redirect(f'/admin/editcontest/{contestId}')
            if info['startTime'] == '' or info['endTime'] == '':
                flash("Start and end times cannot be empty!", "warning")
                return redirect(f'/admin/editcontest/{contestId}')
            res = awstools.updateContestInfo(contestId, info)
            if not res:
                flash("Check your start and end times :<", "warning")
            return redirect(f'/admin/editcontest/{contestId}')

        elif result['form_name'] == 'add_problem':
            if result['problem_name'] == '':
                return redirect(f'/admin/editcontest/{contestId}')
            if result['problem_name'] in c_info['problems']:
                flash("Problem already in contest!", 'warning')
                return redirect(f'/admin/editcontest/{contestId}')
            if type(awstools.getProblemInfo(result['problem_name'])) is str:
                flash("Check your problem ID :<", "warning")
                return redirect(f'/admin/editcontest/{contestId}')
            info = copyinfo(c_info)
            info['problems'].append(result['problem_name'])
            awstools.updateContestInfo(contestId, info)
            return redirect(f'/admin/editcontest/{contestId}')

        elif result['form_name'] == 'remove_problem':
            if result['problem_name'] not in c_info['problems']:
                return redirect(f'/admin/editcontest/{contestId}')
            info = copyinfo(c_info)
            info['problems'].remove(result['problem_name'])
            awstools.updateContestInfo(contestId, info)
            return redirect(f'/admin/editcontest/{contestId}')
        
        elif result['form_name'] == 'add_user':
            username = result['username']
            if username == '':
                return redirect(f'/admin/editcontest/{contestId}')
            info = copyinfo(c_info)
            if username in info["users"]:
                flash("User already in contest!", 'warning')
                return redirect(f'/admin/editcontest/{contestId}')
            if username not in usernames: 
                flash("Check your username :<", "warning")
                return redirect(f'/admin/editcontest/{contestId}')
            info['users'][username] = "0"
            awstools.updateContestInfo(contestId, info)
            return redirect(f'/admin/editcontest/{contestId}')

        elif result['form_name'] == 'remove_user':
            username = result['username']
            info = copyinfo(c_info)
            if username not in info['users']:
                return redirect(f'/admin/editcontest/{contestId}')

            info['users'].pop(username)
            if username in info['scores']:
                info['scores'].pop(username)
            awstools.updateContestInfo(contestId, info)
            return redirect(f'/admin/editcontest/{contestId}')

        elif result['form_name'] == 'freeze_user':
            username = result['username']
            awstools.endParticipation(contestId, username)
            return redirect(f'/admin/editcontest/{contestId}')

        elif result['form_name'] == 'add_link':
            for problem in c_info['problems']:
                problem_info = awstools.getProblemInfo(problem)
                problem_info['contestLink'] = contestId
                problem_info['source'] = c_info['contestName']
                awstools.updateProblemInfo(problem,problem_info)

        elif result['form_name'] == 'add_editorial':
            for problem in c_info['problems']:
                problem_info = awstools.getProblemInfo(problem)
                newinfo = {}
                problem_info['editorials'].append(c_info['editorial'])
                problem_info['editorialVisible'] = True
                awstools.updateProblemInfo(problem_info['problemName'], problem_info)

        elif result['form_name'] == 'download_scoreboard':
            filename = f'{contestId}.csv'
            scoreboard = awstools.getScoreboard(filename)
            mem = io.BytesIO()
            mem.write(scoreboard.encode('utf-8'))
            mem.seek(0)
            return send_file(mem,as_attachment=True,attachment_filename=filename)
        
        elif result['form_name'] == 'generate_scoreboard':
            result = awstools.generateNewScoreboard(contestId)
            return redirect(f'/admin/editcontest/{contestId}')

    return render_template('editcontest.html', info=c_info, problem_names=names, usernames=usernames, form=form,userinfo=userInfo,scoreboard = scoreboard, socket=contestmode.socket())
