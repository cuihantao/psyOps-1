
# coding: utf-8

# Import the needed libraries.
# 
# The re library stands for regular expression.  This is library is used for regular expression searches/
# The time library is used for date and time recognition
# The pandas library stands for Python Data Analysis Library.  This is used for data structures and data analysis tools.  

# In[50]:

import re
import time
import pandas as pd


# This section of code sets up the prerequisites that apply to all other blocks

# In[51]:


daily_file = r'C:\temp\log_daily.txt'

lines = open(daily_file).read().split('\n')


# In[52]:

df=[]
pattern = re.compile('\d\d\ amb_solve3.dir')
for i, line in enumerate(lines):
    for match in re.finditer(pattern, line):
        line_before = lines[i-1]
        df+=[[line[3:5],line[7:10],line[13:15],line[17:20],line[25:30],line[31:38],line[38:51],line[52:56],line[59:66],            line[71:76],line[77:84], line[85:97],line[97:102],line[105:112],line[112:127]]]
        df+=[[line_before[3:5],line_before[7:10],line_before[13:15],line_before[17:20],line_before[25:30],line_before[31:38],              line_before[38:51],line_before[52:56],line_before[59:66],line_before[71:76],line_before[77:84], line_before[85:97],              line_before[97:102],line_before[105:112],line_before[112:127]]]

frame = pd.DataFrame(df, columns=['Day','Iterations','Pms','Qms','P_Mismatch','P_Bus#','P_BusName','P_Volt','P_VoltMagPU',                                  'QmaxMism','Q_Bus#','Q_BusName','Q_Volt','Q_VoltMagPU','Solution Attempt'])

day_num = frame['Day'][0]
bus_num = frame['P_Bus#'][0]

day_num_prior = frame['Day'][1]
bus_num_prior = frame['P_Bus#'][1]



# In[73]:

df1=[]
bus_num_detail = 'Detailed bus flow analysis for'+bus_num
pattern1 = re.compile(bus_num_detail)
for i, line in enumerate(lines):
    for match in re.finditer(pattern1, line):
        df1+=[line[78:81]]
Area_num = df1[0]


# In[54]:

df2=[]
day_num_detail = '------------------ Creating snapshot '+day_num
pattern2 = re.compile(day_num_detail)
for i, line in enumerate(lines):
    for match in re.finditer(pattern2, line):
        df2+=[line[46:56]]
start_date = df2[0]
print start_date


# In[55]:

df2_p=[]
day_num_detail_p = '------------------ Creating snapshot '+day_num_prior
pattern2_p = re.compile(day_num_detail_p)
for i, line in enumerate(lines):
    for match in re.finditer(pattern2_p, line):
        df2_p+=[line[46:56]]
start_date_p = df2_p[0]
print start_date_p


# In[56]:

df3=[]
gen_outage_report_start =  '========= Report on generator status/dispatch changes for the period '+start_date
pattern3 = re.compile(gen_outage_report_start)
pattern4 = ' ========= Total  '
for i, line in enumerate(lines):
    for match in re.finditer(pattern3, line):
        j=3
        while True:
            if pattern4 in lines[i+j]:
                break
            else:
                linenum = lines[i+j]
                j+=1
                df3+=[linenum]


frame1 = pd.DataFrame(df3, columns =['lists'])


# In[57]:

df3_p=[]
gen_outage_report_start_p =  '========= Report on generator status/dispatch changes for the period '+start_date_p
pattern3_p = re.compile(gen_outage_report_start_p)
for i, line in enumerate(lines):
    for match in re.finditer(pattern3_p, line):
        jp=3
        while True:
            if pattern4 in lines[i+jp]:
                break
            else:
                linenum_p = lines[i+jp]
                jp+=1
                df3_p+=[linenum_p]

frame1_p = pd.DataFrame(df3_p, columns=['lists'])


# In[58]:

frame1_p['isin'] = 'x'
frame2 = pd.merge(frame1, frame1_p, how='outer', on=['lists'])
frame2 = frame2[frame2['isin'].isnull()]
frame2 = frame2.drop('isin',1)


# In[112]:

df4=[]
frame2.to_csv(r'C:\temp\Gen_outages.csv', index=None, header=None)
daily_file_gen_out = r'C:\temp\Gen_outages.csv'
lines1 = open(daily_file_gen_out).read().split('\n')
for line in lines1:
    df4 += [[line[:6],line[7:20],line[20:24],line[26:30],line[30:34],line[36:38],line[43:48],            line[60:61],line[65:71],line[75:81],line[84:90],line[95:100],line[102:118],line[120:136]]]

frame3 = pd.DataFrame(df4, columns=['Bus#','BusName','Volt','Area','Zone','ID','BaseCasMW','BaseCsSta','PMin',                                    'PMax','Type','NewSetPn','Start','End'])


# In[60]:

df5=[]
trans_outage_report_start =  '========= Report on branch status changes for the period from '+start_date
pattern5 = re.compile(trans_outage_report_start)
pattern6 = ' ========='
for i, line in enumerate(lines):
    for match in re.finditer(pattern5, line):
        j=3
        while True:
            if pattern6 in lines[i+j]:
                break
            else:
                linenum1 = lines[i+j]
                j+=1
                df5+=[linenum1]


frame4 = pd.DataFrame(df5, columns =['lists'])


# In[61]:

df6=[]
trans_outage_report_start_p =  '========= Report on branch status changes for the period from '+start_date_p
pattern7 = re.compile(trans_outage_report_start_p)
#pattern7=trans_outage_report_start_p
for i, line in enumerate(lines):
    #for match in re.finditer(pattern7, line):
    if re.search(pattern7, line):
        j=3
        while True:
            if pattern6 in lines[i+j]:
                break
            else:
                linenum1 = lines[i+j]
                j+=1
                df6+=[linenum1]

frame5 = pd.DataFrame(df6, columns =['lists'])


# In[62]:

frame5['isin'] = 'x'
frame6 = pd.merge(frame4, frame5, how='outer', on=['lists'])
frame6 = frame6[frame6['isin'].isnull()]
frame6 = frame6.drop('isin',1)


# In[150]:

df7=[]
frame6.to_csv(r'C:\temp\Trans_outages.csv', index=None, header=None)
daily_file_trans_out = r'C:\temp\Trans_outages.csv'
lines2 = open(daily_file_trans_out).read().split('\n')
for line in lines2:
    df7 += [[line[:6],line[7:20],line[20:24],line[26:29],line[30:34],line[35:41],line[42:54],            line[55:59],line[61:64],line[65:69],line[72:74],line[76:77],line[79:86],line[88:95],line[97:104],            line[107:112],line[116:119],line[120:150],line[151:167],line[169:185]]]

frame7 = pd.DataFrame(df7, columns=['Bus#From','BusNameFrom','VoltFrom','AreaFrom','ZoneFrom','Bus#To','BusNameTo','VoltFrom','AreaTo',                                    'ZoneTo','CKT','MT','RateA','RateB','RateC', 'Type','BaseCaseState','NewRates',                                    'Start','End'])
print frame7
#frame7.to_csv(r'C:\temp\Trans_outages1.csv')


# In[152]:

frame8 = frame7[(frame7['AreaFrom'] == Area_num) | (frame7['AreaTo'] == Area_num)]

frame8.to_csv(r'C:\temp\Recommended_Trans_Outages.csv', index=None)


# In[ ]:



