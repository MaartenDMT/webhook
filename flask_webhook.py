from threading import Thread

from flask import Flask, request

from trading import TradeCrypto
from utils.exchanges import get_exchanges

thread = None
app = Flask(__name__)

json_data_list = []
@app.route('/webhook/', methods=['POST'])
def hook():
    
    incoming_data = request.get_json()
    json_data_list.append(incoming_data)
    
    process_data(json_data_list)
    
    return 'Data received'

def process_data(json_data_list:list):
    exchanges: dict[str, any] = get_exchanges()
    
    threads = []
    print(exchanges)
    for incoming_data in json_data_list:
        # Do something with the data here
        thread = Thread(target =TradeCrypto, args=(incoming_data, exchanges))
        thread.start()
        threads.append(thread)
        json_data_list.remove(incoming_data)
        print(json_data_list)
    
    # Wait for all threads to finish before returning
    for thread in threads:
        thread.join()
        threads.remove(thread)
        
    return 'Data processed'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
