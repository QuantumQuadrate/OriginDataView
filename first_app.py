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
import GetData as reciever
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
        #get the data and graph it
        pass


@st.cache(ttl=60*10,show_spinner=False)
def get_stream_filter(stream_dict,stream,length = 4):
    stream_id = str(stream_dict[stream]["id"]).zfill(length)
    return stream_id
#here is where we will start the sub port and read

col1,col2 = st.beta_columns(2)    
with col1:
    start_button = st.button("Start Subscribing")
graphs = {}
with col2:
    stop_button = st.button("Stop Subscribing")

time_slider = st.slider(label="Select a time range for the live graph to display",
    min_value = datetime.time(hour=0,minute=0,second=10),
    value =datetime.time(hour=0,minute=10,second=0),
    step = datetime.timedelta(seconds=1),
    max_value=datetime.time(hour=1),
    format="H:mm:ss"

    )

if start_button:
    try:
        sub_sock.close()
    except:
        pass
    sub_sock = reciever.create_socket_sub()
    window_size = {}
    DATA = {}
    for stream in checked_streams:
        streamID = get_stream_filter(stream_dict,stream)
        DATA[streamID] = reciever.get_data(read_sock,stream,start=time.time(),
            timeout=time_slider)
        sub_sock.setsockopt_string(zmq.SUBSCRIBE, streamID)
        graphs[streamID] = st.empty()
        window_size[streamID] = DATA[streamID].size
    sub_boolean = True

#loop to get the data from subscriber and graph it 
count = 0
debug_write = st.empty()
while sub_boolean:
    
    try:
        [streamID, content] = sub_sock.recv_multipart()
        streamID = streamID.decode('ascii','strict')
        content =json.loads(content.decode('ascii','strict'))
        content['measurement_time'] = pd.to_datetime(content['measurement_time']/(2**32),unit="s")
        content = {key : [content[key]] for key in content}
        content = pd.DataFrame(content).melt('measurement_time')

        if streamID not in DATA:
            #add the data
            pass
        else:
            #append the data
            DATA[streamID] = DATA[streamID].append(content,ignore_index=True).sort_values(
                by=['variable','measurement_time',]
            )

            if DATA[streamID].size > window_size[streamID]:
                #remove the oldest elements
                oldest_time = DATA[streamID].at[0,'measurement_time']
                DATA[streamID] = DATA[streamID][DATA[streamID].measurement_time != oldest_time] 
        for key in DATA:
            fig = px.line(DATA[key],x='measurement_time',y='value',color='variable')
            fig.update_layout(uirevision='true')
            graphs[key].plotly_chart(fig,use_container_width =True)
    except KeyError as e:
        st.write("error with subscribing object, try refreshing page to fix")
    except zmq.ZMQError as e:
        logger.debug(e)
        #all of the proper shutdown calls
        sub_sock.close()
        st.write("Connection error, closing subscription")
        logger.error("Connection error, closing subscription")
        sub_boolean = False
    
    if stop_button:
        sub_sock.close()
        st.write("Breaking while loop")
        sub_boolean = False
    

