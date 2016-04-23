# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 15:07:09 2016
@author: advena
"""
#import re
from datetime import datetime
#import numpy as np
import pandas as pd 
import os 
import sys
import shutil
import sqlite3
from pandas.io import sql

#################################
#         User Inputs           #
#################################
# The locaion of the original raw files.  If you already copied the files
# to a working location, set src_dir = to the working directory, tgt_dir.
#src_dir = r'K:\AFC_MODEL_UPDATES\2016_S\IDC Models'
src_dir = r'C:\temp'

# Working directory.  If src_dir != tgt_dir, a copy of the original raw
# files is copied to tgt_dir to prevent corruption of the originals.
# The copy here will have be modified; a new line will be added to the top 
# to allow for csv parsing without error.
tgt_dir = r'C:\temp'

# The raw files to compare
raw_file1 = r'sum16idctr1p4_v32.RAW'
raw_file2 = r'sum16idctr1p6_v32.RAW'

# SQLite3 database file
# To create a new file each run, enter 'datestr' in the filename;
# datestr will be replaced with a string datetime like 'yyyy-mm-dd_hrmiss'
# This script will overwrite any existing database file with the same name.
sqlite_file=r'compare_raw_datestr.sqlite3'
#sqlite_file=':memory:'  #Too much data to keep in memory.

# Maximim number of columns in any row, likely 28.
max_cols=28

pjm_area_list=[202,205,209,212,215,222,225,320,345]
compare_area_list = pjm_area_list

bus_cols=['Bus_Num', 'Bus_Name', 'Bus_kV', 'Code', 'Area_Num', 'Zone_Num', \
          'Owner_Num','Voltage_pu','Angle']
load_cols=[]
fixed_shunt_cols=[]
gen_cols=['Bus_Num', 'ID', 'Pgen', 'Qgen', 'Qmax', 'Qmin', 'VSched_pu',\
          'Remote_Bus_Num','Mbase', 'R_source_pu', 'X_source_pu',\
          'RTran_pu', 'XTran_pu','Gentap_pu', 'In_Service', 'RMPCT','Pmax',\
          'Pmin','Owner','Owner_Fraction']
branch_cols=[]
xfrmrs_cols=[]
area_cols=['num', 'Unk', 'Unk', 'Unk', 'name']
two_term_dc_cols=[]
vsc_dc_cols=[]
imped_correction_cols=[]  
mutli_term_dc_cols=[]
multi_sctn_line_cols=['Fr_Bus_Num', 'To_Bus_Num', 'Unk', 'Unk', 'Unk']
zone_cols=['Num','Name']
xfer_cols=[]
owner_cols=['Num','Name']
facts_cols=[]
sw_shunt_cols=[]
#gne_cols=[]
#db.close()

#################################
#     Function Dfinitions       #
#################################

def raw_to_df(src_dir, tgt_dir, filename, max_cols=28):
    '''
    src_dir: directory in which the raw files are located
    tgt_dir: directory in which to copy the files 
             (to prevent corrupting originals)
    filename: name of raw file (exluding path)
    ins_hdr: True to add a generic header to the file (col1, col2, ...)
             False if you already added a header to the file.  
    max_cols: The maximim number of columns in any row, likely 28.
    '''
    #create  generic column headers
    cols=["col"+str(i) for i in range(max_cols)]
    #concatenate path and filename
    src=os.path.join(src_dir,filename)
    #copy both files to the target directory
    if src_dir != tgt_dir and tgt_dir!=None and tgt_dir!='':
        print('        copying raw file to working directory: ' + tgt_dir)
        tgt=os.path.join(tgt_dir,filename)
        shutil.copyfile(src, tgt) 
    else:
        tgt=src
    # return dataframe    
    print('        reading raw file into datafrme: ' + tgt_dir)
    lst = pd.read_csv(open(tgt), names=cols, dtype= str )
    return pd.DataFrame(lst)


def define_sections(df):
    sections = []
    first_row = 3
    for row_num, row in df.iterrows():
        if row[0][:4] == "0 / ":
            #section_name = row[0][3:].replace("END OF","").strip()
            section_name = row[0][11:]
            #sections [from line, to line, section name]
            sections += [[first_row, row_num, section_name]]
            first_row = row_num+1
    return sections

def gen_sql_compare():
    '''    
    gen_cols=['Bus_Num', 'ID', 'Pgen', 'Qgen', 'Qmax', 'Qmin', 'VSched_pu',\
          'Remote_Bus_Num','Mbase', 'R_source_pu', 'X_source_pu',\
          'RTran_pu', 'XTran_pu','Gentap_pu', 'In_Service', 'RMPCT','Pmax',\
          'Pmin','Owner','Owner_Fraction']
    '''
    global db
    # Units in both files, but Pmax, Qmax or In_Service changed
    print('        Gen value changes')
    sql_str = '''
    select gen1.Bus_Num, gen1.ID, gen1.Owner
           , gen1.PMax as PMax1, gen2.PMax as PMax2, (gen2.Pmax - gen1.Pmax) as Pmax_delta
           , gen1.QMax as QMax1, gen2.QMax as QMax2, (gen2.Qmax - gen1.Qmax) as Qmax_delta
           , gen1.In_Service as In_Service1, gen2.In_Service as In_Service2
           , (gen1.In_Service - gen2.In_Service) as In_Service_delta
           , 'value' as Change_type
    from gen1, gen2 
    where gen1.Bus_Num = gen2.Bus_Num 
        and gen1.ID = gen2.ID
        and (Pmax1 != Pmax2 
             or Qmax1 != Qmax2
             or In_Service1 != In_Service2)  '''        
    gen_diff = sql.read_frame(sql_str, db)    
    
    # Units only in file 1
    print('        Gens dropped')
    sql_str = '''
    select gen1.Bus_Num, gen1.ID, gen1.Owner
           , gen1.PMax as PMax1, gen2.PMax as PMax2, (gen2.Pmax - gen1.Pmax) as Pmax_delta
           , gen1.QMax as QMax1, gen2.QMax as QMax2, (gen2.Qmax - gen1.Qmax) as Qmax_delta
           , gen1.In_Service as In_Service1, gen2.In_Service as In_Service2
           , (gen1.In_Service - gen2.In_Service) as In_Service_delta
           , 'dropped' as Change_type
    FROM gen1 
    LEFT JOIN gen2
    ON (gen1.Bus_Num = gen2.Bus_Num 
        and gen1.ID = gen2.ID)
    WHERE gen2.Bus_Num is NULL  '''        
    gen_drop = sql.read_frame(sql_str, db)    
    
    # concat results
    gen_diff = gen_diff.append(gen_drop)
    
    # Units only in file 2
    print('        Gens added')
    sql_str = '''
    select gen1.Bus_Num, gen1.ID, gen1.Owner
           , gen1.PMax as PMax1, gen2.PMax as PMax2, (gen2.Pmax - gen1.Pmax) as Pmax_delta
           , gen1.QMax as QMax1, gen2.QMax as QMax2, (gen2.Qmax - gen1.Qmax) as Qmax_delta
           , gen1.In_Service as In_Service1, gen2.In_Service as In_Service2
           , (gen1.In_Service - gen2.In_Service) as In_Service_delta
           , 'added' as Change_type
    FROM gen2 
    LEFT JOIN gen1
    ON (gen1.Bus_Num = gen2.Bus_Num 
        and gen1.ID = gen2.ID)
    WHERE gen1.Bus_Num is NULL  '''        
    gen_add = sql.read_frame(sql_str, db)    
    
    # concat results
    gen_diff = gen_diff.append(gen_add)
    
    return gen_diff
    
def gen_df_compare(gen_df1, gen_df2, area_list=None):
    '''
    Compares the generation data from the two raw files.
    Parameters:
        gen_df1: dataframe containing the generation table from raw file1
        gen_df2: dataframe containing the generation table from raw file2
        cols: list of column names
    Returns dataframe with dropped gen, added gen and changes in Pgen, Pmax,
        Qgen, Qmax, In_Service.
        
    gen_cols=['Bus_Num', 'ID', 'Pgen', 'Qgen', 'Qmax', 'Qmin', 'VSched_pu',\
          'Remote_Bus_Num','Mbase', 'R_source_pu', 'X_source_pu',\
          'RTran_pu', 'XTran_pu','Gentap_pu', 'In_Service', 'RMPCT','Pmax',\
          'Pmin','Owner','Owner_Fraction']
    '''
    if isinstance(area_list, list) and len(area_list)>0:
        gen_df1=gen_df1[gen_df1['Owner'].isin(area_list)]
    # add a column to indicate difference type    
    # dropped 
    Diff = pd.merge(gen_df1, gen_df2, how='left', on=['Bus_Num','ID'])
    Diff = Diff[Diff.loc[:,['Pgen_y']].isnull()] #I picked Pgen arbitrarily.
    print('Dropped gen')
    print(Diff.loc[:,['Bus_Num','ID','Pmax_x','Pmax_y']].head())
    #print(Diff[['Bus_Num','ID','Pmax_x','Pmax_y']].head())
    Diff['dropped'] = '1'

    # added
    added = pd.merge(gen_df1, gen_df2, how='right', on=['Bus_Num','ID'])
    Diff = Diff[Diff['Pgen_x'].isnull()] #I picked Pgen arbitrarily.
    added['added'] = '1'
    print('Added gen')
    print(added[['Bus_Num','ID','Pmax_x','Pmax_y']].head())
    Diff = Diff.append(added)
    added=None

    # changes in Pmax
    delta = pd.merge(gen_df1, gen_df2, how='inner', on=['Bus_Num','ID'])
    delta = delta[delta['Pmax_x'] != delta['Pmax_y']]
    delta['delta_PMax'] = delta['Pmax_x']-delta['Pmax_y']
    print('Delta Pmax')
    print(delta[['Bus_Num','ID','Pmax_x','Pmax_x','delta_PMax']].head())
    Diff = Diff.append(delta)
    delta=None
   
    return Diff

def bus_sql_compare():
    '''
    bus_cols=['Bus_Num', 'Bus_Name', 'Bus_kV', 'Code', 'Area_Num', 'Zone_Num', \
              'Owner_Num','Voltage_pu','Angle']    
    '''
    global db
    # Busses in both files, but Pmax, Qmax or In_Service changed
    print('        Bus name changes')
    sql_str = '''
    select bus1.Bus_Num, bus1.Bus_Name as Name1, bus2.Bus_Name as Name2
           , bus1.Bus_kV, bus1.Area_Num, bus1.Zone_Num
           , 'name' as Change_type
    from bus1, bus2 
    where bus1.Bus_Num = bus2.Bus_Num 
        and bus1.Bus_Name != bus2.Bus_Name  '''        
    bus_diff = sql.read_frame(sql_str, db)    
    
    # Units only in file 1
    print('        buss dropped')
    sql_str = '''
    select bus1.Bus_Num, bus1.Bus_Name as Name1, bus2.Bus_Name as Name2
           , bus1.Bus_kV, bus1.Area_Num, bus1.Zone_Num
           , 'name' as Change_type
    from bus1
    LEFT JOIN bus2
    ON bus1.Bus_Num = bus2.Bus_Num 
    WHERE bus2.Bus_Num is NULL  '''        
    bus_drop = sql.read_frame(sql_str, db)    
    
    # concat results
    bus_diff = bus_diff.append(bus_drop)
    
    # Units only in file 2
    print('        buss added')
    sql_str = '''
    select bus1.Bus_Num, bus1.Bus_Name as Name1, bus2.Bus_Name as Name2
           , bus1.Bus_kV, bus1.Area_Num, bus1.Zone_Num
           , 'name' as Change_type
    from bus2
    LEFT JOIN bus1
    ON bus1.Bus_Num = bus2.Bus_Num 
    WHERE bus1.Bus_Num is NULL  '''        
    bus_add = sql.read_frame(sql_str, db)    
    
    # concat results
    bus_diff = bus_diff.append(bus_add)
    
    return bus_diff
    


#################################
#            Main               #
#################################

start=datetime.now()
print('')
print('Starting raw file comparison script')

#if sqlite_file == r':memory:':
#    db = sqlite3.connect(':memory:')
#else:
datestr=str(datetime.now()).replace(" ","_").replace(":","").split(".")[0]
if 'datestr' in sqlite_file:
    sqlite_file=sqlite_file.replace('datestr',datestr)
try:
    os.remove(os.path.join(tgt_dir,sqlite_file))
except:
    'it was worth a shot'
try:
    db = sqlite3.connect(os.path.join(tgt_dir,sqlite_file))
except:
    print('***  Error, unable to open database ' + os.path.join(tgt_dir,sqlite_file) + '  ***')
    try: 
        db.close()
        print('     Did you forget to close the databse.  Execute "db.close()" and run the script again. ')
    except: 
        print('     Unknown error. ')
    sys.exit()

print('')
print('1. Parsing raw file 1: ' + raw_file1)
# load dataframes
print('    loading raw file')
df1 = raw_to_df(src_dir, tgt_dir, raw_file1, max_cols)
summary1 = list(df1.iloc[0,:][0:7])+[None]
summary1[7] = summary1[6]
summary1[5] = summary1[5].split('/')[1][-4].strip()
summary1[5] = summary1[5].split('/')[0].strip()
summary1 += [df1.iloc[1,:][0]]
summary1 += [df1.iloc[2,:][0] + ',' + df1.iloc[2,:][1]]
for i in range(len(summary1)):
    df1.iloc[0,i]=summary1[i]

df1['data_type']='na'

print('    save to db: ' + sqlite_file)
try:
    sql.write_frame(df1, name='raw1', con=db)
except:
    print('***  Error, unable to create table raw1.  It may already exist.  ***')
    try: 
        db.close()
        print('     Did you forget to close the databse.  Execute "db.close()" and run the script again. ')
    except: 
        print('     Unknown error. ')
    sys.exit()

# Find sections within the dataframe
print('    raw file sections')
section_def1 = define_sections(df1)
print(section_def1)
# create section dataframes
print('    splitting raw file sections')
print
for i, sublist in enumerate(section_def1):
    #print("\n"+str(sublist[2])+": " )
    if 'BUS DATA' in sublist[2].upper():
        bus1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:9]
        df1[sublist[0]:sublist[1]]['data_type']='bus'
        bus1.columns = bus_cols #[s+'1' for s in bus_cols]
        sql.write_frame(bus1, name='bus1', con=db)
        #bus1_data = sql.read_frame('select * from bus1', db)
    elif 'LOAD DATA' in sublist[2].upper():
        load1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:13]
        df1[sublist[0]:sublist[1]]['data_type']='load'
    elif 'FIXED SHUNT DATA' in sublist[2].upper():
        fixed_shunt1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:13]
        df1[sublist[0]:sublist[1]]['data_type']='fixed_shunt'
    elif 'GENERATOR DATA' in sublist[2].upper():
        gen1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:20]
        df1[sublist[0]:sublist[1]]['data_type']='gen'
        gen1.columns = gen_cols #[s+'1' for s in gen_cols]
        sql.write_frame(gen1, name='gen1', con=db)
        #gen1 = gen1.set_index(['Bus_Num', 'ID'])
    elif 'BRANCH DATA' in sublist[2].upper():
        branch1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:18]
        df1[sublist[0]:sublist[1]]['data_type']='bbranch'
    elif 'TRANSFORMER DAT' in sublist[2].upper():
        xfrmr1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:17]
        df1[sublist[0]:sublist[1]]['data_type']='xfrmr'
    elif 'AREA DATA' in sublist[2].upper():
        area1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:5]
        df1[sublist[0]:sublist[1]]['data_type']='area'
    elif 'TWO-TERMINAL DC DATA' in sublist[2].upper():
        two_term_dc1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:17]
        df1[sublist[0]:sublist[1]]['data_type']='two_term_dc'
    elif 'VSC DC LINE DATA' in sublist[2].upper():
        vsc_dc1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:15]
        df1[sublist[0]:sublist[1]]['data_type']='vsc_dc'
    elif 'IMPEDANCE CORRECTION DATA' in sublist[2].upper():
        imped_correction1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:24]
        df1[sublist[0]:sublist[1]]['data_type']='imped_correction'
    elif 'MULTI-TERMINAL DC DATA' in sublist[2].upper():
        multi_term_dc1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:28]
        df1[sublist[0]:sublist[1]]['data_type']='multi_term_dc'
    elif 'MULTI-SECTION LINE DATA' in sublist[2].upper():
        multi_sctn_line1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:5]
        df1[sublist[0]:sublist[1]]['data_type']='multi_sctn_line'
    elif 'ZONE DATA' in sublist[2].upper():
        zone1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:2]
        df1[sublist[0]:sublist[1]]['data_type']='zone'
    elif 'INTER-AREA TRANSFER DATA' in sublist[2].upper():
        xfer1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:28]
        df1[sublist[0]:sublist[1]]['data_type']='xfer'
    elif 'OWNER DATA' in sublist[2].upper():
        owner1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:2]
        df1[sublist[0]:sublist[1]]['data_type']='owner'
    elif 'FACTS DEVICE DATA' in sublist[2].upper():
        facts1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:23]
        df1[sublist[0]:sublist[1]]['data_type']='facts'
    elif 'SWITCHED SHUNT DATA' in sublist[2].upper():
        sw_shunt1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:25]
        df1[sublist[0]:sublist[1]]['data_type']='switched_shunt'
    #elif 'GNE DATA DATA' in sublist[2].upper():
    #    gne1 = df1[sublist[0]:sublist[1]].copy().iloc[:,0:28]
    #    df1[sublist[0]:sublist[1]]['data_type']='gne'
print('run time: ' + str(datetime.now()-start))
#create some room in memory
df1=None


print('')
print('2. Parsing raw file 2: ' + raw_file2)
print()
# load dataframes
print('    loading raw file')
df2 = raw_to_df(src_dir, tgt_dir, raw_file2, max_cols)
summary2 = list(df2.iloc[0,:][0:7])+[None]
summary2[7] = summary2[6]
summary2[5] = summary2[5].split('/')[1][-4].strip()
summary2[5] = summary2[5].split('/')[0].strip()
summary2 += [df2.iloc[1,:][0]]
summary2 += [df2.iloc[2,:][0] + ',' + df2.iloc[2,:][1]]
for i in range(len(summary2)):
    df2.iloc[0,i]=summary2[i]

df2['data_type']='na'

print('    save to db: ' + sqlite_file)
try:
    sql.write_frame(df2, name='raw2', con=db)
except:
    print('***  Error, unable to create table raw2.  It may already exist.  ***')
    sys.exit()
    
# Find sections within the dataframe
print('    raw file sections')
section_def2 = define_sections(df2)
print(section_def2)
# create section dataframes
print('    splitting raw file sections')
for i, sublist in enumerate(section_def2):
    #print("\n"+str(sublist[2])+": " )
    if 'BUS DATA' in sublist[2].upper():
        bus2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:9]
        df2[sublist[0]:sublist[1]]['data_type']='bus'
        bus2.columns = bus_cols #[s+'1' for s in bus_cols]
        sql.write_frame(bus2, name='bus2', con=db)
    elif 'LOAD DATA' in sublist[2].upper():
        load2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:13]
    elif 'FIXED SHUNT DATA' in sublist[2].upper():
        fixed_shunt2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:13]
    elif 'GENERATOR DATA' in sublist[2].upper():
        gen2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:20]
        gen2.columns = gen_cols #[s+'2' for s in gen_cols]
        sql.write_frame(gen2, name='gen2', con=db)
        #gen2 = gen2.set_index(['Bus_Num', 'ID'])
    elif 'BRANCH DATA' in sublist[2].upper():
        branch2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:18]
    elif 'TRANSFORMER DAT' in sublist[2].upper():
        xfrmr2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:17]
    elif 'AREA DATA' in sublist[2].upper():
        area2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:5]
    elif 'TWO-TERMINAL DC DATA' in sublist[2].upper():
        two_term_dc2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:17]
    elif 'VSC DC LINE DATA' in sublist[2].upper():
        vsc_dc2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:15]
    elif 'IMPEDANCE CORRECTION DATA' in sublist[2].upper():
        imped_correction2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:24]
    elif 'MULTI-TERMINAL DC DATA' in sublist[2].upper():
        multi_term_dc2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:28]
    elif 'MULTI-SECTION LINE DATA' in sublist[2].upper():
        multi_sctn_line2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:5]
    elif 'ZONE DATA' in sublist[2].upper():
        zone2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:2]
    elif 'INTER-AREA TRANSFER DATA' in sublist[2].upper():
        xfer2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:28]
    elif 'OWNER DATA' in sublist[2].upper():
        owner2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:2]
    elif 'FACTS DEVICE DATA' in sublist[2].upper():
        facts2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:23]
    elif 'SWITCHED SHUNT DATA' in sublist[2].upper():
        sw_shunt2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:25]
    #elif 'GNE DATA DATA' in sublist[2].upper():
    #    gne2 = df2[sublist[0]:sublist[1]].copy().iloc[:,0:28]
#create some room in memory
df2=None
print('run time: ' + str(datetime.now()-start))
db.commit()
#db.close()

#Find model differences    
print('')
print('3. Comparing models')
print('    Finding generation differences')
#gen_diff = gen_df_compare(gen1, gen2, None)
#gen_diff = gen_df_compare(gen1, gen2, compare_area_list)

gen_diff = gen_sql_compare()
#gen_diff[gen_diff['Change_type']=='added']
#gen_diff[gen_diff['Change_type']=='dropped']
#gen_diff[(gen_diff['Change_type']=='value') & (gen_diff['Pmax_delta']!='0')]
print('\n\n    Generation Differences:')
print(gen_diff.head(10))
# save as excel spreadsheet
gen_diff.to_csv(os.path.join(tgt_dir,'gen_diff_' + datestr + '.csv'))
print('run time: ' + str(datetime.now()-start))

bus_sql_compare()
bus_diff = bus_sql_compare()
print('\n\n    Bus Differences:')
print(bus_diff.head(10))
# save as excel spreadsheet
bus_diff.to_csv(os.path.join(tgt_dir,'bus_diff_' + datestr + '.csv'))
print('run time: ' + str(datetime.now()-start))

print('')
print('Finished raw file comparison script')
print('total run time: ' + str(datetime.now()-start))

