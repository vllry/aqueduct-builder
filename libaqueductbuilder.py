#!/usr/bin/python

import json
import requests
import tarfile
import sqlite3
from os import path, popen, remove, chdir, mkdir, listdir



conf = json.load(open('aqueduct-builder.conf'))
conf['address'] = conf['address'].rstrip('/') + ':' + str(conf['port']) + '/'
for d in conf['dir']: #Ensure all dirs have a trailing slash
	if conf['dir'][d][-1] != '/':
		conf['dir'][d] = conf['dir'][d] + '/'



def _db_con():
	return sqlite3.connect(conf['path']['sqlite'])



def _db_create_environment():
	con = _db_con()
	cur = con.cursor()   
	cur.execute("CREATE TABLE IF NOT EXISTS builds (id INT AUTO_INCREMENT PRIMARY KEY)")
	con.commit()



def db_build_new():
	con = _db_con()
	cur = con.cursor()   
	cur.execute("INSERT INTO builds ()")
	con.commit()
	cur.execute("SELECT last_insert_rowid()")
	buildid = cur.fetchone()[0]
	return buildid



def get_build_file_that_ends_in(buildid, suffix):
	contents = listdir(conf['dir']['result']%buildid)
	cantidates = [s for s in contents if s.endswith(suffix)]
	if len(cantidates):
		return cantidates[0], conf['dir']['result'] % buildid
	else:
		return None



def post(url, postdata):
	r = requests.post(
		url,
		postdata
	)
	return r.text



def build_callback(buildid, url, jobid, arch, os, release):
	location = conf['address'] + 'build/%s/' % buildid
	success = False
	if get_build_file_that_ends_in(buildid, '.deb'):
		success = True

	data = {
		'success' : success,
		'location' : location,
		'jobid' : jobid,
		'arch' : arch,
		'os' : os,
		'release' : release
	}
	print("Sending callback to " + url)
	post(url, data)



def pbuilder_debuild(buildid, filepath, release):
	tgz = conf['path']['basetgz'] % (release)
	dir_result = conf['dir']['result'] % str(buildid)
	mkdir(dir_result)
	chdir(filepath)
	print(popen('pdebuild -- --basetgz %s --buildresult %s' % (tgz, dir_result)).read())



def pbuilder_basetgz_exists(release):
	tgz = conf['path']['basetgz'] % (release)
	return path.exists(tgz)



def pbuilder_basetgz_create(release):
	tgz = conf['path']['basetgz'] % (release)
	print(popen('pbuilder --create --distribution %s --basetgz %s' % (release, tgz)).read())



def pbuilder_basetgz_update(release):
	tgz = conf['path']['basetgz'] % (release)
	print(popen('pbuilder --update --distribution %s --basetgz %s' % (release, tgz)).read())



def untar(filepath, dest):
	tfile = tarfile.open(filepath, 'r:gz')
	tfile.extractall(dest)
	name = tfile.getnames()[0]
	tfile.close() #?
	remove(filepath)
	return name



def pkg_build(buildid, jobid, arch, os, release, filepath):
	filepath = untar(filepath, conf['dir']['processing'])
	filepath = conf['dir']['processing'] + filepath

	if os in ('debian', 'ubuntu'):
		if not pbuilder_basetgz_exists(release):
			print("Creating basetgz " + release)
			pbuilder_basetgz_create(release)
		#else:
			#pbuilder_basetgz_update(release)

		print('Running debuild')
		pbuilder_debuild(buildid, filepath, release)
		build_callback(buildid, jobid, arch, os, release)

	else:
		print('Unsupported os: ' + os)



_db_create_environment() #Run on load
