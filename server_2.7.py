"""
server.py

File Operations Server that listens for client commands and executes
file-related operations using the Protocol class for communication.

Date: 23.11.25
Author: Eli Penso
"""

import socket
import os
import logging
import glob
import shutil
import subprocess
import pyautogui
from protocol import Protocol
import protocol


class FileOperationsServer:
    """
    Server to receive and execute file operation commands from clients.
    """

    # NOTE: __init__ MUST NOT be static. It needs 'self'.
    def __init__(self, host='127.0.0.1', port=6767):
        """
        Initialize server socket and host/port settings.
        Args:
            host (str): Host IP to bind.
            port (int): Port to listen on.
        """
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
        logging.info("Server socket created")


    def start(self):
        """
        Start the server and listen for client connections.
        Handles KeyboardInterrupt and errors gracefully.
        """
        logging.info("Server starting")
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        self.running = True

        print("=" * 60)
        print(f"[SERVER] File Operations Server Started")
        print(f"[SERVER] Listening on {self.host}:{self.port}")
        print("=" * 60)
        logging.info(f"Listening on {self.host}:{self.port}")

        while self.running:
            try:
                client_socket, address = self.socket.accept()
                logging.info(f"New connection from {address}")
                print(f"\n[SERVER] New connection from {address}")
                self.handle_client(client_socket, address)

            except KeyboardInterrupt:
                logging.info("Server interrupted, shutting down")
                print("\n[SERVER] Server shutting down...")
                break

            except Exception as e:
                logging.info(f"Server error: {e}")
                print(f"[SERVER] Error: {e}")

        self.socket.close()
        logging.info("Server socket closed")


    def handle_client(self, client_socket, address):
        """
        Handle requests from a connected client.
        Args:
            client_socket (socket.socket): Connected client socket.
            address (tuple): Client address (IP, port).
        """
        logging.info(f"Handling client {address}")
        buffer = ""

        while True:
            try:
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    logging.info(f"No data from {address}, closing connection")
                    break

                buffer += data

                if Protocol.MESSAGE_END in buffer:
                    message, buffer = buffer.split(Protocol.MESSAGE_END, 1)
                    logging.info(f"Received message from {address}")
                    print(f"[SERVER] Received command from {address[0]}")

                    request = Protocol.parse_message(message + Protocol.MESSAGE_END)
                    command = request['command']

                    logging.info(f"Parsed command: {command}")

                    if not Protocol.validate_command(command):
                        logging.info("Invalid command received")
                        response = Protocol.create_response(
                            Protocol.STATUS_ERROR,
                            "Invalid command"
                        )
                        client_socket.send(response.encode('utf-8'))
                        continue

                    print(f"[SERVER] Executing: {command}")
                    logging.info(f"Executing command: {command}")

                    # Calls instance methods like self.cmd_dir
                    result = self.execute_command(command, request.get('params', {}))

                    response = Protocol.create_response(
                        result['status'],
                        result['message'],
                        result.get('data', {})
                    )

                    client_socket.send(response.encode('utf-8'))
                    logging.info(f"Response sent: {result['status']}")

                    # If there's binary data, send it separately
                    if 'binary' in result:
                        Protocol.send_binary(client_socket, result['binary'])
                        logging.info("Binary data sent")

                    if command == Protocol.CMD_EXIT:
                        logging.info("Exit command received, closing client")
                        break

            except Exception as e:
                logging.info(f"Error handling client {address}: {e}")
                print(f"[SERVER] Error handling client: {e}")

                error_response = Protocol.create_response(
                    Protocol.STATUS_ERROR,
                    str(e)
                )

                try:
                    client_socket.send(error_response.encode('utf-8'))
                except socket.error as e:
                    print(f"Error sending error:{e}")
                    logging.info(f"Error sending error: {e}")
                    pass
                break

        client_socket.close()
        logging.info(f"Connection closed with {address}")
        print(f"[SERVER] Connection closed with {address}")


    def execute_command(self, command, params):
        """
        Execute the requested command.
        Args:
            command (str): Command to execute.
            params (dict): Parameters for the command.
        Returns:
            dict: Dictionary with status, message, and optional data.
        """
        logging.info(f"Executing command handler: {command}")

        if command == Protocol.CMD_DIR:
            return self.cmd_dir(params.get('path', '.'))

        elif command == Protocol.CMD_DELETE:
            return self.cmd_delete(params.get('file_path'))

        elif command == Protocol.CMD_COPY:
            return self.cmd_copy(params.get('source'), params.get('destination'))

        elif command == Protocol.CMD_EXECUTE:
            return self.cmd_execute(params.get('program_path'))

        elif command == Protocol.CMD_SCREENSHOT:
            return self.cmd_screenshot(params.get('save_path', 'screen.jpg'))

        elif command == Protocol.CMD_SEND_PHOTO:
            return self.cmd_send_photo(params.get('image_path'))

        elif command == Protocol.CMD_EXIT:
            logging.info("Exit command acknowledged")
            return {'status': Protocol.STATUS_SUCCESS, 'message': 'Goodbye'}

        logging.info("Unknown command received")
        return {'status': Protocol.STATUS_ERROR, 'message': 'Unknown command'}

    # ============== Command Implementations ==============


    @staticmethod
    def cmd_dir(path):
        """
        List files in a directory.
        Args:
            path (str): Directory path.
        Returns:
            dict: Status, message, and file list.
        """
        logging.info(f"DIR command on path: {path}")
        try:
            if not os.path.exists(path):
                return {'status': Protocol.STATUS_ERROR,
                        'message': f'Path does not exist: {path}',
                        'data': {'files': []}}

            files_list = glob.glob(os.path.join(path, '*.*'))
            return {'status': Protocol.STATUS_SUCCESS,
                    'message': f'Found {len(files_list)} files in {path}',
                    'data': {'files': files_list, 'count': len(files_list)}}
        except Exception as e:
            return {'status': Protocol.STATUS_ERROR, 'message': str(e), 'data': {'files': []}}

    @staticmethod
    def cmd_delete(file_path):
        """
        Delete a specified file.
        Args:
            file_path (str): File to delete.
        Returns:
            dict: Status and message.
        """
        logging.info(f"DELETE command on file: {file_path}")
        try:
            if not file_path:
                return {'status': Protocol.STATUS_ERROR, 'message': 'No file path provided'}

            if os.path.exists(file_path):
                os.remove(file_path)
                return {'status': Protocol.STATUS_SUCCESS, 'message': f'File deleted: {file_path}'}
            else:
                return {'status': Protocol.STATUS_ERROR, 'message': f'File does not exist: {file_path}'}
        except Exception as e:
            return {'status': Protocol.STATUS_ERROR, 'message': str(e)}


    @staticmethod
    def cmd_copy(source, destination):
        """
        Copy a file from source to destination.
        Args:
            source (str): Source file path.
            destination (str): Destination path.
        Returns:
            dict: Status and message.
        """
        logging.info(f"COPY from {source} to {destination}")
        try:
            if not source or not destination:
                return {'status': Protocol.STATUS_ERROR, 'message': 'Missing source or destination'}

            if os.path.exists(source) and os.path.exists(destination):
                shutil.copy(source, destination)
                return {'status': Protocol.STATUS_SUCCESS, 'message': f'File copied: {source} -> {destination}'}
            else:
                return {'status': Protocol.STATUS_ERROR, 'message': f'Source or Destination file does not exist: {source},{destination}\n I THINK YOU KNOW WHO IT IS!!!'}
        except Exception as e:
            return {'status': Protocol.STATUS_ERROR, 'message': str(e)}

    @staticmethod
    def cmd_execute(program_path):
        """
        Execute a program at the specified path.
        Args:
            program_path (str): Path to the program.
        Returns:
            dict: Status and message.
        """
        logging.info(f"EXECUTE program: {program_path}")
        try:
            if not program_path:
                return {'status': Protocol.STATUS_ERROR, 'message': 'No program path provided'}

            subprocess.Popen(program_path)
            return {'status': Protocol.STATUS_SUCCESS, 'message': f'Program executed: {program_path}'}
        except Exception as e:
            return {'status': Protocol.STATUS_ERROR, 'message': str(e)}

    @staticmethod
    def cmd_screenshot(save_path='screen.jpg'):
        """
        Take a screenshot and save it.
        Args:
            save_path (str): File path to save screenshot.
        Returns:
            dict: Status, message, and data with path.
        """
        logging.info(f"SCREENSHOT saving to: {save_path}")
        try:
            image = pyautogui.screenshot()
            image.save(save_path)
            return {'status': Protocol.STATUS_SUCCESS,
                    'message': f'Screenshot saved: {save_path}',
                    'data': {'path': save_path}}
        except Exception as e:
            return {'status': Protocol.STATUS_ERROR, 'message': str(e)}

    @staticmethod
    def cmd_send_photo(image_path):
        """
        Send a photo to the specified path.
        Args:
            image_path (str): Path to the image.
        returns:
            dict: Status and message and data with path and binary data of the photo.
        """
        try:
            with open(image_path, 'rb') as f:
                binary_data = f.read()

            size = len(binary_data)
            logging.info(f"SEND_PHOTO success, size {size}")
            return {
                'status': Protocol.STATUS_SUCCESS,
                'message': f'Photo ready to send: {image_path}',
                'data': {'size': size},
                'binary': binary_data  # Add binary data to return
            }
        except Exception as e:
            print (f"SEND_PHOTO failed, error message: {e}")
            logging.info(f"SEND_PHOTO failed, error message: {e}")
            return {'status': Protocol.STATUS_ERROR, 'message': str(e)} # Added return for error path


def test_server_assertions():

    """
    Validates the contract of all server components.

    Checks:
    1. Initialization: Confirms default host, port, and initial
    running state are correct.
    2. Dispatcher: Ensures the command dispatcher consistently
    returns a structured dictionary.
    3. Command Contract: Validates that all command handlers return
    the required status and message keys.
    4. Error Handling: Verifies that handlers correctly manage
    error conditions like non-existent paths.
    5. Binary Data: Checks the logic for including or excluding
    the 'binary' key in the response based on file existence.
    """

    server = FileOperationsServer()

    assert server.host == '127.0.0.1'
    assert server.port == 6767
    assert server.running is False
    assert server.socket is not None

    response = server.execute_command('FAKE_COMMAND', {})
    assert isinstance(response, dict)
    assert 'status' in response
    assert 'message' in response

    assert isinstance(server.cmd_dir('non_existing_path'), dict)
    assert isinstance(server.cmd_delete(''), dict)
    assert isinstance(server.cmd_copy('', ''), dict)
    assert isinstance(server.cmd_execute(''), dict)
    assert isinstance(server.cmd_screenshot('assertion.jpg'), dict)
    response = server.cmd_send_photo('screen.jpg')
    assert isinstance(response, dict), "Response should be a dict"
    assert 'status' in response and 'message' in response
    if os.path.exists('screen.jpg'):
        assert 'binary' in response
        assert isinstance(response['binary'], bytes)
        assert response['data']['size'] == len(response['binary'])
    else:
        assert 'binary' not in response

    logging.info("server assertions passed")
    print("All server assertions passed")


def init_logs():
    """
    Initialize logging to LOGS/server.log.
    """
    os.makedirs("LOGS", exist_ok=True)
    logging.basicConfig(filename='LOGS/server.log', filemode='w', level=logging.INFO)
    logging.info("Initializing logging to LOGS/client.log.")


def main():
    """
    Main entry point to run the server.
    """
    print("\n" + "=" * 60)
    print("FILE OPERATIONS SERVER")
    print("=" * 60)

    server = FileOperationsServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
    except Exception as e:
        print(f"[SERVER] Error: {e}")


if __name__ == "__main__":
    init_logs()
    logging.info("***Protocol Assertion***\n")
    protocol.test_protocol_assertions()
    logging.info("\n***Server Assertions***\n")
    test_server_assertions()
    logging.info("\n***Main***\n")
    main()
