# -*- coding: utf-8 -*-
'''


'''
import os
import errno
import re

def is_empty(fname):
    return file_empty(fname)
def file_empty(fname):
    import os
    try:
        return os.stat(fname).st_size == 0
    except:
        return True
        
def txt_file_empty(fname):
    try:
        with open(fname) as f:
            for l in f:
                return False
    except IOError:
        return True    
    return True
        
def line_cnt(fname):
    return file_len(fname)
def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1
    
def lines(file_in, regex_str=None):
    return filter_file_lines(file_in, regex_str)
def filter_file_lines(file_in, regex_str=None):
    #import pandas as pd
    lines = []  # pandas.DataFrame()
    print ("regex: ", regex_str)
    pattern = re.compile(regex_str)
    if regex_str == None:
        with open(file_in) as f:
            lines = f.readlines()
    else:
        for line in open(file_in):
            for match in re.finditer(pattern, line):
                lines+=[line]
    return lines   #df.to_list()  #pandas.DataFrame(lst)
def filter_file_lines_test():
    file_in = r'K:\AFC Model Solution Logs\log\log_hourly48.txt'
    regex_str = '\d\d\ amb_solve\d\.dir' 
    print(filter_file_lines(file_in, regex_str))

def find(root_path, pattern='**', recursive=False):
    return find_files(root_path, pattern, recursive)
def find_files(root_path, pattern='**', recursive=False):
    from fnmatch import filter
    import os
    try:
        if recursive:
            ret = []
            for base, dirs, files in os.walk(root_path):
                goodfiles = filter(files, pattern)
                ret.extend(os.path.join(base, f) for f in goodfiles)
            return ret
        else:
            return filter(os.listdir(root_path), pattern)
    except:
        print 'Error: find_files(' + str(root_path) + ', ' + str(pattern) + ') failed.'
        return []  #return empty array to assure calling code does not fail
def find_files_test():
    print('Non-recurive: c:\temp')
    ret = find_files(r'C:\temp', '*.*', False)
    print(ret)
    print('')
    print 'Recurive: c:\temp'
    ret = find_files(r'C:\temp', '*.*', True)
    print(ret)


'''def delete(filename, silent=True):
    if silent:
        try:
            os.remove(filename)
        except OSError as e: # this would be "except OSError, e:" before Python 2.6
            if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
                raise # re-raise exception if a different error occured
    else:
        os.remove(filename)'''

def delete(file_list, silent=True):
    '''
    Delete a file or files
    
    Returns a list of files and their deletion status

    Parameters:
        file_list: file name or list of file names as str
        silent: if true, file not found error will not throw and exception
    '''
    if isinstance(file_list, str):
        file_list = [file_list]
    ret=[]
    for f_name in file_list:
        if not silent:
            os.remove(f_name)
        else: 
            try:
                os.remove(f_name)
                ret+=[[f_name,'deleted']]
            except OSError as e: # this would be "except OSError, e:" before Python 2.6
                if e.errno == errno.ENOENT: # errno.ENOENT = no such file or directory
                    ret+=[[f_name,'file not found']]
                else:
                    ret+=[[f_name,'error: ' + str(e.errno)]]
                    raise # re-raise exception if a different error occured
    return ret  #list of files and delete status
    
def delete_test():
    print("delete_test() not yet written")

def test_all():
    filter_file_lines_test()
    print('')
    print('')
    find_files_test()
    delete_test()