from flask import request, jsonify, abort
from flask import current_app as app
from .models import User
from werkzeug.exceptions import NotFound, InternalServerError, BadRequest, UnsupportedMediaType
import traceback
from . import Session
from .auth_logic import AuthLogic
from .BLConsul import BLConsul
from .config import Config
import requests

bl_consul = BLConsul.get_instance()
auth_logic = AuthLogic()

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

@app.route('/auth/health', methods=['HEAD', 'GET'])
def health_check():
   # print("Health check on auth")
    return "OK", 200


@app.route('/auth/pubkey', methods=['GET'])
def get_pub_key():
    print("PUB KEY ASKED")
    response = {"publicKey" : auth_logic.get_public_key().decode("utf-8") }
    return jsonify(response)

@app.route('/auth/client', methods=['POST'])
def create_client():
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json

    if "username" in content and "password" in content:
        success = auth_logic.create_client(content["username"], content["password"])
    else:
        success = False
    response = jsonify(success)

    return response


@app.route('/auth', methods=['GET'])
def authenticate():
    username = request.authorization.username
    password = request.authorization.password

    if username and password:
        ok, jwt = auth_logic.authenticate(username,password)

        if ok:
            response = {"jwt": jwt.decode("utf-8") }
            return jsonify(response)
        else:
            return "Authentication failed"


    else:
        return "Can't find username and password"



@app.route('/auth/client', methods=['GET'])
def view_clients():
    print("GET /auth.")
    session = Session()
    clients = session.query(User).all()
    session.close()
    return jsonify(User.list_as_dict(clients))


@app.route('/auth/<int:client_id>', methods=['GET'])
def view_client(client_id):
    session = Session()
    client = session.query(User).get(client_id)
    if not client:
        abort(NotFound.code)
    print("GET User {}: {}".format(client_id, client))
    session.close()
    return jsonify(client.as_dict())


@app.route('/auth/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    session = Session()
    client = session.query(User).get(client_id)
    if not client:
        abort(NotFound.code)
    print("DELETE User {}.".format(client_id))
    session.delete(client)
    session.commit()
    session.close()
    return jsonify(client.as_dict())


    

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
