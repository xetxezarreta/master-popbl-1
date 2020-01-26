from flask import request, jsonify, abort
from flask import current_app as app
from .models import Order, Piece
from werkzeug.exceptions import NotFound, InternalServerError, BadRequest, UnsupportedMediaType
import traceback
import requests
import json

from .api_client import ApiClient
from .authenticator import Authenticator
from .order_logic import OrderLogic

import jwt
from .BLConsul import BLConsul
import requests
from .config import Config

from . import Session

api_client = ApiClient()

logic = OrderLogic()
auth = Authenticator()
bl_consul = BLConsul.get_instance()

# Get Service from consul by name and return  ##########################################################################
@app.route('/{}/<string:external_service_name>'.format(Config.SERVICE_NAME))
def external_service_response(external_service_name):
    service = bl_consul.get_service(external_service_name)
    service['Name'] = external_service_name
    print(""*50)
    print(external_service_name)
    if service is None:
        ret_message = "The service does not exist or there is no healthy replica"
        status_code = 404
    else:
        ret_message, status_code = call_external_service(service)
    return ret_message, status_code


@app.route('/{}/kv'.format(Config.SERVICE_NAME))
def key_values():
    kv = bl_consul.get_key_value_items()
    return jsonify(kv), 200


@app.route('/{}/catalog'.format(Config.SERVICE_NAME))
def get_catalog():
    catalog = bl_consul.get_service_catalog()
    return jsonify(catalog), 200


@app.route('/{}/replicas'.format(Config.SERVICE_NAME))
def get_replicas():
    replicas = bl_consul.get_service_replicas()
    return jsonify(replicas), 200


def call_external_service(service):
    url = "http://{host}:{port}/{path}".format(
        host=service['Address'],
        port=service['Port'],
        path=service['Name']
    )
    response = requests.get(url)
    if response:
        ret_message = jsonify({
            "caller": Config.SERVICE_NAME,
            "callerURL": "{}:{}".format(Config.IP, Config.PORT),
            "answerer": service['Name'],
            "answererURL": "{}:{}".format(service['Address'], service['Port']),
            "response": response.text,
            "status_code": response.status_code
        })
        status_code = response.status_code
    else:
        ret_message = "Could not get message"
        status_code = 500
    return ret_message, status_code


@app.route('/order/health', methods=['HEAD', 'GET'])
def health_check():
    # print("Health check on order")
    return "OK:200"


# Order Routes #########################################################################################################
@app.route('/order', methods=['POST'])
def create_order():
    auth_header = request.headers.get('Authorization')

    # Authenticate the user

    if auth_header:
        try:
            auth_token = auth_header.split(" ")[1]
            ok, dec_jwt = auth.authenticate(auth_token)

            if not ok:
                return "Bad Authentication"
            else:
                # Check Permissions
                if auth.check_permission(dec_jwt, "C OWN ORDER"):
                    auth_response = "Authenticated as " + \
                        dec_jwt["name"] + " with C OWN ORDER permissions"
                else:
                    return dec_jwt["name"] + "dosen't have 'C OWN ORDER' permissions"

        except IndexError:
            return "No auth token provided"
    else:
        return "No Auth Token Provided", 400

    # Create Order

    if request.headers['Content-Type'] != 'application/json':
        return "Bad Request", 400
    
    content = request.json

    if "description" in content and "country" in content and "number_of_pieces" in content and "client_id" in content:

        order_id = logic.create_order(
                description=content['description'],
                country=content['country'],
                number_of_pieces=content['number_of_pieces'],
                client_id=content['client_id']
        )
        return "{} \n Order saga {} started.".format(auth_response,order_id)

    else:
        return "Bad Request", 400 


@app.route('/order', methods=['GET'])
def get_all_orders(): 
    response=jsonify(logic.get_all_orders())
    return response


@app.route('/order/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = logic.get_order(order_id)
    if order:
        response=jsonify(order)
        return response
    else:
        return "{}"


@app.route('/order/<int:order_id>', methods=['DELETE'])
def cancel_order(order_id):

    auth_header = request.headers.get('Authorization')

    # Authenticate the user

    if auth_header:
        try:
            auth_token = auth_header.split(" ")[1]
            ok, dec_jwt = auth.authenticate(auth_token)

            if not ok:
                return "Bad Authentication"
            else:
                # Check Permissions
                if auth.check_permission(dec_jwt, "C OWN ORDER"):
                    auth_response = "Authenticated as " + \
                        dec_jwt["name"] + " with C OWN ORDER permissions"
                else:
                    return dec_jwt["name"] + "dosen't have 'C OWN ORDER' permissions"

        except IndexError:
            return "No auth token provided"
    else:
        return "No Auth Token Provided", 400

    # Cancel Order
    
    return logic.cancel_order(order_id)




# Error Handling #######################################################################################################
@app.errorhandler(UnsupportedMediaType)
def unsupported_media_type_handler(e):
    return get_jsonified_error(e)


@app.errorhandler(BadRequest)
def bad_request_handler(e):
    return get_jsonified_error(e)


@app.errorhandler(NotFound)
def resource_not_found_handler(e):
    return get_jsonified_error(e)


@app.errorhandler(InternalServerError)
def server_error_handler(e):
    return get_jsonified_error(e)


def get_jsonified_error(e):
    traceback.print_tb(e.__traceback__)
    return jsonify({"error_code": e.code, "error_message": e.description}), e.code
