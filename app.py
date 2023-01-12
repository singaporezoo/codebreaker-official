import flask
from flask import Flask,Blueprint,session,flash,redirect,url_for,render_template,abort, send_from_directory
from jinja2 import TemplateNotFound
from flask_apscheduler import APScheduler

from waitress import serve
from authlib.integrations.flask_client import OAuth
from main.auth_decorator import login_required

import io
import sys
import json
from password import FLASK_SECRET_KEY, GOOGLE_CLIENT_SECRET
from pytz import utc

from main import problemlistview, submissionview, newuserview, profileview, submissionlistview, contestview, contestlistview, scoreboardview, credits, rankingsview, contestgroupview, editprofileview, problemview, announcelistview, announceview, defaultview, clarificationsview, homeview
from admin import adminview, editproblemlistview, editusersview, editproblemview, editcontestlistview, editcontestview, editannouncelistview, editannounceview, editcontestgroupview, editclarificationsview, viewsubmissions

import awstools #awstools.py contains helper functions for AWS reading and writing to S3 and DB.
import contestmode

from datetime import datetime,timedelta

app = Flask(__name__)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

if contestmode.contest():
    from flask_socketio import SocketIO, send, join_room
    socketio = SocketIO(app, cors_allowed_origins="*")

app.config['SECRET_KEY'] = FLASK_SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 64
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['SESSION_COOKIE_SECURE'] = True

app.add_url_rule('/problems', view_func = problemlistview.problemlist)
app.add_url_rule("/problem/<PROBLEM_NAME>", methods=["GET","POST"], view_func=problemview.problem)
app.add_url_rule('/submission/<subId>', view_func = submissionview.submission, methods = ['GET', 'POST'])
app.add_url_rule('/contests', view_func = contestlistview.contestlist)
app.add_url_rule('/contest/<contestId>', view_func = contestview.contest, methods = ['GET', 'POST'])
app.add_url_rule('/contest/<contestId>/scoreboard', view_func = scoreboardview.scoreboard)
app.add_url_rule('/submissions',view_func = submissionlistview.submissionlist, methods=['GET', 'POST'])
app.add_url_rule('/newuser', view_func = newuserview.newuser, methods = ['GET', 'POST'])
app.add_url_rule('/profile/<username>', view_func = profileview.profile)
app.add_url_rule('/admin',view_func=adminview.admin)
app.add_url_rule('/admin/editproblems',view_func=editproblemlistview.editproblemlist, methods = ['GET', 'POST'])
app.add_url_rule('/admin/editusers',view_func=editusersview.editusers)
app.add_url_rule('/admin/edituserrole',view_func=editusersview.editUserRole, methods = ['POST'])
app.add_url_rule('/admin/editproblemtags', view_func = editproblemview.editProblemTags, methods=['POST'])
app.add_url_rule('/credits',view_func=credits.credits)
app.add_url_rule('/admin/editproblem/<problem_id>', view_func = editproblemview.editproblem, methods = ['GET', 'POST'])
app.add_url_rule('/admin/editcontests',view_func=editcontestlistview.editcontestlist, methods=['GET', 'POST'])
app.add_url_rule('/admin/editcontest/<contestId>', view_func = editcontestview.editcontest, methods = ['GET', 'POST'])
app.add_url_rule('/rankings', view_func = rankingsview.rankings)
app.add_url_rule('/admin/uploadtestdata/<problemId>', view_func = uploadtestdataview.uploadtestdata, methods = ['GET'])
app.add_url_rule('/admin/editcontestproblems',view_func=editcontestview.editcontestproblems, methods = ['POST'])
app.add_url_rule('/admin/editcontestgroupcontests',view_func=editcontestgroupview.editcontestgroupcontests, methods = ['POST'])
app.add_url_rule('/admin/editcontestgroupgroups',view_func=editcontestgroupview.editcontestgroupgroups,methods=['POST'])
app.add_url_rule('/group/<groupId>', view_func=contestgroupview.contestgroup)
app.add_url_rule('/editprofile', view_func=editprofileview.editprofile, methods=['GET','POST'])
app.add_url_rule('/admin/editannouncements', view_func=editannouncelistview.editannouncelist, methods=['GET','POST'])
app.add_url_rule('/admin/editannouncement/<announceId>', view_func=editannounceview.editannounce, methods=['GET','POST'])
app.add_url_rule('/announcements', view_func=announcelistview.announcelist)
app.add_url_rule('/announcement/<announceId>', view_func=announceview.announce)
app.add_url_rule('/admin/editgroup/<groupId>', view_func=editcontestgroupview.editcontestgroup, methods=['GET','POST'])
app.add_url_rule('/clarifications', view_func=clarificationsview.clarifications, methods=['GET','POST'])
app.add_url_rule('/admin/editclarifications', view_func=editclarificationsview.editclarifications, methods=['GET','POST'])
app.add_url_rule('/admin/viewsubmissions/<problemName>', view_func = viewsubmissions.viewsubmissions, methods=['GET','POST'])
app.add_url_rule('/', view_func = homeview.home)

def cppref(path):
    if contestmode.contest() and not contestmode.cppref():
        return "Sorry, you cannot access this resource in contest mode!"
    return send_from_directory('static/cppreference/reference/en',path)
app.add_url_rule("/cppreference/<path:path>", view_func=cppref)
def cppref2(path):
    if contestmode.contest() and not contestmode.cppref():
        return "Sorry, you cannot access this resource in contest mode!"
    return send_from_directory('static/cppreference/reference/common',path)
app.add_url_rule("/common/<path:path>", view_func=cppref2)

#BEGIN: LOGIN -----------------------------------------------------------------------------------------------------------------------------------------------------------

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id="447432932037-5m4ucr9rq8p06otf37rml90a2rsdro4o.apps.googleusercontent.com",
    client_secret=GOOGLE_CLIENT_SECRET,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)

@app.route('/login')
def login():
    for key in list(session.keys()):
        session.pop(key)
    google = oauth.create_client('google')  # create the google oauth client
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')  # create the google oauth client
    token = google.authorize_access_token()  # Access token from google (needed to get user info)
    resp = google.get('userinfo')  # userinfo contains stuff u specificed in the scrope
    user_info = resp.json()
    user = oauth.google.userinfo()  # uses openid endpoint to fetch user info
    # Here you use the profile/user data that you got and query your database find/register the user
    # and set ur own data in the session not the profile from google
    session['profile'] = user_info
    session.permanent = True  # make the session permanant so it keeps existing after broweser gets closed
    
    newUser = (awstools.getCurrentUserInfo()['username'] in ['', 'placeholder'])
    if newUser:
        return redirect('newuser')
    else:
        flash('Quack! You have logged in successfully!', 'success')
        return redirect('/')


@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    flash('Meow. Logout successful', 'info')
    return redirect('/')

#END: LOGIN ------------------------------------------------------------------------------------------------------------------------------------------------------------

if contestmode.contest():
    @socketio.on('message')
    def handlemessage(msg):
        if msg == 'newclarification' or msg == 'adminannounce': #create new clarification, send to all admins
            send(msg, room='admin')
        elif msg == 'announce':
            send(msg, broadcast=True)
        else:
            send(msg, room=msg) #answered clarification, send to room with username

    @socketio.on('online')
    def handleonline(data):
        if len(data['username']) == 0:
            return
        join_room(data['username'])
        if 'admin' in data['role']:
            join_room('admin')

def handleEndParticipation(contestId, username):
    #print(f'handleEnd {contestId} {username}')
    awstools.endParticipation(contestId, username)
    awstools.removeEndContest(f'{contestId} {username}')

def addEndParticipation(contestId, username, time):
    #print(f'addEnd {contestId} {username} {time}')
    try:
        scheduler.remove_job(f'{contestId} {username}')
    except:
        pass
    scheduler.add_job(id=f'{contestId} {username}',func=handleEndParticipation,args=[contestId, username],trigger='date',run_date=time,timezone=utc)
    awstools.updateEndContest(f'{contestId} {username}', time)

if __name__ == '__main__':

    for e in awstools.getAllEndContests():
        if e['endtime'] < datetime.now():
            contestId, username = e['eventId'].split(' ')
            handleEndParticipation(contestId, username)
        else:
            scheduler.add_job(id=e['eventId'],func=handleEndParticipation,args=e['eventId'].split(' '),trigger='date',run_date=e['endtime'],timezone=utc)

    if len(sys.argv) <= 1 or sys.argv[1] != "develop":
        print("DEPLOY MODE")
        if not contestmode.contest():
            print("Deploy without contest mode")
            serve(app, host='0.0.0.0', port=5000, url_scheme='https', threads = 16)
        else:
            print("Deploy with contest mode")
            #socketio.run(app, host='0.0.0.0', use_reloader=False)
            serve(app, host='0.0.0.0', port=5000, url_scheme='https', threads = 100)
            socketio.run(app, host='0.0.0.0', port=5000, certfile='../codebreaker_xyz.crt', keyfile='../codebreaker_xyz.key')
    else:
        print("DEVELOP MODE")
        if not contestmode.contest():
            print("Develop without contest mode")
            app.run(debug=True, host='0.0.0.0', port=443, ssl_context=('../codebreaker_xyz.crt', '../codebreaker_xyz.key'))
        else:
            print("Develop with contest mode")
            socketio.run(app, debug=True, host='0.0.0.0', port=443, certfile='../codebreaker_xyz.crt', keyfile='../codebreaker_xyz.key')
