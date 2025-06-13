import requests


url = 'https://ps.pishock.com/PiShock/'

def make_request(method, data, url, headers=None):
    if headers is None:
        headers = {'Content-Type': 'application/json'}
    if method == 'POST':
        response = requests.post(url, data=data, headers=headers)
    elif method == 'GET':
        response = requests.get(url, params=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def get_user_devices(userid, apikey):
    """
    Get the devices associated with a user.
    
    :param userid: User ID
    :param apikey: API key
    :return: JSON response containing user devices
    """
    data = {'UserId': userid, 'Token': apikey, 'api': 'true'}
    url_with_params = f'{url}GetUserDevices?UserId={userid}&Token={apikey}&api=true'
    return make_request('GET', data, url_with_params)

def operate(operation, intensity, duration, username, apikey, code, name):
    """
    Operate a device with the specified parameters.
    
    :param operation: Operation to perform
    :param intensity: Intensity of the operation
    :param duration: Duration of the operation
    :param username: Username of the user
    :param apikey: API key for authentication
    :param code: Device code
    :param name: Device name
    :return: JSON response from the operation request
    """
    print(f"Operating device with share code: {code}, operation: {operation}, intensity: {intensity}, duration: {duration}, username: {username}, apikey: {apikey}, name: {name}")
    data = {
        'Op': operation,
        'Intensity': intensity,
        'Duration': duration,
        'Username': username,
        'Apikey': apikey,
        'Code': code,
        'Name': name
    }
    headers = {'Content-Type': 'application/json'}
    return #make_request('POST', data, "https://do.pishock.com/api/apioperate/", headers)