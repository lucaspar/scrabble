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
MAX_CONN = 10           # maximum simultaneous connections

# shared resources
THREADLOCK = threading.Lock()
BOARD = ['R', 'E', 'P', 'L', 'I', 'C', 'A']
BOARD_STATE = 0
SEQ_NUM = -1

################################################################################
# Receive the user attempts from proxy
class RecvAttempts(threading.Thread):

    def __init__(self, name, con, client, replicating):
        threading.Thread.__init__(self)
        self.name = name
        self.con = con
        self.client = client
        self.replicating = replicating

    def disconnect(self, exception=None):
        if exception:
            print 'Raised:', exception
        print '\t', 'ROUTING ATTEMPTS FINISHED', self.client
        self.con.close()
        self.serving.clear()
        sys.exit()

    def run(self):

        global SEQ_NUM

        print '\t', 'RECEIVING ATTEMPTS FROM', self.client

        global BOARD
        global BOARD_STATE
        self.con.settimeout(5.0)

        # receive word
        try:
            req = self.con.recv(1024)
            if not req: raise Exception('Invalid word')
        except:
            self.disconnect(sys.exc_info()[0])

        req = req.split(';')
        seq_num = int(req[0])
        word = req[1]
        print '\t\t', self.client, 'says', word

        # wait for concurrent messages
        while seq_num > SEQ_NUM + 1:
            print '.',
            time.sleep(0.1)

        # process the word, update board and board state
        with THREADLOCK:
            SEQ_NUM = SEQ_NUM + 1
            BOARD, points, error = game.process(BOARD, word)
            if not error:
                BOARD_STATE = BOARD_STATE + 1

        # send result
        print '\t\t', common.strAddr(self.client), 'made', points, 'points'
        result = [','.join(BOARD), str(points), error]
        result = ';'.join(result)
        self.con.send(result)

        self.con.close()

################################################################################
class UserAttempts(threading.Thread):

    def __init__(self, name, replicating):
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
            t = RecvAttempts("Connection "+str(con_count), con, client, self.replicating)
            t.start()
            threads.append(t)

        for t in threads:
            print ':: Finishing user attemtps threads ::'
            t.join()

        tcp.close()

################################################################################
class ServeBoard(threading.Thread):

    def __init__(self, name, replicating):
        threading.Thread.__init__(self)
        self.name = name
        self.replicating = replicating

    def run(self):

        global BOARD
        global BOARD_STATE

        tcp = common.tcp(HOST, PORT+128, MAX_CONN)

        while self.replicating.is_set():

            con, client = tcp.accept()
            con.settimeout(5.0)

            print '\t', 'SENDING BOARD TO', client[0]
            print '\t\t', ''.join(BOARD), SEQ_NUM

            with THREADLOCK:
                con.send(','.join(BOARD)+';'+str(BOARD_STATE))

            time.sleep(1)

            con.close()
        tcp.close()

################################################################################
class FeedingBoard(threading.Thread):

    def __init__(self, name, replicating):
        threading.Thread.__init__(self)
        self.name = name
        self.replicating = replicating

    def run(self):

        global BOARD
        global BOARD_STATE
        global SEQ_NUM

        tcp = common.tcp(HOST, PORT+64, 1)

        while replicating.is_set():

            con, client = tcp.accept()
            con.settimeout(5.0)

            # receive letter from proxy
            try:
                req = con.recv(1024)
                if not req: raise Exception('Empty feed')
            except:
                print sys.exc_info()[0]
                sys.exit()

            req = req.split(';')
            seq_num = int(req[0])
            letter = req[1]
            print '\t\t', client[0], 'added', letter

            # wait for concurrent messages
            while seq_num > SEQ_NUM + 1:
                print 'w',
                time.sleep(0.1)

            # process the word, update board and board state
            with THREADLOCK:
                SEQ_NUM = SEQ_NUM + 1
                BOARD.append(letter)
                BOARD_STATE = BOARD_STATE + 1

            # send ready sign
            con.send('r')
            con.close()

        print ':: Finishing feeding board thread ::'
        tcp.close()

################################################################################
# Run proxy server
if __name__ == "__main__":

    game.clearScreen()

    replicating = threading.Event()
    replicating.set()

    t_serving_board = ServeBoard("Serve Board", replicating)
    t_user_attempts = UserAttempts("User Attempts", replicating)
    t_feeding_board = FeedingBoard("Feed Board", replicating)

    t_serving_board.daemon = True
    t_user_attempts.daemon = True
    t_feeding_board.daemon = True

    t_serving_board.start()
    t_user_attempts.start()
    t_feeding_board.start()

    try:
        while 1:
            time.sleep(1)
    except KeyboardInterrupt:
        print "Attempting to close replica threads."
        replicating.clear()

        t_serving_board.join(timeout=0.5)
        t_user_attempts.join(timeout=0.5)
        t_feeding_board.join(timeout=0.5)

        if t_serving_board.isAlive() or t_user_attempts.isAlive() or t_feeding_board.isAlive():
            print 'Bye'
            common.terminate()

        print "Replica threads successfully closed :)"
