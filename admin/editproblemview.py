from flask import flash, render_template, session, request, redirect
from forms import updateProblemForm
import json
import tags
import awstools, contestmode
import subprocess
import compilesub

def editProblemTags():
    userInfo = awstools.getCurrentUserInfo()
    problemId = request.form['problemId']
    newTags = json.loads(request.form['newTags'])
    if userInfo == None:
        return {'status':300,'error':'Access to resource denied'}

    if userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin':
        return {'status':300,'error':'Access to resource denied'}

    tagList = tags.tags()

    for i in newTags:
        if i not in tagList:
            return {'status':300,'error':'Invalid Tag!'}

    awstools.updateTags(problemId, newTags)

    return {'status':200,'error':''}

def verifyDependency(dependency):
    ranges = dependency.split(',')
    for i in ranges:
        nums = i.split('-')
        if len(nums) > 2:
            return False
        elif len(nums) > 1:
            x, y = int(nums[0]), int(nums[1])
            if (x > y):
                return False
    return True

def editproblem(problemName):
    userInfo = awstools.getCurrentUserInfo()
    if userInfo == None or (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin'):
        flash("Admin access is required", "warning")
        return redirect("/")

    if contestmode.contest() and (userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers()):
        flash("You do not have access in contest mode", "warning")
        return redirect("/")
    
    problem_info = awstools.getProblemInfo(problemName)
    if (type(problem_info) is str):
        return 'Sorry, this problem does not exist'
    
    if not awstools.isAllowedAccess(problem_info,userInfo):
        return "Sorry, this problem does not exist"

    if problem_info['problem_type'] == 'Interactive':
        if 'nameA' not in problem_info.keys():
            problem_info['nameA'] = 'placeholderA'
        if 'nameB' not in problem_info.keys():
            problem_info['nameB'] = 'placeholderA'

    form = updateProblemForm()
    if problem_info['problem_type'] == 'Interactive':
        form.problem_type.choices = ["Interactive", "Batch", "Communication"]
    elif problem_info['problem_type'] == 'Batch':
        form.problem_type.choices = ["Batch", "Communication", "Interactive"]
    else:
        form.problem_type.choices = ["Communication", "Batch", "Interactive"]

    subsURL = f'admin/viewsubmissons/{problemName}'

    if 'tags' not in problem_info.keys():
        problem_info['tags'] = []

    tagList = []
    for i in tags.tags():
        if i in problem_info['tags']:
            tagList.append([i,True])
        else:
            tagList.append([i,False])
    
    creatorOptions = {'show' : False}
    if 'creator' in problem_info and problem_info['creator'] == userInfo['username']:
        creatorOptions['show'] = True    
        problemsToHideSubmissions = awstools.getProblemsToHideSubmissions()

        creatorOptions['isHideSubmissions'] = (problemName in problemsToHideSubmissions)

    if form.is_submitted():
        result = request.form
        files = request.files

        if result['form_name'] == 'problem_info':
            info = {}
            info['fullFeedback'] = ('feedback' in result)
            info['analysisVisible'] = ('analysis' in result)
            info['superhidden'] = problem_info['superhidden']
            if (userInfo['role'] == 'superadmin'):
                info['superhidden'] = ('superhidden' in result)
            if(info['superhidden']):
                info['analysisVisible'] = False
            info['customChecker'] = ('checker' in result)
            info['attachments'] = ('attachments' in result)
            info['title'] = result['problem_title']
            info['source'] = result['problem_source']

            if 'creator' not in problem_info:
                info['creator'] = None
                print("BRUH")
            else:
                info['creator'] = problem_info['creator']

            if 'nameA' in result.keys():
                info['nameA'] = result['nameA']
            if 'nameB' in result.keys():
                info['nameB'] = result['nameB']

            if result['problem_author'] != "":
                authors = result['problem_author'].split(",")
                for author in authors:
                    author = author.replace(" ","")
                    user = awstools.getUserInfoFromUsername(author)
                    if user['username'] == "":
                        flash(f"User {author} not found!", "warning")
                        return redirect(f'/admin/editproblem/{problemName}')
            info['author'] = result['problem_author']
            info['problem_type'] = result['problem_type']
            info['timeLimit'] = result['time_limit']
            info['EE'] = ('ee' in result)
            info['editorialVisible'] = ('editorial_visible' in result)
            info['memoryLimit'] = result['memory_limit']
            info['createdTime'] = problem_info['createdTime']
            info['editorials'] = problem_info['editorials']
            info['contestUsers'] = problem_info['contestUsers']
            if result['contest_link'] != "":
                contest = awstools.getContestInfo(result['contest_link'])
                if contest == None:
                    flash(f"Invalid contest id!", "warning")
                    return redirect(f'/admin/editproblem/{problemName}')
            info['contestLink'] = result['contest_link']
            if info['superhidden'] and ('allowAccess' not in problem_info):
                awstools.addAllowAccess(problemName)
            awstools.updateProblemInfo(problemName, info)
            if problem_info['problem_type'] == 'Communication':
                awstools.updateCommunicationFileNames(problemName,info)
            return redirect(f'/admin/editproblem/{problemName}')
        
        elif result['form_name'] == 'statement_upload':
            if 'statement' not in files:
                flash('Statement not found', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            if files['statement'].filename == '':
                flash('Statement not found', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            file_name = files['statement'].filename
            if '.' not in file_name:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            ext_file = file_name.rsplit('.', 1)[1].lower()
            if ext_file == 'pdf':
                awstools.uploadStatement(files['statement'], f'{problemName}.pdf')
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problemName}')
                return redirect(f'/admin/editproblem/{problemName}')
            elif ext_file == 'html':
                awstools.uploadStatement(files['statement'], f'{problemName}.html')
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problemName}')
                return redirect(f'/admin/editproblem/{problemName}')
            else:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'delete_html':
            awstools.deleteStatement(f'{problemName}.html')
            flash('HTML statement deleted!', 'success')
            awstools.validateProblem(f'{problemName}')
            return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'delete_pdf':
            awstools.deleteStatement(f'{problemName}.pdf')
            flash('PDF statement deleted!', 'success')
            awstools.validateProblem(f'{problemName}')
            return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'sync_testcases':
            awstools.testcaseUploadLambda(f'{problemName}')
            return redirect(f'/admin/editproblem/{problemName}')
       
        elif result['form_name'] == 'update_count':
            awstools.updateCountLambda(f'{problemName}')
            flash('Updated number of testcases!', 'success')
            awstools.validateProblem(f'{problemName}')
            return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'validate':
            awstools.validateProblem(f'{problemName}')
            flash('Validated problem!','success')
            return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'add_subtask':
            problem_info['subtaskScores'].append(0)
            problem_info['subtaskDependency'].append('1')
            info = {}
            info['subtaskScores'] = problem_info['subtaskScores']
            info['subtaskDependency'] = problem_info['subtaskDependency']
            awstools.updateSubtaskInfo(problemName, info)
            return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'remove_subtask':
            if len(problem_info['subtaskScores']) == 1:
                flash('hisssss! cannot have less than one subtask', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            problem_info['subtaskScores'].pop()
            problem_info['subtaskDependency'].pop()
            info = {}
            info['subtaskScores'] = problem_info['subtaskScores']
            info['subtaskDependency'] = problem_info['subtaskDependency']
            awstools.updateSubtaskInfo(problemName, info)
            return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'update_subtask':
            info = {}
            info['subtaskScores'] = []
            info['subtaskDependency'] = []
            i = 0
            total = 0
            while ('sc_' + str(i)) in result:
                score = int(result['sc_' + str(i)])
                info['subtaskScores'].append(score)
                total += score
                dep = result['dp_' + str(i)]
                dep = dep.replace(" ","")
                if not verifyDependency(dep):
                    flash('Invalid subtask dependency', 'warning')
                    return redirect(f'/admin/editproblem/{problemName}')
                info['subtaskDependency'].append(dep)
                i += 1
            if total > 100:
                flash('Total score cannot be more than 100!', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            awstools.updateSubtaskInfo(problemName, info)
            awstools.validateProblem(f'{problemName}')
            return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'add_editorial':
            problem_info['editorials'].append("")
            info = {}
            info['editorials'] = problem_info['editorials']
            awstools.updateEditorialInfo(problemName, info)
            return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'remove_editorial':
            if (len(problem_info['editorials']) != 0):
                problem_info['editorials'].pop()
            info = {}
            info['editorials'] = problem_info['editorials']
            awstools.updateEditorialInfo(problemName, info)
            return redirect(f'/admin/editproblem/{problemName}')
        
        elif result['form_name'] == 'update_editorials':
            info = {}
            info['editorials'] = []
            i = 0
            while ('e_' + str(i)) in result:
                link = result['e_' + str(i)]
                info['editorials'].append(link)
                i += 1
            awstools.updateEditorialInfo(problemName, info)
            return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'add_access':
            problem_info['allowAccess'].append("")
            info = {}
            info['allowAccess'] = problem_info['allowAccess']
            awstools.updateAccessInfo(problemName, info)
            return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'remove_access':
            if (len(problem_info['allowAccess']) != 0):
                problem_info['allowAccess'].pop()
            info = {}
            info['allowAccess'] = problem_info['allowAccess']
            awstools.updateAccessInfo(problemName, info)
            return redirect(f'/admin/editproblem/{problemName}')
        
        elif result['form_name'] == 'update_access':
            info = {}
            info['allowAccess'] = []
            i = 0
            while ('u_' + str(i)) in result:
                link = result['u_' + str(i)]
                info['allowAccess'].append(link)
                i += 1
            awstools.updateAccessInfo(problemName, info)
            return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'checker_upload':
            if 'checker' not in files:
                flash('Statement not found', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            if files['checker'].filename == '':
                flash('Checker not found', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            file_name = files['checker'].filename
            if '.' not in file_name:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            ext_file = file_name.rsplit('.', 1)[1].lower()
            if ext_file == 'cpp':
                awstools.uploadChecker(files['checker'], f'source/{problemName}.cpp')
                response = awstools.compileChecker(problemName = problemName)

                if response['status'] == 200:
                    flash('Uploaded!', 'success')
                    awstools.validateProblem(f'{problemName}')
                    return redirect(f'/admin/editproblem/{problemName}')
                else:
                    flash(response['error'], 'warning')
                    return redirect(f'/admin/editproblem/{problemName}')
            else:
                flash('Compile Error', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'grader_upload':
            if 'grader' not in files:
                flash('Grader not found', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            if files['grader'].filename == '':
                flash('Grader not found', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            file_name = files['grader'].filename
            if '.' not in file_name:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            ext_file = file_name.rsplit('.', 1)[1].lower()
            if ext_file == 'cpp':
                awstools.uploadGrader(files['grader'], f'{problemName}/grader.cpp')
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problemName}')
                return redirect(f'/admin/editproblem/{problemName}')
            else:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'fileB_upload':
            if 'fileB' not in files:
                flash('Header not found', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            if files['fileB'].filename == '':
                flash('Header not found', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            file_name = files['fileB'].filename
            if '.' not in file_name:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            ext_file = file_name.rsplit('.', 1)[1].lower()
            if ext_file == 'h':
                name = problem_info['nameB']
                awstools.uploadGrader(files['fileB'], f'{problemName}/{name}.h')
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problemName}')
                return redirect(f'/admin/editproblem/{problemName}')
            else:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'fileA_upload':
            if 'fileA' not in files:
                flash('Header not found', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            if files['fileA'].filename == '':
                flash('Header not found', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            file_name = files['fileA'].filename
            if '.' not in file_name:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            ext_file = file_name.rsplit('.', 1)[1].lower()
            if ext_file == 'h':
                name = problem_info['nameA']
                awstools.uploadGrader(files['fileA'], f'{problemName}/{name}.h')
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problemName}')
                return redirect(f'/admin/editproblem/{problemName}')
            else:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] == 'header_upload':
            if 'header' not in files:
                flash('Header not found', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            if files['header'].filename == '':
                flash('Header not found', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            file_name = files['header'].filename
            if '.' not in file_name:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            ext_file = file_name.rsplit('.', 1)[1].lower()
            if ext_file == 'h':
                awstools.uploadGrader(files['header'], f'{problemName}/{problemName}.h')
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problemName}')
                return redirect(f'/admin/editproblem/{problemName}')
            else:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            
        elif result['form_name'] == 'attachments_upload':
            if 'attachments' not in files:
                flash('Attachments not found', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            if files['attachments'].filename == '':
                flash('Attachments not found', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            file_name = files['attachments'].filename
            if '.' not in file_name:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')
            ext_file = file_name.rsplit('.', 1)[1].lower()
            if ext_file == 'zip':
                awstools.uploadAttachments(files['attachments'], f'{problemName}.zip')
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problemName}')
                return redirect(f'/admin/editproblem/{problemName}')
            else:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] in ['regrade_problem', 'regrade_nonzero', 'regrade_acs']:
            # REGRADE PROBLEM

            # Regrade type can be NORMAL, AC, NONZERO
            regradeType = 'NORMAL'
            if result['form_name'] == 'regrade_nonzero': regradeType = 'NONZERO'
            if result['form_name'] == 'regrade_acs': regradeType = 'AC'

            if userInfo['role'] in ['admin','superadmin']:
                awstools.regradeProblem(problemName=problemName, regradeType=regradeType)
                flash('Regrade request sent to server!', 'success')
            else: 
                flash('You need admin access to do this', 'warning')
            return redirect(f'/admin/editproblem/{problemName}')

        elif result['form_name'] in ['enableHideSubmissions', 'disableHideSubmssions']:
            if not creatorOptions['show']:
                flash('idk what you are doing but it shouldnt be allowed', 'danger')
                return redirect(f'/admin/editproblem/{problemName}')
            
            if creatorOptions['isHideSubmissions']:
                awstools.setProblemToHideSubmissions(problemName, False)
            else:
                awstools.setProblemToHideSubmissions(problemName, True)

    return render_template('editproblem.html', form=form, info=problem_info, userinfo=userInfo, subsURL=subsURL, socket=contestmode.socket(), tags=tagList, creatorOptions=creatorOptions)
