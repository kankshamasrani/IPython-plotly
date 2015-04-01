
# coding: utf-8

# [Apache Spark](https://spark.apache.org/)'s meteoric rise has been incredible. It is one of the fastest growing open source projects and is a perfect fit for the graphing tools that [Plotly](https://plot.ly/) provides. Plotly's ability to graph and share images from [Spark DataFrames](https://spark.apache.org/docs/latest/sql-programming-guide.html) quickly and easily make it a great tool for any data scientist and [Plotly Enterprise](https://plot.ly/product/enterprise/) make it easy to securely host and share those Plotly graphs.
# 
# This notebook will go over the details of getting set up with IPython Notebooks for graphing Spark data with Plotly.
# 
# ---
# 
# First you'll have to create an ipython profile for pyspark, you can do this locally or you can do it on the cluster that you're running Spark.
# 
# Start off by creating a new ipython profile. (Spark should have ipython install but you may need to install ipython notebook yourself).
# 
# ```sh
# ipython profile create pyspark
# ```
# 
# Next you'll have to edit some configurations. Spark/Hadoop have plenty of ports that they open up so you'll have to change the below file to avoid any conflicts that might come up. 
# 
# ```sh
# ~/.ipython/profile_pyspark/ipython_notebook_config.py
# ```
# 
# If you're not running Spark locally, you'll have to add some other configurations. [Cloudera's blog](http://blog.cloudera.com/blog/2014/08/how-to-use-ipython-notebook-with-apache-spark/) has a great post about some of the other things you can add, like passwords.
# 
# IPython's documentation also has some excellent recommendations for settings that you can find on [the "Securing a Notebook Server" post on ipython.org.](http://ipython.org/ipython-doc/3/notebook/public_server.html#running-a-notebook-server)
# 
# You'll likely want to set a port, and an IP address to be able to access the notebook.
# 
# Next you'll need to set a couple of environmental variables. You can do this at the command line or you can set it up in your computer's/master node's bash_rc/bash_profile files.
# 
# 
# ```sh
# export SPARK_HOME="$HOME/Downloads/spark-1.3.0"
# ```
# 
# Now we'll need to add a file to make sure that we boot up with the Spark Context. Basically when we start the IPython Notebook, we need to be bring in the Spark Context. We need to set up a startup script that runs everytime we start a notebook from this profile. 
# 
# Setting startup scripts are actually extremely easy - you just put them in the IPython Notebook directory under the "startup" folder. You can learn more about IPython configurations on the [IPython site](http://ipython.org/ipython-doc/1/config/overview.html).
# 
# We'll create a file called `pyspark_setup.py`
# 
# in it we'll put
# 
# ```py
# import os
# import sys
#  
# spark_home = os.environ.get('SPARK_HOME', None)
#  
# # check if it exists
# if not spark_home:
#     raise ValueError('SPARK_HOME environment variable is not set')
#  
# # check if it is a directory
# if not os.path.isdir(spark_home):
#     raise ValueError('SPARK_HOME environment variable is not a directory')
#  
# #check if we can find the python sub-directory
# if not os.path.isdir(os.path.join(spark_home, 'python')):
#     raise ValueError('SPARK_HOME directory does not contain python')
#  
# sys.path.insert(0, os.path.join(spark_home, 'python'))
#  
# #check if we can find the py4j zip file
# if not os.path.exists(os.path.join(spark_home, 'python/lib/py4j-0.8.2.1-src.zip')):
#     raise ValueError('Could not find the py4j library - \
#             maybe your version number is different?(Looking for 0.8.2.1)')
#  
# sys.path.insert(0, os.path.join(spark_home, 'python/lib/py4j-0.8.2.1-src.zip'))
#  
# with open(os.path.join(spark_home, 'python/pyspark/shell.py')) as f:
#     code = compile(f.read(), os.path.join(spark_home, 'python/pyspark/shell.py'), 'exec')
#     exec(code)
# ```
# 
# And now we're all set! When we start up an ipython notebook, we'll have the Spark Context available in our IPython notebooks. This is one time set up! So now we're ready to run things normally!

# We can test for the Spark Context's existence with `print sc`.

# In[1]:

from __future__ import print_function #python 3 support
print(sc)


# Now that we've got the SparkContext, let's pull in some other useful Spark tools that we'll need. We'll be using pandas for some downstream analysis as well as Plotly for our graphing.
# 
# We'll also need the SQLContext to be able to do some nice Spark SQL transformations.

# In[2]:

from pyspark.sql import SQLContext
sqlContext = SQLContext(sc)

import plotly.plotly as py
from plotly.graph_objs import *
import pandas as pd
import requests
requests.packages.urllib3.disable_warnings()


# The data we'll be working with is a sample of the [open bike rental data.](http://www.bayareabikeshare.com/datachallenge) Essentially people can rent bikes and ride them from one station to another. This data provides that information. [You can snag the sample I am using in JSON format here.](https://github.com/anabranch/Interactive-Graphs-with-Plotly/raw/master/btd2.json).
# 
# Now we can import it.

# In[3]:

btd = sqlContext.jsonFile("btd2.json")


# Now we can see that it's a DataFrame by printing its type.

# In[4]:

print(type(btd))


# Now **RDD** is the base abstraction of Apache Spark, it's the Resilient Distributed Dataset. It is an immutable, partitioned collection of elements that can be operated on in a distributed manner. The DataFrame builds on that but is also immutable - meaning you've got to think in terms of transformations - not just manipulations.
# 
# Because we've got a json file, we've loaded it up as a DataFrame - a new introduction in Spark 1.3. The DataFrame interface which is similar to pandas style DataFrames except for that immutability described above.

# We can print the schema easily, which gives us the layout of the data. Everything that I'm describing can be [found in the Pyspark SQL documentation.](https://spark.apache.org/docs/latest/api/python/pyspark.sql.htm)

# In[5]:

btd.printSchema()


# We can grab a couple, to see what the layout looks like.

# In[6]:

btd.take(3)


# Now one thing I'd like to look at is the duration distribution - can we see how common certain ride times are?
# 
# To answer that we'll get the durations and the way we'll be doing it is through the Spark SQL Interface. To do so we'll register it as a table.

# In[7]:

sqlCtx.registerDataFrameAsTable(btd, "bay_area_bike")


# Now as you may have noted above, the durations are in seconds. Let's start off by looking at all rides under 2 hours.

# In[8]:

60 * 60 * 2 # 2 hours in seconds


# In[9]:

df2 = sqlCtx.sql("SELECT Duration as d1 from bay_area_bike where Duration < 7200")


# We've created a new DataFrame from the transformation and query - now we're ready to plot it. One of the great things about plotly is that you can throw very large datasets at it and it will do just fine. It's certainly a much more scalable solution than matplotlib.
# 
# Below I create a histogram of the data.

# In[10]:

data = Data([Histogram(x=df2.toPandas()['d1'])])


# In[11]:

py.iplot(data, filename="spark/less_2_hour_rides")


# That was simple and we can see that plotly was able to handle the data without issue. We can see that big uptick in rides that last less than ~30 minutes (2000 seconds) - so let's look at that distribution.

# In[12]:

df3 = sqlCtx.sql("SELECT Duration as d1 from bay_area_bike where Duration < 2000")


# A great thing about Apache Spark is that you can sample easily from large datasets, you just set the amount you would like to sample and you're all set.

# In[13]:

s1 = df2.sample(False, 0.05, 20)
s2 = df3.sample(False, 0.05, 2500)


# In[14]:

data = Data([
        Histogram(x=s1.toPandas()['d1'], name="Large Sample"),
        Histogram(x=s2.toPandas()['d1'], name="Small Sample")
    ])


# Plotly converts those samples into beautifully overlayed histograms. This is a great way to eyeball different distributions.

# In[15]:

py.iplot(data, filename="spark/sample_rides")


# What's really powerful about Plotly is sharing this data is simple. I can take the above graph and change the styling or bins visually. A common workflow is to make a rough sketch of the graph in code, then make a more refined version with notes to share with management like the one below. Plotly's online interface allows you to edit graphs in other languages as well.

# In[16]:

from IPython.display import HTML
HTML("""<div>
    <a href="https://plot.ly/~bill_chambers/101/" target="_blank" title="Comparing Ride Length - 2 Distinct Samples" style="display: block; text-align: center;"><img src="https://plot.ly/~bill_chambers/101.png" alt="Comparing Ride Length - 2 Distinct Samples" style="max-width: 100%;width: 936px;"  width="936" onerror="this.onerror=null;this.src='https://plot.ly/404.png';" /></a>
    <script data-plotly="bill_chambers:101" src="https://plot.ly/embed.js" async></script>
</div>
""")


# Now let's check out bike rentals from individual stations. We can do a groupby with Spark DataFrames just as we might in Pandas. We've also seen at this point how easy it is to convert a Spark DataFrame to a pandas DataFrame.

# In[17]:

dep_stations = btd.groupBy(btd['Start Station']).count().toPandas().sort('count', ascending=False)
dep_stations


# Now that we've got a better sense of which stations might be interesting to look at, let's graph out, the number of trips leaving from the top two stations over time.

# In[18]:

dep_stations['Start Station'][:3] # top 3 stations


# we'll add a handy function to help us convert all of these into appropriate count data. We're just using pandas resampling function to turn this into day count data.

# In[19]:

def transform_df(df):
    df['counts'] = 1
    df['Start Date'] = df['Start Date'].apply(pd.to_datetime)
    return df.set_index('Start Date').resample('D', how='sum')


# In[20]:

pop_stations = [] # being popular stations - we could easily extend this to more stations
for station in dep_stations['Start Station'][:3]:
    temp = transform_df(btd.where(btd['Start Station'] == station).select("Start Date").toPandas())
    pop_stations.append(
        Scatter(
        x=temp.index,
        y=temp.counts,
        name=station
        )
    )


# In[21]:

data = Data(pop_stations)
py.iplot(data, filename="spark/over_time")


# Interestingly we can see similar patterns for the Embarcadero and Ferry Buildings. We also get a consistent break between work weeks and work days. There also seems to be an interesting pattern between fall and winter usage for the downtown stations that doesn't seem to affect the Caltrain station.

# You can learn more about Plotly Enterprise and collaboration tools with the links below:
# 
# - [Collaborations and Language Support](https://plot.ly/ipython-notebooks/collaboration/)
# - [Network Graphing](https://plot.ly/ipython-notebooks/network-graphs/)
# - [Maps with Plotly](https://plot.ly/ipython-notebooks/basemap-maps/)
# - [Plotly Enterprise](https://plot.ly/product/enterprise/)
