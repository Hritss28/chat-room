from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import xmlrpc.client
import threading
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Koneksi ke XML-RPC server
def get_xmlrpc_client():
    return xmlrpc.client.ServerProxy("http://localhost:8001", allow_none=True)

@app.route('/')
def index():
    """Halaman utama - redirect ke login jika belum login"""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Halaman registrasi"""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form.get('email', '').strip()
        
        # Validasi input
        if not username or not password:
            flash('Username dan password harus diisi!', 'error')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('Username minimal 3 karakter!', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password minimal 6 karakter!', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Konfirmasi password tidak cocok!', 'error')
            return render_template('register.html')
        
        try:
            client = get_xmlrpc_client()
            result = client.register(username, password, email)
            
            if result['success']:
                flash('Registrasi berhasil! Silakan login.', 'success')
                return redirect(url_for('login'))
            else:
                flash(result['message'], 'error')
                return render_template('register.html')
        
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman login"""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        if not username or not password:
            flash('Username dan password harus diisi!', 'error')
            return render_template('login.html')
        
        try:
            client = get_xmlrpc_client()
            result = client.login(username, password)
            
            if result['success']:
                session['username'] = username
                session['user_id'] = result['user_id']
                session['session_token'] = result['session_token']
                flash(f'Selamat datang, {username}!', 'success')
                return redirect(url_for('index'))
            else:
                flash(result['message'], 'error')
                return render_template('login.html')
        
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return render_template('login.html')
    
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
        session.clear()
        flash('Anda telah logout.', 'info')
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
    
    if len(message) > 500:
        return jsonify({'success': False, 'error': 'Pesan terlalu panjang (max 500 karakter)'})
    
    try:
        client = get_xmlrpc_client()
        result = client.send_message(session['username'], message)
        
        if result['success']:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': result['message']})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_messages')
def get_messages():
    """Ambil pesan terbaru via AJAX"""
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
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
    app.run(debug=True,host='0.0.0.0', port=5000)