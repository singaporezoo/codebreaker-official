from flask import render_template, session, flash, request, redirect
import tags
import awstools
import contestmode

def problemlist():
    if contestmode.contest():
        return redirect(f'/contest/{contestmode.contestId()}')

    command = request.args.get('command')
    if command != 'newest' and command != None and command != 'unsolved' and command != 'recommended':
        flash('Invalid url!', 'warning')
        return redirect('/')
    sortable = True
    if command == 'newest':
        sortable = False

    problems = awstools.getAllProblemsLimited()
    userInfo = awstools.getCurrentUserInfo()
    problemScores = {}
    if userInfo != None:
        problemScores = userInfo['problemScores']
    for i in problems:
        if 'tags' not in i.keys():
            i['tags'] = []
        else:
            i['tagtext'] = 'Tags: '
            for j in i['tags']:
                i['tagtext'] += j
                if j != i['tags'][-1]:
                    i['tagtext'] += ', '

    problemInfo = [dict((key,value) for key, value in P.items() if key in ['problemName','analysisVisible','title', 'source', 'author','problem_type','noACs','contestLink', 'createdTime', 'EE', 'tags', 'tagtext']) for P in problems] #impt info goes into the list (key in [list])
    problemInfo = [problem for problem in problemInfo if problem['analysisVisible']] # Filter out hidden problems
    problemInfo.sort(key = lambda x:-x['noACs'])

    if command == 'newest':
        problemInfo.sort(key = lambda x:x['createdTime'])
        problemInfo.reverse()
    if command == 'unsolved':
        if not userInfo is None:
            problemInfo = [problem for problem in problemInfo if not (problem['problemName'] in userInfo['problemScores'] and userInfo['problemScores'] [problem['problemName']] == 100 ) ]
    if command == 'recommended':
        if userInfo is None:
            flash('Please login to access this feature!', 'warning')
            return redirect('/')
        else:
            rec = awstools.getRecommendedProblems(userInfo['username'])
            tmp = []
            for i in range(1, 10):
                if str(i) not in rec:
                    continue
                for problemName in rec[str(i)]:
                    problem = [problem.copy() for problem in problemInfo if problem['problemName'] == problemName][0]
                    problem['diff'] = i
                    tmp.append(problem)
            problemInfo = tmp
    
    for i in range(len(problemInfo)):
        name = problemInfo[i]['problemName']
        score = "N/A" 
        if name in problemScores:
            score = problemScores[name]
        problemInfo[i]['yourScore'] = score

        authors = problemInfo[i]["author"]
        problemInfo[i]["author"] = [x.replace(" ", "") for x in authors.split(",")]

    ''' FILTER OUT THE PROBLEMS THAT ARE IN CONTEST SO #AC CANNOT BE SEEN '''
    contestproblems = contestmode.contestproblems()
    if contestmode.contest():
        problemInfo = [problem for problem in problemInfo if problem['problemName'] not in contestproblems]

    ''' Tags '''
    tag = tags.tags()
    tagList = [[i,len([j for j in problemInfo if i in j['tags']])] for i in tag]
    
    return render_template('problemlist.html', problemInfo=problemInfo, userinfo=awstools.getCurrentUserInfo(), sortable=sortable, command = command, socket=contestmode.socket(), tags=tagList)
