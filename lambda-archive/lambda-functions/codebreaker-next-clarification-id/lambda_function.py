# Model works on the general principle of Kth Nearest Neighbours
# For each user, we make a list of all the problems solved by them
# We then find the top 10 users with the highest correlation of solved problems and give further multiplier, since these problems solved are likely the best indicators
# Reconmend the problems based on that

import json
from lib import pearsonr
import awstools
from pprint import pprint

T = [0, 0, 0.4, 0.7, 0.75, 0.8, 1, 30]

def build():
	usersInfo = awstools.getUsersTable()
	problems = set()
	for user in usersInfo:
		for problem in user['problemScores']:
			if float(user['problemScores'][problem]) >= 50:
				problems.add(problem)
	problemIds = {}
	numScore = [0 for i in range(len(problems))]
	t=0
	for i in problems:
		problemIds[i] = t
		t+=1

	data = {}
	for user in usersInfo:
		unx = 1
		for problem in user['problemScores']:
			x = float(user['problemScores'][problem])
			if x >= 50: unx = 0
		if unx == 1:continue

		data[user['username']] = [0 for i in range(len(problems))]
		for problem in user['problemScores']:
			if float(user['problemScores'][problem]) < 50: 
				continue
			else:
				id = problemIds[problem]
				numScore[id]+=1
				data[user['username']][id] = float(user['problemScores'][problem])

	return data, problemIds, numScore

def recommend(username, data, problemIds, numScore):
	N = len(problemIds)

	corr = {}
	corx = []
	for user in data:
		if user == username:
			continue
		P = pearsonr(data[username], data[user])
		corr[user] = P**2
		corx.append([P, user])

	corx.sort(key = lambda x:-x[0])

	tx = 0
	for i in range(100):
		tx += corx[i][0]
		corr[corx[i][1]] += tx/(i+1)
		
	# Adding additional weight to 100 top users

	problemValues = [0 for i in range(N)]

	for user in data:
		if user == username:continue
		P = corr[user]
		for i in range(N):
			val = data[user][i]*P
			problemValues[i] += val

	allProblemInfo = awstools.getAllProblemsLimited()
	userInfo = awstools.getUserInfoFromUsername(username)

	def run(coeff):

		bestProblems = []
		for problem in problemIds:
			id = problemIds[problem]
			val = problemValues[id]
			bestProblems.append([val/(numScore[id]**coeff),problem])
			# This reduces biases towards problems solved by few people (high dividing factor) or too many (small dividing factor)

		bestProblems.sort(key = lambda x:-x[0])


		# Filtering off problems that are a) not on analysis mode or b) not 
		
		bestProblems = [p for p in bestProblems if allProblemInfo[p[1]]['analysisVisible'] == True]

		bestProblems = [p for p in bestProblems if p[1] not in userInfo['problemScores'].keys() or int(userInfo['problemScores'][p[1]]) != 100]	

		suggest = [i[1] for i in bestProblems[:10]]

		return suggest

	results = {}

	for i in range(1,8):
		coeff = T[i]
		results[i] = run(coeff)

	return results

def lambda_handler(event, context):
    # Structure will be {'user': '0rang3'}
    data, problemIds, numScore = build()
    return recommend(event['user'], data, problemIds, numScore)

if __name__ == '__main__':
	pprint(lambda_handler({'user': 'zaneyu'}, None))