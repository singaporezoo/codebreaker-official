import os
import csv
import awstools
import datetime
from pprint import pprint

TIMEZERO = datetime.datetime(year=2005,month=1,day=18)

def StringToDate(s):
	return datetime.datetime.strptime(s,"%Y-%m-%d %X")

def lambda_handler(event,context):
	
	os.chdir('/tmp')
	
	TOTAL_SUBMISSIONS = 0
	SKIPPED = 0
	PROCESSED_SUBMISSIONS = 0

	contestId = event['contestId']
	contestInfo = awstools.getContestInfo(contestId)
	endTime = contestInfo['endTime']
	startTime = contestInfo['startTime']

	if endTime == 'Unlimited':
		endTime = datetime.datetime(year=3000,month=1,day=18)
	else:
		endTime = StringToDate(contestInfo['endTime'])
	
	startTime = StringToDate(contestInfo['startTime'])
	
	problems = contestInfo['problems']
	users = list(contestInfo['users'].keys())
	usersDict = {}
	for i in users:usersDict[i] = True

	def userInContest(user):
		return user in usersDict

	allProblemsInfo = {}
	for problem in problems:
		info = awstools.getProblemInfo(problem)
		info['subtaskCount'] = len(info['subtaskScores'])
		def dependencyFix(dependency):
			out = []
			for i in range(len(dependency)):
				tmp = dependency[i].split(',')
				res = []
				for tcrange in tmp:
					tcrange = [int(tc) for tc in tcrange.split('-')]
					if len(tcrange)==1:
						tcrange = [tcrange[0],tcrange[0]]
					res.append(tcrange)
				out.append(res)
			return out

		info['subtaskDependency'] = dependencyFix(info['subtaskDependency'])
		info['testcaseCount'] = int(info['testcaseCount'])
		allProblemsInfo[problem] = info

	lastScoreChange = {}
	for user in users:
		lastScoreChange[user] = TIMEZERO
	# I'm checking if there is bug when u change one, all

	results = {}
	emptyUser = {}
	for problem in problems:
		emptyUser[problem] = [0] * allProblemsInfo[problem]['subtaskCount']

	for user in users:
		newEmptyUser = {}
		for x in emptyUser:
			newEmptyUser[x] = emptyUser[x].copy()
		results[user] = newEmptyUser

	for problem in problems:
		problemInfo = allProblemsInfo[problem]
		submissions = awstools.getSubmissionsListProblem(problem)
		submissions.sort(key = lambda x:x['submissionTime'])
		TOTAL_SUBMISSIONS += len(submissions)
		for submission in submissions:
			submissionUsername = submission['username']
			if not userInContest(submissionUsername):
				continue # User is not in contest
			if (min(results[submissionUsername][problem]) == 100):
				continue # Full score already
			submissionTimeString = submission['submissionTime']
			submissionTime = StringToDate(submissionTimeString)
			if submissionTime >= endTime:
				continue
			scores = submission['score']
			if (len(scores) - 1 != problemInfo['testcaseCount']):
				# Subtract 1 because scores is a 1-indexed array
				continue # Invalid submission, could cause breakdown later 
			PROCESSED_SUBMISSIONS+=1
			for subtask in range(problemInfo['subtaskCount']):
				if results[submissionUsername][problem][subtask] == 100:
					continue # Full score of subtask already
				subtaskRanges = problemInfo['subtaskDependency'][subtask]
				subtaskScore = 100
				for r in subtaskRanges:
					for tc in range(r[0],r[1]+1):
						subtaskScore = min(subtaskScore,scores[tc])
				if results[submissionUsername][problem][subtask] < subtaskScore:
					results[submissionUsername][problem][subtask] = subtaskScore
					lastScoreChange[submissionUsername] = max(lastScoreChange[submissionUsername],submissionTime)

	for user in users:
		if lastScoreChange[user] == TIMEZERO:
			lastScoreChange[user] = 'N/A'
		elif lastScoreChange[user] < startTime:
			lastScoreChange[user] = 'N/A'
		else:
			lastScoreChange[user] -= startTime
			lastScoreChange[user] = str(lastScoreChange[user])
		
	scoreboard = []
	for username in users:
		problemScores = {}
		totalScore = 0
		for problem in problems:
			problemInfo = allProblemsInfo[problem]
			problemScore = 0
			for subtask in range(problemInfo['subtaskCount']):
				subtaskMaxScore = problemInfo['subtaskScores'][subtask]
				userScore = results[username][problem][subtask]
				problemScore += userScore * subtaskMaxScore / 100
			problemScore = round(float(problemScore),2)
			problemScores[problem] = problemScore
			totalScore += problemScore
			if int(problemScores[problem]) == problemScores[problem]:
				problemScores[problem] = int(problemScores[problem])

		totalScore = round(totalScore,2)
		if int(totalScore) == totalScore: totalScore = int(totalScore)
		obj = {'username':username,'problemScores':problemScores, 'totalScore':totalScore}
		scoreboard.append(obj)

	def intoSeconds(username):
		if username not in lastScoreChange.keys(): return 0
		if lastScoreChange[username] == 'N/A': return 0
		time = (datetime.datetime.strptime(lastScoreChange[username], '%H:%M:%S') - datetime.datetime(1900, 1, 1)).total_seconds()
		return int(time)

	scoreboard.sort(key = lambda x:x['totalScore'] * 100000 - intoSeconds(x['username'])) 
	scoreboard.reverse() # Write with largest first
	trueRank = 0
	currentRank = 0
	previousScore = 1e9

	with open(f'{contestId}.csv','w', encoding='UTF8') as f:
		writer = csv.writer(f) # Declaring csv writer 
		# https://www.pythontutorial.net/python-basics/python-write-csv-file/

		headerRow = ['Rank','Username']
		for i in problems:
			headerRow.append(i)
		headerRow.append('Total Score')
		headerRow.append('Time')
		writer.writerow(headerRow)

		for user in scoreboard:
			trueRank += 1
			if user['totalScore'] < previousScore:
				currentRank = trueRank
			previousScore = user['totalScore']

			userRow = [currentRank]
			userRow.append(user['username'])
			for problem in problems:
				userRow.append(user['problemScores'][problem])
			userRow.append(user['totalScore'])
			userRow.append(lastScoreChange[user['username']])
			writer.writerow(userRow)

		f.close()

	awstools.scoreboardUpload(f'{contestId}.csv')

	print(f"Success after processing {TOTAL_SUBMISSIONS} submissions (with {PROCESSED_SUBMISSIONS} processed) and skipping {SKIPPED} submissions")

	return {
		'status':200
	}

if __name__ == '__main__':
	lambda_handler({'contestId': 'sgpsparring21'},None)