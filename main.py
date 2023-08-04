from getpass import getpass
import json
import requests as re
import datetime
import urllib3
import asyncio

class Lnd:
    rest_host = None
    admin_macaroon = None

    def __init__(self, rest_host, admin_macaroon):
        self.rest_host = rest_host
        self.admin_macaroon = admin_macaroon

    def call_lnd(self, method, route, data = None):
        headers = { 'Grpc-Metadata-macaroon': self.admin_macaroon }
        if method == 'GET':
            return re.get(self.rest_host + route, headers = headers, params = data, verify = False)
        elif method == 'DELETE':
            return re.delete(self.rest_host + route, headers = headers, verify=False)
        else:
            print("Unsupported method: " + method)
            return None

    def get_info(self):
        raw_result = self.call_lnd('GET', '/v1/getinfo')
        return raw_result.json() 
    
    def list_channels(self):
        raw_result = self.call_lnd('GET', '/v1/channels')
        return raw_result.json()['channels']
    
    async def close_channel(self, txid, vout, chan_id):
        try:
            raw_result = self.call_lnd('DELETE', f'/v1/channels/{txid}/{vout}')
            return raw_result.text
        except Exception as e:
            print("Error closing channel: ", chan_id)
            print(e)
            return None
    
    async def close_channels(self, channels):
        tasks = []
        for channel in channels:
            txid, vout = channel['channel_point'].split(':')
            # Schedules concurrnet tasks to avoid blocking call
            tasks.append(self.close_channel(txid, vout, channel['chan_id']))
        
        print("Awaiting Channel Closures... This may take a while. (mine some blocks if you're on regtest)")
        result = await asyncio.gather(*tasks)
        print('\nRESULTS:\n', result, '\n')

    # Gets list of channels that have not been active in the last two weeks
    def get_inactive_channels(self):
        channels = self.list_channels()
        two_weeks = datetime.timedelta(days=14).total_seconds()
        return [x for x in channels if int(x['lifetime']) - int(x['uptime']) > two_weeks]

def pj(_json):
    print(json.dumps(_json, indent=4))

def setup_lnd():
    rest_host = getpass("Enter your LND REST host: ")
    # regtest host
    # rest_host = 'https://127.0.0.1:8082'

    while not rest_host.startswith("https://"):
        print("Invalid host, must be https://")
        rest_host = getpass("Enter your LND REST host: ")

    admin_macaroon = getpass("Enter your LND admin macaroon: ")
    # regtest mac
    # admin_macaroon = '0201036c6e6402f801030a10428349ebc1f9f9caacfc61c4682027e31201301a160a0761646472657373120472656164120577726974651a130a04696e666f120472656164120577726974651a170a08696e766f69636573120472656164120577726974651a210a086d616361726f6f6e120867656e6572617465120472656164120577726974651a160a076d657373616765120472656164120577726974651a170a086f6666636861696e120472656164120577726974651a160a076f6e636861696e120472656164120577726974651a140a057065657273120472656164120577726974651a180a067369676e6572120867656e657261746512047265616400000620aba84495ce85eb72c03b61e68fb7bd95fe84609dad72936fe7ba8326b92e844c' 
    while not admin_macaroon:
        print("Invalid macaroon")
        admin_macaroon = getpass("Enter your LND admin macaroon: ")

    LND = Lnd(rest_host, admin_macaroon)
    return LND


def main():
    LND = setup_lnd()
    
    # List of channels that have been inactive for two weeks
    cold_channels = LND.get_inactive_channels()

    # For testing closes
    # cold_channels = ['245191093059585', '231996953526273', '238594023292929'] 

    if len(cold_channels) == 0:
        print('No inactive channels to close!')
        return
    
    chan_ids = [x['chan_id'] for x in cold_channels]
    response = None 
    while response not in {'y', 'n'}:
        response = input(f'Close {len(cold_channels)} inactive channels? {chan_ids} (y/n):')
    
    if response == 'n':
        print('Exiting...')
        return;
    
    print('Closing channels...')
    asyncio.run(LND.close_channels(cold_channels))

    print(f'Closed {len(cold_channels)} channels. All done!')

if __name__ == '__main__':
    urllib3.disable_warnings() 
    main()
