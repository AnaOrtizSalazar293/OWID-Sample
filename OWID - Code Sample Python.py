#!/usr/bin/env python
# coding: utf-8

# In[162]:


#Plastic Waste Bilateral Trade - Data Collection, Merging, Cleaning, and Exploratory Visualizations
import pandas as pd
import numpy as np
import requests
import io
import json
import time
from urllib.request import urlopen
#import from io import StringIO#

#Using 'requests' to obtain import data from UN Comtrade for the five most recent years for 100 sample countries 
#(LIMITED TO 100 REQUESTS PER HOUR AND ONE REQUEST PER SECOND)

#define country list to obtain
r = urlopen('https://comtrade.un.org/Data/cache/reporterAreas.json')
d = json.loads(r.read())['results']
country = [sub['id'] for sub in d ][1:72] + [sub['id'] for sub in d ][74:77] + [sub['id'] for sub in d ][93:119]

#loop to download bilateral imports of plastic scraps
#NOTE: THIS LOOP CAN TAKE UP TO 20+ MINUTES RUNNING. READ IN THE FILE BELOW IF PREFERRED, WHICH IS THE LOOP'S OUTPUT
#final=pd.read_csv('imports.csv')

final_df=[]

for j in country:
        params = {
        "max": 1200,
        "type":"C",
        "freq":"A",
        "px": "HS",
        "r" : j,
        "p" : "all",
        "rg" : 1,
        "cc" : 3915,
        "fmt" : 'csv'    
        }

        unctdata=requests.get('https://comtrade.un.org/api/get?ps=2016%2C2017%2C2018%2C2019', params = params)
        unctdf = pd.read_csv(io.StringIO(unctdata.text))
        final_df.append(unctdf)
        final = pd.concat(final_df)
        time.sleep(2)
final


# In[1]:


import pandas as pd
import numpy as np
import requests
import io
import json
import time
from urllib.request import urlopen
#import from io import StringIO#
final=pd.read_csv('imports.csv')


# In[7]:


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

#merge datasets
finaldf = pd.merge(finaldat,regionsdf[['Reporter ISO','sub-region']], on='Reporter ISO', how='left')
finaldf = finaldf.rename(columns={'sub-region':'Region Reporter'})
finaldf = pd.merge(finaldf, regionsdf[['sub-region', 'Reporter ISO']], left_on='Partner ISO', right_on = 'Reporter ISO', how='left')
finaldf = finaldf.rename(columns={'Reporter ISO_x':'Reporter ISO', 'sub-region': 'Region Partner'})
finaldf = finaldf.drop(['Reporter ISO_y'], axis=1)
finaldf


# In[14]:


#Generate Adjacency Matrices from Edge Lists for Each Year
edgedf = finaldf[['Region Partner','Region Reporter', 'Netweight (kg)', 'Year']]
edge2016 = edgedf[edgedf['Year'] == 2016]
edge2017 = edgedf[edgedf['Year'] == 2017]
edge2018 = edgedf[edgedf['Year'] == 2018]
edge2019 = edgedf[edgedf['Year'] == 2019]

#2016
df2016=pd.crosstab(edge2016['Region Partner'], edge2016['Region Reporter'], values=edge2016['Netweight (kg)'], aggfunc='sum')
idx = df2016.columns.union(df2016.index)
df2016 = df2016.reindex(index=idx, columns=idx, fill_value=0)
df2016


# In[5]:


#Plotting Chord diagram with holoviews (need to install first)
import holoviews as hv
from holoviews import opts, dim
from bokeh.sampledata.les_mis import data

hv.extension('bokeh')
hv.output(size=200)


# In[31]:


#regenerate edge list to get same number of sources and destinations
edge2016c = df2016.stack().reset_index()
edge2016c = edge2016c.rename(columns={'level_0':'Source'})
edge2016c = edge2016c.rename(columns={'level_1':'Target'})
edge2016c = edge2016c.rename(columns={0:'Value'})

#replace NaNs (no trade transactions) for zeros
edge2016c['Value'] = edge2016c['Value'].fillna(0).astype(np.int64)

(edge2016c['Value'] < 0).values.any()
#edge2016c[edge2016c['Value'] <0]


# In[33]:


#create dataset for labels 

regions= list(set(edge2016c['Source'].unique().tolist()))
regions_df = hv.Dataset(pd.DataFrame(regions,columns=['Region']))


# In[34]:


get_ipython().run_cell_magic('opts', 'Chord [height=250 width=250 title="Plastic Imports" labels="Region"]', '%%opts Chord (node_color="Region" node_cmap="Category20" edge_color="Source" edge_cmap=\'Category20\')\nhv.Chord((edge2016c, regions_df))')


# In[35]:


#Exploratory Visualizations
import plotly.express as px

#Imports by Country Importer and Source
noncountries = ['World','Other Asia, nes','LAIA, nes','Other Europe, nes', 'Other Africa, nes','Areas, nes','Oceania, nes','Free Zones']
df2016_countries = finaldf[finaldf['Year'] == 2016]
#df2017_countries = finaldf[finaldf['Year'] == 2017]
#df2018_countries = finaldf[finaldf['Year'] == 2018]
#df2019_countries = finaldf[finaldf['Year'] == 2019]
df2016_countries = df2016_countries[~df2016_countries['Partner'].isin(noncountries)]

#Remove China and Hong Kong and plot separately
ChinaHK = ['China', 'China, Hong Kong SAR']
df2016_countriesnc = df2016_countries[~df2016_countries['Reporter'].isin(ChinaHK)]

#No China and Hong Kong
fig = px.bar(df2016_countriesnc, y="Netweight (kg)", x="Reporter", color="Partner", title="Plastic Imports by Source")
fig.update_layout({
'plot_bgcolor': 'rgba(0, 0, 0, 0)',
'paper_bgcolor': 'rgba(0, 0, 0, 0)',
})
fig.show()

#All countries
fig1 = px.bar(df2016_countries, y="Netweight (kg)", x="Reporter", color="Partner", title="Plastic Imports by Source")
fig1.update_layout({
'plot_bgcolor': 'rgba(0, 0, 0, 0)',
'paper_bgcolor': 'rgba(0, 0, 0, 0)',
})
fig1.show()

#get total values
df2016_countries_total = df2016_countries.groupby(['Reporter'], as_index=False)['Netweight (kg)'].sum()

#change in time China
dfChina = finaldf[finaldf['Reporter'].isin(ChinaHK)]
dfChina = dfChina[dfChina['Partner'] == 'World'].sort_values(by=['Year'])

fig2 = px.line(dfChina, x='Year', y='Netweight (kg)', color='Reporter', color_discrete_sequence=["purple", "blue"])
fig2.update_layout({'plot_bgcolor': 'rgba(0, 0, 0, 0)','paper_bgcolor': 'rgba(0, 0, 0, 0)',})
fig2.show()

df2016_countries_total


# In[39]:


#Networks by year
from pyvis.network import Network
import networkx as nx

G = nx.from_pandas_edgelist(df2016_countries, source='Partner', target='Reporter', edge_attr='Netweight (kg)')

weight = dict(df2016_countries['Netweight (kg)'])
    
net = Network(notebook=True, directed=True)
net.from_nx(G)
net.repulsion()
net.show('g2016.html')


# In[96]:


#convert to scripts (.py)
#!jupyter nbconvert --to script *.ipynb


# In[ ]:




