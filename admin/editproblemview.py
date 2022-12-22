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

def editproblem(problem_id):
    userInfo = awstools.getCurrentUserInfo()
    if userInfo == None or (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin'):
        flash("Admin access is required", "warning")
        return redirect("/")

    if contestmode.contest() and (userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers()):
        flash("You do not have access in contest mode", "warning")
        return redirect("/")
    
    problem_info = awstools.getProblemInfo(problem_id)
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
        form.problem_type.choices = ["Batch", "Communcation", "Interactive"]
    else:
        form.problem_type.choices = ["Communication", "Batch", "Interactive"]

    subsURL = f'admin/viewsubmissons/{problem_id}'

    if 'tags' not in problem_info.keys():
        problem_info['tags'] = []

    tagList = []
    for i in tags.tags():
        if i in problem_info['tags']:
            tagList.append([i,True])
        else:
            tagList.append([i,False])

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
                        return redirect(f'/admin/editproblem/{problem_id}')
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
                    return redirect(f'/admin/editproblem/{problem_id}')
            info['contestLink'] = result['contest_link']
            if info['superhidden'] and ('allowAccess' not in problem_info):
                awstools.addAllowAccess(problem_id)
            awstools.updateProblemInfo(problem_id, info)
            if problem_info['problem_type'] == 'Communication':
                awstools.updateCommunicationFileNames(problem_id,info)
            return redirect(f'/admin/editproblem/{problem_id}')
        
        elif result['form_name'] == 'statement_upload':
            if 'statement' not in files:
                flash('Statement not found', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            if files['statement'].filename == '':
                flash('Statement not found', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            file_name = files['statement'].filename
            if '.' not in file_name:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            ext_file = file_name.rsplit('.', 1)[1].lower()
            if ext_file == 'pdf':
                awstools.uploadStatement(files['statement'], f'{problem_id}.pdf')
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problem_id}')
                return redirect(f'/admin/editproblem/{problem_id}')
            elif ext_file == 'html':
                awstools.uploadStatement(files['statement'], f'{problem_id}.html')
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problem_id}')
                return redirect(f'/admin/editproblem/{problem_id}')
            else:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'delete_html':
            awstools.deleteStatement(f'{problem_id}.html')
            flash('HTML statement deleted!', 'success')
            awstools.validateProblem(f'{problem_id}')
            return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'delete_pdf':
            awstools.deleteStatement(f'{problem_id}.pdf')
            flash('PDF statement deleted!', 'success')
            awstools.validateProblem(f'{problem_id}')
            return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'sync_testcases':
            awstools.testcaseUploadLambda(f'{problem_id}')
            return redirect(f'/admin/editproblem/{problem_id}')
       
        elif result['form_name'] == 'update_count':
            awstools.updateCountLambda(f'{problem_id}')
            flash('Updated number of testcases!', 'success')
            awstools.validateProblem(f'{problem_id}')
            return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'validate':
            awstools.validateProblem(f'{problem_id}')
            flash('Validated problem!','success')
            return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'add_subtask':
            problem_info['subtaskScores'].append(0)
            problem_info['subtaskDependency'].append('1')
            info = {}
            info['subtaskScores'] = problem_info['subtaskScores']
            info['subtaskDependency'] = problem_info['subtaskDependency']
            awstools.updateSubtaskInfo(problem_id, info)
            return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'remove_subtask':
            if len(problem_info['subtaskScores']) == 1:
                flash('hisssss! cannot have less than one subtask', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            problem_info['subtaskScores'].pop()
            problem_info['subtaskDependency'].pop()
            info = {}
            info['subtaskScores'] = problem_info['subtaskScores']
            info['subtaskDependency'] = problem_info['subtaskDependency']
            awstools.updateSubtaskInfo(problem_id, info)
            return redirect(f'/admin/editproblem/{problem_id}')

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
                    return redirect(f'/admin/editproblem/{problem_id}')
                info['subtaskDependency'].append(dep)
                i += 1
            if total > 100:
                flash('Total score cannot be more than 100!', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            awstools.updateSubtaskInfo(problem_id, info)
            awstools.validateProblem(f'{problem_id}')
            return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'add_editorial':
            problem_info['editorials'].append("")
            info = {}
            info['editorials'] = problem_info['editorials']
            awstools.updateEditorialInfo(problem_id, info)
            return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'remove_editorial':
            if (len(problem_info['editorials']) != 0):
                problem_info['editorials'].pop()
            info = {}
            info['editorials'] = problem_info['editorials']
            awstools.updateEditorialInfo(problem_id, info)
            return redirect(f'/admin/editproblem/{problem_id}')
        
        elif result['form_name'] == 'update_editorials':
            info = {}
            info['editorials'] = []
            i = 0
            while ('e_' + str(i)) in result:
                link = result['e_' + str(i)]
                info['editorials'].append(link)
                i += 1
            awstools.updateEditorialInfo(problem_id, info)
            return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'add_access':
            problem_info['allowAccess'].append("")
            info = {}
            info['allowAccess'] = problem_info['allowAccess']
            awstools.updateAccessInfo(problem_id, info)
            return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'remove_access':
            if (len(problem_info['allowAccess']) != 0):
                problem_info['allowAccess'].pop()
            info = {}
            info['allowAccess'] = problem_info['allowAccess']
            awstools.updateAccessInfo(problem_id, info)
            return redirect(f'/admin/editproblem/{problem_id}')
        
        elif result['form_name'] == 'update_access':
            info = {}
            info['allowAccess'] = []
            i = 0
            while ('u_' + str(i)) in result:
                link = result['u_' + str(i)]
                info['allowAccess'].append(link)
                i += 1
            awstools.updateAccessInfo(problem_id, info)
            return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'checker_upload':
            if 'checker' not in files:
                flash('Statement not found', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            if files['checker'].filename == '':
                flash('Checker not found', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            file_name = files['checker'].filename
            if '.' not in file_name:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            ext_file = file_name.rsplit('.', 1)[1].lower()
            if ext_file == 'cpp':
                awstools.uploadChecker(files['checker'], f'source/{problem_id}.cpp')
                awstools.getChecker(problem_id, f'tmp/checkers/{problem_id}.cpp')

                sourceName = f"tmp/checkers/{problem_id}.cpp"
                compiledName = f"tmp/checkers/{problem_id}"

                try:
                    cmd=f"g++ -O2 -o {compiledName} {sourceName} -m64 -static -std=gnu++14 -lm -s -w -Wall"
                    #print(cmd)
                    subprocess.run(cmd, shell=True, check=True)
		
                except:
                    flash("Checker Compile Error!", 'warning')
                    return redirect(f'/admin/editproblem/{problem_id}')

                awstools.uploadCompiledChecker(compiledName, f'compiled/{problem_id}')
                subprocess.run(f"rm {sourceName}", shell=True)
                subprocess.run(f"rm {compiledName}", shell=True)
                
                # Compile checker
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problem_id}')
                return redirect(f'/admin/editproblem/{problem_id}')
            else:
                flash('Compile Error', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'grader_upload':
            if 'grader' not in files:
                flash('Grader not found', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            if files['grader'].filename == '':
                flash('Grader not found', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            file_name = files['grader'].filename
            if '.' not in file_name:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            ext_file = file_name.rsplit('.', 1)[1].lower()
            if ext_file == 'cpp':
                awstools.uploadGrader(files['grader'], f'{problem_id}/grader.cpp')
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problem_id}')
                return redirect(f'/admin/editproblem/{problem_id}')
            else:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'fileB_upload':
            if 'fileB' not in files:
                flash('Header not found', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            if files['fileB'].filename == '':
                flash('Header not found', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            file_name = files['fileB'].filename
            if '.' not in file_name:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            ext_file = file_name.rsplit('.', 1)[1].lower()
            if ext_file == 'h':
                name = problem_info['nameB']
                awstools.uploadGrader(files['fileB'], f'{problem_id}/{name}.h')
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problem_id}')
                return redirect(f'/admin/editproblem/{problem_id}')
            else:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'fileA_upload':
            if 'fileA' not in files:
                flash('Header not found', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            if files['fileA'].filename == '':
                flash('Header not found', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            file_name = files['fileA'].filename
            if '.' not in file_name:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            ext_file = file_name.rsplit('.', 1)[1].lower()
            if ext_file == 'h':
                name = problem_info['nameA']
                awstools.uploadGrader(files['fileA'], f'{problem_id}/{name}.h')
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problem_id}')
                return redirect(f'/admin/editproblem/{problem_id}')
            else:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] == 'header_upload':
            if 'header' not in files:
                flash('Header not found', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            if files['header'].filename == '':
                flash('Header not found', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            file_name = files['header'].filename
            if '.' not in file_name:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            ext_file = file_name.rsplit('.', 1)[1].lower()
            if ext_file == 'h':
                awstools.uploadGrader(files['header'], f'{problem_id}/{problem_id}.h')
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problem_id}')
                return redirect(f'/admin/editproblem/{problem_id}')
            else:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            
        elif result['form_name'] == 'attachments_upload':
            if 'attachments' not in files:
                flash('Attachments not found', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            if files['attachments'].filename == '':
                flash('Attachments not found', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            file_name = files['attachments'].filename
            if '.' not in file_name:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')
            ext_file = file_name.rsplit('.', 1)[1].lower()
            if ext_file == 'zip':
                awstools.uploadAttachments(files['attachments'], f'{problem_id}.zip')
                flash('Uploaded!', 'success')
                awstools.validateProblem(f'{problem_id}')
                return redirect(f'/admin/editproblem/{problem_id}')
            else:
                flash('Invalid file format', 'warning')
                return redirect(f'/admin/editproblem/{problem_id}')

        elif result['form_name'] in ['regrade_problem', 'regrade_nonzero', 'regrade_acs']:
            # REGRADE PROBLEM

            # Regrade type can be NORMAL, AC, NONZERO
            regrade_type = 'NORMAL'
            if result['form_name'] == 'regrade_nonzero': regrade_type = 'NONZERO'
            if result['form_name'] == 'regrade_acs': regrade_type = 'AC'

            if userInfo['role'] in ['admin','superadmin']:
                awstools.regradeProblem(problemName=probleem_id, regrade_type=regrade_type)
                flash('Regrade request sent to server!', 'success')
            else: 
                flash('You need admin access to do this', 'warning')
            return redirect(f'/admin/editproblem/{problem_id}')


    return render_template('editproblem.html', form=form, info=problem_info, userinfo=userInfo, subsURL=subsURL, socket=contestmode.socket(), tags=tagList)
