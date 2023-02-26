from concurrent.futures import ThreadPoolExecutor, as_completed

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
    

    print(json_data_list)
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for incoming_data in json_data_list:
            future = executor.submit(TradeCrypto, incoming_data, exchanges)
            futures.append(future)
            json_data_list.remove(incoming_data)
        
        # Wait for all futures to complete before returning
        for future in as_completed(futures):
            try:
                result = future.result(35)
            except Exception as e:
                print(f'Exception: {e}')
        
    return 'Data processed'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
