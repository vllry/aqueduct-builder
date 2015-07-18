#!/usr/bin/python

import urllib.request
import json
import tarfile
import sqlite3
from os import path, popen, remove, chdir, mkdir, listdir



conf = json.load(open('aqueduct-builder.conf'))
conf['address'] = conf['address'].rstrip('/') + ':' + str(conf['port']) + '/'
for d in conf['dir']: #Ensure all dirs have a trailing slash
	if conf['dir'][d][-1] != '/':
		conf['dir'][d] = conf['dir'][d] + '/'



def db_con():
	return sqlite3.connect(conf['path']['sqlite'])



def db_build_new(os, release, submitted_file, callbackurl):
	con = db_con()
	cur = con.cursor()   
	cur.execute("INSERT INTO builds (os, release) VALUES('%s', '%s')" % (os,release))
	con.commit()
	cur.execute("SELECT last_insert_rowid()")
	buildid = cur.fetchone()[0]
	cur.execute("INSERT INTO progress (id, callbackurl) VALUES('%s', '%s')" % (buildid,callbackurl))
	con.commit()
	return buildid



def db_progress_tarfile(buildid, filename):
	con = db_con()
	cur = con.cursor()
	cur.execute("UPDATE progress SET tarfile='%s' WHERE id=%s" % (filename, buildid))
	con.commit()



def db_progress_extracted(buildid, filename):
	con = db_con()
	cur = con.cursor()
	cur.execute("UPDATE progress SET extracted='%s' WHERE id=%s" % (filename, buildid))
	cur.execute("UPDATE progress SET tarfile=NULL WHERE id=%s" % (buildid))
	con.commit()



def db_progress_done(buildid):
	con = db_con()
	cur = con.cursor()
	cur.execute("DELETE FROM progress WHERE id=%s" % (buildid))
	con.commit()



def get_build_file_that_ends_in(buildid, suffix):
	contents = listdir(conf['dir']['result']%buildid)
	cantidates = [s for s in contents if s.endswith(suffix)]
	if len(cantidates):
		return cantidates[0], conf['dir']['result'] % buildid
	else:
		return None



def build_callback(buildid):
	con = db_con()
	cur = con.cursor()
	cur.execute("SELECT callbackurl FROM progress WHERE id=%s" % buildid)
	url = cur.fetchone()[0]

	deb_location = conf['address'] + 'build/%s/deb' % buildid
	success = '0'
	if get_build_file_that_ends_in(buildid, '.deb'):
		success = '1'

	urllib.request.urlopen(url.replace('%success', success).replace('%url',deb_location))



def pbuilder_debuild(buildid, filepath, release):
	tgz = conf['path']['basetgz'] % (release)
	dir_result = conf['dir']['result'] % str(buildid)
	mkdir(dir_result)
	chdir(filepath)
	popen('pdebuild -- --basetgz %s --buildresult %s > %sbuild.log' % (tgz, dir_result, dir_result))



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



def pkg_build(buildid, os, release, filepath):
	filepath = untar(filepath, conf['dir']['processing'])
	filepath = conf['dir']['processing'] + filepath
	db_progress_extracted(buildid, filepath)

	if os in ('debian', 'ubuntu'):
		if not pbuilder_basetgz_exists(release):
			pbuilder_basetgz_create(release)
		#else:
			#pbuilder_basetgz_update(release)

		pbuilder_debuild(buildid, filepath, release)
		build_callback(buildid)
		db_progress_done(buildid)

	else:
		print('Unsupported os: ' + os)
