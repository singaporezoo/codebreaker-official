from flask import render_template, session, redirect, request, flash
import re
import awstools, contestmode
from forms import addProblemForm

def editproblemlist():
    userInfo=awstools.getCurrentUserInfo()
    problems = awstools.getAllProblemsLimited()
    if userInfo == None or (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin'):
        flash("Admin access is required", "warning")
        return redirect("/")

    if contestmode.contest() and (userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers()):
        flash("You do not have access in contest mode", "warning")
        return redirect("/")

    problemNames = [P['problemName'] for P in problems]
    
    form = addProblemForm()

    problemScores = {}
    if userInfo != None:
        problemScores = userInfo['problemScores']
    problemInfo = [dict((key,value) for key, value in P.items() if key in ['problemName', 'title', 'source', 'author','problem_type','superhidden','validated','contestLink','allowAccess']) for P in problems] #impt info goes into the list (key in [list])
    hiddenFromAnalysis = awstools.getProblemsToHideFromAnalysis()
    for problem in problemInfo:
        problem['analysisVisible'] = problem['problemName'] not in hiddenFromAnalysis 
    #filtering hidden problems
    if userInfo['role'] == 'admin':
        problemInfo = [p for p in problemInfo if ('superhidden' not in p or p['superhidden'] == False) or ('allowAccess' in p and userInfo['username'] in p['allowAccess'])]

    for i in range(len(problemInfo)):
        name = problemInfo[i]['problemName']
        score = 0
        if name in problemScores:
            score = problemScores[name]

        problemInfo[i]['yourScore'] = score

        authors = problemInfo[i]["author"]
        problemInfo[i]["author"] = [x.replace(" ", "") for x in authors.split(",")]
    
    if form.is_submitted():
        result = request.form
        if result['problem_id'] == '':
            flash('oopsies! did you accidentally click to add problem?', 'warning')
            return redirect('/admin/editproblems')
        if result['problem_id'] in problemNames:
            flash('oopsies! problem id already taken :(', 'warning')
            return redirect('/admin/editproblems')
        if not result['problem_id'].islower():
            flash('Problem Ids cannot have capital letters!', 'warning')
            return redirect('/admin/editproblems')
        if not re.match(r'^[\w]*$', result['problem_id']):
            flash ('Invalid problem Id!', 'warning')
            return redirect('/admin/editproblems')
        
        awstools.createProblemWithId(result['problem_id'], userInfo['username'])
        problem_id = result['problem_id']
        return redirect(f'/admin/editproblem/{problem_id}')

    return render_template('editproblemlist.html', form=form, problemInfo=problemInfo, userinfo=userInfo, socket=contestmode.socket())


