import psutil , os

def kill_proc_tree(pid, including_parent=True):
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        child.kill()
    if including_parent:
        parent.kill()

def terminate():
    me = os.getpid()
    kill_proc_tree(me)
