import atexit
import queue
import subprocess
import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, redirect, request, url_for

from trading import TradeCrypto
from utils.exchanges import get_exchanges


def run_svinx() -> None:
    try:
        p = subprocess.Popen("svix listen http://localhost:8000/webhook/", stdout=subprocess.PIPE, shell=True)
        print(p.communicate())
    except subprocess.CalledProcessError as e:
        print(e)
    except Exception as e:
        print(e)

run_svinx()
scheduler = BackgroundScheduler()
scheduler.add_job(func=run_svinx, trigger="interval", seconds=7_200)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(scheduler.shutdown)

thread = None
app = Flask(__name__)

# Create a thread-safe queue to store incoming data
incoming_data_queue = queue.Queue()

@app.route('/webhook/', methods=['POST'])
def hook():
    
    incoming_data = request.get_json()
    incoming_data_queue.put(incoming_data)

    
     # Redirect to the start_processing endpoint
    return redirect(url_for('start_processing'))



def process_data():
    exchanges: dict[str, any] = get_exchanges()
    
    while True:
        try:
            incoming_data = incoming_data_queue.get(timeout=1)
            TradeCrypto(incoming_data, exchanges)
        except queue.Empty:
            break
        
    return 'Data processed'


@app.route('/process/')
def start_processing():
    # Start a separate thread to process incoming data
    global thread
    if thread is None or not thread.is_alive():
        thread = threading.Thread(target=process_data)
        thread.start()
        thread.join(25)
    return 'Data processing started'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
