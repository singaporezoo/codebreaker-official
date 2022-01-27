from flask import flash, render_template, session, request, redirect
import awstools, contestmode
from forms import addClarificationForm

def clarifications():

    userInfo = awstools.getCurrentUserInfo()
    if userInfo == None:
        flash("Please login to view this page", "warning")
        return redirect("/")
    username = userInfo["username"]

    if contestmode.contest():
        contestinfo = awstools.getContestInfo(contestmode.contestId())
        if contestinfo["public"] == 0 and not username in contestinfo["users"]:
            flash("Sorry, you've not been invited to this private contest!", "warning")
            return redirect("/announcements")

    clarifications = awstools.getClarificationsByUser(username)
    clarifications.sort(key=lambda x:x['clarificationId'], reverse=True)

    if contestmode.contest() and contestmode.contestId() != 'analysismirror':
        contestproblems = contestmode.contestproblems()
        clarifications = [i for i in clarifications if (i['problemId'] in contestproblems)]

    problems = awstools.getAllProblemsHidden()
    names = []
    for i in range(len(problems)):
        if problems[i]['analysisVisible'] and not problems[i]['superhidden']:
            names.append(problems[i]['problemName'])
    names.sort()

    if contestmode.contest() and contestmode.contestId() != 'analysismirror':
        names = contestmode.contestproblems()

    form = addClarificationForm()

    if form.is_submitted():
        result = request.form
        question = result['clarification_question']
        problemId = result['clarification_problem_id']
        if problemId not in names and problemId != "":
            flash("Invalid problem id!","warning")
            return redirect('/clarifications')
        if question == "":
            flash("Question cannot be blank!","warning")
            return redirect('/clarifications')
        if contestmode.contest() and contestmode.contestId() != 'analysismirror' and problemId == "":
            flash("You cannot make general clarifications in contests!", "warning")
            return redirect('./clarifications')
        awstools.createClarification(username, question, problemId)
        return redirect('/clarifications')

    return render_template('clarifications.html', userinfo = userInfo, form=form, clarifications=clarifications, problem_names = names, contest = contestmode.contest(), users=contestmode.allowedusers(), cppref=contestmode.cppref(), socket=contestmode.socket())
