#!/usr/bin/python

import json
import tarfile
import sqlite3
from os import path, popen, remove, chdir



conf = json.load(open('aqueduct-builder.conf'))



def db_new_build_id(os, release, submitted_file):
	con = sqlite3.connect('aqueduct-builder.sqlite')
	cur = con.cursor()   
	cur.execute("INSERT INTO builds (os, release, submitted_file) VALUES('%s', '%s', '%s')" % (os,release,submitted_file))
	con.commit()
	cur.execute("SELECT last_insert_rowid()")
	return cur.fetchone()[0]



def pbuilder_debuild(filepath, release):
	chdir(filepath)
	return popen('pdebuild -- --basetgz /var/cache/pbuilder/%s.base.tgz' % (release)).read()


def pbuilder_basetgz_exists(release):
	return path.exists('/var/cache/pbuilder/' + release + '.base.tgz')


def pbuilder_basetgz_create(release):
	print(popen('pbuilder --create --distribution ' + release + ' --basetgz /var/cache/pbuilder/' + release + '.base.tgz').read())


def pbuilder_basetgz_update(release):
	print(popen('pbuilder --update --distribution ' + release + ' --basetgz /var/cache/pbuilder/' + release + '.base.tgz').read())


def pbuilder_build(release):
	print(popen('pbuilder --debuild --distribution ' + release + ' --basetgz /var/cache/pbuilder/' + release + '.base.tgz').read())


def untar(filepath, dest):
	tfile = tarfile.open(filepath, 'r:gz')
	tfile.extractall(dest)
	name = tfile.getnames()[0]
	tfile.close() #?
	remove(filepath)
	return name



def pkg_build(os, release, filepath):
	filepath = untar(filepath, conf['dir']['processing'])
	filepath = conf['dir']['processing'] + '/' + filepath

	if os in ('debian', 'ubuntu'):
		if not pbuilder_basetgz_exists(release):
			pbuilder_basetgz_create(release)
		#else:
			#pbuilder_basetgz_update(release)

		buildlog = pbuilder_debuild(filepath, release)
		print("before")
		print(buildlog)
		print("after")

	else:
		print('Unsupported os: ' + os)
