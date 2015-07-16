#!/usr/bin/python

import json
import tarfile



conf = json.load(open('aqueduct-builder.conf'))



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


def pkg_build(pkg_type, path):
	untar(path, conf['dir']['processing'])
	filename = path.split('/')[-1]
	print(filename)

	#dirpath = path.join(conf['dir']['processing'], )
	#if path.isdir(dirpath):
	#	release_file = path.join(dirpath, 'AqueductBuild')
	#	f = open(release_file, 'r')
	#	release = f.read().strip()
	#	f.close()
	#	remove(release_file)
#
#		if not pbuilder_basetgz_exists(release):
#			pbuilder_basetgz_create(release)
#		else:
#			pbuilder_basetgz_update(release)
