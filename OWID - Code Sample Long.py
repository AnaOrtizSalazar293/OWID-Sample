#!/usr/bin/env python
# coding: utf-8

# In[87]:


#A snippet of code (at least 100 lines) that you wrote for a data science or data analysis task, 
#reflecting your current skill level in Python. This should preferably be a link to GitHub but can be an 
#attachment if the script cannot be made public.

import pandas as pd
import numpy as np
import requests
import io
import json
import time
from urllib.request import urlopen
#import from io import StringIO#

#Using 'requests' to obtain import data from UN Comtrade for the five most recent years for 100 sample countries 
#(LIMITED TO 100 REQUESTS PER HOUR)

#define country list to obtain
r = urlopen('https://comtrade.un.org/Data/cache/reporterAreas.json')
d = json.loads(r.read())['results']
country = [ sub['id'] for sub in d ][1:20]

#loop to download bilateral imports of plastic scraps
#NOTE: THIS LOOP CAN TAKE UP TO 30+ MINUTES RUNNING.

final_df=[]

for j in country:
        params = {
        "max": 1000,
        "type":"C",
        "freq":"A",
        "px": "HS",
        "ps": '2015%2C2016%2C2017%2C2018%2C2019',
        "r" : j,
        "p" : "all",
        "rg" : 1,
        "cc" : 3915,
        "fmt" : 'csv'    
        }

        unctdata=requests.get('https://comtrade.un.org/api/get', params = params)
        unctdf = pd.read_csv(io.StringIO(unctdata.text))
        final_df.append(unctdf)
        final = pd.concat(final_df)
        time.sleep(2)
final
#url='https://comtrade.un.org/api/get?max=1000&type=C&freq=A&px=HS&ps=2000%2C2001%2C2002%2C2003%2C2004&r=4%2C8%2C50%2C699%2C170&p=all&rg=1&cc=3915&fmt=csv'
#unctdata=requests.get(url)
#unctdf = pd.read_csv(io.StringIO(unctdata.text))
#unctdf


# In[89]:


url='https://comtrade.un.org/api/get?max=1000&type=C&freq=A&px=HS&ps=2000%2C2001%2C2002%2C2003%2C2004&r=4%2C8%2C50%2C699%2C170&p=all&rg=1&cc=3915&fmt=csv'
unctdata=requests.get(url)
unctdf = pd.read_csv(io.StringIO(unctdata.text))
unctdf


# In[81]:


final['Year'].unique()


# In[83]:


#clean dataset
#get unique values of classification column
final['Classification'].unique()
#remove empty queries
finaldat = final[final.Classification != "No data matches your query or your query is too complex. Request JSON or XML format for more information."]
#get column names
finaldat.keys()
#keep only relevant columns
finaldat = finaldat[['Year','Trade Flow','Reporter Code','Reporter','Reporter ISO','Partner Code','Partner','Partner ISO','Netweight (kg)']]

#generate reporter and partner region columns
regionsdf = pd.read_csv('https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.csv')
regionsdf = regionsdf.rename(columns={'alpha-3':'Reporter ISO'})
finaldf = pd.merge(finaldat,regionsdf[['Reporter ISO','sub-region']], on='Reporter ISO', how='left')
finaldf = finaldf.rename(columns={'sub-region':'Region Reporter'})
finaldf = pd.merge(finaldf, regionsdf[['sub-region', 'Reporter ISO']], left_on='Partner ISO', right_on = 'Reporter ISO', how='left')
finaldf = finaldf.rename(columns={'Reporter ISO_x':'Reporter ISO', 'sub-region': 'Region Partner'})
finaldf = finaldf.drop(['Reporter ISO_y'], axis=1)
finaldf


# In[28]:


edgedf = finaldf[['Region Partner','Region Reporter', 'Netweight (kg)', 'Year']]
edge2000 = edgedf[edgedf['Year'] == 2000]
edge2005 = edgedf[edgedf['Year'] == 2005]
edge2010 = edgedf[edgedf['Year'] == 2010]
df2000=pd.crosstab(edge2000['Region Partner'], edge2000['Region Reporter'], values=edge2000['Netweight (kg)'], aggfunc='sum')
idx = df2000.columns.union(df2000.index)
df2000 = df2000.reindex(index=idx, columns=idx, fill_value=0)
df2000


# In[2]:


#Plotting Chord diagram with holoviews
import holoviews as hv
from holoviews import opts, dim
from bokeh.sampledata.les_mis import data

hv.extension('bokeh')
hv.output(size=200)


# In[30]:


#regenerate edge list to get same number of sources and destinations
edge2000 = df2000.stack().reset_index()
edge2000 = edge2000.rename(columns={'level_0':'Source'})
edge2000 = edge2000.rename(columns={'level_1':'Target'})
edge2000 = edge2000.rename(columns={0:'Value'})

edge2000['Value'] = edge2000['Value'].fillna(0).astype(int)

#edge2000.Value=edge2000.Value.mask(edge2000.Value.lt(0),0)
(edge2000['Value'] < 0).values.any()


# In[3]:


edge2000 = pd.read_csv('edge2000.csv')[['Source','Target','Value']]


# In[6]:


#create dataset for labels 

regions= list(set(edge2000['Source'].unique().tolist()))
regions
regions_df = hv.Dataset(pd.DataFrame(regions,columns=['Region']))
regions_df


# In[8]:


get_ipython().run_cell_magic('opts', 'Chord [height=250 width=250 title="Plastic Imports" labels="Region"]', '%%opts Chord (node_color="Region" node_cmap="Category20" edge_color="Source" edge_cmap=\'Category20\')\nhv.Chord((edge2000, regions_df))')


# In[79]:


#Networks by year
from pyvis.network import Network
import networkx as nx

G = nx.from_pandas_edgelist(finaldf_g, source='Partner', target='Reporter', edge_attr='Netweight (kg)')

#nx.set_node_attributes(G, pd.Series(finaldf_g['Netweight (kg)'], index=finaldf_g['Partner']).to_dict(), 'weight')
#nx.set_node_attributes(G, pd.Series(nodes.gender, index=nodes.node).to_dict(), 'gender')

weight = dict(finaldf_g['Netweight (kg)'])
    
net = Network(notebook=True, directed=True)
net.from_nx(G)
net.show('g2000.html')


# In[94]:


get_ipython().system("jupyter nbconvert --to script 'OWID-CodeSampleLong.ipynb'")


# In[ ]:




