# Copyright 2022 ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import json
import os
import psutil
import resourcescfg
import resourcesgenerate
import socket
import subprocess
import sys
import tempfile
import time

def invoke(cmdline, found_values, outfn):
    with tempfile.TemporaryFile() as stdoutfile, tempfile.TemporaryFile() as stderrfile:
        start_time = time.time()
        p = subprocess.Popen(cmdline, stderr=stderrfile, stdout=stdoutfile)
        childproc = psutil.Process(pid=p.pid)
        all_total_rss=[]
        all_total_vms=[]
        meta_units=dict()
        meta_units['maxrss'] = 'bytes'
        meta_units['walltime'] = 'seconds'
        meta_units['maxvms'] = 'bytes'
        found_values['meta_units'] = meta_units
        while True:
            children_list = childproc.children(recursive=True) + [childproc]
            try:
                total_rss = sum([c.memory_info().rss for c in children_list])
                total_vms = sum([c.memory_info().vms for c in children_list])
            except psutil.NoSuchProcess:
                continue
            all_total_rss.append(total_rss)
            all_total_vms.append(total_vms)
            time.sleep(1)

            spent_time = time.time() - start_time
            found_values['maxrss'] = max(all_total_rss)
            found_values['walltime'] = spent_time
            found_values['maxvms'] = max(all_total_vms)
            found_values['meta_rss'] = all_total_rss
            found_values['meta_vms'] = all_total_vms
            found_values['meta_final'] = False


            if p.poll() != None:
                # child has exited
                found_values['meta_final'] = True
                found_values['meta_returncode'] = p.returncode

            # write resource results
            with open(outfn, 'w') as outf:
                found_values['meta_success'] = found_values['meta_final'] and found_values['meta_returncode'] == 0
                json.dump(found_values, outf)
            os.sync()

            if found_values['meta_final']:
                break

        stderrfile.seek(0)
        stdoutfile.seek(0)

        stdout_data=stdoutfile.read().decode('utf-8')
        stderr_data=stderrfile.read().decode('utf-8')

    return found_values, stdout_data, stderr_data

if __name__ == '__main__':
    tablename,rowname,colname,datadir,tablesdir,cmdline=sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6:]
    names_for_datapoint='__'.join(sys.argv[1:4])
    v = dict()

    v['meta_tablename'] = tablename
    v['meta_rowname'] = rowname
    v['meta_colname'] = colname
    v['meta_cmdline'] = sys.argv[6:]

    outfn_data = '%s/%s_%s.json' % (datadir,resourcescfg.general_tag_fn, names_for_datapoint)

    v,stdout_data,stderr_data = invoke(cmdline, v, outfn_data)

    with open('%s/%s_%s_out.txt' % (tablesdir,resourcescfg.general_tag_fn, names_for_datapoint), 'w') as outf:
        print('stdout:\n%s\nstderr:\n%s\n' % (stdout_data,stderr_data), file=outf)

    print('stdout:\n%s\nstderr:\n%s\n' % (stdout_data,stderr_data))

    # update latex output
    # don't regenerate, bugs can frustrate builds
#    resourcesgenerate.regenerate(datadir,tablesdir)

    if v['meta_returncode'] != 0:
            print('resourcerecord.py: failed command %s. return code: %d' % (cmdline, v['meta_returncode']))
            print('stdout:\n%s\n' % stdout_data)
            print('stderr:\n%s\n' % stderr_data)
    sys.exit(v['meta_returncode'])

