#!/usr/bin/env python


# If os arch is 64-bit increase number of idle threads (threads are cheap at startup. Linux schedulers are smarter now)

import os,optparse
from subprocess import Popen,PIPE

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
		self.used_memory = self.usedMemory())

	def free_rawoutput(self):
		freecmd = """/bin/free -m"""
		free = Popen(freecmd, shell=True, stdout=PIPE)
		freeout = free.wait().stdout.read()
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
		self.nr_cores = self.numberCores()
		self.nr_live_threads = self.numberLiveThreads()

	def cpuinfo_rawoutput(self):
		cpuinfocmd = """/bin/cat /proc/cpuinfo"""
		cpuinfo = Popen(cpuinfocmd, shell=True, stdout=PIPE)
		cpuinfoout = cpuinfo.wait().stdout.read()
		return cpuinfooout

	def cpuinfo_dict(self):
		cpuinfo = cpuinfo_rawoutput()
		cpuinfo_d = CPUInfo()
		for i in cpuinfo.split('\n'):
			var,val = i.split(':')
			cpuinfo_d[var]  = val
		return cpuinfo_d

	def numberCPUs(self):
		cpu_d = cpuinfo_dict()
		return int(cpu_d['physical id']) + 1

	def numberCores(self):
		cpu_d = cpuinfo_dict()
		nr_cpus = numberCPUs()
		nr_cores_per_cpu = int(cpu_d['cpu cores'])
		return nr_cores_per_cpu * nr_cpus

	def numberHT(self):
		cpu_d = cpuinfo_dict()
		return int(cpu_d['processor']) + 1

	def haveHT(self):
		if numberHT() == numberCores():
			return False
		return True

	def numberLiveThreads(self):
		pass
		

class VarnishStats(dict):
    def __init__(self, *args):
        dict.__init__(self, args)

    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        return val

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)

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

__version__ = '0.1'
usage = "Aha"

# Are we running on hardware or software (vz,etc)
def arch_type():
	pass

parser = optparse.OptionParser(usage=usage, version=__version__)
parser.add_option('-n', help='Varnish installation base directory')
# parser.print_help()

if os.path.isdir("/usr/local/varnish/bin"):
	varnish_binpath_default	= "/usr/local/varnish/bin/"
	varnish_statpath 	= varnish_binpath_default + "varnishstat"
	varnish_admpath		= varnish_binpath_default + "varnishadm"
else:
	varnish_binpath_default	= os.path.dirname(which("varnishstat"))
	varnish_statpath 	= varnish_binpath_default + "varnishstat"
	varnish_admpath		= varnish_binpath_default + "varnishadm"


stat1cmd = varnish_statpath + """ -1 -f client_drop,backend_unhealthy,backend_fail,fetch_failed,n_wrk_failed,n_wrk_lqueue,n_work_queued,n_wrk_drop,n_expied,n_lru_nuked,n_objoverflow"""
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

print vs

#for n in range(i, 0, 0):
#testsd:
