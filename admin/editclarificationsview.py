from flask import flash, render_template, session, request, redirect
import awstools, contestmode
from forms import answerClarificationForm

def editclarifications():

    userInfo = awstools.getCurrentUserInfo()
    if userInfo == None or (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin'):
        flash("Admin access is required", "warning")
        return redirect("/")
    if contestmode.contest() and (userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers()):
        flash("You do not have access in contest mode", "warning")
        return redirect("/")
    username = userInfo["username"]

    clarifications = awstools.getAllClarifications()
    unanswered = [i for i in clarifications if i['answer'] == ""]
    answered = [i for i in clarifications if i['answer'] != ""]
    unanswered.sort(key=lambda x:x['clarificationId'])
    answered.sort(key=lambda x:x['clarificationId'],reverse=True)

    answers = ["Yes", "No", "Answered in task description", "No comment", "Investigating", "Invalid question"]

    form = answerClarificationForm()

    if form.is_submitted():
        result = request.form
        clarification_id = int(result['clarification_id'])
        answer = result['clarification_answer']
        info = awstools.getClarificationInfo(clarification_id)
        info['answer'] = answer
        info['answeredBy'] = username
        awstools.updateClarificationInfo(clarification_id, info)
        return redirect('/admin/editclarifications')

    return render_template('editclarifications.html', userinfo = userInfo, form=form, answered = answered, unanswered = unanswered, answers=answers, contest = contestmode.contest(), socket=contestmode.socket())
