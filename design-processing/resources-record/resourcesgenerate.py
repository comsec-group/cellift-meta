# Copyright 2022 ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only


"""
Code to generate LaTeX tables from data.
"""

import glob
import sys
import tabulate
import resourcescfg
import copy
import matplotlib.pyplot as plt

# insert this string in the table if the corresponding command failed
FAILSTRING_LATEX='$\otimes$'
FAILSTRING_PLAIN='XXX'
FAILSTRING='CMDFAILED'
MISSING='-'
MISSING_RAW=-1
FAILED_RAW=-2

short_units={
        'kbytes': 'kB',
        'seconds': 's',
        'bytes': 'B'
        }

name_metadata = {
        'row': ('Test Row',0),
        'vanilla': ('Original',0),
        'cellift': ('CellIFT',1),
        'glift_plus': ('GLIFT',2),
#        'glift': ('GLIFT',3),
}

# mapping from col tag to long name and order key
col_metadata={
        'instr': ('Instrument',0),
        'synth': ('Synthesis', 1),
        'run': ('Run', 2),
        'col': ('Test Col', 2)
        }

def format_bytes(size):
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'k', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return '%.1f %s' % (size, power_labels[n]+'B')

def format_seconds(seconds):
    seconds = round(seconds)
    minutes = seconds//60
    seconds -= minutes*60
    hours = minutes//60
    minutes -= hours*60
    return "%d:%02d:%02d" % (hours,minutes,seconds)

def format_cell(datapoint, fieldname, all_units, success):
    unit=short_units[all_units[fieldname]]
    value=datapoint[fieldname]
    if 'meta_final' not in datapoint:
        print('table %s row %s: no meta_final field!' % (datapoint['meta_tablename'], datapoint['meta_rowname']))
        raise Exception('no meta_final data')
    assert 'meta_final' in datapoint
    prepend=''
    global FAILSTRING
    if not success:
        prepend=FAILSTRING
    if unit == 'B':
        return prepend + ' ' + format_bytes(value)
    if unit == 's':
        return prepend + ' ' + format_seconds(value)
    return '%s %s %s' % (prepend, value,unit)

def handle_row(table_datapoints, rowname, all_colnames, all_units, hostname, fieldname, rawdata):
    row_datapoints=[datapoint for datapoint in table_datapoints if datapoint['meta_rowname'] == rowname]
    row=[rowname]

    failedrow = False
    for col in all_colnames:
        col_datapoints=[datapoint for datapoint in row_datapoints if datapoint['meta_colname'] == col]
        if len(col_datapoints) == 0:
            if failedrow:
                if rawdata:
                    row += [FAILED_RAW]
                else:
                    row += [FAILSTRING]
            else:
                if rawdata:
                    row += [MISSING_RAW]
                else:
                    row += [MISSING]
            continue
        if len(col_datapoints) > 1:
            print('too many row+col datapoints for row %s col %s hostname %s: %s' % (rowname,col,hostname, col_datapoints))
        assert len(col_datapoints) == 1
        datapoint=col_datapoints.pop()
        assert len(col_datapoints) == 0
        success = datapoint['meta_final'] and datapoint['meta_returncode'] == 0
        if rawdata:
            colfield = datapoint[fieldname]
            assert colfield >= 0
            if not success:
                colfield = -colfield
                assert colfield != FAILED_RAW
                assert colfield != MISSING_RAW
        else:
            colfield=format_cell(datapoint, fieldname, all_units, success)
        if not success:
            failedrow = True
        row += [colfield]
    return row

def col_longname(col):
        longname=col
        if col in col_metadata:
            longname=col_metadata[col][0]
        else:
            print('Warning: No long name known for column %s' % (col,))
        return longname

def col_sortorder(col):
    order=0
    if col in col_metadata:
        order= col_metadata[col][1]
    else:
        print('Warning: No sort order known for column %s' % (col,))
    return order

def row_sortorder(row):
    rowname=row[0]
    order=0
    if rowname in name_metadata:
        order = name_metadata[rowname][1]
    else:
        print('warning: No sort order known for row %s' % rowname)
    return order

def row_rewritename(row):
    name=row[0]
    if name in name_metadata:
        name = name_metadata[name][0]
    else:
        print('warning: No nice name known for row %s' % name)
    return [name] + row[1:]

def set_failstring(tablerows, new_failstring):
    tablerows = copy.copy(tablerows)
    return [[c.replace(FAILSTRING, new_failstring) for c in r] for r in tablerows]

fnbase = None
fnbase_dir = None

def handle_table(all_datapoints, tablename, all_units, tablesdir, hostname, all_phase_values):
    name_mapping = {
            'elapsed-wallclock': 'Time (s)',
            'maxrss': 'Max RSS (kB)' }
    table_datapoints=[datapoint for datapoint in all_datapoints if datapoint['meta_tablename'] == tablename and datapoint['meta_hostname'] == hostname]

    # Get unique set of rownames, colnames, fieldnames.
    # Make sure ordering is defined (i.e. in a list) deterministic (i.e. sorted).
    all_rownames={datapoint['meta_rowname'] for datapoint in table_datapoints}
    all_colnames=sorted({datapoint['meta_colname'] for datapoint in table_datapoints}, key=lambda x: col_sortorder(x) )
    all_colnames=[c for c in all_colnames if c != 'run']

    # Get all fieldnames.
    all_fieldnames=[]
    for x in table_datapoints:
        all_fieldnames += [fieldname for fieldname in list(x) if 'meta' not in fieldname]
    all_fieldnames=sorted(set(all_fieldnames))

    # Think of some header names.
    headers=['Name']
    for col in all_colnames:
        headers.append('%s' % (col_longname(col),))

    for fieldname in all_fieldnames:

        # Construct table per row.
        tablerows=[]
        tablerows_raw=[]

        for rowname in all_rownames:
            row = handle_row(table_datapoints, rowname, all_colnames, all_units, hostname, fieldname, True)
            tablerows_raw.append(row)
            row = handle_row(table_datapoints, rowname, all_colnames, all_units, hostname, fieldname, False)
            tablerows.append(row)

        # Sort rows
        tablerows = sorted(tablerows, key=lambda row: row_sortorder(row))
        tablerows = [row_rewritename(row) for row in tablerows]

        tablerows_raw = sorted(tablerows_raw, key=lambda row: row_sortorder(row))
        tablerows_raw = [row_rewritename(row) for row in tablerows_raw]

        raw_rownames=[]

        for row in tablerows_raw:
            raw_rownames.append( tablename.replace('pulpissimo', 'PULP').replace('ariane_smallcaches','Ariane').replace('ibex', 'Ibex') + '\n' + row[0])
            for colname,col in zip(all_colnames,row[1:]):
                ix = (colname,hostname,fieldname)
                if ix not in all_phase_values:
                    all_phase_values[ix] = []
                if col < 0:
                    col = -col
                all_phase_values[ix].append(col)


        # Save constructed table in LaTeX formatting.
        global fnbase
        global fnbase_dir
        fnbase_dir='%s' % (tablesdir,)
        fnbase='%s/%s_%s_%s_tab' % (fnbase_dir, tablename, fieldname, hostname)
        with open(fnbase+'.tex', 'w') as fplatex, open(fnbase+'.txt', 'w') as fpplain, open(fnbase+'.raw', 'w') as fpraw:
            col_alignment = ['left'] + ['right'] * (len(headers)-1)
#            print('alignment: %s' % (col_alignment,))
            header = '%s %s %s' % (tablename, fieldname, hostname)
            latexrows = set_failstring(tablerows, FAILSTRING_LATEX)
            plainrows = set_failstring(tablerows, FAILSTRING_PLAIN)
            print('%% %s:\n%s\n' % (header, tabulate.tabulate(latexrows, headers=headers, tablefmt='latex_raw', colalign=col_alignment)), file=fplatex)
            print('\n%s:\n\n%s\n' % (header, tabulate.tabulate(plainrows, headers=headers, tablefmt='plain', colalign=col_alignment)), file=fpplain)
            print('\n%s:\n\n%s\n' % (header, tabulate.tabulate(tablerows_raw, headers=headers, tablefmt='plain', colalign=col_alignment)), file=fpraw)

    return raw_rownames

def transform_filter_datapoint(datapoint):
    if '_trace' in datapoint['meta_rowname']:
        print('warning: ignoring _trace row data')
        return None
    if '_notrace' in datapoint['meta_rowname']:
        datapoint['meta_rowname'] = datapoint['meta_rowname'].replace('_notrace','')
    return datapoint

def regenerate(datadir, tablesdir):
    units_mapping = {'seconds': 's', 'kbytes': 'kB'}
    all_hostnames=set()
    all_datapoints=list()
    all_units=dict()
    for fn in glob.glob('%s/%s*' % (datadir,resourcescfg.general_tag_fn)):
        datapoint=eval(open(fn).read())
        datapoint = transform_filter_datapoint(datapoint)
        if datapoint == None:
            continue
        all_hostnames.add(datapoint['meta_hostname'])
        all_datapoints.append(datapoint)
        all_units={**all_units,**datapoint['meta_units']}

    for hostname in all_hostnames:
      all_phase_values=dict()
      rownames=[]
      all_tables = {datapoint['meta_tablename'] for datapoint in all_datapoints if datapoint['meta_hostname'] == hostname}
      for tablename in all_tables:
        rownames += handle_table(all_datapoints, tablename, all_units, tablesdir, hostname, all_phase_values)
      configs=list(all_phase_values)
      plots={(k[1],k[2]) for k in configs}
      for plot in plots:
        fig, ax = plt.subplots()
        print(' *** %s' % (plot,))
        prev_row = [0] * len(rownames)
        for k in list(all_phase_values):
          if (k[1],k[2]) != plot:
              continue
          print('%s: %s %s' % (k,all_phase_values[k], rownames, ))
#          ax.set_yscale('log')
          if len(rownames) != len(all_phase_values[k]):
              print('rownames:\n%s\nall phase values:\n%s\n' % (rownames, all_phase_values[k]))
              print('Incomplete i guess? not drawing these bars.')
              break
          else:
              if 'mxarss' in plot[1]:
                  for k in all_phase_values:
                      print('maxrss')
                      all_phase_values[k] /= (1024*1024*1024)
              ax.bar(rownames, all_phase_values[k], 0.4, label=col_longname(k[0]), bottom=prev_row)
          prev_row = [prev_row[i] + all_phase_values[k][i] for i in range(len(prev_row))]
        ax.set_ylabel(plot[1].replace('walltime', 'Time (s)').replace('maxrss','RSS High Watermark (GB)'))
#        ax.set_title('%s' % (plot[1].replace('walltime', 'Instrumentation Performance')))
        ax.legend()
        global fnbase
        global fnbase_dir
        fn='%s/%s-%s.png' % (fnbase_dir, plot[0], plot[1])
        plt.savefig(fn)
        fn='%s/%s-%s.pdf' % (fnbase_dir, plot[0], plot[1])
        plt.savefig(fn)
        print('saved %s' % fn)

if __name__ == '__main__':
    regenerate(sys.argv[1], sys.argv[2])


