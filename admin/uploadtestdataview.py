import awstools
import json
from flask import Flask, render_template, request, url_for, redirect, flash, session, get_flashed_messages, make_response, send_file

def uploadtestdata(problemId):
	userInfo = awstools.getCurrentUserInfo()
	problemInfo = awstools.getProblemInfo(problemId)

	if problemInfo == None:
		flash('This problem does not exist', 'warning')
		return redirect('/admin')

	if userInfo == None or userInfo['role'] != 'admin':
		flash ('You are not authorised to view this resource!', 'danger')
		return redirect('/')

	credentials = awstools.getTokens(problemId)
	credentials = json.dumps(credentials)

	return render_template('uploadtestdata.html', userinfo=userInfo, probleminfo=problemInfo, stsKeys=credentials)