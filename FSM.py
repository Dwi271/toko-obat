import re
from enum import Enum, auto
from engine import NLPEngine

# Membuat class State untuk FSM
class State(Enum):
    IDLE = auto()
    ORDERING = auto()
    CONFIRMATION = auto()
    PAYMENT = auto()

class CoffeeFSM:
    def __init__(self):
        # Inisialisasi awal State dan keranjang (cart)
        self.state = State.IDLE
        self.nlp = NLPEngine()
        self.cart = []
        self.response = "Selamat datang di Logic Medicine Shop! Butuh obat atau vitamin apa hari ini? Ketik 'menu' untuk melihat pilihan."
        
    def get_response(self):
        return self.response
        
    def calculate_total(self):
        return sum(item['price'] * item['qty'] for item in self.cart)

    def get_menu_text(self):
        """Rangkuman teks daftar menu untuk chatbot"""
        teks_menu = "**Daftar Obat & Vitamin Logic Medicine Shop:**\n\n"
        for key, data in self.nlp.menu_data.items():
            teks_menu += f"- {data['emoji']} **{key.capitalize()}** (Rp {data['price']:,}): *{data['desc']}*\n"
        teks_menu += "\nSilakan ketik pesanan Anda (contoh: *'Pesan 2 paracetamol'*)."
        return teks_menu
        
    def reduce_cart(self, item_to_reduce, qty_to_remove):
        """Logika untuk mengurangi atau menghapus item dari keranjang"""
        found = False
        message = ""
        for item in self.cart:
            if item['item'] == item_to_reduce:
                item['qty'] -= qty_to_remove
                found = True
                
                # Jika kuantitas habis atau kurang dari 0, hapus dari list keranjang
                if item['qty'] <= 0:
                    self.cart.remove(item)
                    message = f"✅ **{item_to_reduce.capitalize()}** telah dihapus dari keranjang."
                else:
                    message = f"✅ **{item_to_reduce.capitalize()}** dikurangi. Sisa pesanan: {item['qty']}."
                break
                
        if not found:
            message = f"❌ Gagal: Obat **{item_to_reduce.capitalize()}** tidak ditemukan di keranjang Anda."
            
        # Jika keranjang kosong setelah penghapusan, kembalikan state ke IDLE
        if len(self.cart) == 0:
            self.state = State.IDLE
            message += " Keranjang Anda sekarang kosong. Silakan pesan obat kembali."
        else:
            message += " Ada tambahan lain? (Ketik 'bayar' untuk selesai)"
            
        return message

    def step(self, user_input):
        """Fungsi utama penggerak FSM / Transisi Antar State"""
        intent = self.nlp.detect_intent(user_input)
        
        # Global Reset
        if intent == "RESET":
            self.state = State.IDLE
            self.cart = []
            self.response = "Sistem di-reset. Selamat datang kembali! Butuh obat atau vitamin apa hari ini?"
            return
            
        if self.state == State.IDLE:
            if intent == "ASK_MENU":
                self.response = self.get_menu_text()
            elif intent == "REDUCE_ITEM":
                self.response = "Keranjang Anda masih kosong, belum ada obat yang bisa dihapus."
            else:
                orders = self.nlp.parse_orders(user_input)
                if orders:
                    self.cart.extend(orders)
                    self.state = State.ORDERING
                    self.response = "Produk berhasil ditambahkan ke keranjang. Ada tambahan obat atau vitamin lain? (Ketik 'bayar' untuk selesai)"
                else:
                    self.response = "Maaf, nama obat tidak dikenali atau format salah. Ketik 'menu' untuk melihat pilihan."
                    
        elif self.state == State.ORDERING:
            if intent == "CHECKOUT":
                if len(self.cart) > 0:
                    self.state = State.CONFIRMATION
                    total = self.calculate_total()
                    self.response = f"Total tagihan obat Anda Rp {total:,}. Lanjut ke pembayaran? (Ya/Tidak)"
                else:
                    self.response = "Keranjang Anda kosong. Silakan pilih obat atau vitamin dulu!"
            elif intent == "ASK_MENU":
                self.response = self.get_menu_text()
            elif intent == "REDUCE_ITEM":
                # Menangkap pola angka dan nama obat untuk dihapus
                match = re.search(self.nlp.re_reduce, user_input.lower())
                if match:
                    qty_str = match.group(2)
                    # Jika angka tidak diketik (misal: "batal cacing"), hapus semua otomatis
                    qty_to_remove = int(qty_str) if qty_str else 999 
                    
                    # Mencocokkan nama obat dari input
                    item_to_reduce = None
                    for key in self.nlp.menu_data.keys():
                        if key in user_input.lower():
                            item_to_reduce = key
                            break
                            
                    if item_to_reduce:
                        self.response = self.reduce_cart(item_to_reduce, qty_to_remove)
                    else:
                        self.response = "Obat apa yang ingin dihapus? Pastikan namanya ada di keranjang."
                else:
                    self.response = "Format hapus salah. Contoh: 'hapus 1 cacing' atau 'batal paracetamol'."
            else:
                orders = self.nlp.parse_orders(user_input)
                if orders:
                    # Logika tambahan: Cek jika obat sudah ada di keranjang, cukup tambahkan qty-nya
                    for new_order in orders:
                        item_exists = False
                        for cart_item in self.cart:
                            if cart_item['item'] == new_order['item']:
                                cart_item['qty'] += new_order['qty']
                                item_exists = True
                                break
                        if not item_exists:
                            self.cart.append(new_order)
                            
                    self.response = "Pesanan tambahan dimasukkan ke keranjang. Ada lagi?"
                else:
                    self.response = "Obat tidak dikenali. Ketik 'bayar' jika pesanan Anda sudah cukup."

        elif self.state == State.CONFIRMATION:
            if intent == "YES":
                self.state = State.PAYMENT
                self.response = "Terima kasih! Obat sedang disiapkan dan dikemas. Silakan lakukan pembayaran di kasir apotek."
            elif intent == "NO":
                self.state = State.ORDERING
                self.response = "Baik, kembali ke daftar belanja. Ingin menambah pesanan atau 'hapus' obat tertentu?"
            else:
                self.response = "Mohon jawab dengan 'Ya' atau 'Tidak' untuk mengonfirmasi obat Anda."
                
        elif self.state == State.PAYMENT:
            self.response = "Transaksi pengambilan obat selesai. Semoga lekas sembuh! Ketik 'reset' untuk membuat pesanan baru."