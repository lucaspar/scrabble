#!/usr/bin/python
from Tkinter import *
import threading
import common
import socket
import time
import game
import sys
import os

# constants
HOST = '127.0.0.1'      # proxy address
PORT = 5000             # port

# game properties
board = []
points = 0
error = ''

################################################################################
class UpdateUI(threading.Thread):

    def __init__(self, name, playing):
        threading.Thread.__init__(self)
        self.name = name
        self.playing = playing

    def run(self):

        # shared game properties
        global board
        global points
        global error

        # connect to host
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dest = (HOST, PORT)
        tcp.connect(dest)
        tcp.settimeout(5.0)

        # set user interface
        bg = '#444'
        ui_root = Tk()
        ui_root.title('SCRABBLE')
        ui_root.geometry("500x500")
        ui_root.resizable(0, 0)

        frame = Frame(master=ui_root, width=500, height=500, bg=bg)
        frame.pack_propagate(0)
        frame.pack(fill=BOTH, expand=1)

        board_ui = StringVar()
        error_ui = StringVar()
        points_ui = StringVar()

        board_ui.set('')
        error_ui.set('')
        points_ui.set('')

        l_board = Label(master=frame, bg=bg, textvariable = board_ui, font=("Ubuntu", 44))
        l_error = Label(master=frame, bg=bg, textvariable = error_ui)
        l_points = Label(master=frame, bg=bg, textvariable = points_ui)

        l_board.pack(side='top')
        l_error.pack(side='bottom')
        l_points.pack(side='right')

        # playing
        try:
            while playing.is_set():

                # receive current board
                try:
                    board = (tcp.recv(1024)).split(';')[0].split(',')
                except socket.timeout:
                    continue

                # updating UI
                board_ui.set('  '.join(board))
                points_ui.set(str(points) + ' PONTOS')
                if len(error) > 0:
                    error_ui.set('Erro: ' + error)
                else:
                    error_ui.set('')

                ui_root.update_idletasks()

                # timeout for redraw
                time.sleep(0.1)

                # ready signal
                tcp.send('r')

            tcp.close()
            print '\n\t', ':: Update UI loop finished ::'
            print '\n\t', ':: Update UI connection closed ::'

        except:
            e = sys.exc_info()[0]
            tcp.close()
            playing.clear()
            print '\n\t', ':: Update UI interrupted ::', e

################################################################################
class UserInput(threading.Thread):

    def __init__(self, name, playing):
        threading.Thread.__init__(self)
        self.name = name
        self.playing = playing

    def run(self):

        # game properties
        global board
        global points
        global error

        # user input connection
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dest = (HOST, PORT+1)
        tcp.connect(dest)
        tcp.settimeout(5.0)

        # play game
        try:
            while playing.is_set():

                # send bet
                msg = raw_input()
                tcp.send(msg)

                # get result
                answer = (tcp.recv(1024)).split(';')
                print answer
                points = points + float(answer[0])
                error = answer[1]

                # ready signal
                tcp.send('r')

            tcp.close()
            print '\n\t', ':: User input loop finished ::'
            print '\n\t', ':: User input connection closed ::'

        except:
            e = sys.exc_info()[0]
            tcp.close()
            playing.clear()
            print '\n\t', ':: User input interrupted ::', e

################################################################################
if __name__ == "__main__":

    playing = threading.Event()
    playing.set()

    t_update_ui = UpdateUI("Update UI", playing)
    t_user_input = UserInput("User Input", playing)

    t_update_ui.start()
    t_user_input.start()

    try:
        while 1:
            time.sleep(.1)
    except KeyboardInterrupt:
        print "Attempting to close player threads."
        playing.clear()
        t_update_ui.join(timeout=0.5)
        t_user_input.join(timeout=0.5)

        if t_update_ui.isAlive() or t_user_input.isAlive():
            print 'Bye'
            common.terminate()

        print "Player threads successfully closed :)"
