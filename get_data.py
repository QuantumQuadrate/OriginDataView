import zmq
import json
import streamlit as st
from loguru import logger
import configparser
import datetime
import time
import numpy as np
import pandas as pd


def create_socket_sub():
    config = configparser.ConfigParser(inline_comment_prefixes = ';')
    config.read("origin-server.cfg")
    ip = config.get('Server','ip')
    sub_port = config.getint('Server', 'pub_port')

    context = zmq.Context()
    sub_sock = context.socket(zmq.SUB)
    sub_sock.connect("tcp://{}:{}".format(ip,sub_port))
    logger.debug("Connected to sub socket id: {}".format(id(sub_sock)))
    return sub_sock
    
@st.cache(hash_funcs={zmq.sugar.socket.Socket: id})
def create_socket_read(session_id):
    config = configparser.ConfigParser(inline_comment_prefixes = ';')
    config.read("origin-server.cfg")
    ip = config.get('Server','ip')
    read_port = config.getint('Server','read_port')

    context = zmq.Context()
    read_sock = context.socket(zmq.REQ)
    read_sock.connect("tcp://{}:{}".format(ip,read_port))
    logger.debug("Connected to read socket")
    return read_sock

@st.cache(ttl=10*60,hash_funcs={zmq.sugar.socket.Socket: id},show_spinner=False)
def get_available_streams(read_sock):
    """!@brief Request the knownStreams object from the server.
    @return knownStreams
    """
    # Sending an empty JSON object requests an object containing the
    # available streams
    logger.debug("read sock id: {}".format(id(read_sock)))
    
    read_sock.send_string('{}')
    try:
        err, known_streams = json.loads(read_sock.recv())
    except:
        logger.error("Error connecting to data server")
        st.write("Error connecting to data server")
    return known_streams



@st.cache(ttl=10*60,hash_funcs={zmq.sugar.socket.Socket: id},show_spinner=False)
def get_data(read_sock, stream,start=None, timeout = datetime.timedelta(seconds=600),raw=True):
    #first convert the datetime object to just seconds
    if not isinstance(timeout,datetime.timedelta):
        timeout = datetime.timedelta(hours=timeout.hour,
            minutes=timeout.minute,seconds=timeout.second) 
    if start is None:
        start = time.time()
    stop = start - timeout.total_seconds()
    request = {
            'stream': stream.strip(),
            'start': start,
            'stop': stop,
            'raw': raw,
        }
    read_sock.send_string(json.dumps(request))
    try:
            msg = read_sock.recv()
            data = json.loads(msg)
    except:
        msg = "There was an error communicating with the server"
        logger.error(msg)
        data = (1, {'error': msg, 'stream': {}})
    
    if data[0] != 0:
        msg = "The server responds to the request with error message: `{}`"
        logger.error(msg.format(data[1]["error"]))
        return {}
    else:
        if raw == False:
            return data[1]
        data[1]['measurement_time'] = pd.to_datetime(np.array(data[1]['measurement_time'])/(2**32),unit="s")

        return pd.DataFrame(data[1]).melt('measurement_time')



    