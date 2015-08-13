import json
from platform import dist, uname
import requests
import tarfile
from os import path, popen, remove, chdir, listdir

from libaqueduct import Singleton



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



def new_buildid():
	ids = listdir(conf['dir']['result'])
	num = 1
	for i in sorted(ids, reverse=True):
		try: #Protect against errors caused by nonnumber items
			num = int(i) + 1
		except ValueError:
			pass
		else:
			break

	return str(num)



def get_build_file_that_ends_in(buildid, suffix):
	contents = listdir(conf['dir']['result'] + buildid)
	cantidates = [s for s in contents if s.endswith(suffix)]
	if len(cantidates):
		return cantidates[0], conf['dir']['result'] + buildid
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
	success = 0
	if get_build_file_that_ends_in(buildid, '.deb'):
		success = 1

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
	dir_result = conf['dir']['result'] + buildid
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



class CurrentBuild(metaclass=Singleton):
	def __init__(self):
		self.dictionary = {}



def daemon(q):
	cur = CurrentBuild()
	while True:
		b = q.dequeue() #Block and wait for a job
		cur.dictionary = b
		pkg_build(b['buildid'], b['callbackurl'], b['jobid'], b['arch'], b['os'], b['release'], b['source'])
		cur.dictionary = {}
