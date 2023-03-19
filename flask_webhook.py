import queue
import threading

from flask import Flask, redirect, request, url_for

from trading import TradeCrypto
from utils.exchanges import get_exchanges

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
