from datetime import datetime
from config import BOT_NAME, BOT_CREATOR


class Messages:
    @staticmethod
    def get_start_message(
        display_name: str,
        user_id: int,
        role: str = "Reguler",
        verification_status: str = "Belum Terverifikasi",
        expired_at: str = "—",
        limit_remaining: str = "10",
        total_requests: int = 0
    ) -> str:
        return f"""```
🎌  KIFZL DEV BOT
(BY @KIFZLDEV)
───────────────────────────────────────

"KONNICHIWA, WATASHI WA KIFZL_BOT DESU"
Saya siap bantu convert file & management kontak.
✦ Created by: @KIFZLDEV

───────────────────────────────────────
📍 STATUS AKUN
───────────────────────────────────────
• NAMA          : {display_name}
• ID            : {user_id}
• ROLE          : {role}
• VERIFIKASI    : {verification_status}
• MASA AKTIF    : {expired_at}
• LIMIT HARIAN  : {limit_remaining}
• TOTAL OPERASI : {total_requests}

───────────────────────────────────────
⚡ FITUR UTAMA
───────────────────────────────────────
🜲 STATUS               — Cek akses
🜲 MSG → TXT            — Convert
🜲 TXT → VCF            — Convert
🜲 VCF → TXT            — Ekstrak
🜲 CREATE ADM & NAVY    — Buat kontak admin/navy
🜲 RAPIKAN TXT          — Bersihkan format
🜲 XLS → VCF            — Convert XLS
🜲 GABUNG FILE          — Gabungkan
🜲 HITUNG KONTAK        — Hitung kontak
🜲 CEK NAMA KONTAK      — Validasi nama
🜲 SPLIT FILE           — Bagi file
🎁 REDEEM CODE          — Aktivasi

───────────────────────────────────────
```"""

    @staticmethod
    def get_menu_message() -> str:
        return """```
🜲 MENU UTAMA 🜲
───────────────────────────────────────

Pilih menu yang tersedia di bawah ini:

───────────────────────────────────────
⚡ FITUR UTAMA
───────────────────────────────────────
🜲 STATUS             — Cek status akun & akses
🜲 MSG → TXT          — Ubah pesan menjadi teks
🜲 TXT → VCF          — Konversi teks menjadi VCF
🜲 VCF → TXT          — Konversi VCF menjadi teks
🜲 BUAT ADMIN & NAVY  — Kelola admin/Navy
🜲 RAPIKAN TXT        — Bersihkan dan rapikan TXT
🜲 XLS → VCF          — Ekstrak data dari XLS ke VCF
🜲 GABUNG FILE        — Gabungkan beberapa file
🜲 HITUNG KONTAK      — Hitung jumlah kontak
🜲 CEK NAMA KONTAK    — Cek/memperbarui nama kontak
🜲 SPLIT FILE         — Bagi file menjadi beberapa
🎁 REDEEM CODE        — Tukarkan kode redeem

───────────────────────────────────────
KIFZL DEV BOT (BY @KIFZLDEV)
───────────────────────────────────────
```"""

    @staticmethod
    def file_received() -> str:
        return "✨ Siap Kak, file-nya sudah aku terima! ⏳ Lagi aku proses dulu..."

    @staticmethod
    def success() -> str:
        return "✅ Berhasil Kak! Ini hasil prosesnya ✨"

    @staticmethod
    def error_format() -> str:
        return "⚠️ Sepertinya format file belum sesuai nih Kak..."

    @staticmethod
    def invalid_number() -> str:
        return "❌ Format nomor tidak valid. Nomor harus mengandung '+' atau angka 0."

    @staticmethod
    def progress(percent: int) -> str:
        return f"⏳ Sedang memproses {percent}%..."

    @staticmethod
    def cancelled() -> str:
        return "```\n❌ Proses dibatalkan\n```"

    @staticmethod
    def access_denied(user_role: str, required_role: str) -> str:
        return f"""```
──────────────────────────
🔒 AKSES DITOLAK
──────────────────────────
Role Anda          : {user_role}
Akses Dibutuhkan   : {required_role}

Silakan pilih opsi di bawah ini untuk
mendapatkan akses:
──────────────────────────
```"""

    @staticmethod
    def verification_required(user_name: str) -> str:
        return f"""```
🔐 VERIFIKASI DIPERLUKAN
───────────────────────────────────────

Hai {user_name}!

Untuk menggunakan bot ini, kamu harus
bergabung ke grup wajib terlebih dahulu.

Silakan klik tombol di bawah untuk
bergabung, lalu klik "Verifikasi Ulang".

───────────────────────────────────────
```"""

    @staticmethod
    def redeem_prompt() -> str:
        return """```
🎁 REDEEM CODE
───────────────────────────────────────

Masukkan kode redeem Anda untuk
mengaktifkan VIP/VVIP.

───────────────────────────────────────
📌 Cara mendapatkan kode:
───────────────────────────────────────
• Hubungi admin/owner
• Ikuti event/promo
• Gabung grup VIP

Silakan masukkan kode:
───────────────────────────────────────
```"""

    @staticmethod
    def redeem_success(code: str, role_type: str, duration: int) -> str:
        return f"""```
🎉 REDEEM BERHASIL!
───────────────────────────────────────

🔑 Kode    : {code}
⭐ Akses   : {role_type.upper()}
🕒 Durasi  : {duration} hari

───────────────────────────────────────
Selamat menikmati fitur premium!
───────────────────────────────────────
```"""

    @staticmethod
    def redeem_failed(message: str) -> str:
        return f"""```
❌ REDEEM GAGAL
───────────────────────────────────────

{message}

───────────────────────────────────────
```"""

    @staticmethod
    def create_admin_mode_select() -> str:
        return """```
📨 CREATE ADMIN & NAVY
───────────────────────────────────────

Pilih mode yang ingin digunakan:

MODE A - GUIDED
Input bertahap (satu per satu)

MODE B - AUTO PARSE
Input block teks otomatis

MODE C - MINIMAL
Input satu nomor minimal

───────────────────────────────────────
```"""

    @staticmethod
    def ask_admin_number() -> str:
        return """```
📞 NOMOR ADMIN
───────────────────────────────────────

MODE A - GUIDED

Kirimkan nomor Admin
(format +62... atau 0...)

Bisa kirim beberapa nomor dengan enter

───────────────────────────────────────
```"""

    @staticmethod
    def ask_navy_number() -> str:
        return """```
🚢 NOMOR NAVY
───────────────────────────────────────

Kirimkan nomor Navy
(format +62... atau 0...)

Bisa kirim beberapa nomor dengan enter

───────────────────────────────────────
```"""

    @staticmethod
    def ask_filename() -> str:
        return """```
📝 NAMA FILE
───────────────────────────────────────

Masukkan nama file output
(tanpa ekstensi .vcf)

Contoh: ADMIN DAN NAVY

───────────────────────────────────────
```"""

    @staticmethod
    def ask_contact_format() -> str:
        return """```
👤 FORMAT NAMA KONTAK
───────────────────────────────────────

Masukkan format nama kontak

Contoh: admin
Hasil: admin 01, navy 01

───────────────────────────────────────
```"""

    @staticmethod
    def split_file_start() -> str:
        return """```
✂️ SPLIT FILE
───────────────────────────────────────

Kirim file .txt atau .vcf yang ingin
dipecah menjadi beberapa file

───────────────────────────────────────
```"""

    @staticmethod
    def split_ask_output_name() -> str:
        return """```
📝 NAMA FILE OUTPUT
───────────────────────────────────────

Masukkan nama dasar file output
(tanpa ekstensi)

Contoh: kontak
Hasil: kontak1, kontak2, kontak3...

───────────────────────────────────────
```"""

    @staticmethod
    def split_ask_file_prefix() -> str:
        return """```
🔢 AWALAN NOMOR FILE
───────────────────────────────────────

Masukkan awalan nomor file

Contoh: 1
Hasil: kontak1, kontak2, kontak3...

───────────────────────────────────────
```"""

    @staticmethod
    def split_ask_contact_prefix() -> str:
        return """```
👤 AWALAN NOMOR KONTAK
───────────────────────────────────────

Masukkan awalan nomor kontak

Contoh: 01
Hasil: kontak 01, kontak 02, kontak 03...

───────────────────────────────────────
```"""

    @staticmethod
    def split_mode_select() -> str:
        return """```
⚙️ MODE SPLIT
───────────────────────────────────────

Pilih mode split file:

PER KONTAK: Split berdasarkan jumlah
            kontak per file

PER BAGIAN: Bagi file menjadi X bagian

───────────────────────────────────────
```"""

    @staticmethod
    def gabung_file_start() -> str:
        return """```
🗄️ GABUNG FILE
───────────────────────────────────────

Kirim file-file yang ingin digabung
(format .txt atau .vcf)

Kirim satu per satu, lalu tekan
"✅ SELESAI ✅" jika sudah

───────────────────────────────────────
```"""

    @staticmethod
    def txt_to_vcf_start() -> str:
        return """```
🏷️ TXT TO VCF
───────────────────────────────────────

Kirim file .txt yang berisi nomor telepon
untuk dikonversi menjadi file .vcf

───────────────────────────────────────
```"""

    @staticmethod
    def vcf_to_txt_start() -> str:
        return """```
♻️ VCF TO TXT
───────────────────────────────────────

Kirim file .vcf untuk mengekstrak
nomor telepon menjadi file .txt

───────────────────────────────────────
```"""

    @staticmethod
    def xls_to_vcf_start() -> str:
        return """```
📊 XLS TO VCF
───────────────────────────────────────

Kirim file .xlsx atau .xls untuk
mengekstrak nomor telepon ke VCF

───────────────────────────────────────
```"""

    @staticmethod
    def msg_to_txt_start() -> str:
        return """```
📝 MSG TO TXT
───────────────────────────────────────

Kirim pesan/teks yang ingin dikonversi
menjadi file .txt

───────────────────────────────────────
```"""

    @staticmethod
    def rapikan_txt_start() -> str:
        return """```
✨ RAPIKAN TXT
───────────────────────────────────────

Kirim file .txt yang ingin dirapikan
(hapus duplikat, format nomor, dll)

───────────────────────────────────────
```"""

    @staticmethod
    def hitung_kontak_start() -> str:
        return """```
🔢 HITUNG KONTAK
───────────────────────────────────────

Kirim file .txt atau .vcf untuk
menghitung jumlah kontak

───────────────────────────────────────
```"""

    @staticmethod
    def cek_nama_start() -> str:
        return """```
🔍 CEK NAMA KONTAK
───────────────────────────────────────

Kirim file .vcf untuk mengecek
dan menampilkan nama kontak

───────────────────────────────────────
```"""
