import json
from platform import dist, uname
import requests
import tarfile
import sqlite3
from os import path, popen, remove, chdir, mkdir, listdir



conf = json.load(open('aqueduct-builder.conf'))
conf['address'] = conf['address'].rstrip('/') + ':' + str(conf['port']) + '/'
for d in conf['dir']: #Ensure all dirs have a trailing slash
	if conf['dir'][d][-1] != '/':
		conf['dir'][d] = conf['dir'][d] + '/'



def get_os():
	return dist()[0].lower()



def get_arch():
	arch = uname()[4]
	if arch == 'x86':
		arch = 'i386'
	elif arch == 'x86_64':
		arch = 'amd64'
	return arch



def _db_con():
	return sqlite3.connect(conf['path']['sqlite'])



def _db_create_environment():
	con = _db_con()
	cur = con.cursor()   
	cur.execute("CREATE TABLE IF NOT EXISTS builds (id INT AUTO_INCREMENT PRIMARY KEY, dummy int)")
	con.commit()



def db_build_new():
	con = _db_con()
	cur = con.cursor()   
	cur.execute("INSERT INTO builds(dummy) VALUES(42)")
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



def pbuilder_debuild(buildid, filepath, arch, release):
	tgz = conf['path']['basetgz'] % (arch, release)
	dir_result = conf['dir']['result'] % str(buildid)
	mkdir(dir_result)
	chdir(filepath)
	print(popen('pdebuild -- --architecture %s --basetgz %s --buildresult %s' % (arch, tgz, dir_result)).read())



def pbuilder_basetgz_exists(arch, release):
	tgz = conf['path']['basetgz'] % (arch, release)
	return path.exists(tgz)



def pbuilder_basetgz_create(arch, release):
	tgz = conf['path']['basetgz'] % (arch, release)
	print(popen('pbuilder --create --architecture %s --distribution %s --basetgz %s' % (arch, release, tgz)).read())



def pbuilder_basetgz_update(arch, release):
	tgz = conf['path']['basetgz'] % (arch, release)
	print(popen('pbuilder --update --architecture %s --distribution %s --basetgz %s' % (arch, release, tgz)).read())



def untar(filepath, dest):
	tfile = tarfile.open(filepath, 'r:gz')
	tfile.extractall(dest)
	name = tfile.getnames()[0]
	tfile.close() #?
	remove(filepath)
	return name



def pkg_build(buildid, callbackurl, jobid, arch, os, release, filepath):
	filepath = untar(filepath, conf['dir']['processing'])
	filepath = conf['dir']['processing'] + filepath

	build_arch = arch
	if arch == 'all':
		build_arch = get_arch()

	if os == get_os():
		if not pbuilder_basetgz_exists(build_arch, release):
			print("Creating basetgz for %s, %s" % (build_arch, release))
			pbuilder_basetgz_create(build_arch, release)
		else:
			pbuilder_basetgz_update(build_arch, release)

		print('Running debuild')
		pbuilder_debuild(buildid, filepath, build_arch, release)
		build_callback(buildid, callbackurl, jobid, arch, os, release)

	else:
		print('Unsupported os: ' + os)



_db_create_environment() #Run on load
