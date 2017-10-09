#!/usr/bin/python
import threading
import common
import socket
import game
import time
import sys

# constants
HOST = ''               # server address
PORT = 6000             # port
MAX_CONN = 5            # maximum simultaneous connections

# shared resources
THREADLOCK = threading.Lock()
BOARD = ['R', 'E', 'P', 'L', 'I', 'C', 'A']
BOARD_STATE = 0
SEND_BOARD = True

################################################################################
# Send current board to proxy
class SendBoard(threading.Thread):

    def __init__(self, name, con, client, serving):
        threading.Thread.__init__(self)
        self.name = name
        self.con = con
        self.client = client
        self.serving = serving
        self.board_state = -1

    def run(self):
        print '\t', 'SENDING BOARD TO', self.client

        global BOARD
        global BOARD_STATE
        global SEND_BOARD
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

            while self.replicating.is_set():

                # min time interval between board messages
                time.sleep(0.1)

                # send current board, update local state knowledge
                if self.board_state < BOARD_STATE:
                    self.con.send(','.join(BOARD)+';')
                    self.board_state = BOARD_STATE
                    break

        print '\t', 'SENDING BOARD FINISHED', self.client
        self.con.close()

################################################################################
# Receive the user attempts from proxy
class RecvAttempts(threading.Thread):

    def __init__(self, name, con, client, replicating):
        threading.Thread.__init__(self)
        self.name = name
        self.con = con
        self.client = client
        self.replicating = replicating

    def run(self):
        print '\t', 'RECEIVING ATTEMPTS FROM', self.client

        global BOARD
        global BOARD_STATE
        self.con.settimeout(5.0)

        while self.replicating.is_set():

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

        print '\t', 'RECEIVING ATTEMPTS FINISHED', self.client
        self.con.close()

################################################################################
class UserAttempts(threading.Thread):

    def __init__(self, name, playing):
        threading.Thread.__init__(self)
        self.name = name
        self.replicating = replicating

    def run(self):
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        orig = (HOST, PORT+1)

        tcp.bind(orig)
        tcp.listen(MAX_CONN)

        con_count = 0
        threads = []
        while self.replicating.is_set():
            con, client = tcp.accept()
            t = RecvAttempts("Connection "+str(con_count), con, client, replicating)
            t.start()
            threads.append(t)

        for t in threads:
            print ':: Finishing user attemtps threads ::'
            t.join()

        tcp.close()

################################################################################
class ServeBoard(threading.Thread):

    def __init__(self, name, playing):
        threading.Thread.__init__(self)
        self.name = name
        self.replicating = replicating

    def run(self):
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        orig = (HOST, PORT)

        tcp.bind(orig)
        tcp.listen(MAX_CONN)

        con_count = 0
        threads = []
        while self.replicating.is_set():
            con, client = tcp.accept()
            t = SendBoard("Connection "+str(con_count), con, client, replicating)
            t.start()
            threads.append(t)

        for t in threads:
            print ':: Finishing board replicating threads ::'
            t.join()

        tcp.close()

################################################################################
# Run proxy server
if __name__ == "__main__":

    game.clearScreen()

    replicating = threading.Event()
    replicating.set()

    t_serving_board = ServeBoard("Serve Board", replicating)
    t_user_attempts = UserAttempts("User Attempts", replicating)

    t_serving_board.start()
    t_user_attempts.start()

    try:
        while 1:
            time.sleep(.1)
    except KeyboardInterrupt:
        print "Attempting to close replica threads."
        replicating.clear()
        t_serving_board.join(timeout=0.5)
        t_user_attempts.join(timeout=0.5)

        if t_serving_board.isAlive() or t_user_attempts.isAlive():
            print 'Bye'
            common.terminate()

        print "Game threads successfully closed :)"
