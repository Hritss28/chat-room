from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import xmlrpc.client
import threading
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Koneksi ke XML-RPC server
def get_xmlrpc_client():
    return xmlrpc.client.ServerProxy("http://localhost:8001", allow_none=True)

@app.route('/')
def index():
    """Halaman utama - redirect ke login jika belum login"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman login"""
    if request.method == 'POST':
        username = request.form['username']
        if username:
            try:
                client = get_xmlrpc_client()
                result = client.login(username)
                session['username'] = username
                return redirect(url_for('index'))
            except Exception as e:
                return render_template('login.html', error=f"Error: {str(e)}")
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    if 'username' in session:
        try:
            client = get_xmlrpc_client()
            client.logout(session['username'])
        except:
            pass
        session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/send_message', methods=['POST'])
def send_message():
    """Kirim pesan via AJAX"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'success': False, 'error': 'Pesan kosong'})
    
    try:
        client = get_xmlrpc_client()
        result = client.send_message(session['username'], message)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_messages')
def get_messages():
    """Ambil pesan terbaru via AJAX"""
    last_id = request.args.get('last_id', 0, type=int)
    
    try:
        client = get_xmlrpc_client()
        messages = client.get_messages(last_id)
        online_users = client.get_online_users()
        return jsonify({
            'success': True,
            'messages': messages,
            'online_users': online_users
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)