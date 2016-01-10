from flask import Flask, render_template, request, redirect, url_for, abort
from flask.ext.script import Manager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate,MigrateCommand
import datetime
import cloudinary.uploader

app = Flask(__name__)
app.config.from_object('kickstarterclone.default_settings')
manager = Manager(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

from kickstarterclone.models import *

@app.route("/") #Home directory
def hello():
    projects = db.session.query(Project).order_by(Project.time_created.desc()).limit(10)
    return render_template('index.html', projects=projects)

@app.route("/projects/create/",methods=['GET','POST']) #Creation directory
def create():
	if request.method == "GET":
		return render_template("create.html")
	if request.method == "POST":
		now = datetime.datetime.now()
		time_ending = request.form.get("funding_end_date")
		time_ending = datetime.datetime.strptime(time_ending,"%Y-%m-%d")

		cover_photo = request.files['cover_photo']
		uploaded_image = cloudinary.uploader.upload(cover_photo,crop='limit',width=680,height=550)
		image_filename = uploaded_image['public_id']

		new_project = Project(
			member_id = 1 '''Hardcoded value for demonstartion''', 
			name = request.form.get("project_name"),
			short_description= request.form.get("short_description"),
			first_description = request.form.get("long_description"),
			goal_amount = request.form.get("funding_goal"),
			image_filename = image_filename,
			time_start = now,
			time_end = time_ending,
			time_created = now
			)
		db.session.add(new_project)
		db.session.commit()

		return redirect(url_for('project_detail',project_id = new_project.id))

@app.route("/projects/<int:project_id>/") #Project directory
def project_detail(project_id):
	project = db.session.query(Project).get(project_id)
	if project is None:
		abort(404)
	return render_template("project_detail.html",project = project)

@app.route("/projects/<int:project_id>/pledge/",methods=['GET','POST']) #Pledge directory
def pledge(project_id):
	project = db.session.query(Project).get(project_id)
	if project is None:
		abort(404)
	if request.method == "GET":
		return render_template("pledge.html",project=project)
	if request.method == "POST":

		guest = db.session.query(Member).filter_by(id=2).one()

		new_pledge = Pledge(
				member_id = guest.id,
				project_id = project.id,
				amount = request.form.get("amount"),
				time_created = datetime.datetime.now()
			)
		db.session.add(new_pledge)
		db.session.commit()

		return redirect(url_for('project_detail',project_id = new_pledge.project_id))

@app.route('/search/') #Search directory 
def search():
	query = request.args.get("q") or ""
	projects = db.session.query(Project).filter(
		Project.name.ilike('%'+query+'%') |
		Project.short_description.ilike('%'+query+'%') |
		Project.first_description.ilike('%'+query+'%')
	).all()
	project_count = len(projects)

	query_text = query if query != "" else "all projects"

	return render_template('search.html', 
		query_text=query_text,
		projects=projects,
		project_count=project_count
	)
		