from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime
import os
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

print("Database path:", os.path.abspath('kasir.db'))

app = Flask(__name__)
app.secret_key = 'rahasia_anda'

conn = sqlite3.connect('kasir.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS produk (id INTEGER PRIMARY KEY, nama TEXT, harga INTEGER)''')
# Tambahkan kolom username jika belum ada
cursor.execute("PRAGMA table_info(transaksi)")
columns = [col[1] for col in cursor.fetchall()]
if 'username' not in columns:
    try:
        cursor.execute("ALTER TABLE transaksi ADD COLUMN username TEXT")
        conn.commit()
    except:
        pass
cursor.execute('''CREATE TABLE IF NOT EXISTS transaksi (
    id INTEGER PRIMARY KEY,
    nama_produk TEXT,
    jumlah INTEGER,
    total INTEGER,
    metode TEXT,
    tanggal TEXT,
    username TEXT
)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS pengguna (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)''')

# Tambahkan user jika belum ada
users = [
    ('denis', 'admin', 'pemilik'),
    ('almas', 'kr1', 'karyawan'),
    ('najim', 'kr2', 'karyawan'),
    ('dafa', 'kr3', 'karyawan'),
    ('karyawan4', 'karyawan123', 'karyawan'),
]
for u in users:
    cursor.execute('INSERT OR IGNORE INTO pengguna (username, password, role) VALUES (?, ?, ?)', u)
conn.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute('SELECT * FROM pengguna WHERE LOWER(username)=? AND LOWER(password)=?',
                       (username.lower(), password.lower()))
        user = cursor.fetchone()
        if user:
            session['username'] = user[1]
            session['role'] = user[3]
            return redirect(url_for('index'))
        else:
            error = "Username atau password salah"
    return render_template('login.html', error=error)

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    cursor.execute('SELECT * FROM produk')
    produk = cursor.fetchall()
    return render_template('index.html', produk=produk, role=session.get('role'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/tambah_produk', methods=['GET', 'POST'])
def tambah_produk():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session.get('role') != 'pemilik':
        return redirect(url_for('index'))  # Hanya pemilik yang boleh akses
    if request.method == 'POST':
        nama = request.form['nama']
        harga_input = request.form['harga']
        harga_str = harga_input.replace('.', '').replace(',', '')
        harga = int(harga_str)
        cursor.execute('INSERT INTO produk (nama, harga) VALUES (?, ?)', (nama, harga))
        conn.commit()
        return redirect(url_for('index'))
    return render_template('tambah_produk.html')

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'username' not in session:
        return redirect(url_for('login'))
    keranjang = []
    total = 0
    cursor.execute('SELECT id, nama, harga FROM produk')
    for pid, nama, harga in cursor.fetchall():
        qty_str = request.form.get(f'qty_{pid}', '')
        try:
            qty = int(qty_str) if qty_str.strip() != '' else 0
        except ValueError:
            qty = 0
        if qty > 0:
            keranjang.append({'nama': nama, 'harga': harga, 'qty': qty})
            total += harga * qty
    if not keranjang:
        return redirect(url_for('index'))
    session['keranjang'] = keranjang
    session['total'] = total
    return render_template('checkout.html', keranjang=keranjang, total=total)

@app.route('/bayar', methods=['POST'])
def bayar():
    if 'username' not in session:
        return redirect(url_for('login'))
    metode = request.form['metode']
    total = session.get('total', 0)
    keranjang = session.get('keranjang', [])
    tanggal = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    username = session.get('username', '-')
    # Simpan transaksi per produk
    for item in keranjang:
        cursor.execute('INSERT INTO transaksi (nama_produk, jumlah, total, metode, tanggal, username) VALUES (?, ?, ?, ?, ?, ?)',
                       (item['nama'], item['qty'], item['harga'] * item['qty'], metode, tanggal, username))
    conn.commit()
    session.pop('keranjang', None)
    session.pop('total', None)
    return render_template('sukses.html', total=total, qr=None)

@app.route('/riwayat')
def riwayat():
    if 'username' not in session:
        return redirect(url_for('login'))
    cursor.execute('SELECT * FROM transaksi')
    data = cursor.fetchall()
    return render_template('riwayat.html', data=data)

def export_transaksi_to_excel():
    cursor.execute('SELECT id, nama_produk, jumlah, total, metode, tanggal, username FROM transaksi')
    data = cursor.fetchall()
    columns = ['ID', 'Nama Produk', 'Jumlah', 'Total', 'Metode', 'Tanggal', 'Karyawan']
    df = pd.DataFrame(data, columns=columns)
    df.to_excel('riwayat_transaksi.xlsx', index=False)
    print("Riwayat transaksi berhasil diekspor ke Excel.")

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Jakarta'))
    scheduler.add_job(export_transaksi_to_excel, 'cron', hour=22, minute=30)
    scheduler.start()

start_scheduler()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')