import threading
import time
import subprocess
import sys

def run_xmlrpc_server():
    """Jalankan XML-RPC server"""
    subprocess.run([sys.executable, "xmlrpc_server.py"])

def run_flask_app():
    """Jalankan Flask app"""
    time.sleep(2)  # Tunggu XML-RPC server siap
    subprocess.run([sys.executable, "app.py"])

if __name__ == "__main__":
    print("Memulai Chat Room Application...")
    print("1. Starting XML-RPC Server...")
    
    # Jalankan XML-RPC server di thread terpisah
    xmlrpc_thread = threading.Thread(target=run_xmlrpc_server, daemon=True)
    xmlrpc_thread.start()
    
    print("2. Starting Flask Application...")
    
    # Jalankan Flask app
    try:
        run_flask_app()
    except KeyboardInterrupt:
        print("\nAplikasi dihentikan.")