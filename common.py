import sortedcontainers
import psutil
import socket
import errno
import os

# Return string from address tuple, as in "host:port"
def strAddr(addr):
    return str(addr[0])+':'+str(addr[1])

# Terminate process tree which called it
def kill_proc_tree(pid, including_parent=True):
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        child.kill()
    if including_parent:
        parent.kill()

# Terminate process which called it
def terminate():
    me = os.getpid()
    kill_proc_tree(me)

# Return server tcp socket
def tcp_server(host, port, max_conn=10):
    return tcp(host, port, max_conn=10)
def tcp(host, port, max_conn=10):
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    orig = (host, port)
    tcp.bind(orig)
    tcp.listen(max_conn)
    return tcp

# Return client tcp socket
def tcp_client(host, port, timeout=5):
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dest = (host, port)
    tcp.connect(dest)
    tcp.settimeout(timeout)
    return tcp

# Blocking synchronous single communication channel
def unicast(address, port, message, response_size=1024, timeout=5):
    response = None

    # connect to host
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dest = (address, port)
    tcp.connect(dest)
    tcp.settimeout(timeout)

    # send message
    tcp.send(message)

    # receive response
    if response_size>0:
        try: response = tcp.recv(response_size)
        except socket.timeout: pass

    return response

# Blocking synchronous multicast to group
def replicast(group, message, port_stride=0):
    responses = {}
    for address, port in group.items():
        try:
            responses[address] = unicast(address, port+port_stride, message)
        except socket.error as serr:
            print 'replicast: Replica %s is unreachable:' % address, serr

    return responses

# Return first "not None" response it gets from a replica
def replicast_once(group, message, port_stride=0):
    response = None
    for address, port in group.items():
        try:
            response = unicast(address, port+port_stride, message)
            if response is None: continue
            else: break
        except socket.error as serr:
            print 'replicast_once: Replica %s is unreachable:' % address, serr

    return response
