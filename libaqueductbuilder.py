#!/usr/bin/python

import json
import tarfile
import sqlite3
from os import path, popen, remove, chdir, mkdir, listdir



conf = json.load(open('aqueduct-builder.conf'))
for d in conf['dir']: #Ensure all dirs have a trailing slash
	if conf['dir'][d][-1] != '/':
		conf['dir'][d] = conf['dir'][d] + '/'



def db_new_build_id(os, release, submitted_file):
	con = sqlite3.connect('aqueduct-builder.sqlite')
	cur = con.cursor()   
	cur.execute("INSERT INTO builds (os, release, submitted_file) VALUES('%s', '%s', '%s')" % (os,release,submitted_file))
	con.commit()
	cur.execute("SELECT last_insert_rowid()")
	return cur.fetchone()[0]



def get_build_file_that_ends_in(buildid, suffix):
	contents = listdir(conf['dir']['result']%buildid)
	cantidates = [s for s in contents if s.endswith(suffix)]
	if len(cantidates):
		return cantidates[0], conf['dir']['result'] % buildid
	else:
		return None



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

	if os in ('debian', 'ubuntu'):
		if not pbuilder_basetgz_exists(release):
			pbuilder_basetgz_create(release)
		#else:
			#pbuilder_basetgz_update(release)

		pbuilder_debuild(buildid, filepath, release)

	else:
		print('Unsupported os: ' + os)
