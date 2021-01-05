#!/usr/bin/env python
# -*- coding: utf-8 -*-

import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import numpy as np
import time
import pandas as pd
from loguru import logger
import datetime

import zmq
import json
import get_data as reciever
from streamlit.report_thread import get_report_ctx

import plotly.graph_objects as go
import altair as alt
import plotly.express as px

ctx = get_report_ctx()
session_id = ctx.session_id
st.set_page_config(layout='wide')

stream_selection = st.sidebar
readme_expander = st.beta_expander(label="readme")
readme_expander.write("""Every interaction with a widget will rerun the whole script and 
stop the subscription execution.
Just click the start subscribing button to resubscribe""")
data_expander = st.beta_expander(label="read data")



#set up the site
#get all of the streams we can subscribe to
sub_boolean = False
read_sock = reciever.create_socket_read(session_id)
stream_dict = reciever.get_available_streams(read_sock)["streams"]
known_streams = list(stream_dict.keys())
check_boxes = [stream_selection.checkbox(stream, key=stream) for stream in known_streams]
checked_streams = [stream for stream,checked in zip(known_streams,check_boxes) if checked]

with data_expander:
    day = st.date_input(label="Select the day to get the data for, if today, it will get the last 24hrs")
        
        
    if st.button("get data"):
        diff = abs(datetime.date.today()-day)
        timeout = datetime.timedelta(hours=1)
        date_data = pd.DataFrame()
        #get the data and graph it
        if int(diff.total_seconds()) == 0:
            start = time.time()
            #get the last 24 hours
            for stream in checked_streams:
                for i in range(24):
                    date_data = date_data.append(
                        reciever.get_data(
                            read_sock,stream,start,timeout=timeout,raw=False
                            ),ignore_index=True
                        )
                    start = start-timeout.total_seconds()
                date_data = date_data.dropna()
                plot_data = pd.DataFrame()
                for definition in stream_dict[stream]["definition"]:
                    st.write(definition)
                    plot_data[definition] = date_data[definition].apply(pd.Series).average
                
                plot_data['measurement_time'] = date_data['measurement_time'].apply(pd.Series).start/(2**32)
                plot_data['measurement_time'] = pd.to_datetime(plot_data['measurement_time'],unit="s")
                plot_data = plot_data.melt('measurement_time')
                fig = px.line(plot_data,x='measurement_time',y='value',color='variable')
                st.plotly_chart(fig)


                    


@st.cache(ttl=60*10,show_spinner=False)
def get_stream_filter(stream_dict,stream,length = 4):
    stream_id = str(stream_dict[stream]["id"]).zfill(length)
    return stream_id
#here is where we will start the sub port and read


live_graph_container = st.beta_expander(label="Live Graphing",expanded=True)
with live_graph_container:
    col1,col2 = st.beta_columns(2)    
    with col1:
        start_button = st.button("Start Subscribing")
    graphs = {}
    with col2:
        stop_button = st.button("Stop Subscribing")
    time_slider = st.slider(label="Select a time range for the live graph to display",
        min_value = datetime.time(hour=0,minute=0,second=10),
        value =datetime.time(hour=0,minute=4,second=0),
        step = datetime.timedelta(seconds=1),
        max_value=datetime.time(hour=1),
        format="H:mm:ss"
        )
#this will init the subscribe loop
#and get the data
if start_button:
    try:
        sub_sock.close()
    except:
        pass
    #sub port
    sub_sock = reciever.create_socket_sub()
    window_size = {}
    DATA = {}
    for stream in checked_streams:
        streamID = get_stream_filter(stream_dict,stream)
        DATA[streamID] = reciever.get_data(read_sock,stream,start=time.time(),
            timeout=time_slider)
        DATA[streamID].sort_values(by=['measurement_time','variable'],inplace=True)
        sub_sock.setsockopt_string(zmq.SUBSCRIBE, streamID)
        window_size[streamID] = DATA[streamID].shape
        #initiate graphs
        with live_graph_container:
            graphs[streamID] = st.empty()

    sub_boolean = True

#loop to get the data from subscriber and graph it 

while sub_boolean:
    #get some data before graphing
    for i in range(3*len(DATA.keys())):

        try:
            [streamID, content] = sub_sock.recv_multipart()
        except zmq.ZMQError as e:
            logger.debug(e)
            #all of the proper shutdown calls
            sub_sock.close()
            st.write("Connection error, closing subscription")
            logger.error("Connection error, closing subscription")
            sub_boolean = False


        streamID = streamID.decode('ascii','strict')
        content =json.loads(content.decode('ascii','strict'))
        content['measurement_time'] = pd.to_datetime(content['measurement_time']/(2**32),unit="s")
        content = {key : [content[key]] for key in content}
        content = pd.DataFrame(content).melt('measurement_time')

        #append the data
        DATA[streamID] = DATA[streamID].append(content,ignore_index=True)

    #get rid of old times
    for streamID in DATA:
        #get how much it changed by
        row0,col0 = window_size[streamID]
        row1,col1 = DATA[streamID].shape
        diff = row1-row0
        DATA[streamID].sort_values(by='measurement_time',inplace=True)
        #remove that amount from the oldest measurement times
        if diff > 0:
            DATA[streamID].drop(DATA[streamID].loc[0:int(diff)-1].index,inplace=True)
        #resort by variable and time
        DATA[streamID].sort_values(by=['measurement_time','variable'],inplace=True)

    #plot the new data
    for key in DATA:
        fig = px.line(DATA[key],x='measurement_time',y='value',color='variable')
        fig.update_layout(uirevision='true')
        with live_graph_container:
            graphs[key].plotly_chart(fig,use_container_width =True)
    
    if stop_button:
        sub_sock.close()
        st.write("Breaking while loop")
        sub_boolean = False
    

