#!/usr/bin/env python


# If os arch is 64-bit increase number of idle threads (threads are cheap when started initially, Linux schedulers are smarter now)

import os,optparse
from subprocess import Popen,PIPE

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