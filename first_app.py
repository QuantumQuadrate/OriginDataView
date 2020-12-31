#!/usr/bin/env python
# -*- coding: utf-8 -*-

import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import numpy as np
import time
import pandas as pd
from loguru import logger

import zmq
import json
import GetData as reciever
from streamlit.report_thread import get_report_ctx

ctx = get_report_ctx()
session_id = ctx.session_id


#set up the site
#get all of the streams we can subscribe to
read_sock = reciever.create_socket_read()
stream_dict = reciever.get_available_streams(read_sock)["streams"]
known_streams = list(stream_dict.keys())
check_boxes = [st.sidebar.checkbox(stream, key=stream) for stream in known_streams]
checked_streams = [stream for stream,checked in zip(known_streams,check_boxes) if checked]

sub_boolean = False

@st.cache(ttl=60*10)
def get_stream_filter(stream_dict,stream,length = 4):
    stream_id = str(stream_dict[stream]["id"]).zfill(length)
    return stream_id
#here is where we will start the sub port and read

start_button = st.button("Start Subscribing")
graph = st.empty()
stop_button = st.button("Stop Subscribing")
    
if start_button:
    try:
        sub_sock.close()
    except:
        pass
    sub_sock = create_socket_sub(session_id)
    for stream in checked_streams:
        sub_sock.setsockopt_string(zmq.SUBSCRIBE, get_stream_filter(stream_dict,stream))
    st.write(checked_streams)
    sub_boolean = True
    st.write("Started Subscribing")

#loop to get the data from subscriber and graph it 
count = 0
DATA = {}
while sub_boolean:
    try:
        [streamID, content] = sub_sock.recv_multipart()
        content =json.loads(content.decode('ascii','strict'))
        dat = {key:content[key] for key in content if key != "measurement_time"}
        content = pd.DataFrame(dat, index=[content["measurement_time"]])

        if streamID not in DATA:
            #add the data
            DATA[streamID] = content
        else:
            #append the data
            DATA[streamID] = DATA[streamID].append(content)
            if DATA[streamID].size > 1000:
                #remove the first element
                DATA[streamID].drop(DATA[streamID].head(1).index,inplace=True)
        count = count + 1
        for key in DATA:
            graph.line_chart(DATA[key])
        time.sleep(.01)
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
    

