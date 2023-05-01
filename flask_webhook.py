import atexit
import logging
import os
import queue
import signal
import subprocess
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request

from trading import TradeCrypto
from utils.exchanges import get_exchanges

app = Flask(__name__)

# Create a thread-safe queue to store incoming data
incoming_data_queue = queue.Queue()

# Create an event to signal the thread to stop
stop_event = threading.Event()

def run_svinx():
    global svinx_process  # Declare the subprocess as a global variable
    
    try:
        # Check if the subprocess already exists and terminate it if it does
        if svinx_process:
            os.kill(svinx_process.pid, signal.SIGTERM)
        # Create the new subprocess
        svinx_process = subprocess.Popen("svix listen http://localhost:8000/webhook/", stdout=subprocess.PIPE, shell=True)
    except subprocess.CalledProcessError as e:
        logging.error(e)
    except Exception as e:
        logging.error(e)
    logging.info("Running the command 'svix listen http://localhost:8000/webhook/'")

svinx_process = None  # Initialize the subprocess variable to None

def process_data():
    exchanges = get_exchanges()
    while not stop_event.is_set():
        try:
            incoming_data = incoming_data_queue.get(timeout=1)
            TradeCrypto(incoming_data, exchanges)
        except queue.Empty:
            pass
        except Exception as e:
            logging.error(e)
    logging.info("Thread stopped")

@app.route('/webhook/', methods=['POST'])
def hook():
    incoming_data = request.get_json()
    try:
        incoming_data_queue.put(incoming_data)
    except Exception as e:
        logging.error(e)
        logging.exception(e)
    return jsonify(success=True)

def handle_signal(signal_number, frame):
    logging.info(f"Received signal {signal_number}. Shutting down...")
    stop()

def stop():
    scheduler.shutdown
    stop_event.set()
    thread.join()
    request.environ.get('werkzeug.server.shutdown')()

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Start the thread
    thread = threading.Thread(target=process_data)
    thread.start()

    # Start the svix process
    run_svinx()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=run_svinx, trigger="interval", seconds=7200)
    scheduler.start()

    print(scheduler.get_jobs())
    
    # Shut down the scheduler and thread when exiting the app
    atexit.register(stop)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    

    # Start the Flask app
    with app.app_context():
        app.run(host='127.0.0.1', port=8000)
