import zmq
import json
import streamlit as st
from loguru import logger
import configparser


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
def get_data(read_sock, stream,config, timeout = 300):
    pass