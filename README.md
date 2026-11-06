# 📺 HBO Max Checker

Script Python untuk mengecek validitas (Live/Dead) akun HBO Max secara massal. Script ini membaca file cookie berformat **Netscape HTTP Cookie File**, mendeteksi region secara otomatis, dan menembak API internal HBO Max untuk mengambil nama profil.


## 📋 Prasyarat
- Python 3.8 atau lebih baru.
- Library `requests`.

## ⚙️ Instalasi

1. **Buat dan Aktifkan Virtual Environment (Disarankan):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   python3 hbomax_cek.py
   
