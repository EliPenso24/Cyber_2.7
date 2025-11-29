"""
protocol.py

Communication protocol for the file-operations system.
Provides methods for creating, parsing, and validating JSON messages
between client and server.

Date: 23.11.25
Author: Eli Penso
"""

import json
import logging


def test_protocol_assertions():
    """
Validates the Protocol's communication contract.

    Checks:
    1. Constants: Core protocol values are defined.
    2. Format: Ensures JSON requests and responses are correctly generated.
    3. Parsing: Verifies message strings are accurately converted to dictionaries.
    4. Validation: Confirms command strings are correctly identified.
    """

    assert Protocol.STATUS_SUCCESS == "success"
    assert Protocol.STATUS_ERROR == "error"
    assert Protocol.MESSAGE_END == "<END>"
    req = Protocol.create_request(Protocol.CMD_DIR, {"path": "."})
    parsed_req = Protocol.parse_message(req)
    assert parsed_req["type"] == "request"
    assert parsed_req["command"] == Protocol.CMD_DIR
    assert parsed_req["params"] == {"path": "."}
    resp = Protocol.create_response(Protocol.STATUS_SUCCESS, "OK", {"files": []})
    parsed_resp = Protocol.parse_message(resp)
    assert parsed_resp["type"] == "response"
    assert parsed_resp["status"] == Protocol.STATUS_SUCCESS
    assert parsed_resp["message"] == "OK"
    assert parsed_resp["data"] == {"files": []}
    assert Protocol.validate_command(Protocol.CMD_DIR)
    assert not Protocol.validate_command("INVALID")
    logging.info("protocol assertions passed")
    print("All protocol assertions passed")


class Protocol:
    """
    JSON-based protocol for client/server communication.
    Defines command types, status codes, and helper methods.
    """

    # Command types
    CMD_DIR = "DIR"
    CMD_DELETE = "DELETE"
    CMD_COPY = "COPY"
    CMD_EXECUTE = "EXECUTE"
    CMD_SCREENSHOT = "TAKE_SCREENSHOT"
    CMD_SEND_PHOTO = "SEND_PHOTO"
    CMD_EXIT = "EXIT"

    # Status codes
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"

    # End-of-message marker
    MESSAGE_END = "<END>"

    @staticmethod
    def send_binary(comm_socket, binary_data):
        """
        Send binary data (like image bytes) through socket.
        Parameters:
            comm_socket: The socket to send through
            binary_data: The bytes to send
        """
        sent = 0
        while sent < len(binary_data):
            sent += comm_socket.send(binary_data[sent:])
        logging.info(f"Sent {len(binary_data)} bytes of binary data")

    @staticmethod
    def receive_binary(comm_socket, size):
        """
        Receive exact amount of binary data from socket.
        Parameters:
            comm_socket: The socket to receive from
            size: Exact number of bytes to receive
        Returns:
            bytes: The binary data received
        """
        binary_data = b''
        while len(binary_data) < size:
            chunk = comm_socket.recv(4096)
            if not chunk:
                break
            binary_data += chunk
        logging.info(f"Received {len(binary_data)} bytes of binary data")
        return binary_data

    @staticmethod
    def create_request(command, params=None):
        """
        Create a request message to send to the server.
        Args:
            command (str): The command name.
            params (dict, optional): Command parameters. Defaults to empty dict.
        Returns:
            str: JSON-formatted request string with end marker.
        """
        request = {"type": "request", "command": command, "params": params or {}}
        logging.info("Request JSON created")
        return json.dumps(request) + Protocol.MESSAGE_END

    @staticmethod
    def create_response(status, message, data=None):
        """
        Create a response message to send to the client.
        Args:
            status (str): "success" or "error".
            message (str): Description of the result.
            data (dict, optional): Optional data payload. Defaults to empty dict.
        Returns:
            str: JSON-formatted response string with end marker.
        """
        response = {"type": "response", "status": status, "message": message, "data": data or {}}
        logging.info("Response JSON created")
        return json.dumps(response) + Protocol.MESSAGE_END

    @staticmethod
    def parse_message(message):
        """
        Parse a received message string into a dictionary.
        Args:
            message (str): Raw message string including end marker.
        Returns:
            dict: Parsed message content.
        """
        logging.info("Parsing message")
        cleaned = message.replace(Protocol.MESSAGE_END, "")
        logging.info("Message parsed successfully")
        return json.loads(cleaned)

    @staticmethod
    def validate_command(command):
        """
        Check if a command is supported.
        Args:
            command (str): Command to validate.
        Returns:
            bool: True if command is valid, False otherwise.
        """
        logging.info(f"Validating command: {command}")
        valid_commands = {
            Protocol.CMD_DIR,
            Protocol.CMD_DELETE,
            Protocol.CMD_COPY,
            Protocol.CMD_EXECUTE,
            Protocol.CMD_SCREENSHOT,
            Protocol.CMD_SEND_PHOTO,
            Protocol.CMD_EXIT
        }
        result = command in valid_commands
        logging.info(f"Command valid: {result}")
        return result