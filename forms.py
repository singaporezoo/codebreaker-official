from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, BooleanField, SelectField, SubmitField, TextAreaField, validators

class SubmitForm(FlaskForm):
    code = TextAreaField('Code Goes Here')
    codeA = TextAreaField('Code Goes Here')
    codeB = TextAreaField('Code Goes Here')
    language = SelectField('language')
    submit = SubmitField('Submit Code')

class ResubmitForm(FlaskForm):
    code = TextAreaField('Code Goes Here')
    codeA = TextAreaField('Code Goes Here')
    codeB = TextAreaField('Code Goes Here')
    submit = SubmitField('Resubmit')

class NewUserForm(FlaskForm):
    username = StringField('username')
    name = StringField('name')
    school = StringField('school')
    submit = SubmitField('Register')
    nation = SelectField('nation')

class EditProfileForm(FlaskForm):
    name = StringField('name')
    school = StringField('school')
    theme = SelectField('theme')
    hue = DecimalField('hue')
    submit = SubmitField('Save')

class searchSubmissionForm(FlaskForm):
    username = StringField('username')
    problem = StringField('problem')
    submit = SubmitField('Search')

class updateProblemForm(FlaskForm):
    problem_title = StringField('problem_title')
    problem_author = StringField('problem_author')
    problem_source = StringField('problem_source')
    problem_type = SelectField('problem_type')
    contest_link = StringField('contest_link')
    time_limit = DecimalField('time_limit')
    memory_limit = IntegerField('memory_limit')
    feedback = BooleanField('feedback')
    editorial_visible = BooleanField('editorial_visible')
    analysis = BooleanField('analysis')
    checker = BooleanField('checker')
    superhidden = BooleanField('superhidden')
    attachments = BooleanField('attachments')
    submit = SubmitField('Update')
    nameA = StringField('nameA')
    nameB = StringField('nameB')
    ee = BooleanField('ee')
    public_statement = BooleanField('public_statement')

class addProblemForm(FlaskForm):
    problem_id = StringField('problem_id')
    submit = SubmitField('Add Problem')

class beginContestForm(FlaskForm):
    submit = SubmitField('Begin Contest')

class addContestForm(FlaskForm):
    contest_id = StringField('contest_id')
    group_id = StringField('group_id')
    submit = SubmitField('Add Contest')

class updateContestForm(FlaskForm):
    contest_name = StringField('contest_name')
    contest_duration = StringField('contest_duration')
    contest_start = StringField('contest_start')
    contest_end = StringField('contest_end')
    contest_description = TextAreaField('contest_description')
    contest_public = BooleanField('contest_public')
    contest_scoreboardpublic = BooleanField('contest_scoreboardpublic')
    editorial_visible = BooleanField('editorial_visible')
    editorial = StringField('editorial')
    contest_sub_limit = DecimalField('sub_limit')
    contest_sub_delay = DecimalField('sub_delay')
    submit = SubmitField('Update')

class updateContestGroupForm(FlaskForm):
    contest_group_name = StringField('contest_group_name')
    contest_group_description = TextAreaField('contest_group_description')
    contest_group_visible = BooleanField('contest_group_visible')
    submit = SubmitField('Update')

class addAnnouncementForm(FlaskForm):
    announce_id = StringField('announce_id')
    submit = SubmitField('Add Announcement')

class updateAnnouncementForm(FlaskForm):
    announce_name = StringField('announce_name')
    announce_summary = TextAreaField('announce_summary')
    announce_text = TextAreaField('announce_text')
    announce_visible = BooleanField('announce_visible')
    announce_admin_only = BooleanField('announce_admin_only')
    announce_link = StringField('announce_link')
    submit = SubmitField('Update')

class addClarificationForm(FlaskForm):
    clarification_question = TextAreaField('clarification_question')
    clarification_problem_id = StringField('clarification_problem_id')
    submit = SubmitField('Add Clarification')

class answerClarificationForm(FlaskForm):
    clarification_id = DecimalField('clarification_id')
    clarification_answer = StringField('clarification_answer')
    submit = SubmitField('Answer')
