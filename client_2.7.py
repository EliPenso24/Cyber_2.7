"""
client.py

File Operations Client that connects to a server, sends commands,
and receives responses using the Protocol class.

Date: 23.11.25
Author: Eli Penso
"""

import os
import logging
import socket
from protocol import Protocol


class FileOperationsClient:
    """
    Client to send commands to the FileOperationsServer.
    """

    def __init__(self, host='127.0.0.1', port=6767):
        """
        Initialize the client.

        Args:
            host (str): Server host IP.
            port (int): Server port.
        """
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        logging.info("Client object created.")

    def connect(self):
        """
        Connect to the server.

        Returns:
            bool: True if connected successfully, False otherwise.
        """
        try:
            logging.info(f"Attempting to connect to server {self.host}:{self.port}")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            logging.info("Connected successfully.")
            print(f"\n[CLIENT] Connected to server at {self.host}:{self.port}")
            return True
        except Exception as e:
            logging.info(f"Connection failed: {e}")
            print(f"[CLIENT] Connection failed: {e}")
            return False

    def send_command(self, command, params=None):
        """
        Send a command to the server.

        Args:
            command (str): Command to send.
            params (dict, optional): Command parameters.

        Returns:
            dict: Server response with status, message, and optional data.
        """
        if not self.connected:
            logging.info("Attempted to send a command while not connected.")
            return {'status': Protocol.STATUS_ERROR, 'message': 'Not connected to server'}

        try:
            logging.info(f"Creating request. Command: {command}, Params: {params}")
            request = Protocol.create_request(command, params)
            self.socket.send(request.encode('utf-8'))

            buffer = ""
            while Protocol.MESSAGE_END not in buffer:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    logging.info("Server returned empty response.")
                    break
                buffer += data

            logging.info(f"Full response received: {buffer}")
            response = Protocol.parse_message(buffer)
            logging.info(f"Parsed response: {response}")

            # Check if we need to receive binary data (photo)
            if response.get('data', {}).get('size'):
                size = response['data']['size']
                logging.info(f"Receiving binary data: {size} bytes")
                binary_data = Protocol.receive_binary(self.socket, size)
                response['binary'] = binary_data
                logging.info("Binary data received")

            return response

        except Exception as e:
            logging.info(f"Error sending command: {e}")
            return {'status': Protocol.STATUS_ERROR, 'message': str(e)}

    def disconnect(self):
        """
        Disconnect from the server.
        """
        if self.socket:
            logging.info("Disconnecting from server.")
            self.socket.close()
            self.connected = False
            logging.info("Disconnected successfully.")
            print("[CLIENT] Disconnected from server")

    # ============== User-friendly command methods ==============

    def dir_command(self, path):
        """Send DIR command to list files in a directory."""
        logging.info(f"DIR called with path: {path}")
        return self.send_command(Protocol.CMD_DIR, {'path': path})

    def delete_command(self, file_path):
        """Send DELETE command to delete a file."""
        logging.info(f"DELETE called with file: {file_path}")
        return self.send_command(Protocol.CMD_DELETE, {'file_path': file_path})

    def copy_command(self, source, destination):
        """Send COPY command to copy a file."""
        logging.info(f"COPY called: {source} -> {destination}")
        return self.send_command(Protocol.CMD_COPY, {'source': source, 'destination': destination})

    def execute_command(self, program_path):
        """Send EXECUTE command to run a program."""
        logging.info(f"EXECUTE called with: {program_path}")
        return self.send_command(Protocol.CMD_EXECUTE, {'program_path': program_path})

    def take_screenshot(self, save_path='screen.jpg'):
        """Send SCREENSHOT command to take a screenshot."""
        logging.info(f"SCREENSHOT called. Saving to: {save_path}")
        return self.send_command(Protocol.CMD_SCREENSHOT, {'save_path': save_path})

    def send_photo(self, image_path):
        """Send SEND_PHOTO command to send an image file."""
        logging.info(f"SEND_PHOTO called with: {image_path}")
        return self.send_command(Protocol.CMD_SEND_PHOTO, {'image_path': image_path})

    def exit_command(self):
        """Send EXIT command and disconnect from server."""
        logging.info("EXIT command called.")
        result = self.send_command(Protocol.CMD_EXIT)
        self.disconnect()
        return result


def test_client_assertions():
    """
    Validates the contract of all client components.

    Checks:
    1. Initialization: Confirms default host, port, and initial connection state are correct.
    2. Disconnection Error: Verifies `send_command` returns an error status when not connected.
    3. Command Wrappers: Ensures all user-friendly methods
    (e.g., `dir_command`) return the expected disconnection error dictionary.
    4. Final State: Confirms `exit_command` processes the request and ensures
    the client's connection status is finalized.
    """
    client = FileOperationsClient()

    assert client.host == '127.0.0.1'
    assert client.port == 6767
    assert client.connected is False
    assert client.socket is None

    response = client.send_command('FAKE_COMMAND')
    assert isinstance(response, dict)
    assert response.get('status') == Protocol.STATUS_ERROR

    expected_error = {'status': Protocol.STATUS_ERROR, 'message': 'Not connected to server'}

    assert client.dir_command('.') == expected_error
    assert client.delete_command('a.txt') == expected_error
    assert client.copy_command('a', 'b') == expected_error
    assert client.execute_command('prog.exe') == expected_error
    assert client.take_screenshot() == expected_error
    assert client.send_photo('img.jpg') == expected_error

    result = client.exit_command()
    assert result == expected_error
    assert client.connected is False

    logging.info("Client assertions passed (tested contract without live connection).")
    print("All client assertions passed (tested contract without live connection).")


def init_logs():
    """
    Initialize logging to LOGS/client.log.
    """
    os.makedirs("LOGS", exist_ok=True)
    logging.basicConfig(filename='LOGS/client.log', filemode='w', level=logging.INFO)
    logging.info("Initializing logging to LOGS/client.log.")


def display_menu():
    """
    Display the main menu to the user.
    """
    logging.info("Displaying menu to user.")
    print("\n" + "=" * 24)
    print("FILE OPERATIONS CLIENT")
    print("=" * 24)
    print("1. DIR -                        Displays files via given directory")
    print("2. DELETE -                            Deletes file via given path")
    print("3. COPY -              Copies file to another file via given paths")
    print("4. EXECUTE -                    Executes command via given program")
    print("5. SCREENSHOT -           Saves screenshot of screen to screen.jpg")
    print("6. SEND_PHOTO - Saves sent data fron screen.jpg to sent_screen.jpg")
    print("7. EXIT -                                        Exits the program")
    print("=" * 24)


def main():
    """
    Main function to run the client.
    """
    logging.info("Client started.")
    print("\n" + "=" * 60)
    print("FILE OPERATIONS CLIENT")
    print("=" * 60)

    client = FileOperationsClient()

    if not client.connect():
        logging.info("Client failed to connect. Exiting.")
        print("[CLIENT] Failed to connect to server. Exiting...")
        return

    while True:
        display_menu()
        choice = input("\nEnter your choice (1-7): ").strip()
        logging.info(f"User selected option: {choice}")

        if choice == '1':
            path = input("Enter directory path: ")
            logging.info(f"User input for DIR: {path}")
            result = client.dir_command(path)
            print(f"\n[{result['status'].upper()}] {result['message']}")
            if result['status'] == Protocol.STATUS_SUCCESS:
                files = result.get('data', {}).get('files', [])
                for f in files:
                    print(f"  {f}")

        elif choice == '2':
            file_path = input("Enter file path to delete: ")
            logging.info(f"User input for DELETE: {file_path}")
            result = client.delete_command(file_path)
            print(f"\n[{result['status'].upper()}] {result['message']}")

        elif choice == '3':
            source = input("Enter source file path: ")
            destination = input("Enter destination file path: ")
            logging.info(f"User input for COPY: {source} -> {destination}")
            result = client.copy_command(source, destination)
            print(f"\n[{result['status'].upper()}] {result['message']}")

        elif choice == '4':
            program = input("Enter program to execute: ")
            logging.info(f"User input for EXECUTE: {program}")
            result = client.execute_command(program)
            print(f"\n[{result['status'].upper()}] {result['message']}")

        elif choice == '5':
            logging.info("User selected SCREENSHOT")
            result = client.take_screenshot('screen.jpg')
            print(f"\n[{result['status'].upper()}] {result['message']}")

        elif choice == '6':
            logging.info("User selected SEND_PHOTO")
            result = client.send_photo('screen.jpg')

            if 'binary' in result:
                with open('sent_screen.jpg', 'wb') as f:
                    f.write(result['binary'])
                print(f"\n[{result['status'].upper()}]  Photo saved as sent_screen.jpg")
                logging.info("Photo saved to sent_screen.jpg")

        elif choice == '7':
            logging.info("User selected EXIT")
            result = client.exit_command()
            print(f"\n[{result['status'].upper()}] {result['message']}\n I hope you enjoyed! ;) ")

            break

        else:
            logging.info(f"Invalid user input: {choice}")
            print("\n[ERROR] Invalid choice! Please enter 1-7")


if __name__ == "__main__":
    test_client_assertions()
    init_logs()
    main()