from xmlrpc.server import SimpleXMLRPCServer
import threading
import time
from datetime import datetime

class ChatServer:
    def __init__(self):
        self.messages = []
        self.users = {}
        self.online_users = set()
    
    def login(self, username):
        """Login user dan tandai sebagai online"""
        if username not in self.users:
            self.users[username] = {
                'joined': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        self.online_users.add(username)
        return f"User {username} berhasil login"
    
    def logout(self, username):
        """Logout user"""
        if username in self.online_users:
            self.online_users.remove(username)
        return f"User {username} telah logout"
    
    def send_message(self, username, message):
        """Kirim pesan ke chat room"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        msg_data = {
            'username': username,
            'message': message,
            'timestamp': timestamp,
            'id': len(self.messages) + 1
        }
        self.messages.append(msg_data)
        return True
    
    def get_messages(self, last_id=0):
        """Ambil pesan terbaru setelah last_id"""
        new_messages = [msg for msg in self.messages if msg['id'] > last_id]
        return new_messages
    
    def get_online_users(self):
        """Ambil daftar user yang online"""
        return list(self.online_users)
    
    def get_total_messages(self):
        """Ambil total jumlah pesan"""
        return len(self.messages)

def start_xmlrpc_server():
    """Jalankan server XML-RPC"""
    server = SimpleXMLRPCServer(("localhost", 8001), allow_none=True)
    chat_server = ChatServer()
    
    server.register_instance(chat_server)
    print("XML-RPC Server berjalan di http://localhost:8001")
    server.serve_forever()

if __name__ == "__main__":
    start_xmlrpc_server()