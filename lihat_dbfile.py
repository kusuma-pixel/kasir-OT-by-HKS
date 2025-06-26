import sqlite3

# Terhubung ke database
conn = sqlite3.connect('kasir.db')
cursor = conn.cursor()

print("📦 Daftar Produk")
print("-" * 40)
try:
    cursor.execute("SELECT * FROM produk")
    produk = cursor.fetchall()
    if produk:
        for row in produk:
            print(f"ID: {row[0]}, Nama: {row[1]}, Harga: {row[2]}")
    else:
        print("Tidak ada data produk.")
except Exception as e:
    print("Tabel produk tidak ditemukan:", e)

print("\n🧾 Riwayat Transaksi")
print("-" * 40)
try:
    cursor.execute("SELECT * FROM riwayat")
    riwayat = cursor.fetchall()
    if riwayat:
        for row in riwayat:
            print(f"ID: {row[0]}, Produk: {row[1]}, Jumlah: {row[3]}, Total: {row[4]}, Metode: {row[5]}, Tanggal: {row[6]}")
    else:
        print("Tidak ada data riwayat.")
except Exception as e:
    print("Tabel riwayat tidak ditemukan:", e)

conn.close()
