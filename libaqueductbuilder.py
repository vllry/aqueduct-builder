#!/usr/bin/python

import json
import tarfile
import sqlite3
from os import path, popen



conf = json.load(open('aqueduct-builder.conf'))



def db_new_build_id(os, release, submitted_file):
	con = sqlite3.connect('aqueduct-builder.sqlite')
	cur = con.cursor()   
	cur.execute("INSERT INTO builds (os, release, submitted_file) VALUES('%s', '%s', '%s')" % (os,release,submitted_file))
	con.commit()
	cur.execute("SELECT last_insert_rowid()")
	return cur.fetchone()


def pbuilder_basetgz_exists(release):
	return path.exists('/var/cache/pbuilder/' + release + '.base.tgz')


def pbuilder_basetgz_create(release):
	print(popen('pbuilder --create --distribution ' + release + ' --basetgz /var/cache/pbuilder/' + release + '.base.tgz').read())


def pbuilder_basetgz_update(release):
	print(popen('pbuilder --update --distribution ' + release + ' --basetgz /var/cache/pbuilder/' + release + '.base.tgz').read())


def pbuilder_build(release):
	print(popen('pbuilder --debuild --distribution ' + release + ' --basetgz /var/cache/pbuilder/' + release + '.base.tgz').read())


def untar(path, dest):
	tfile = tarfile.open(path, 'r:gz')
	tfile.extractall(dest)


def pkg_build(os, release, path):
	untar(path, conf['dir']['processing'])
	filename = path.split('/')[-1]

	if os == "debian":
		if not pbuilder_basetgz_exists(release):
			pbuilder_basetgz_create(release)
		else:
			pbuilder_basetgz_update(release)

	else:
		print('Unsupported os: ' + os)
