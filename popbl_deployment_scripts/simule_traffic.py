import requests
import random
import time

# CONST
HOST = "3.221.155.103"
PORT = "8443"
RANDOM_LIMIT = 1000000000000000
USERNAME = "simulation_user"
PASSWORD = "1234"

# URLS

URL_CREATE_USER = "https://{}:{}/auth/client".format(HOST, PORT)
URL_AUTHENTICATE = "https://{}:{}/auth".format(HOST, PORT)
URL_PAYMENT = "https://{}:{}/payment/perform_deposit".format(HOST, PORT)
URL_ORDER = "https://{}:{}/order".format(HOST, PORT)


new_client = {
    "username": USERNAME,
    "password": PASSWORD
}


payment_deposit = {
    "clientId": 2,
    "quantity": 50
}


# Helpers

# Log response
def log_response(call, response):
    print("Call to {} \n returned:  {}").format(call, response.text)


def sleep_rnd_time(lower, upper):
    random_seconds = random.randint(lower, upper)
    print("Sleeping {} seconds".format(random_seconds))
    time.sleep(random_seconds)


def get_order_dict():
    NUMBER_OF_PIECES = [2, 3, 5, 10, 15]
    CODES = ["araba", "bizkaia", "gipuzkoa", "madrid"]

    new_order = {
        "number_of_pieces": NUMBER_OF_PIECES[random.randrange(0, 4)],
        "description": "test",
        "client_id": 2,
        "country": CODES[random.randrange(0, 3)]
    }

    return new_order

user_id = 0

while(True):

    user_id += 1
    # Create sim user
    response = requests.post(URL_CREATE_USER, verify=False, json=new_client)
    log_response("CREATE_USER", response)

    # Get  token
    response = requests.get(URL_AUTHENTICATE, auth=(
        USERNAME, PASSWORD), verify=False)
    log_response("GET_TOKEN", response)

    token = response.json()["jwt"]

    header = {'Authorization': 'Bearer ' + token}

    # Create Payment

    response = requests.post(URL_PAYMENT, verify=False, json=payment_deposit)
    log_response("PERFORM_DEPOSIT", response)

    # Create Order

    for i in range(2 , random.randrange(3,10)):
        response = requests.post(URL_ORDER, verify=False,
                                json=get_order_dict(), headers=header)

        log_response("CREATE_ORDER", response)

        sleep_rnd_time(10,60)

    
    sleep_rnd_time(20,60)

