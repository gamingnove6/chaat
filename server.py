import socket
import threading

clients = []

def handle_client(client_socket, addr):
    print(f"New client connected: {addr}")
    clients.append(client_socket)
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                clients.remove(client_socket)
                client_socket.close()
                print(f"Client disconnected: {addr}")
                break
            # Broadcast message to other clients
            for sock in clients:
                if sock != client_socket:
                    sock.send(message.encode('utf-8'))
        except:
            clients.remove(client_socket)
            client_socket.close()
            print(f"Client disconnected: {addr}")
            break

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 8080))
    server.listen(3)  # Up to 3 clients
    print("Server listening on port 8080...")

    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()

if __name__ == "__main__":
    main()
