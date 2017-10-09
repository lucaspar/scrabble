#!/usr/bin/python

from Tkinter import *
import threading
import socket
import time
import game
import sys
import os

board = ['A', 'E', 'I', 'K', 'R']
points = 4
error = 'Jebediah detectado'

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
    while True:

        # updating UI
        board_ui.set('  '.join(board))
        points_ui.set(str(points) + ' PONTOS')
        if len(error) > 0:
            error_ui.set('Erro: ' + error)
        else:
            error_ui.set('')

        ui_root.update_idletasks()

        # timeout for redraw
        time.sleep(0.2)

    print '\n\t', ':: Update UI loop finished ::'
    print '\n\t', ':: Update UI connection closed ::'

except:
    e = sys.exc_info()[0]
    print '\n\t', ':: Update UI interrupted ::', e
