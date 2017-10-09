#!/usr/bin/python
import threading
import common
import socket
import game
import time
import sys

# constants
HOST = ''               # server address
PORT = 5000             # clients port
PORT_REP = 6000         # replicas port
MAX_CONN = 10           # maximum simultaneous connections
MAX_REP = 4             # maximum number of replicas
REP_ADDR = [            # replicas' address
    '192.168.0.104',
    '192.168.0.104',
    '192.168.0.104'
]
REP_NUM = 1             # number of replicas
#REP_NUM = len(REP_ADDR)

if MAX_REP < REP_NUM: raise Exception, 'REP_NUM is greater than MAX_REP'

# shared resources
THREADLOCK = threading.Lock()
BOARD = ['P', 'R', 'O', 'X', 'Y']
BOARD_STATE = 0
BOARD_CHANGE = False

################################################################################
# Periodically send the board to a connected client
class SendBoard(threading.Thread):

    def __init__(self, name, con, client, serving):
        threading.Thread.__init__(self)
        self.name = name
        self.con = con
        self.client = client
        self.serving = serving
        self.board_state = -1

    def run(self):
        print '\t', 'ROUTING BOARD TO', self.client

        global BOARD
        global BOARD_STATE
        self.con.settimeout(5.0)
        self.con.send(','.join(BOARD)+';')

        while self.serving.is_set():

            # client ready to receive new board
            try:
                ready = self.con.recv(1)
                if not ready:
                    break
            except socket.timeout:
                continue

            while self.serving.is_set():

                # min time interval between board messages
                time.sleep(0.1)

                # send current board, update local state knowledge
                if self.board_state < BOARD_STATE:
                    self.con.send(','.join(BOARD)+';')
                    self.board_state = BOARD_STATE
                    break

        print '\t', 'ROUTING BOARD FINISHED', self.client
        self.con.close()

################################################################################
# Receive the user attempts from a connected client
class RecvAttempts(threading.Thread):

    def __init__(self, name, con, client, serving):
        threading.Thread.__init__(self)
        self.name = name
        self.con = con
        self.client = client
        self.serving = serving

    def run(self):
        print '\t', 'ROUTING ATTEMPTS FROM', self.client

        global BOARD
        global BOARD_STATE
        self.con.settimeout(5.0)

        while self.serving.is_set():

            # receive word
            try:
                word = self.con.recv(1024)
                if not word: break
                print '\t\t', self.client, 'says', word
            except socket.timeout:
                continue;

            # process the word, update board and board state
            with THREADLOCK:
                BOARD, points, error = game.process(BOARD, word)
                if len(error) == 0:
                    BOARD_STATE = BOARD_STATE + 1

            # send result
            print '\t\t', self.client, 'made', points, 'points'
            self.con.send(str(points) + ';' + error)

            while True:
                try:
                    # client ready to receive new board
                    ready = self.con.recv(1)
                    if ready:
                        break
                except socket.timeout:
                    print 'Waiting for ready signal'
                    continue;

        print '\t', 'ROUTING ATTEMPTS FINISHED', self.client
        self.con.close()

################################################################################
# Listen to user attempts connections
class UserAttempts(threading.Thread):

    def __init__(self, name, playing):
        threading.Thread.__init__(self)
        self.name = name
        self.serving = serving

    def run(self):
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        orig = (HOST, PORT+1)

        tcp.bind(orig)
        tcp.listen(MAX_CONN)

        con_count = 0
        threads = []
        while self.serving.is_set():
            con, client = tcp.accept()
            t = RecvAttempts("Connection "+str(con_count), con, client, serving)
            t.start()
            threads.append(t)

        for t in threads:
            print ':: Finishing threads for routing user attemtps ::'
            t.join()

        tcp.close()

################################################################################
# Listen to board server connections
class ServeBoard(threading.Thread):

    def __init__(self, name, playing):
        threading.Thread.__init__(self)
        self.name = name
        self.serving = serving

    def run(self):
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        orig = (HOST, PORT)

        tcp.bind(orig)
        tcp.listen(MAX_CONN)

        con_count = 0
        threads = []
        while self.serving.is_set():
            con, client = tcp.accept()
            t = SendBoard("Connection "+str(con_count), con, client, serving)
            t.start()
            threads.append(t)

        for t in threads:
            print ':: Finishing threads for routing board serving ::'
            t.join()

        tcp.close()

################################################################################
# Listen to board server connections to replicas
class ServeBoardRep(threading.Thread):

    def __init__(self, name, playing):
        threading.Thread.__init__(self)
        self.name = name
        self.serving = serving

    def run(self):
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        orig = (HOST, PORT_REP)

        tcp.bind(orig)
        tcp.listen(MAX_REP)

        con_count = 0
        threads = []
        while self.serving.is_set():
            con, client = tcp.accept()
            t = SendBoardRep("Connection "+str(con_count), con, client, serving)
            t.start()
            threads.append(t)

        for t in threads:
            print ':: Finishing threads for routing replica board ::'
            t.join()

        tcp.close()

################################################################################
# Run proxy server
if __name__ == "__main__":

    game.clearScreen()

    serving = threading.Event()
    serving.set()

    t_serving_board = ServeBoard("Serve Board", serving)
    t_user_attempts = UserAttempts("User Attempts", serving)

    t_serving_board.start()
    t_user_attempts.start()

    try:
        while 1:
            time.sleep(.1)
    except KeyboardInterrupt:
        print "Attempting to close game threads."
        serving.clear()
        t_serving_board.join(timeout=0.5)
        t_user_attempts.join(timeout=0.5)

        if t_serving_board.isAlive() or t_user_attempts.isAlive():
            print 'Bye'
            common.terminate()

        print "Game threads successfully closed :)"
