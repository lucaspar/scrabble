#!/usr/bin/python

from Tkinter import *
import threading
import socket
import time
import game
import sys
import os

class Interface:

    def __init__(self):
        self.ui_root = Tk()
        self.ui_root.title('SCRABBLE')
        self.ui_root.geometry("600x400")
        self.ui_root.resizable(0, 0)

    # set user interface
    def setInterface(self):
        bg = '#48d'
        self.frame = Frame(master=self.ui_root, width=600, height=400, padx=30, pady=20, bg=bg)
        self.frame.pack_propagate(0)
        self.frame.pack(fill=BOTH, expand=1)

        self.board_ui = StringVar()
        self.error_ui = StringVar()
        self.points_ui = StringVar()

        self.board_ui.set('')
        self.error_ui.set('')
        self.points_ui.set('')

        self.l_board = Message(master=self.frame, bg=bg, textvariable = self.board_ui, width=600, font=("Ubuntu Mono", 42), anchor=NW)
        self.l_error = Label(master=self.frame, bg=bg, textvariable = self.error_ui)
        self.l_points = Label(master=self.frame, bg=bg, textvariable = self.points_ui)

        self.l_board.pack(side='top')
        self.l_error.pack(side='bottom')
        self.l_points.pack(side='right')

    # update user interface
    def update(self, board, points, error):
        self.board_ui.set(' '.join(board))
        self.points_ui.set(str(points) + ' PONTOS')
        if len(error) > 0:
            self.error_ui.set('Erro: ' + error)
        else:
            self.error_ui.set('')

        self.ui_root.update_idletasks()

if __name__ == '__main__':

    #board = ['G', 'U', 'I']
    board = ['R', 'E', 'P', 'L', 'I', 'C', 'A', 'E', 'F', 'E', 'G', 'M',
             'S', 'P', 'E', 'E', 'S', 'G', 'M', 'S', 'P', 'E', 'E', 'S',
             'G', 'A', 'R', 'H', 'T', 'A', 'E', 'C', 'A', 'N', 'R', 'C']
    points = 15
    error = 'Mensagem de erro'

    gui = Interface()
    gui.setInterface()

    # playing
    try:
        while True:

            # updating UI
            gui.update(board, points, error)

            # timeout for redraw
            time.sleep(0.2)

        print '\n\t', ':: Update UI loop finished ::'
        print '\n\t', ':: Update UI connection closed ::'

    except:
        e = sys.exc_info()
        print '\n\t', ':: Update UI interrupted ::', e
