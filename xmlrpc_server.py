from xmlrpc.server import SimpleXMLRPCServer
import threading
import time
import socket
from datetime import datetime
import mysql.connector
import bcrypt
import uuid
from db_config import DB_CONFIG

class ChatServer:
    def __init__(self):
        self.db_config = DB_CONFIG
        self.init_db_connection()
    
    def init_db_connection(self):
        """Initialize database connection"""
        try:
            self.db = mysql.connector.connect(**self.db_config)
            self.cursor = self.db.cursor(dictionary=True)
            print("Connected to MySQL database")
        except mysql.connector.Error as e:
            print(f"Error connecting to MySQL: {e}")
            self.db = None
            self.cursor = None
    
    def get_db_connection(self):
        """Get fresh database connection"""
        try:
            if not self.db or not self.db.is_connected():
                self.init_db_connection()
            return self.db, self.cursor
        except Exception as e:
            print(f"Database connection error: {e}")
            return None, None
    
    def register(self, username, password, email=""):
        """Register new user"""
        db, cursor = self.get_db_connection()
        if not db:
            return {"success": False, "message": "Database connection error"}
        
        try:
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return {"success": False, "message": "Username sudah digunakan"}
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Insert new user
            query = "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)"
            cursor.execute(query, (username, password_hash, email))
            db.commit()
            
            return {"success": True, "message": f"User {username} berhasil didaftarkan"}
        
        except mysql.connector.Error as e:
            return {"success": False, "message": f"Database error: {str(e)}"}
    
    def login(self, username, password):
        """Login user dengan username dan password"""
        db, cursor = self.get_db_connection()
        if not db:
            return {"success": False, "message": "Database connection error"}
        
        try:
            # Get user data
            query = "SELECT id, username, password_hash FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            
            if not user:
                return {"success": False, "message": "Username tidak ditemukan"}
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                # Update user status
                cursor.execute("UPDATE users SET is_online = TRUE, last_login = NOW() WHERE id = %s", (user['id'],))
                
                # Create session token
                session_token = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO user_sessions (user_id, session_token) VALUES (%s, %s)",
                    (user['id'], session_token)
                )
                db.commit()
                
                return {
                    "success": True, 
                    "message": f"User {username} berhasil login",
                    "user_id": user['id'],
                    "session_token": session_token
                }
            else:
                return {"success": False, "message": "Password salah"}
        
        except mysql.connector.Error as e:
            return {"success": False, "message": f"Database error: {str(e)}"}
    
    def logout(self, username):
        """Logout user"""
        db, cursor = self.get_db_connection()
        if not db:
            return {"success": False, "message": "Database connection error"}
        
        try:
            # Update user status
            cursor.execute("UPDATE users SET is_online = FALSE WHERE username = %s", (username,))
            
            # Deactivate sessions
            cursor.execute(
                "UPDATE user_sessions SET is_active = FALSE WHERE user_id = (SELECT id FROM users WHERE username = %s)",
                (username,)
            )
            db.commit()
            
            return {"success": True, "message": f"User {username} telah logout"}
        
        except mysql.connector.Error as e:
            return {"success": False, "message": f"Database error: {str(e)}"}
    
    def send_message(self, username, message):
        """Kirim pesan ke chat room"""
        db, cursor = self.get_db_connection()
        if not db:
            return {"success": False, "message": "Database connection error"}
        
        try:
            # Get user ID
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if not user:
                return {"success": False, "message": "User tidak ditemukan"}
            
            # Insert message
            query = "INSERT INTO messages (user_id, username, message) VALUES (%s, %s, %s)"
            cursor.execute(query, (user['id'], username, message))
            db.commit()
            
            return {"success": True, "message": "Pesan berhasil dikirim"}
        
        except mysql.connector.Error as e:
            return {"success": False, "message": f"Database error: {str(e)}"}
    
    def get_messages(self, last_id=0):
        """Ambil pesan terbaru setelah last_id"""
        db, cursor = self.get_db_connection()
        if not db:
            return []
        
        try:
            # Pastikan last_id adalah integer dan tidak None
            if last_id is None:
                last_id = 0
            last_id = int(last_id)
            
            # Coba query sederhana dulu
            if last_id == 0:
                query = """
                    SELECT id, username, message, 
                           DATE_FORMAT(timestamp, '%H:%i:%s') as timestamp
                    FROM messages 
                    ORDER BY id ASC 
                    LIMIT 50
                """
                cursor.execute(query)
            else:
                query = """
                    SELECT id, username, message, 
                           DATE_FORMAT(timestamp, '%H:%i:%s') as timestamp
                    FROM messages 
                    WHERE id > %s 
                    ORDER BY id ASC 
                    LIMIT 50
                """
                cursor.execute(query, (last_id,))
                
            messages = cursor.fetchall()
            
            # Debug log
            print(f"Retrieved {len(messages)} messages after ID {last_id}")
            
            return messages
        
        except mysql.connector.Error as e:
            print(f"MySQL Error in get_messages: {e}")
            print(f"Query parameters: last_id={last_id} (type: {type(last_id)})")
            
            # Fallback: coba query tanpa parameter
            try:
                simple_query = "SELECT id, username, message, DATE_FORMAT(timestamp, '%H:%i:%s') as timestamp FROM messages ORDER BY id DESC LIMIT 10"
                cursor.execute(simple_query)
                messages = cursor.fetchall()
                print(f"� Fallback: Retrieved {len(messages)} messages")
                return messages
            except Exception as fallback_error:
                print(f"Fallback query also failed: {fallback_error}")
                return []
                
        except Exception as e:
            print(f"Unexpected error in get_messages: {e}")
            print(f"Parameters: last_id={last_id} (type: {type(last_id)})")
            return []
    
    def get_online_users(self):
        """Ambil daftar user yang online"""
        db, cursor = self.get_db_connection()
        if not db:
            return []
        
        try:
            cursor.execute("SELECT username FROM users WHERE is_online = TRUE ORDER BY username")
            users = cursor.fetchall()
            return [user['username'] for user in users]
        
        except mysql.connector.Error as e:
            print(f"Error getting online users: {e}")
            return []
    
    def get_total_messages(self):
        """Ambil total jumlah pesan"""
        db, cursor = self.get_db_connection()
        if not db:
            return 0
        
        try:
            cursor.execute("SELECT COUNT(*) as total FROM messages")
            result = cursor.fetchone()
            return result['total'] if result else 0
        
        except mysql.connector.Error as e:
            print(f"Error getting message count: {e}")
            return 0

def start_xmlrpc_server():
    """Jalankan server XML-RPC"""
    server = SimpleXMLRPCServer(("0.0.0.0", 8001), allow_none=True)
    chat_server = ChatServer()
    
    server.register_instance(chat_server)
    
    # Tampilkan informasi server
    local_ip = socket.gethostbyname(socket.gethostname())
    print("Connected to MySQL database")
    print("XML-RPC Server berjalan di:")
    print(f"- Network: http://{local_ip}:8001")
    print("- Untuk HP: gunakan IP address komputer ini")
    
    server.serve_forever()

if __name__ == "__main__":
    start_xmlrpc_server()