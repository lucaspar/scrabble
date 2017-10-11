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
TIME_INTERVAL = 0.3     # small time interval
MAX_CONN = 10           # maximum simultaneous connections
MAX_LETTERS = 30        # maximum number of letters on the board
MAX_REP = 4             # maximum number of replicas
REP_ADDR = {            # replicas' address
    '192.168.0.104':PORT_REP,
    #'127.0.0.1':PORT_REP,
    #'192.168.0.104':PORT_REP,
}
REP_NUM = len(REP_ADDR) # number of replicas

if MAX_REP < REP_NUM: raise Exception, 'REP_NUM is greater than MAX_REP'

# shared resources
THREADLOCK = threading.Lock()
BOARD = ['P', 'R', 'O', 'X', 'Y']
BOARD_STATE = -1
WORDLIST = game.Dictionary()

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

    def disconnect(self, exception=None):
        if exception: print 'SendBoard Raised:', exception
        print '\t', 'ROUTING BOARD FINISHED', self.client

        # disconnect and finish thread
        self.con.close()
        sys.exit()

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
                if not ready: self.disconnect()
            except socket.timeout:
                continue
            except:
                self.disconnect(sys.exc_info()[0])

            # min time interval between board messages
            time.sleep(TIME_INTERVAL)

            # send current board, update local state knowledge
            #if self.board_state < BOARD_STATE:
            self.con.send(','.join(BOARD)+';')
            self.board_state = BOARD_STATE

        self.disconnect()

################################################################################
# Receive the user attempts from a connected client
class RecvAttempts(threading.Thread):

    def __init__(self, name, con, client, serving):
        threading.Thread.__init__(self)
        self.serving    = serving
        self.client     = client
        self.name       = name
        self.con        = con
        self.con.settimeout(5.0)

    def disconnect(self, exception=None):
        if exception: print 'RecvAttempts Raised:', exception
        print '\t', 'ROUTING ATTEMPTS FINISHED', self.client
        self.con.close()
        sys.exit()

    def run(self):
        print '\t', 'ROUTING ATTEMPTS FROM', self.client

        global BOARD
        global BOARD_STATE
        global WORDLIST

        while self.serving.is_set():

            # receive word
            try:
                word = self.con.recv(1024)
                if not word: raise Exception('Invalid word')
                print '\t\t', common.strAddr(self.client), 'says', word
            except socket.timeout:
                continue;
            except:
                self.disconnect(sys.exc_info()[0])

            # if valid word
            if WORDLIST.contains(word):

                # send word to replicas
                responses = common.replicast(group=REP_ADDR, message=word, port_stride=1)
                res = responses.itervalues().next().split(';')

                # process the word, update board and board state
                points = res[1]
                error = res[2]
                with THREADLOCK:
                    if set(BOARD) != set(res[0]):
                        BOARD = res[0]
                        BOARD_STATE = BOARD_STATE + 1

                # send result
                print '\t\t', common.strAddr(self.client), 'made', points, 'pts'
                self.con.send(str(points) + ';' + error)

            # send failure
            else:
                print '\t\t', common.strAddr(self.client), 'sent invalid', word
                self.con.send('0;Ops, palavra inexistente')

        self.disconnect()

################################################################################
# Listen to user attempts connections
class UserAttempts(threading.Thread):

    def __init__(self, name, playing):
        threading.Thread.__init__(self)
        self.name = name
        self.serving = serving

    def run(self):

        tcp = common.tcp(HOST, PORT+1, MAX_CONN)

        con_count = 0
        threads = []
        while self.serving.is_set():
            con, client = tcp.accept()
            t = RecvAttempts("RECV_ATTEMPTS_"+str(con_count), con, client, serving)
            con_count = con_count + 1
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

        tcp = common.tcp(HOST, PORT, MAX_CONN)
        con_count = 0
        threads = []
        while self.serving.is_set():
            con, client = tcp.accept()
            t = SendBoard("SEND_BOARD_"+str(con_count), con, client, serving)
            con_count = con_count + 1
            t.start()
            threads.append(t)

        for t in threads:
            print ':: Finishing threads for routing board serving ::'
            t.join()

        tcp.close()

################################################################################
# Feed the board with new letters
class FeedingBoard(threading.Thread):

    def __init__(self, name, serving):
        threading.Thread.__init__(self)
        self.name = name
        self.serving = serving

    def run(self):
        while serving.is_set():
            if len(BOARD) < MAX_LETTERS:
                # choose a letter and multicast to replicas
                letter = game.chooseLetter()
                responses = common.replicast(group=REP_ADDR, message=letter, port_stride=64)

            # the more letter on the board, the less new letters over time
            interval = max(len(BOARD)/5, 0.4)
            time.sleep(interval)

################################################################################
# Periodically get the current board
class RetrieveBoard(threading.Thread):

    def __init__(self, name, serving):
        threading.Thread.__init__(self)
        self.name = name
        self.serving = serving

    def run(self):

        global BOARD
        global BOARD_STATE

        while serving.is_set():

            board = common.replicast_once(group=REP_ADDR, message='board', port_stride=128)

            if board and board_state > BOARD_STATE:

                board = board.split(';')
                board_state = int(board[1])
                board = board[0].split(',')

                with THREADLOCK:
                    BOARD = board
                    BOARD_STATE = board_state
                    print ''.join(BOARD), BOARD_STATE

            # wait for checking again
            time.sleep(TIME_INTERVAL)

################################################################################
# Run proxy server
if __name__ == "__main__":

    game.clearScreen()

    serving = threading.Event()
    serving.set()

    t_serving_board = ServeBoard("SERVE BOARD", serving)
    t_user_attempts = UserAttempts("USER ATTEMPTS", serving)
    t_feeding_board = FeedingBoard("FEED BOARD", serving)
    t_retrive_board = RetrieveBoard("RETRIEVE BOARD", serving)

    t_serving_board.daemon = True
    t_user_attempts.daemon = True
    t_feeding_board.daemon = True
    t_retrive_board.daemon = True

    t_serving_board.start()
    t_user_attempts.start()
    t_feeding_board.start()
    t_retrive_board.start()

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print "Attempting to close proxy threads."
        serving.clear()

        t_serving_board.join(timeout=0.5)
        t_user_attempts.join(timeout=0.5)
        t_feeding_board.join(timeout=0.5)
        t_retrive_board.join(timeout=0.5)

        if t_serving_board.isAlive() or t_user_attempts.isAlive() or \
            t_feeding_board.isAlive() or t_retrive_board.isAlive():
            print 'Bye'
            common.terminate()

        print "Proxy threads successfully closed :)"
