import signal
import sys

terminate = False
def signal_handling(signum,frame):
    global terminate
    terminate = True

def register_termination():
    signal.signal(signal.SIGINT,signal_handling)

def check_terminate():
    if terminate:
        print("goodbye")
        sys.exit()
