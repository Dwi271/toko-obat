import re

class NLPEngine:
    def __init__(self):
        # DATA MENU TOKO OBAT
        self.menu_data = {
            "paracetamol": {"price": 8500, "emoji": "💊", "desc": "Pereda demam, sakit kepala, dan nyeri ringan"},
            "amoxicillin": {"price": 15000, "emoji": "🧪", "desc": "Antibiotik untuk mengatasi infeksi bakteri (butuh resep)"},
            "vitamin": {"price": 25000, "emoji": "🍊", "desc": "Multivitamin C dan Zinc untuk daya tahan tubuh"},
            "promag": {"price": 9000, "emoji": "🟢", "desc": "Obat sakit maag, asam lambung, dan kembung"},
            "cacing": {"price": 12000, "emoji": "🪱", "desc": "Obat cacing keluarga untuk mengatasi infeksi parasit"}
        }
        
        # PERBAIKAN FATAL: Dihapus tanda [ ] agar tidak memotong huruf sembarangan
        self.re_split = r',|\bdan\b|\bserta\b'
        self.re_reduce = r'(kurang|hapus|batal|cancel|remove)\s*(\d+)?\s*([a-zA-Z_]+)'
        
    def _parse_single_segment(self, text):
        """Memproses item dan jumlah di dalam satu segmen kalimat"""
        text = text.lower().strip()
        
        qty_match = re.search(r'\d+', text)
        qty = int(qty_match.group()) if qty_match else 1
        
        # Pencarian kata kunci menu di dalam teks
        for item_key in self.menu_data.keys():
            if item_key in text: 
                return {
                    "item": item_key,
                    "qty": qty,
                    "price": self.menu_data[item_key]['price'],
                    "emoji": self.menu_data[item_key]['emoji']
                }
        return None

    def parse_orders(self, full_text):
        """Memecah kalimat majemuk menjadi list pesanan"""
        segments = re.split(self.re_split, full_text.lower())
        found_orders = []
        for segment in segments:
            if segment.strip():
                order = self._parse_single_segment(segment)
                if order:
                    found_orders.append(order)
        return found_orders

    def detect_intent(self, text):
        """Mendeteksi maksud pengguna untuk kontrol FSM"""
        text = text.lower()
        if re.search(r"(reset|ulang|batal semua)", text):
            return "RESET"
        if re.search(r"(menu|daftar|apa saja|jual apa|list)", text):
            return "ASK_MENU"
        if re.search(r"(bayar|selesai|checkout|cukup)", text):
            return "CHECKOUT"
        if re.search(r"(ya|yes|oke|betul|siap|lanjut)", text):
            return "YES"
        if re.search(r"(tidak|nggak|batal|nanti)", text):
            return "NO"
        if re.search(self.re_reduce, text):
            return "REDUCE_ITEM"
        
        return "UNKNOWN"