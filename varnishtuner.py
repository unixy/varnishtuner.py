#!/usr/bin/env python
# varnishtuner.py v0.1.0a - Varnish Cache tuner script
# Copyright (C) 2015 Joe Hmamouche <joe@unixy.net>

import os,sys,optparse,re
from subprocess import Popen,PIPE
from datetime import timedelta

class SystemInfo():
	def __init__(self):
		self.rawUptime = self.getUptimeRawContent()
		self.uptimeSeconds = self.getSystemUptimeSeconds(self.rawUptime)
		self.uptime = self.getSystemUptimeShow(self.uptimeSeconds)

	def getUptimeRawContent(self):
		try:
			f = open("/proc/uptime", "r")
		except:
			return float(0)
		uptime = f.read()
		return uptime

	def getSystemUptimeSeconds(self,rawuptime):
		return self.rawUptime.split()[0]

	def getSystemUptimeShow(self,uptimeseconds):
		return str(timedelta(seconds=float(uptimeseconds)))
		

class CPUInfo(dict):
	def __init__(self, *args):
		dict.__init__(self, args)

	def __getitem__(self, key):
		val = dict.__getitem__(self, key)
		return val

	def __setitem__(self, key, val):
		dict.__setitem__(self, key, val)


class ServerMemory():
	def __init__(self):
		self.free_raw = self.free_rawoutput()
		self.free_memory = self.freeMemory()
		self.total_memory = self.totalMemory()
		self.used_memory = self.usedMemory()

	def free_rawoutput(self):
		freecmd = """/usr/bin/free -m"""
		free = Popen(freecmd, shell=True, stdout=PIPE)
		free.wait()
		freeout = free.stdout.read().split('\n')
		return freeout

	def freeMemory(self):
		return int(self.free_raw[1].split()[3])

	def totalMemory(self):
		return int(self.free_raw[1].split()[1])

	def usedMemory(self):
		return int(self.free_raw[1].split()[2])

class ServerCPUInfo():

        def __init__(self):
                self.cpuinfo_raw = self.cpuinfo_rawoutput()
                self.nr_ht = self.numberHT()
		self.have_ht = self.haveHT()
                self.nr_cores = self.numberCores()
                self.nr_live_threads = self.numberLiveThreads()
		self.max_threads = self.maxAvailableThreads()

        def cpuinfo_rawoutput(self):
                cpuinfocmd = """/bin/cat /proc/cpuinfo"""
                cpuinfo = Popen(cpuinfocmd, shell=True, stdout=PIPE)
		cpuinfo.wait()
		cpuinfoout = cpuinfo.stdout.read()
		return cpuinfoout

        def cpuinfo_dict(self):
                cpuinfo = self.cpuinfo_rawoutput()
                cpuinfo_d = CPUInfo()
                for i in cpuinfo.split('\n'):
			if len(i) <= 0:
				continue
			var,val = [],[]
			var,val = i.split(':')
                        cpuinfo_d[var.strip()] = val.strip()
                return cpuinfo_d

	# This isn't reliable because a CPU assigned to a VM can show
	# physical id: 6 when the node only has two cores available to it
        def numberCPUs(self):
                cpu_d = self.cpuinfo_dict()
                return int(cpu_d['physical id']) + 1

	# See numberCPUs
        def numberCores(self):
                cpu_d = self.cpuinfo_dict()
                nr_cpus = self.numberCPUs()
                nr_cores_per_cpu = int(cpu_d['cpu cores'])
                return nr_cores_per_cpu * nr_cpus

	# This is the most reliable attribute in a VM. The count
	# gives you the number of HT/cores available to a VM
        def numberHT(self):
                cpu_d = self.cpuinfo_dict()
                return int(cpu_d['processor']) + 1

        def haveHT(self):
                if self.numberHT() == self.numberCores():
                        return False
                return True

	# Some VMs have a subset of HT threads available. So even though
	# CPUs * nr_cores > nr_ht, it doesn't mean vms have all those available
	def maxAvailableThreads(self):
		return self.numberHT()

        def numberLiveThreads(self):
                pass

class VarnishOptions(dict):
	def __init__(self, *args):
		dict.__init__(self, args)

	def __getitem__(self, key):
		val = dict.__getitem__(self, key)
		return val

	def __setitem__(self, key, val):
		dict.__setitem__(self, key, val)

class VarnishStats(dict):
	def __init__(self, *args):
		dict.__init__(self, args)

	def __getitem__(self, key):
		val = dict.__getitem__(self, key)
		return val

	def __setitem__(self, key, val):
		dict.__setitem__(self, key, val)

class VarnishConfig():

	def __init__(self, file):
		self.all_options_text = self.getVarnishConfigText(file)
		self.startupThreadCount = self.getStartupThreadCount(self.all_options_text)
		self.numberThreadPoolMin = self.getNumberThreadPoolMin(self.all_options_text)
		self.numberThreadPoolMax = self.getNumberThreadPoolMax(self.all_options_text)
		self.numberThreadPools = self.getNumberThreadPools(self.all_options_text)
		self.maxThreadCount = self.getMaxThreadCount(self.all_options_text)
		self.storageType = self.getVarnishStorageType(self.all_options_text)
		self.memorySetting = self.getMemorySetting(self.all_options_text)
		self.possibleMemUsage = self.getPossibleMemoryUsage()
		self.sess_workspace = self.getSessionWorkspace(self.all_options_text)

	def getSessionWorkspace(self, options):
		for i in options:
			if i.find("DAEMON_OPTS=") != -1:
				val = re.match(".*sess_workspace=(\d+).*", i)
		if val:
			return int(val.group(1))
		return 0

	def getVarnishConfigText(self,options_file):
		try:
			f = open(options_file, "r")
		except:
			msg_out("Unable to open file: " + options_file)
			sys.exit(1)
		configtext = f.read().split('\n')
		return configtext


	def getNumberThreadPools(self, options):
		for i in options:
			if i.find("DAEMON_OPTS=") != -1:
				val = re.match(".*thread_pools=(\d+).*", i)
		if val:
			return int(val.group(1))
		return 0

	def getNumberThreadPoolMin(self, options):
		for i in options:
			if i.find("DAEMON_OPTS=") != -1:
				val = re.match(".*thread_pool_min=(\d+).*", i)
		if val:
			return int(val.group(1))
		return 0

	def getNumberThreadPoolMax(self, options):
		for i in options:
			if i.find("DAEMON_OPTS=") != -1:
				val = re.match(".*thread_pool_max=(\d+).*", i)
		if val:
			return int(val.group(1))
		return 0

	def getStartupThreadCount(self, options):
		return self.getNumberThreadPools(options) * self.getNumberThreadPoolMin(options)

	def getMaxThreadCount(self, options):
		return self.getNumberThreadPools(options) * self.getNumberThreadPoolMax(options)

	def getVarnishStorageType(self, options):
		for i in options:
			if i.find("DAEMON_OPTS=") != -1:
				if i.find("malloc") != -1:
					return "Malloc"
				if i.find("file") != -1:
					return "File"
				if i.find("persistent") != -1:
					return "Persistent"
				else:
					return "Unknown"

	# Memory field is free form (K, M, G, etc).
	# Need to normalize to MB.
	def getMemorySetting(self, options):
		mem_str = ''
		for i in options:
			if i.find("DAEMON_OPTS=") != -1:
				if i.find("malloc") != -1:
					mem_str = i.split(',')[1].strip('"')
				else:
					mem_str = i.split(',')[2].strip('"')
				break
		mem_str = mem_str.lower()
		if len(mem_str) > 0 and not mem_str.isalnum():
			return int(mem_str) / (1024)

		if mem_str.find('k') != -1 or mem_str.find('kb') != -1:
			return int(int(mem_str.strip('k').strip('kb')) / 1024)
		elif mem_str.find('m') != -1 or mem_str.find('mb') != -1:
			return int(mem_str.strip('m').strip('mb'))
		elif mem_str.find('g') != -1 or mem_str.find('gb') != -1:
			return int(mem_str.strip('g').strip('gb')) * 1024
		elif mem_str.find('t') != -1 or mem_str.find('tb') != -1:
			return int(mem_str.strip('t').strip('tb')) * (1024*1024)

	# There's roughly +10% overhead 
	def getPossibleMemoryUsage(self):
		return float(self.getMemorySetting(self.all_options_text)) * 1.10

def VarnishStats1():
	stat1cmd = varnish_statpath + """ -1 -f uptime,client_drop,backend_unhealthy,""" + \
			"""backend_fail,fetch_failed,n_wrk_failed,n_wrk_lqueue,""" + \
			"""n_wrk_queued,n_wrk_drop,n_expied,n_lru_nuked,n_objoverflow"""
	stat1 = Popen(stat1cmd, shell=True, stdout=PIPE)
	stat1.wait()

	vs = VarnishStats()
	outstat = stat1.stdout.read()
	i=0

	for line in outstat.split('\n'):
		if len(line) <= 0:
			continue
		var,val = [],[]
		var, val, rest = line.split(None,2)
		vs[var] = val
		i = i+1
	return vs

def msg_out(msg):
	sys.stdout.write("\t|>>\t" + msg + "\n")
	sys.stdout.flush()

def showNewline(with_str = None):
	if with_str and len(with_str) > 0:
		msg_out(with_str)
	else:
		msg_out('')

def showAuthor():
	msg_out("""Varnishtuner v""" + __version__ + """ Joe Hmamouche <joe@unixy.net>""")

def showVarnishVersion(vs):
	versioncmd = varnish_statpath + """ -V"""
	version = Popen(versioncmd, shell=True, stdout=PIPE, stderr=PIPE)
	version.wait()
	out = version.stderr.read()
	if out.find("revision") != -1:
		msg = out.split("(")[1].split(")")[0]
		msg_out("""Running """ + msg)

def showUptime(vs, si):
	uptime = str(timedelta(seconds = float(vs['uptime'])))
	msg_out("""Server uptime: """ + si.uptime)
	msg_out("""Varnish uptime: """ + uptime)

def showLoadAverage():
	pass

def showSystemUptime():
	pass

def showBanner(vs, si):
	showNewline()
	showAuthor()
	showVarnishVersion(vs)
	showUptime(vs, si)
	showNewline('----------------------')

def SessionWorkspaceSize(vs, vc):
	if vc.sess_workspace <= 0:
		return 0
	if vc.sess_workspace > 0 and vc.sess_workspace < 100000:
		return 1
	elif vc.sess_workspace > 100000 and vc.sess_workspace > 200000:
		return 2

def isSessionWorkspaceOK(vs, vc):
	ret = SessionWorkspaceSize(vs, vc)
	if ret < 1:
		return 1
	elif ret >= 1 and ret < 2:
		return -1
	elif ret >=2:
		return -2

# Forceful eviction of objects from cache to make room
# for others.
def isObjectEvicted(vs):
	return (int(vs['n_lru_nuked']) > 0)

# Check backend fail counters
def isBackendFrail(vs):
	return (int(vs['backend_fail']) > 0)

# Check n_wrk_lqueue, n_wrk_queued, n_wrk_failed

# Need to warn about queued work
def isWrkQueueGrowing(vs):
	return (int(vs['n_wrk_queued']) > 0)

# Things aren't going well with caching
# if this is true
def isRequestDrop(vs):
	return (int(vs['n_wrk_drop']) > 0)

# Varnish had to drop client request due to resource
# shortage
def isClientDropped(vs):
	return (int(vs['client_drop']) > 0)

def isUptimeShort(si):
	if si.uptimeSeconds < (24 * 60 * 60):
		msg_out("Varnish started recently (< 24HRs). It needs to run for a bit longer.")

def isAvailableMemoryOverrun():
	pass

# Locate varnish's prefix path if possible and its binaries' location
# Credit: http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def showNumberHTThreads(sci):
	msg_out("Available CPU Threads: " + str(sci.nr_ht))

def showMemoryInfo(sm):
	msg_out("Total/Free/Used: " + str(sm.total_memory) + "MB / " + str(sm.free_memory) + "MB / " + str(sm.used_memory) + "MB")

def showServerSettings(sm, sci):
	showNumberHTThreads(sci)
	showMemoryInfo(sm)

def showStorageType(vc):
	msg_out("Varnish cache storage type: \"" + vc.storageType + "\"")

def showMemoryAllocation(vc):
	msg_out("Memory Allocate to Varnish: " + str(vc.memorySetting) + "MB")

def showThreadSettings(vc):
	msg_out("Varnish Startup Threads: " + str(vc.startupThreadCount))
	msg_out("Varnish Max Threads: " + str(vc.maxThreadCount))

def showVarnishSettings(vc):
	showStorageType(vc)
	showMemoryAllocation(vc)
	showThreadSettings(vc)

def checkVitals(vs, vc, si):

	if isSessionWorkspaceOK(vs, vc) < 1:
		msg_out("Increase sess_workspace ( > " + str(vc.sess_workspace) + " )")
	if isObjectEvicted(vs) and isClientDropped(vs):
		msg_out("Increase Varnish memory allocation ( > " + str(vc.memorySetting) + "MB )")
	elif isObjectEvicted(vs) or isClientDropped(vs):
		msg_out("Increase Varnish memory allocation ( > " + str(vc.memorySetting) + "MB )")

	if isWrkQueueGrowing(vs):
		msg_out("Increase thread_pool_min ( > " + str(vc.startupThreadCount) + " but < 400)")

	if isBackendFrail(vs):
		msg_out("Backend's weak. Ensure it's optimal (backend_fail: " + str(vs['backend_fail']) + ")")
		
__version__ = '0.1.0a'
usage = 'usage'

# dmidecode doesn't do much in VZ envinronments
def isVZ():
	unamecmd = """/bin/uname -a"""
	unamep = Popen(unamecmd, shell=True, stdout=PIPE)
	unamep.wait()
	uname = unamep.stdout.read()
	if uname.find("stab") != -1:
		return True
	return False
	
# Are we running on hardware or software (vz,etc)
def arch_type():
#	if isVZ():
	pass

parser = optparse.OptionParser(usage=usage, version=__version__)
parser.add_option('-b', '--base', help='Varnish installation base directory (Default: /usr/local/varnish)')
parser.add_option('-o', '--options-file', help='Varnish options file (Default: /etc/sysconfig/varnish)')
# parser.print_help()

if os.path.isdir("/usr/local/varnish/bin"):
	varnish_binpath_default	= "/usr/local/varnish/bin/"
	varnish_statpath 	= varnish_binpath_default + "varnishstat"
	varnish_admpath		= varnish_binpath_default + "varnishadm"
else:
	varnish_binpath_default	= os.path.dirname(which("varnishstat"))
	varnish_statpath 	= varnish_binpath_default + "varnishstat"
	varnish_admpath		= varnish_binpath_default + "varnishadm"


SI = SystemInfo()
VS = VarnishStats1()
SCI = ServerCPUInfo()
SM = ServerMemory()
VC = VarnishConfig("/etc/sysconfig/varnish")

showBanner(VS, SI)
showServerSettings(SM, SCI)
showVarnishSettings(VC)
showNewline()
showNewline("---- Recommendations -----")
showNewline()
checkVitals(VS, VC, SI)
showNewline()
