# ============================================================
#  FULL POS SYSTEM - 80mm Thermal Printer
#  With Login, Cash Drawer, Split Payment, Hold Sale,
#  Discount, Loyalty, Label Print, Stock Alert, Dashboard, Audit
# ============================================================

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import qrcode
import barcode
from barcode.writer import ImageWriter
import json
import os
import csv
import shutil
import subprocess
import hashlib
import uuid
from datetime import datetime, timedelta
from PIL import Image
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    import cv2
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False

# ================= PATH SETUP =================
APP_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(APP_DIR)

INVOICE_DIR = os.path.join(APP_DIR, "invoices")
BACKUP_DIR = os.path.join(APP_DIR, "backups")
PHOTO_DIR = os.path.join(APP_DIR, "product_photos")
BARCODE_DIR = os.path.join(APP_DIR, "barcodes")
QRCODE_DIR = os.path.join(APP_DIR, "qrcodes")
LABEL_DIR = os.path.join(APP_DIR, "labels")

for d in [INVOICE_DIR, BACKUP_DIR, PHOTO_DIR, BARCODE_DIR, QRCODE_DIR, LABEL_DIR]:
    os.makedirs(d, exist_ok=True)

print(f"✅ POS System Started")
print(f"📁 App folder: {APP_DIR}")

# ================= SETTINGS =================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Files
DATA_FILE = os.path.join(APP_DIR, "products.json")
SALES_FILE = os.path.join(APP_DIR, "sales.json")
PURCHASES_FILE = os.path.join(APP_DIR, "purchases.json")
RETURNS_FILE = os.path.join(APP_DIR, "returns.json")
UDHAAR_FILE = os.path.join(APP_DIR, "udhaar.json")
SUPPLIERS_FILE = os.path.join(APP_DIR, "suppliers.json")
CUSTOMERS_FILE = os.path.join(APP_DIR, "customers.json")
USERS_FILE = os.path.join(APP_DIR, "users.json")
CASH_FILE = os.path.join(APP_DIR, "cash_drawer.json")
HOLD_FILE = os.path.join(APP_DIR, "hold_sales.json")
LOYALTY_FILE = os.path.join(APP_DIR, "loyalty.json")
AUDIT_FILE = os.path.join(APP_DIR, "audit_log.json")
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "business_name": "मेरो पसल",
    "address": "काठमाडौं, नेपाल",
    "phone": "98XXXXXXXX",
    "vat_number": "123456789",
    "vat_percent": 13,
    "printer_width": "80",
    "loyalty_percent": 1,  # 1% को points
    "low_stock_threshold": 5,
    "currency": "Rs."
}

# ================= PASSWORD HASH =================
def hash_password(password):
    """Password लाई SHA-256 मा hash गर्ने"""
    return hashlib.sha256(password.encode()).hexdigest()

# ================= DEFAULT USERS =================
def ensure_default_users():
    """पहिलो पटक admin user बनाउने"""
    users = load_json(USERS_FILE, [])
    if not users:
        users = [
            {
                "id": 1,
                "username": "admin",
                "password": hash_password("admin123"),
                "full_name": "Administrator",
                "role": "admin",
                "active": True,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M")
            },
            {
                "id": 2,
                "username": "cashier",
                "password": hash_password("cashier123"),
                "full_name": "Cashier 1",
                "role": "cashier",
                "active": True,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
        ]
        save_json(USERS_FILE, users)
        print("✅ Default users created:")
        print("   admin / admin123")
        print("   cashier / cashier123")
    return users

# ================= DATA FUNCTIONS =================
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_products():    return load_json(DATA_FILE, [])
def save_products(p):   save_json(DATA_FILE, p)
def load_sales():       return load_json(SALES_FILE, [])
def save_sales(s):      save_json(SALES_FILE, s)
def load_purchases():   return load_json(PURCHASES_FILE, [])
def save_purchases(p):  save_json(PURCHASES_FILE, p)
def load_returns():     return load_json(RETURNS_FILE, [])
def save_returns(r):    save_json(RETURNS_FILE, r)
def load_udhaar():      return load_json(UDHAAR_FILE, [])
def save_udhaar(u):     save_json(UDHAAR_FILE, u)
def load_suppliers():   return load_json(SUPPLIERS_FILE, [])
def save_suppliers(s):  save_json(SUPPLIERS_FILE, s)
def load_customers():   return load_json(CUSTOMERS_FILE, [])
def save_customers(c):  save_json(CUSTOMERS_FILE, c)
def load_users():       return load_json(USERS_FILE, [])
def save_users(u):      save_json(USERS_FILE, u)
def load_cash():        return load_json(CASH_FILE, [])
def save_cash(c):       save_json(CASH_FILE, c)
def load_holds():       return load_json(HOLD_FILE, [])
def save_holds(h):      save_json(HOLD_FILE, h)
def load_loyalty():     return load_json(LOYALTY_FILE, [])
def save_loyalty(l):    save_json(LOYALTY_FILE, l)
def load_audit():       return load_json(AUDIT_FILE, [])
def save_audit(a):      save_json(AUDIT_FILE, a)
def load_settings():    return load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
def save_settings(s):   save_json(SETTINGS_FILE, s)

# ================= AUDIT LOG =================
def audit_log(action, details="", user="system"):
    """हरेक काम को record राख्ने"""
    logs = load_audit()
    logs.append({
        "id": str(uuid.uuid4())[:8],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action": action,
        "details": details
    })
    # 10000 भन्दा बढी भए पुरानो मेट्ने
    if len(logs) > 10000:
        logs = logs[-10000:]
    save_audit(logs)

# ================= AUTO BACKUP =================
def auto_backup():
    today = datetime.now().strftime("%Y%m%d_%H%M%S")
    files = [DATA_FILE, SALES_FILE, PURCHASES_FILE, RETURNS_FILE,
             UDHAAR_FILE, SUPPLIERS_FILE, CUSTOMERS_FILE, SETTINGS_FILE,
             USERS_FILE, CASH_FILE, HOLD_FILE, LOYALTY_FILE, AUDIT_FILE]
    bdir = os.path.join(BACKUP_DIR, f"backup_{today}")
    os.makedirs(bdir, exist_ok=True)
    for f in files:
        if os.path.exists(f):
            shutil.copy(f, os.path.join(bdir, os.path.basename(f)))
    # 30 दिन भन्दा पुरानो delete
    cutoff = datetime.now() - timedelta(days=30)
    for folder in os.listdir(BACKUP_DIR):
        path = os.path.join(BACKUP_DIR, folder)
        if os.path.isdir(path):
            try:
                d = datetime.strptime(folder.replace("backup_", ""), "%Y%m%d_%H%M%S")
                if d < cutoff:
                    shutil.rmtree(path)
            except:
                pass
    return bdir

# ================= BARCODE & QR =================
def generate_barcode(pid, pname, custom=None):
    if custom:
        n = ''.join(filter(str.isdigit, str(custom)))
        n = n.zfill(12)[:12]
    else:
        n = str(pid).zfill(12)
    ean = barcode.get('ean13', n, writer=ImageWriter())
    safe_name = ''.join(c for c in pname if c.isalnum() or c in '_-')[:30]
    saved = ean.save(os.path.join(BARCODE_DIR, f"{safe_name}_{pid}"))
    return saved if saved.endswith(".png") else saved + ".png"

def generate_qr(product, custom=None):
    data = custom.strip() if custom else (
        f"ID: {product['id']}\nName: {product['name']}\n"
        f"Price: {product['price']}\nQuantity: {product['quantity']}\n"
        f"Category: {product['category']}")
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H,
                       box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    safe_name = ''.join(c for c in product['name'] if c.isalnum() or c in '_-')[:30]
    fp = os.path.join(QRCODE_DIR, f"{safe_name}_{product['id']}.png")
    img.save(fp)
    return fp

def copy_product_photo(source_path, product_id):
    if not source_path or not os.path.exists(source_path):
        return None
    ext = os.path.splitext(source_path)[1].lower() or ".jpg"
    dest = os.path.join(PHOTO_DIR, f"product_{product_id}{ext}")
    try:
        shutil.copy(source_path, dest)
        return dest
    except:
        return None

# ================= INVOICE =================
def generate_invoice_number(prefix, existing):
    today = datetime.now().strftime("%Y%m%d")
    cnt = sum(1 for x in existing if x.get('invoice_no', '').startswith(f"{prefix}-{today}"))
    return f"{prefix}-{today}-{cnt + 1:03d}"

def save_invoice_html(inv, is_sale=True):
    """80mm Thermal Printer - Perfect fit"""
    fname = os.path.join(INVOICE_DIR, f"{inv['invoice_no']}.html")
    s = load_settings()
    title = "SALES INVOICE" if is_sale else "PURCHASE INVOICE"
    party_label = "Customer" if is_sale else "Supplier"
    
    rows = ""
    for i, item in enumerate(inv['items'], 1):
        name = item['name'][:18]
        rows += f'<tr><td class="l">{i}.{name}</td><td class="r">{item["quantity"]}x{item["unit_price"]:,.0f}</td><td class="r">{item["total"]:,.0f}</td></tr>\n'
    
    vat_row = ""
    if inv.get('vat_amount', 0) > 0:
        vat_row = f'<tr><td class="r" colspan="2">VAT({s.get("vat_percent", 13)}%):</td><td class="r">{inv["vat_amount"]:,.0f}</td></tr>'
    
    disc_row = ""
    if inv.get('discount', 0) > 0:
        disc_row = f'<tr><td class="r" colspan="2">Discount:</td><td class="r">-{inv["discount"]:,.0f}</td></tr>'
    
    pay_row = ""
    if is_sale:
        paid = inv.get('paid', inv['total'])
        due = inv.get('due', 0)
        pay_row = f'<tr><td class="r" colspan="2">Paid:</td><td class="r">{paid:,.0f}</td></tr>'
        if due > 0:
            pay_row += f'<tr><td class="r" colspan="2"><b>Due:</b></td><td class="r"><b>{due:,.0f}</b></td></tr>'
        # Split payment info
        if inv.get('payment_method') == 'Split':
            pay_row += f'<tr><td class="r" colspan="2" style="font-size:9px">Split Payment:</td><td class="r" style="font-size:9px"></td></tr>'
            for pm in inv.get('payments', []):
                pay_row += f'<tr><td class="r" colspan="2" style="font-size:9px">{pm["method"]}:</td><td class="r" style="font-size:9px">{pm["amount"]:,.0f}</td></tr>'
    
    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{inv["invoice_no"]}</title>
<style>
@page {{ size: 80mm auto; margin: 2mm; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: Arial, sans-serif; width: 76mm; padding: 2mm; font-size: 11px; line-height: 1.2; color: #000; background: #fff; }}
.h {{ text-align:center; border-bottom:1px dashed #000; padding-bottom:2px; margin-bottom:3px; }}
.h h1 {{ font-size:14px; margin:0; font-weight:bold; }}
.h p {{ font-size:9px; margin:1px 0; }}
.h h2 {{ font-size:11px; margin-top:2px; font-weight:bold; }}
.i {{ font-size:10px; margin-bottom:2px; }}
.i .row {{ display:flex; justify-content:space-between; }}
table {{ width:100%; border-collapse:collapse; font-size:10px; }}
th {{ font-size:9px; padding:1px; border-bottom:1px solid #000; }}
td {{ padding:1px; }}
td.l {{ text-align:left; }}
td.r {{ text-align:right; }}
.tot {{ margin-top:2px; border-top:1px dashed #000; padding-top:2px; }}
.tot table td {{ padding:1px; font-size:10px; }}
.grand td {{ font-size:12px; font-weight:bold; border-top:1px solid #000; border-bottom:1px solid #000; padding:2px 1px; }}
.f {{ text-align:center; margin-top:3px; font-size:9px; border-top:1px dashed #000; padding-top:2px; }}
.btn {{ position: fixed; top: 10px; right: 10px; background: #27ae60; color: white; border: none; padding: 10px 20px; font-size: 14px; border-radius: 5px; cursor: pointer; z-index: 999; }}
.btn2 {{ right: 130px; background: #e74c3c; }}
@media print {{ .btn {{ display: none !important; }} body {{ width: 80mm; padding: 1mm; }} @page {{ size: 80mm auto; margin: 1mm; }} }}
</style></head><body>

<button class="btn btn2" onclick="window.close()">❌ Close</button>
<button class="btn" onclick="window.print()">🖨️ Print</button>

<div class="h">
<h1>{s.get("business_name", "मेरो पसल")}</h1>
<p>{s.get("address", "")}</p>
<p>Ph: {s.get("phone", "")} | VAT: {s.get("vat_number", "")}</p>
<h2>--- {title} ---</h2>
</div>

<div class="i">
<div class="row"><span><b>Inv:</b> {inv["invoice_no"]}</span><span>{inv["date"][:16]}</span></div>
<div class="row"><span><b>{party_label}:</b> {inv.get("party_name", "Walk-in")[:18]}</span><span>{inv.get("party_phone", "")}</span></div>
</div>

<div style="border-top:1px dashed #000; margin:2px 0;"></div>

<table>
<thead><tr>
<th class="l" style="width:48%">Item</th>
<th class="r" style="width:24%">Qty×Rate</th>
<th class="r" style="width:28%">Amt</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>

<div class="tot"><table>
<tr><td class="r" colspan="2">Subtotal:</td><td class="r">{inv["subtotal"]:,.0f}</td></tr>
{disc_row}{vat_row}
<tr class="grand"><td class="r" colspan="2"><b>GRAND TOTAL:</b></td><td class="r"><b>{inv["total"]:,.0f}</b></td></tr>
{pay_row}
</table></div>

<div class="f">
<p>धन्यवाद! फेरि आउनुहोस् 🙏</p>
<p style="font-size:8px">*** {inv["invoice_no"]} ***</p>
</div>
</body></html>'''
    
    try:
        with open(fname, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return fname

def save_thermal_receipt(inv, is_sale=True):
    """80mm Thermal - Plain text"""
    fname = os.path.join(INVOICE_DIR, f"{inv['invoice_no']}_thermal.txt")
    s = load_settings()
    W = 42
    lines = ["=" * W]
    lines.append(s.get('business_name', 'मेरो पसल').center(W))
    lines.append(s.get('address', '').center(W))
    lines.append(f"Ph: {s.get('phone', '')}".center(W))
    lines.append("=" * W)
    lines.append(("SALES INVOICE" if is_sale else "PURCHASE INVOICE").center(W))
    lines.append("-" * W)
    lines.append(f"Inv:  {inv['invoice_no']}")
    lines.append(f"Date: {inv['date']}")
    lines.append(f"Party: {inv.get('party_name', 'Walk-in')[:20]}")
    lines.append("-" * W)
    for item in inv['items']:
        lines.append(f"{item['name'][:20]:<20}{item['quantity']:>4}{item['unit_price']:>8.0f}{item['total']:>10.0f}")
    lines.append("-" * W)
    lines.append(f"{'Subtotal:':<32}{inv['subtotal']:>10.0f}")
    if inv.get('discount', 0) > 0:
        lines.append(f"{'Discount:':<32}{-inv['discount']:>10.0f}")
    if inv.get('vat_amount', 0) > 0:
        lines.append(f"{'VAT:':<32}{inv['vat_amount']:>10.0f}")
    lines.append("=" * W)
    lines.append(f"{'GRAND TOTAL:':<32}{inv['total']:>10.0f}")
    lines.append("=" * W)
    if is_sale:
        paid = inv.get('paid', inv['total'])
        due = inv.get('due', 0)
        lines.append(f"{'Paid:':<32}{paid:>10.0f}")
        if due > 0:
            lines.append(f"{'Due:':<32}{due:>10.0f}")
    lines.append("")
    lines.append("धन्यवाद! फेरि आउनुहोस्".center(W))
    with open(fname, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return fname
    # ================= MAIN APP CLASS =================
class POSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🏪 Full POS System")
        self.geometry("1400x850")
        self.minsize(1300, 780)
        
        # Default users ensure
        ensure_default_users()
        
        # State variables
        self.current_user = None
        self.selected_id = None
        self.camera_window = None
        self.sale_cart = []
        self.purchase_cart = []
        self.scan_target = None
        self.cap = None
        self.scan_active = False
        self.photo_path = None
        
        # Split Payment
        self.split_payments = []
        
        # Day session
        self.day_open = False
        
        self.backup_path = auto_backup()
        
        # Login first (don't build UI yet)
        self.withdraw()  # Hide main window
        self.show_login_window()
    
    # ==================================================
    # 🔐 LOGIN WINDOW
    # ==================================================
    def show_login_window(self):
        """Login window देखाउने"""
        self.login_win = ctk.CTkToplevel(self)
        self.login_win.title("🔐 POS Login")
        self.login_win.geometry("450x550")
        self.login_win.resizable(False, False)
        self.login_win.grab_set()
        
        # Center मा राख्ने
        self.login_win.update_idletasks()
        x = (self.login_win.winfo_screenwidth() // 2) - 225
        y = (self.login_win.winfo_screenheight() // 2) - 275
        self.login_win.geometry(f"450x550+{x}+{y}")
        
        self.login_win.protocol("WM_DELETE_WINDOW", self.exit_app)
        
        # Header
        header = ctk.CTkFrame(self.login_win, height=120, corner_radius=0,
                                fg_color="#2c3e50")
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="🏪",
                     font=("Arial", 45)).pack(pady=(20, 0))
        ctk.CTkLabel(header, text="Full POS System",
                     font=("Arial", 20, "bold"),
                     text_color="white").pack()
        
        # Login Form
        form = ctk.CTkFrame(self.login_win, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=40, pady=30)
        
        ctk.CTkLabel(form, text="🔐 Login",
                     font=("Arial", 22, "bold")).pack(pady=(10, 20))
        
        # Username
        ctk.CTkLabel(form, text="Username:", anchor="w",
                     font=("Arial", 12, "bold")).pack(fill="x", pady=(5, 2))
        self.login_username = ctk.CTkEntry(form, placeholder_text="admin",
                                              height=38, font=("Arial", 13))
        self.login_username.pack(fill="x", pady=(0, 12))
        
        # Password
        ctk.CTkLabel(form, text="Password:", anchor="w",
                     font=("Arial", 12, "bold")).pack(fill="x", pady=(5, 2))
        self.login_password = ctk.CTkEntry(form, placeholder_text="••••••",
                                              height=38, font=("Arial", 13),
                                              show="•")
        self.login_password.pack(fill="x", pady=(0, 12))
        
        # Show password checkbox
        self.show_pass_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(form, text="Show password",
                         variable=self.show_pass_var,
                         font=("Arial", 11),
                         command=self.toggle_password_show).pack(anchor="w", pady=(0, 15))
        
        # Login button
        ctk.CTkButton(form, text="🔓 Login",
                      height=45, font=("Arial", 14, "bold"),
                      fg_color="#27ae60", hover_color="#219150",
                      command=self.do_login).pack(fill="x", pady=(5, 10))
        
        # Enter key binding
        self.login_password.bind("<Return>", lambda e: self.do_login())
        self.login_username.bind("<Return>", lambda e: self.login_password.focus())
        
        # Hint box
        hint = ctk.CTkFrame(form, fg_color="#fff3cd", corner_radius=8)
        hint.pack(fill="x", pady=(15, 0))
        ctk.CTkLabel(hint, text="💡 Default Login",
                     font=("Arial", 11, "bold")).pack(pady=(8, 3))
        ctk.CTkLabel(hint, text="Admin:  admin / admin123\nCashier:  cashier / cashier123",
                     font=("Arial", 10), justify="left").pack(pady=(0, 8))
        
        # Focus
        self.login_username.focus()
    
    def toggle_password_show(self):
        if self.show_pass_var.get():
            self.login_password.configure(show="")
        else:
            self.login_password.configure(show="•")
    
    def do_login(self):
        """Login process"""
        username = self.login_username.get().strip()
        password = self.login_password.get().strip()
        
        if not username or not password:
            messagebox.showwarning("चेतावनी", "Username र Password हाल्नुहोस्!")
            return
        
        users = load_users()
        hashed = hash_password(password)
        
        user = None
        for u in users:
            if u['username'].lower() == username.lower():
                if u['password'] == hashed:
                    if not u.get('active', True):
                        messagebox.showerror("गल्ती", "यो user निष्क्रिय छ!")
                        return
                    user = u
                    break
                else:
                    messagebox.showerror("गल्ती", "Password गलत छ!")
                    return
        
        if not user:
            messagebox.showerror("गल्ती", "Username भेटिएन!")
            return
        
        # Login successful
        self.current_user = user
        audit_log("LOGIN", f"User {username} logged in", user=username)
        
        # Close login, show main
        self.login_win.destroy()
        self.deiconify()  # Show main window
        
        # Build main UI
        self.build_main_ui()
        self.refresh_all()
        
        # Show welcome
        self.status.configure(
            text=f"✅ Welcome {user['full_name']} ({user['role'].upper()})"
        )
        
        # Check day session
        self.after(500, self.check_day_session)
        
        # Bindings
        self.bind("<F2>", lambda e: self.scan_for_sale())
        self.bind("<F3>", lambda e: self.scan_for_purchase())
        self.bind("<F4>", lambda e: self.open_camera())
    
    def exit_app(self):
        """App बन्द गर्ने"""
        if messagebox.askyesno("Exit", "बन्द गर्ने?"):
            try:
                if self.current_user:
                    audit_log("LOGOUT", f"User {self.current_user['username']} logged out",
                              user=self.current_user['username'])
            except:
                pass
            self.destroy()
    
    def check_day_session(self):
        """दिन सुरु भयो कि भएन जाँच"""
        cash = load_cash()
        today = datetime.now().strftime("%Y-%m-%d")
        
        today_open = None
        for c in cash:
            if c['date'].startswith(today) and c['type'] == 'open':
                today_open = c
                break
        
        if not today_open:
            # Day open गर्न भन्ने
            if messagebox.askyesno("📅 Day Open",
                "आजको दिन सुरु गर्नुहोस्?\n\n"
                "Cash drawer को opening balance हाल्नुहोस्।"):
                self.day_open_dialog()
        else:
            self.day_open = True
            self.status.configure(
                text=f"✅ Welcome {self.current_user['full_name']} | Day OPEN"
            )
    
    # ==================================================
    # 💵 DAY OPEN DIALOG
    # ==================================================
    def day_open_dialog(self):
        """दिन सुरु गर्ने dialog"""
        win = ctk.CTkToplevel(self)
        win.title("💵 Day Open")
        win.geometry("420x380")
        win.grab_set()
        win.attributes('-topmost', True)
        
        ctk.CTkLabel(win, text="📅 Day Open",
                     font=("Arial", 18, "bold")).pack(pady=15)
        
        ctk.CTkLabel(win, text=f"Date: {datetime.now().strftime('%Y-%m-%d')}",
                     font=("Arial", 12), text_color="#7f8c8d").pack()
        
        form = ctk.CTkFrame(win)
        form.pack(pady=15, padx=25, fill="x")
        
        ctk.CTkLabel(form, text="Opening Cash (Rs.):",
                     anchor="w", font=("Arial", 12, "bold")).pack(fill="x", pady=(5, 2))
        self.open_cash_entry = ctk.CTkEntry(form, placeholder_text="5000", height=38,
                                              font=("Arial", 14, "bold"))
        self.open_cash_entry.pack(fill="x", pady=(0, 10))
        self.open_cash_entry.insert(0, "0")
        
        ctk.CTkLabel(form, text="Remark (optional):",
                     anchor="w", font=("Arial", 12)).pack(fill="x", pady=(5, 2))
        remark_e = ctk.CTkEntry(form, placeholder_text="Notes", height=32)
        remark_e.pack(fill="x", pady=(0, 10))
        
        def do_open():
            try:
                opening = float(self.open_cash_entry.get().strip() or 0)
            except:
                messagebox.showerror("गल्ती", "रकम सही हाल्नुहोस्!")
                return
            
            cash = load_cash()
            today = datetime.now().strftime("%Y-%m-%d")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cash.append({
                "date": now,
                "type": "open",
                "amount": opening,
                "user": self.current_user['username'],
                "remark": remark_e.get().strip()
            })
            save_cash(cash)
            audit_log("DAY_OPEN", f"Opening cash: Rs. {opening:,.0f}",
                      user=self.current_user['username'])
            
            self.day_open = True
            win.destroy()
            self.status.configure(text=f"✅ Day OPEN | Opening: Rs. {opening:,.0f}")
            messagebox.showinfo("सफल", f"दिन सुरु भयो!\nOpening Cash: Rs. {opening:,.0f}")
        
        ctk.CTkButton(win, text="✅ Day Open",
                      height=42, font=("Arial", 13, "bold"),
                      fg_color="#27ae60", hover_color="#219150",
                      command=do_open).pack(pady=10)
        
        self.open_cash_entry.focus()
        self.open_cash_entry.select_range(0, "end")
    
    # ==================================================
    # 🏗️ MAIN UI BUILD
    # ==================================================
    def build_main_ui(self):
        """Main UI बनाउने"""
        # Header
        header = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color="#2c3e50")
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Left - Logo
        ctk.CTkLabel(header, text="🏪 Full POS",
                     font=("Arial", 18, "bold"),
                     text_color="white").pack(side="left", padx=15)
        
        # Center - Stats
        self.stats_label = ctk.CTkLabel(header, text="",
                                          font=("Arial", 11),
                                          text_color="#ecf0f1")
        self.stats_label.pack(side="left", padx=30)
        
        # Right - User info
        user_frame = ctk.CTkFrame(header, fg_color="#34495e", corner_radius=5)
        user_frame.pack(side="right", padx=10, pady=8)
        
        role_color = {"admin": "#e74c3c", "manager": "#f39c12", "cashier": "#3498db"}.get(
            self.current_user['role'], "#7f8c8d")
        
        ctk.CTkLabel(user_frame, text="👤",
                     font=("Arial", 14),
                     text_color="white").pack(side="left", padx=(8, 3))
        ctk.CTkLabel(user_frame, text=self.current_user['full_name'],
                     font=("Arial", 11, "bold"),
                     text_color="white").pack(side="left", padx=3)
        ctk.CTkLabel(user_frame, text=f"({self.current_user['role'].upper()})",
                     font=("Arial", 9),
                     text_color=role_color).pack(side="left", padx=(3, 8))
        
        ctk.CTkButton(header, text="🚪 Logout", width=90, height=32,
                      font=("Arial", 11, "bold"),
                      fg_color="#e74c3c", hover_color="#c0392b",
                      command=self.logout).pack(side="right", padx=5, pady=12)
        
        # Day status indicator
        self.day_indicator = ctk.CTkLabel(header, text="",
                                            font=("Arial", 10, "bold"))
        self.day_indicator.pack(side="right", padx=10)
        
        # Tabs
        self.tabs = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=5)
        
        # सबै Tabs
        self.tab_dashboard = self.tabs.add("📊 Dashboard")
        self.tab_products = self.tabs.add("📦 Products")
        self.tab_sales = self.tabs.add("📤 Sales")
        self.tab_purchases = self.tabs.add("📥 Purchases")
        self.tab_returns = self.tabs.add("↩️ Returns")
        self.tab_udhaar = self.tabs.add("💰 Udhaar")
        self.tab_loyalty = self.tabs.add("🏆 Loyalty")
        self.tab_history = self.tabs.add("📋 History")
        self.tab_reports = self.tabs.add("📈 Reports")
        self.tab_invoices = self.tabs.add("🧾 Invoices")
        self.tab_cash = self.tabs.add("💵 Cash Drawer")
        self.tab_audit = self.tabs.add("📝 Audit Log")
        self.tab_users = self.tabs.add("👥 Users")
        self.tab_backup = self.tabs.add("☁️ Backup")
        self.tab_settings = self.tabs.add("⚙️ Settings")
        
        # Build each tab
        self.build_dashboard_tab()
        self.build_products_tab()
        self.build_sales_tab()
        self.build_purchases_tab()
        self.build_returns_tab()
        self.build_udhaar_tab()
        self.build_loyalty_tab()
        self.build_history_tab()
        self.build_reports_tab()
        self.build_invoices_tab()
        self.build_cash_tab()
        self.build_audit_tab()
        self.build_users_tab()
        self.build_backup_tab()
        self.build_settings_tab()
        
        # Bottom Status Bar
        status_frame = ctk.CTkFrame(self, height=28, corner_radius=0,
                                      fg_color="#ecf0f1")
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)
        
        self.status = ctk.CTkLabel(status_frame, text="✅ तयार",
                                     font=("Arial", 10),
                                     text_color="#2c3e50")
        self.status.pack(side="left", padx=15)
        
        self.clock_label = ctk.CTkLabel(status_frame, text="",
                                          font=("Arial", 10, "bold"),
                                          text_color="#2c3e50")
        self.clock_label.pack(side="right", padx=15)
        
        # Clock update
        self.update_clock()
        
        # Role-based access
        self.apply_role_permissions()
        
        # Day indicator
        self.update_day_indicator()
    
    def update_clock(self):
        """Clock update हरेक second"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.clock_label.configure(text=f"🕐 {now}")
        except:
            return
        self.after(1000, self.update_clock)
    
    def update_day_indicator(self):
        """Day status देखाउने"""
        if self.day_open:
            self.day_indicator.configure(text="🟢 DAY OPEN",
                                           text_color="#27ae60")
        else:
            self.day_indicator.configure(text="🔴 DAY CLOSED",
                                           text_color="#e74c3c")
    
    def apply_role_permissions(self):
        """Role अनुसार tabs disable गर्ने"""
        role = self.current_user['role']
        
        # Cashier लाई यी tabs नदेखाउने
        if role == "cashier":
            restricted = ["👥 Users", "📝 Audit Log", "⚙️ Settings"]
            try:
                for tab in restricted:
                    # Hide tab (CustomTkinter मा direct hide हुँदैन)
                    # Alternative: disabled color
                    pass
            except:
                pass
    
    def logout(self):
        """Logout गर्ने"""
        if not messagebox.askyesno("Logout", "Logout गर्ने?"):
            return
        
        audit_log("LOGOUT", f"User {self.current_user['username']} logged out",
                  user=self.current_user['username'])
        
        # Destroy all tabs
        for widget in self.winfo_children():
            widget.destroy()
        
        # Reset state
        self.current_user = None
        self.sale_cart = []
        self.purchase_cart = []
        self.split_payments = []
        
        # Hide main, show login
        self.withdraw()
        self.show_login_window()
    
    def on_tab_change(self):
        current = self.tabs.get()
        if "Sales" in current:
            self.after(200, lambda: self.sale_barcode_entry.focus())
        elif "Purchases" in current:
            self.after(200, lambda: self.pur_barcode_entry.focus())
    
    # ==================================================
    # 📊 DASHBOARD TAB
    # ==================================================
    def build_dashboard_tab(self):
        """Dashboard with real-time stats"""
        main = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        # Top cards
        ctk.CTkLabel(main, text="📊 Live Dashboard",
                     font=("Arial", 18, "bold")).pack(pady=(15, 10))
        
        cards = ctk.CTkFrame(main, fg_color="transparent")
        cards.pack(fill="x", padx=20, pady=10)
        
        self.dash_today_sales = self.create_stat_card(
            cards, "📤 आजको Sale", "Rs. 0", "#27ae60")
        self.dash_today_purchase = self.create_stat_card(
            cards, "📥 आजको Purchase", "Rs. 0", "#e74c3c")
        self.dash_today_profit = self.create_stat_card(
            cards, "💰 आजको नाफा", "Rs. 0", "#2980b9")
        self.dash_today_items = self.create_stat_card(
            cards, "📦 आज बिक्री items", "0", "#8e44ad")
        
        # Row 2
        cards2 = ctk.CTkFrame(main, fg_color="transparent")
        cards2.pack(fill="x", padx=20, pady=10)
        
        self.dash_products = self.create_stat_card(
            cards2, "📦 कुल Products", "0", "#3498db")
        self.dash_low_stock = self.create_stat_card(
            cards2, "⚠️ Low Stock", "0", "#e67e22")
        self.dash_customers = self.create_stat_card(
            cards2, "👥 Customers", "0", "#9b59b6")
        self.dash_udhaar = self.create_stat_card(
            cards2, "💰 Udhaar Due", "Rs. 0", "#c0392b")
        
        # Low stock list
        low_frame = ctk.CTkFrame(main)
        low_frame.pack(fill="both", expand=True, padx=20, pady=(15, 10))
        
        ctk.CTkLabel(low_frame, text="⚠️ Low Stock Alert",
                     font=("Arial", 14, "bold"),
                     text_color="#e74c3c").pack(pady=(10, 5))
        
        cols = ("ID", "Product", "Stock", "Min", "Status")
        self.low_stock_tree = ttk.Treeview(low_frame, columns=cols,
                                             show="headings", height=8)
        for c, w in zip(cols, [50, 300, 80, 80, 150]):
            self.low_stock_tree.heading(c, text=c)
            self.low_stock_tree.column(c, width=w, anchor="center")
        self.low_stock_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.low_stock_tree.tag_configure("low", background="#fdedec")
        self.low_stock_tree.tag_configure("critical", background="#e74c3c",
                                            foreground="white")
        
        # Refresh button
        ctk.CTkButton(main, text="🔄 Refresh Dashboard",
                      width=200, height=36, font=("Arial", 12, "bold"),
                      fg_color="#3498db",
                      command=self.refresh_dashboard).pack(pady=(0, 15))
    
    def create_stat_card(self, parent, title, value, color):
        """Statistics card बनाउने"""
        card = ctk.CTkFrame(parent, corner_radius=10, height=100,
                             border_width=2, border_color=color)
        card.pack(side="left", fill="x", expand=True, padx=6)
        card.pack_propagate(False)
        
        ctk.CTkLabel(card, text=title, font=("Arial", 11),
                     text_color="#7f8c8d").pack(pady=(15, 5))
        lbl = ctk.CTkLabel(card, text=value, font=("Arial", 22, "bold"),
                             text_color=color)
        lbl.pack()
        return lbl
    
    def refresh_dashboard(self):
        """Dashboard update गर्ने"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            sales = load_sales()
            purchases = load_purchases()
            products = load_products()
            customers = load_customers()
            udhaar = load_udhaar()
            
            # Today's sales
            today_sales = [s for s in sales if s['date'].startswith(today)]
            ts = sum(s['total'] for s in today_sales)
            items_sold = sum(sum(i['quantity'] for i in s['items']) for s in today_sales)
            
            # Today's purchase
            today_pur = [p for p in purchases if p['date'].startswith(today)]
            tp = sum(p['total'] for p in today_pur)
            
            # Profit (approx - sale - cost)
            profit = ts - tp
            
            self.dash_today_sales.configure(text=f"Rs. {ts:,.0f}")
            self.dash_today_purchase.configure(text=f"Rs. {tp:,.0f}")
            self.dash_today_profit.configure(text=f"Rs. {profit:,.0f}",
                                               text_color="#27ae60" if profit >= 0 else "#e74c3c")
            self.dash_today_items.configure(text=f"{items_sold}")
            
            # Products stats
            low_stock = [p for p in products if p['quantity'] <= 5]
            self.dash_products.configure(text=f"{len(products)}")
            self.dash_low_stock.configure(text=f"{len(low_stock)}")
            self.dash_customers.configure(text=f"{len(customers)}")
            
            udhaar_due = sum(u['due'] for u in udhaar if u['due'] > 0)
            self.dash_udhaar.configure(text=f"Rs. {udhaar_due:,.0f}")
            
            # Low stock tree
            for r in self.low_stock_tree.get_children():
                self.low_stock_tree.delete(r)
            
            for p in sorted(products, key=lambda x: x['quantity']):
                if p['quantity'] <= 10:
                    if p['quantity'] <= 2:
                        tag = "critical"
                        status = "🔴 Critical"
                    else:
                        tag = "low"
                        status = "⚠️ Low"
                    self.low_stock_tree.insert("", "end", tags=(tag,), values=(
                        p['id'], p['name'], p['quantity'], 5, status))
        except Exception as e:
            print(f"Dashboard error: {e}")
            # ==================================================
    # 📦 PRODUCTS TAB
    # ==================================================
    def build_products_tab(self):
        main = ctk.CTkFrame(self.tab_products, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        left = ctk.CTkScrollableFrame(main, width=310, corner_radius=8)
        left.pack(side="left", fill="y", padx=(0, 8))
        
        ctk.CTkLabel(left, text="📝 Product Details",
                     font=("Arial", 14, "bold")).pack(pady=(8, 5))
        
        for label, attr, ph in [
            ("नाम:", "name_entry", "Laptop"),
            ("मूल्य:", "price_entry", "75000"),
            ("Cost Price:", "cost_entry", "60000"),
            ("Quantity:", "qty_entry", "5"),
            ("Category:", "cat_entry", "Electronics"),
            ("Min Stock:", "min_stock_entry", "5"),
        ]:
            ctk.CTkLabel(left, text=label, anchor="w",
                         font=("Arial", 11)).pack(fill="x", padx=12)
            e = ctk.CTkEntry(left, placeholder_text=ph, height=28)
            e.pack(fill="x", padx=12, pady=(0, 4))
            setattr(self, attr, e)
        
        # Manual/Auto section
        mf = ctk.CTkFrame(left, fg_color="#f8f9fa", corner_radius=6,
                           border_width=1, border_color="#dee2e6")
        mf.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(mf, text="⚙️ Manual / Auto",
                     font=("Arial", 11, "bold")).pack(pady=(6, 3))
        
        self.bc_mode = ctk.StringVar(value="auto")
        r1 = ctk.CTkFrame(mf, fg_color="transparent")
        r1.pack(fill="x", padx=8)
        ctk.CTkLabel(r1, text="🏷️", font=("Arial", 11)).pack(side="left")
        ctk.CTkRadioButton(r1, text="Auto", variable=self.bc_mode, value="auto",
                            font=("Arial", 10),
                            command=self.toggle_bc).pack(side="left", padx=2)
        ctk.CTkRadioButton(r1, text="Manual", variable=self.bc_mode, value="manual",
                            font=("Arial", 10),
                            command=self.toggle_bc).pack(side="left", padx=2)
        self.bc_entry = ctk.CTkEntry(mf, placeholder_text="12 digits",
                                       height=26, state="disabled")
        self.bc_entry.pack(fill="x", padx=8, pady=(0, 5))
        
        self.qr_mode = ctk.StringVar(value="auto")
        r2 = ctk.CTkFrame(mf, fg_color="transparent")
        r2.pack(fill="x", padx=8)
        ctk.CTkLabel(r2, text="📱", font=("Arial", 11)).pack(side="left")
        ctk.CTkRadioButton(r2, text="Auto", variable=self.qr_mode, value="auto",
                            font=("Arial", 10),
                            command=self.toggle_qr).pack(side="left", padx=2)
        ctk.CTkRadioButton(r2, text="Manual", variable=self.qr_mode, value="manual",
                            font=("Arial", 10),
                            command=self.toggle_qr).pack(side="left", padx=2)
        self.qr_entry = ctk.CTkTextbox(mf, height=50,
                                         font=("Arial", 10), state="disabled")
        self.qr_entry.pack(fill="x", padx=8, pady=(0, 6))
        
        # Buttons
        btn = {"height": 32, "font": ("Arial", 11, "bold")}
        ctk.CTkButton(left, text="➕ Add", fg_color="#27ae60",
                      command=self.add_product, **btn).pack(fill="x", padx=12, pady=2)
        ctk.CTkButton(left, text="✏️ Update", fg_color="#f39c12",
                      command=self.update_product, **btn).pack(fill="x", padx=12, pady=2)
        ctk.CTkButton(left, text="🧹 Clear", fg_color="#95a5a6",
                      command=self.clear_form, height=28,
                      font=("Arial", 10)).pack(fill="x", padx=12, pady=2)
        
        # Label print button
        ctk.CTkButton(left, text="🏷️ Print Labels", fg_color="#9b59b6",
                      command=self.print_labels, **btn).pack(fill="x", padx=12, pady=2)
        
        ctk.CTkButton(left, text="📷 Camera Scan", fg_color="#e67e22",
                      command=self.open_camera, **btn).pack(fill="x", padx=12, pady=(6, 10))
        
        # RIGHT - Product List
        right = ctk.CTkFrame(main, corner_radius=8)
        right.pack(side="right", fill="both", expand=True)
        
        # Search
        sf = ctk.CTkFrame(right, fg_color="transparent")
        sf.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(sf, text="🔍", font=("Arial", 14)).pack(side="left", padx=(0, 5))
        self.search_entry = ctk.CTkEntry(sf, placeholder_text="Search...", height=28)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_list())
        ctk.CTkButton(sf, text="🔄", width=40, height=28,
                      command=self.refresh_list).pack(side="left")
        
        # Table
        tf = ctk.CTkFrame(right)
        tf.pack(fill="both", expand=True, padx=10, pady=6)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Arial", 11), rowheight=26)
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        
        cols = ("ID", "नाम", "मूल्य", "Cost", "Qty", "Category", "Status")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", height=11)
        for c, w in zip(cols, [45, 180, 90, 90, 60, 120, 80]):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.tag_configure("low", background="#fff3cd")
        self.tree.tag_configure("critical", background="#fdedec")
        
        # Action buttons
        act = ctk.CTkFrame(right, fg_color="transparent")
        act.pack(fill="x", padx=10, pady=(0, 4))
        b = {"height": 30, "font": ("Arial", 10, "bold"), "width": 90}
        ctk.CTkButton(act, text="📱 QR", fg_color="#3498db",
                      command=self.show_qr, **b).pack(side="left", padx=2)
        ctk.CTkButton(act, text="🏷️ Barcode", fg_color="#9b59b6",
                      command=self.show_barcode, **b).pack(side="left", padx=2)
        ctk.CTkButton(act, text="🗑️ Delete", fg_color="#e74c3c",
                      command=self.delete_product, **b).pack(side="left", padx=2)
        ctk.CTkButton(act, text="🖨️ Print", fg_color="#16a085",
                      command=self.print_selected, **b).pack(side="left", padx=2)
        ctk.CTkButton(act, text="💾 CSV", fg_color="#8e44ad",
                      command=self.export_csv, **b).pack(side="left", padx=2)
    
    # ==================================================
    # 📤 SALES TAB (Split Payment + Hold + Discount)
    # ==================================================
    def build_sales_tab(self):
        main = ctk.CTkFrame(self.tab_sales, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        # LEFT - Product picker
        left = ctk.CTkFrame(main, width=310, corner_radius=8)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        
        ctk.CTkLabel(left, text="🛍️ Barcode / Product",
                     font=("Arial", 14, "bold")).pack(pady=(12, 6))
        
        ctk.CTkLabel(left, text="📷 Barcode Scan:", anchor="w",
                     font=("Arial", 11, "bold"),
                     text_color="#e67e22").pack(fill="x", padx=12, pady=(0, 2))
        
        self.sale_barcode_entry = ctk.CTkEntry(
            left, placeholder_text="Scan वा Type → Enter",
            height=36, font=("Arial", 13, "bold"),
            border_color="#e67e22", border_width=2)
        self.sale_barcode_entry.pack(fill="x", padx=12, pady=(0, 4))
        self.sale_barcode_entry.bind("<Return>", lambda e: self.on_sale_barcode_enter())
        self.sale_barcode_entry.bind("<KP_Enter>", lambda e: self.on_sale_barcode_enter())
        
        ctk.CTkButton(left, text="📷 Camera Scan", height=30,
                      font=("Arial", 10), fg_color="#e67e22",
                      command=self.scan_for_sale
                      ).pack(fill="x", padx=12, pady=(0, 6))
        
        ctk.CTkLabel(left, text="─── वा product छान्नुहोस् ───",
                     font=("Arial", 9), text_color="#95a5a6").pack(pady=(0, 4))
        
        self.sale_product_var = ctk.StringVar(value="")
        self.sale_product_menu = ctk.CTkOptionMenu(
            left, variable=self.sale_product_var,
            values=["— छान्नुहोस् —"], width=280, height=30,
            command=self.on_sale_product_select)
        self.sale_product_menu.pack(fill="x", padx=12, pady=(0, 6))
        
        info = ctk.CTkFrame(left, fg_color="#f0f8ff", corner_radius=6)
        info.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkLabel(info, text="मूल्य:", font=("Arial", 11)).pack(side="left", padx=8, pady=4)
        self.sale_price_label = ctk.CTkLabel(info, text="—",
                                               font=("Arial", 12, "bold"),
                                               text_color="#2980b9")
        self.sale_price_label.pack(side="left", padx=2)
        ctk.CTkLabel(info, text="Stock:", font=("Arial", 11)).pack(side="left", padx=(15, 3), pady=4)
        self.sale_stock_label = ctk.CTkLabel(info, text="—",
                                               font=("Arial", 12, "bold"),
                                               text_color="#27ae60")
        self.sale_stock_label.pack(side="left", padx=2)
        
        ctk.CTkLabel(left, text="Quantity:", anchor="w",
                     font=("Arial", 11)).pack(fill="x", padx=12)
        self.sale_qty_entry = ctk.CTkEntry(left, placeholder_text="1", height=30)
        self.sale_qty_entry.pack(fill="x", padx=12, pady=(0, 6))
        
        # Line discount
        ctk.CTkLabel(left, text="Line Discount (Rs.):", anchor="w",
                     font=("Arial", 10, "bold"),
                     text_color="#e67e22").pack(fill="x", padx=12)
        self.sale_line_discount = ctk.CTkEntry(left, placeholder_text="0", height=28)
        self.sale_line_discount.pack(fill="x", padx=12, pady=(0, 6))
        
        ctk.CTkButton(left, text="➕ Cart मा थप्नुहोस्", height=36,
                      font=("Arial", 12, "bold"), fg_color="#3498db",
                      hover_color="#2980b9",
                      command=self.add_to_sale_cart
                      ).pack(fill="x", padx=12, pady=4)
        
        # Hold/Park button
        ctk.CTkButton(left, text="⏸️ Hold / Park Sale", height=32,
                      font=("Arial", 11, "bold"), fg_color="#f39c12",
                      hover_color="#d68910",
                      command=self.hold_sale
                      ).pack(fill="x", padx=12, pady=4)
        
        # Cart Summary
        tf = ctk.CTkFrame(left, fg_color="#fff3cd", corner_radius=6)
        tf.pack(fill="x", padx=12, pady=(4, 6))
        ctk.CTkLabel(tf, text="🛒 Cart Summary",
                     font=("Arial", 12, "bold")).pack(pady=(6, 3))
        self.cart_items_label = ctk.CTkLabel(tf, text="Items: 0",
                                               font=("Arial", 11))
        self.cart_items_label.pack()
        self.cart_total_label = ctk.CTkLabel(tf, text="Rs. 0",
                                               font=("Arial", 16, "bold"),
                                               text_color="#e67e22")
        self.cart_total_label.pack(pady=(0, 6))
        
        # CENTER - Cart
        center = ctk.CTkFrame(main, corner_radius=8)
        center.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        cart_header = ctk.CTkFrame(center, fg_color="transparent")
        cart_header.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(cart_header, text="🛒 Cart Items",
                     font=("Arial", 14, "bold")).pack(side="left")
        
        # Hold button count
        self.hold_count_label = ctk.CTkLabel(cart_header, text="",
                                                font=("Arial", 11, "bold"),
                                                text_color="#e67e22")
        self.hold_count_label.pack(side="right", padx=5)
        
        ctk.CTkButton(cart_header, text="📂 Resume Hold", width=120, height=28,
                      font=("Arial", 10, "bold"), fg_color="#e67e22",
                      command=self.show_hold_list).pack(side="right", padx=5)
        
        cart_cols = ("#", "Product", "Qty", "Rate", "Disc", "Total")
        self.cart_tree = ttk.Treeview(center, columns=cart_cols,
                                        show="headings", height=8)
        for c, w in zip(cart_cols, [35, 180, 50, 90, 60, 100]):
            self.cart_tree.heading(c, text=c)
            self.cart_tree.column(c, width=w, anchor="center")
        self.cart_tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        ca = ctk.CTkFrame(center, fg_color="transparent")
        ca.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkButton(ca, text="🗑️ Selected", width=130, height=30,
                      fg_color="#e74c3c",
                      command=self.remove_from_sale_cart,
                      font=("Arial", 11)).pack(side="left", padx=2)
        ctk.CTkButton(ca, text="🧹 Cart खाली", width=120, height=30,
                      fg_color="#95a5a6",
                      command=self.clear_sale_cart,
                      font=("Arial", 11)).pack(side="left", padx=2)
        
        # Customer
        cust = ctk.CTkFrame(center)
        cust.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkLabel(cust, text="👤 Customer:",
                     font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.sale_customer_var = ctk.StringVar(value="— Walk-in —")
        self.sale_customer_menu = ctk.CTkOptionMenu(
            cust, variable=self.sale_customer_var,
            values=["— Walk-in —"], width=200, height=30,
            command=self.on_customer_select)
        self.sale_customer_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkButton(cust, text="➕ नयाँ", width=75, height=30,
                      font=("Arial", 10, "bold"), fg_color="#27ae60",
                      command=self.add_customer_dialog
                      ).grid(row=0, column=2, padx=3, pady=5)
        
        # Loyalty points display
        self.loyalty_label = ctk.CTkLabel(cust, text="",
                                            font=("Arial", 10, "bold"),
                                            text_color="#9b59b6")
        self.loyalty_label.grid(row=0, column=3, padx=5, pady=5)
        
        self.sale_customer_info = ctk.CTkLabel(
            cust, text="", font=("Arial", 10), text_color="#7f8c8d")
        self.sale_customer_info.grid(row=1, column=0, columnspan=4,
                                       padx=5, pady=(0, 5))
        
        # RIGHT - Payment
        right = ctk.CTkScrollableFrame(main, width=300, corner_radius=8)
        right.pack(side="right", fill="y")
        
        ctk.CTkLabel(right, text="💰 Payment",
                     font=("Arial", 14, "bold")).pack(pady=(12, 8))
        
        # Subtotal
        ctk.CTkLabel(right, text="Subtotal:", anchor="w",
                     font=("Arial", 11)).pack(fill="x", padx=15)
        self.sale_subtotal_label = ctk.CTkLabel(right, text="Rs. 0",
                                                  font=("Arial", 13, "bold"))
        self.sale_subtotal_label.pack(pady=(0, 6))
        
        # Bill Discount
        ctk.CTkLabel(right, text="Bill Discount (Rs.):", anchor="w",
                     font=("Arial", 11, "bold"),
                     text_color="#e67e22").pack(fill="x", padx=15)
        self.sale_discount_entry = ctk.CTkEntry(right, placeholder_text="0", height=28)
        self.sale_discount_entry.pack(fill="x", padx=15, pady=(0, 4))
        self.sale_discount_entry.bind("<KeyRelease>",
                                       lambda e: self.update_sale_totals())
        
        # Discount % quick buttons
        disc_row = ctk.CTkFrame(right, fg_color="transparent")
        disc_row.pack(fill="x", padx=15, pady=(0, 6))
        for pct in [5, 10, 15, 20]:
            ctk.CTkButton(disc_row, text=f"{pct}%", width=55, height=24,
                          font=("Arial", 9, "bold"),
                          fg_color="#f39c12",
                          command=lambda p=pct: self.apply_percent_discount(p)
                          ).pack(side="left", padx=2)
        
        # VAT
        self.sale_vat_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(right, text="VAT (13%)", variable=self.sale_vat_var,
                         font=("Arial", 11),
                         command=self.update_sale_totals
                         ).pack(fill="x", padx=15, pady=4)
        
        self.sale_vat_label = ctk.CTkLabel(right, text="VAT: Rs. 0",
                                             font=("Arial", 11),
                                             text_color="#7f8c8d")
        self.sale_vat_label.pack(pady=2)
        
        ctk.CTkFrame(right, height=2,
                     fg_color="#dee2e6").pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(right, text="GRAND TOTAL:",
                     font=("Arial", 12, "bold")).pack()
        self.sale_grand_label = ctk.CTkLabel(right, text="Rs. 0",
                                               font=("Arial", 24, "bold"),
                                               text_color="#27ae60")
        self.sale_grand_label.pack(pady=5)
        
        # Payment method
        ctk.CTkLabel(right, text="Payment Method:", anchor="w",
                     font=("Arial", 11)).pack(fill="x", padx=15, pady=(10, 3))
        self.sale_payment_var = ctk.StringVar(value="Cash")
        ctk.CTkOptionMenu(right, variable=self.sale_payment_var,
                           values=["Cash", "Card", "eSewa", "Khalti",
                                   "Fonepay", "Credit/Udhaar", "Split"],
                           width=270, height=30,
                           command=self.on_payment_method_change
                           ).pack(padx=15, pady=(0, 6))
        
        # Split payment section (hidden by default)
        self.split_frame = ctk.CTkFrame(right, fg_color="#e8f8f5",
                                          corner_radius=6,
                                          border_width=1,
                                          border_color="#16a085")
        
        ctk.CTkLabel(self.split_frame, text="💳 Split Payment",
                     font=("Arial", 11, "bold"),
                     text_color="#16a085").pack(pady=(6, 3))
        
        # Split payment rows
        self.split_rows = []
        for i in range(3):
            row = ctk.CTkFrame(self.split_frame, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)
            
            method_var = ctk.StringVar(value="Cash" if i == 0 else "")
            method = ctk.CTkOptionMenu(row, variable=method_var,
                                         values=["Cash", "Card", "eSewa", "Khalti"],
                                         width=110, height=26,
                                         font=("Arial", 10))
            method.pack(side="left", padx=2)
            
            amt = ctk.CTkEntry(row, placeholder_text="0", width=120, height=26)
            amt.pack(side="left", padx=2)
            amt.bind("<KeyRelease>", lambda e: self.calc_split())
            
            self.split_rows.append((method_var, amt))
        
        self.split_total_label = ctk.CTkLabel(self.split_frame, text="Split: Rs. 0",
                                                font=("Arial", 10, "bold"),
                                                text_color="#16a085")
        self.split_total_label.pack(pady=(3, 6))
        
        # Paid entry
        ctk.CTkLabel(right, text="Paid (Rs.):", anchor="w",
                     font=("Arial", 11)).pack(fill="x", padx=15)
        self.sale_paid_entry = ctk.CTkEntry(right, placeholder_text="Full", height=28)
        self.sale_paid_entry.pack(fill="x", padx=15, pady=(0, 6))
        self.sale_paid_entry.bind("<KeyRelease>",
                                    lambda e: self.update_sale_totals())
        
        self.sale_due_label = ctk.CTkLabel(right, text="Due: Rs. 0",
                                             font=("Arial", 11),
                                             text_color="#e74c3c")
        self.sale_due_label.pack(pady=2)
        
        # Loyalty redemption
        self.sale_use_loyalty = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(right, text="Use Loyalty Points",
                         variable=self.sale_use_loyalty,
                         font=("Arial", 10),
                         command=self.update_sale_totals
                         ).pack(fill="x", padx=15, pady=(6, 2))
        
        # Checkout
        ctk.CTkButton(right, text="🧾 Checkout & Print", height=42,
                      font=("Arial", 13, "bold"), fg_color="#27ae60",
                      hover_color="#219150",
                      command=self.checkout_sale
                      ).pack(fill="x", padx=15, pady=(8, 6))
        
        ctk.CTkButton(right, text="🧹 Reset", height=30,
                      font=("Arial", 11), fg_color="#95a5a6",
                      command=self.reset_sale_tab
                      ).pack(fill="x", padx=15)
    
    # ==================================================
    # 📥 PURCHASES TAB
    # ==================================================
    def build_purchases_tab(self):
        main = ctk.CTkFrame(self.tab_purchases, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        left = ctk.CTkScrollableFrame(main, width=340, corner_radius=8)
        left.pack(side="left", fill="y", padx=(0, 8))
        
        ctk.CTkLabel(left, text="📥 Purchase",
                     font=("Arial", 14, "bold")).pack(pady=(12, 6))
        
        # Barcode
        ctk.CTkLabel(left, text="📷 Barcode Scan:", anchor="w",
                     font=("Arial", 11, "bold"),
                     text_color="#e67e22").pack(fill="x", padx=12, pady=(0, 2))
        self.pur_barcode_entry = ctk.CTkEntry(
            left, placeholder_text="Scan → Enter",
            height=34, font=("Arial", 13, "bold"),
            border_color="#e67e22", border_width=2)
        self.pur_barcode_entry.pack(fill="x", padx=12, pady=(0, 6))
        self.pur_barcode_entry.bind("<Return>",
                                      lambda e: self.on_purchase_barcode_enter())
        
        # Mode
        mode_frame = ctk.CTkFrame(left, fg_color="#f8f9fa", corner_radius=6,
                                    border_width=1, border_color="#dee2e6")
        mode_frame.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(mode_frame, text="⚙️ Product Mode",
                     font=("Arial", 11, "bold")).pack(pady=(6, 3))
        
        self.pur_mode = ctk.StringVar(value="existing")
        r_row = ctk.CTkFrame(mode_frame, fg_color="transparent")
        r_row.pack(fill="x", padx=8, pady=(0, 6))
        ctk.CTkRadioButton(r_row, text="पुरानो", variable=self.pur_mode,
                            value="existing", font=("Arial", 10),
                            command=self.toggle_purchase_mode).pack(side="left", padx=4)
        ctk.CTkRadioButton(r_row, text="नयाँ", variable=self.pur_mode,
                            value="new", font=("Arial", 10),
                            command=self.toggle_purchase_mode).pack(side="left", padx=4)
        
        # Existing
        self.existing_frame = ctk.CTkFrame(left, fg_color="transparent")
        self.existing_frame.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkLabel(self.existing_frame, text="Product छान्नुहोस्:",
                     anchor="w", font=("Arial", 11)).pack(fill="x")
        self.pur_product_var = ctk.StringVar(value="")
        self.pur_product_menu = ctk.CTkOptionMenu(
            self.existing_frame, variable=self.pur_product_var,
            values=["— छान्नुहोस् —"], width=290, height=30)
        self.pur_product_menu.pack(fill="x", pady=(0, 4))
        
        # New product frame
        self.new_product_frame = ctk.CTkFrame(left, fg_color="#fff8e1",
                                                corner_radius=6,
                                                border_width=1,
                                                border_color="#ffc107")
        
        ctk.CTkLabel(self.new_product_frame, text="🆕 नयाँ Product",
                     font=("Arial", 12, "bold"),
                     text_color="#e67e22").pack(pady=(6, 6))
        
        # Photo
        ctk.CTkLabel(self.new_product_frame, text="📷 Photo:",
                     anchor="w", font=("Arial", 10)).pack(fill="x", padx=8)
        photo_row = ctk.CTkFrame(self.new_product_frame, fg_color="transparent")
        photo_row.pack(fill="x", padx=8, pady=(0, 6))
        self.photo_preview_label = ctk.CTkLabel(
            photo_row, text="No photo", width=80, height=80,
            fg_color="#e0e0e0", corner_radius=6,
            font=("Arial", 9), text_color="#7f8c8d")
        self.photo_preview_label.pack(side="left", padx=(0, 6))
        ctk.CTkButton(photo_row, text="📁 छान्नुहोस्", width=90, height=30,
                      font=("Arial", 10), fg_color="#3498db",
                      command=self.choose_photo).pack(side="left", padx=2)
        ctk.CTkButton(photo_row, text="❌", width=30, height=30,
                      font=("Arial", 10), fg_color="#e74c3c",
                      command=self.clear_photo).pack(side="left", padx=2)
        
        # New product fields
        for label, attr, ph in [
            ("Product नाम *:", "new_prod_name", "Laptop"),
            ("Category:", "new_prod_cat", "Electronics"),
        ]:
            ctk.CTkLabel(self.new_product_frame, text=label,
                         anchor="w", font=("Arial", 10)).pack(fill="x", padx=8)
            e = ctk.CTkEntry(self.new_product_frame, placeholder_text=ph, height=28)
            e.pack(fill="x", padx=8, pady=(0, 4))
            setattr(self, attr, e)
        
        ctk.CTkLabel(self.new_product_frame, text="💰 Sale Price *:",
                     anchor="w", font=("Arial", 10, "bold"),
                     text_color="#27ae60").pack(fill="x", padx=8)
        self.new_prod_sale_price = ctk.CTkEntry(
            self.new_product_frame, placeholder_text="85000", height=28,
            border_color="#27ae60", border_width=2)
        self.new_prod_sale_price.pack(fill="x", padx=8, pady=(0, 4))
        
        ctk.CTkLabel(self.new_product_frame, text="⚠️ Min Stock:",
                     anchor="w", font=("Arial", 10)).pack(fill="x", padx=8)
        self.new_prod_min_stock = ctk.CTkEntry(
            self.new_product_frame, placeholder_text="5", height=28)
        self.new_prod_min_stock.pack(fill="x", padx=8, pady=(0, 4))
        
        # Barcode mode
        ctk.CTkLabel(self.new_product_frame, text="🏷️ Barcode:",
                     anchor="w", font=("Arial", 10)).pack(fill="x", padx=8)
        bc_row = ctk.CTkFrame(self.new_product_frame, fg_color="transparent")
        bc_row.pack(fill="x", padx=8, pady=(0, 4))
        self.new_bc_mode = ctk.StringVar(value="auto")
        ctk.CTkRadioButton(bc_row, text="Auto", variable=self.new_bc_mode,
                            value="auto", font=("Arial", 10),
                            command=self.toggle_new_bc).pack(side="left", padx=2)
        ctk.CTkRadioButton(bc_row, text="Manual", variable=self.new_bc_mode,
                            value="manual", font=("Arial", 10),
                            command=self.toggle_new_bc).pack(side="left", padx=2)
        self.new_bc_entry = ctk.CTkEntry(self.new_product_frame,
                                           placeholder_text="12 digits",
                                           height=26, state="disabled")
        self.new_bc_entry.pack(fill="x", padx=8, pady=(0, 8))
        
        # Purchase details
        ctk.CTkLabel(left, text="─── Purchase Details ───",
                     font=("Arial", 9),
                     text_color="#95a5a6").pack(pady=(8, 4))
        
        ctk.CTkLabel(left, text="💵 किन्ने मूल्य (Cost) *:", anchor="w",
                     font=("Arial", 11, "bold"),
                     text_color="#e74c3c").pack(fill="x", padx=12)
        self.pur_price_entry = ctk.CTkEntry(left, placeholder_text="60000",
                                              height=30,
                                              border_color="#e74c3c",
                                              border_width=2)
        self.pur_price_entry.pack(fill="x", padx=12, pady=(0, 6))
        
        ctk.CTkLabel(left, text="📦 Quantity *:", anchor="w",
                     font=("Arial", 11)).pack(fill="x", padx=12)
        self.pur_qty_entry = ctk.CTkEntry(left, placeholder_text="1", height=30)
        self.pur_qty_entry.pack(fill="x", padx=12, pady=(0, 6))
        self.pur_qty_entry.bind("<Return>",
                                  lambda e: self.on_purchase_qty_enter())
        
        # Supplier
        ctk.CTkLabel(left, text="─── Supplier ───",
                     font=("Arial", 9),
                     text_color="#95a5a6").pack(pady=(8, 4))
        
        sup_row = ctk.CTkFrame(left, fg_color="transparent")
        sup_row.pack(fill="x", padx=12, pady=(0, 4))
        ctk.CTkLabel(sup_row, text="🏢 Supplier:", anchor="w",
                     font=("Arial", 11)).pack(side="left")
        ctk.CTkButton(sup_row, text="➕ नयाँ", width=70, height=24,
                      font=("Arial", 9, "bold"), fg_color="#27ae60",
                      command=self.add_supplier_dialog).pack(side="right", padx=2)
        
        self.pur_supplier_var = ctk.StringVar(value="")
        self.pur_supplier_menu = ctk.CTkOptionMenu(
            left, variable=self.pur_supplier_var,
            values=["— छान्नुहोस् —"], width=290, height=30,
            command=self.on_supplier_select)
        self.pur_supplier_menu.pack(fill="x", padx=12, pady=(0, 4))
        
        self.pur_supplier_info = ctk.CTkLabel(left, text="",
                                                font=("Arial", 10),
                                                text_color="#7f8c8d")
        self.pur_supplier_info.pack(pady=(0, 6))
        
        ctk.CTkButton(left, text="➕ Cart मा थप्नुहोस्", height=40,
                      font=("Arial", 12, "bold"), fg_color="#3498db",
                      command=self.add_to_purchase_cart
                      ).pack(fill="x", padx=12, pady=(6, 4))
        
        pt = ctk.CTkFrame(left, fg_color="#fdedec", corner_radius=6)
        pt.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkLabel(pt, text="📥 Purchase Cart",
                     font=("Arial", 12, "bold")).pack(pady=(6, 3))
        self.pur_cart_items = ctk.CTkLabel(pt, text="Items: 0",
                                             font=("Arial", 11))
        self.pur_cart_items.pack()
        self.pur_cart_total = ctk.CTkLabel(pt, text="Rs. 0",
                                             font=("Arial", 16, "bold"),
                                             text_color="#e74c3c")
        self.pur_cart_total.pack(pady=(0, 6))
        
        # CENTER
        center = ctk.CTkFrame(main, corner_radius=8)
        center.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        ctk.CTkLabel(center, text="🛒 Purchase Items",
                     font=("Arial", 14, "bold")).pack(pady=(10, 5))
        
        pcols = ("#", "Product", "Qty", "Cost", "Total")
        self.pur_cart_tree = ttk.Treeview(center, columns=pcols,
                                            show="headings", height=15)
        for c, w in zip(pcols, [40, 220, 60, 100, 110]):
            self.pur_cart_tree.heading(c, text=c)
            self.pur_cart_tree.column(c, width=w, anchor="center")
        self.pur_cart_tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        pa = ctk.CTkFrame(center, fg_color="transparent")
        pa.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(pa, text="🗑️ हटाउने", width=130, height=30,
                      fg_color="#e74c3c",
                      command=self.remove_from_purchase_cart,
                      font=("Arial", 11)).pack(side="left", padx=2)
        ctk.CTkButton(pa, text="🧹 खाली", width=100, height=30,
                      fg_color="#95a5a6",
                      command=self.clear_purchase_cart,
                      font=("Arial", 11)).pack(side="left", padx=2)
        
        # RIGHT
        right = ctk.CTkFrame(main, width=280, corner_radius=8)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        
        ctk.CTkLabel(right, text="💰 Payment",
                     font=("Arial", 14, "bold")).pack(pady=(12, 8))
        
        ctk.CTkLabel(right, text="Subtotal:", anchor="w",
                     font=("Arial", 11)).pack(fill="x", padx=15)
        self.pur_subtotal_label = ctk.CTkLabel(right, text="Rs. 0",
                                                 font=("Arial", 13, "bold"))
        self.pur_subtotal_label.pack(pady=(0, 6))
        
        ctk.CTkLabel(right, text="Discount (Rs.):", anchor="w",
                     font=("Arial", 11)).pack(fill="x", padx=15)
        self.pur_discount_entry = ctk.CTkEntry(right, placeholder_text="0", height=28)
        self.pur_discount_entry.pack(fill="x", padx=15, pady=(0, 6))
        self.pur_discount_entry.bind("<KeyRelease>",
                                       lambda e: self.update_purchase_totals())
        
        ctk.CTkFrame(right, height=2,
                     fg_color="#dee2e6").pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(right, text="GRAND TOTAL:",
                     font=("Arial", 12, "bold")).pack()
        self.pur_grand_label = ctk.CTkLabel(right, text="Rs. 0",
                                              font=("Arial", 24, "bold"),
                                              text_color="#e74c3c")
        self.pur_grand_label.pack(pady=5)
        
        ctk.CTkButton(right, text="🧾 Purchase Invoice",
                      height=44, font=("Arial", 13, "bold"),
                      fg_color="#e74c3c", hover_color="#c0392b",
                      command=self.checkout_purchase
                      ).pack(fill="x", padx=15, pady=(15, 8))
        
        ctk.CTkButton(right, text="🧹 Reset", height=30,
                      font=("Arial", 11), fg_color="#95a5a6",
                      command=self.reset_purchase_tab
                      ).pack(fill="x", padx=15)
        
        self.toggle_purchase_mode()
    
    # ==================================================
    # PRODUCT FUNCTIONS
    # ==================================================
    def toggle_bc(self):
        if self.bc_mode.get() == "manual":
            self.bc_entry.configure(state="normal")
        else:
            self.bc_entry.configure(state="disabled")
            self.bc_entry.delete(0, "end")
    
    def toggle_qr(self):
        if self.qr_mode.get() == "manual":
            self.qr_entry.configure(state="normal")
        else:
            self.qr_entry.configure(state="disabled")
            self.qr_entry.delete("1.0", "end")
    
    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        products = load_products()
        kw = self.search_entry.get().strip().lower() if hasattr(self, 'search_entry') else ""
        if kw:
            products = [p for p in products if kw in p['name'].lower() or kw in p['category'].lower()]
        
        low = 0
        total = 0
        for p in products:
            min_stock = p.get('min_stock', 5)
            if p['quantity'] <= min_stock:
                low += 1
                tag = "critical" if p['quantity'] <= 2 else "low"
                status = "🔴 Critical" if p['quantity'] <= 2 else "⚠️ Low"
            else:
                tag = ""
                status = "✅"
            
            total += p['price'] * p['quantity']
            self.tree.insert("", "end", tags=(tag,) if tag else (), values=(
                p['id'], p['name'], f"Rs.{p['price']}",
                f"Rs.{p.get('cost_price', 0)}",
                p['quantity'], p['category'], status))
        
        self.stats_label.configure(
            text=f"📦 {len(products)} products | 💰 Rs.{total:,.0f} | ⚠️ {low} low"
        )
        
        # Product menus update
        options = [f"{p['id']}. {p['name']} ({p['quantity']})" for p in load_products()]
        if not options:
            options = ["— छान्नुहोस् —"]
        self.sale_product_menu.configure(values=options)
        self.pur_product_menu.configure(values=options)
    
    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        v = self.tree.item(sel[0])['values']
        self.selected_id = v[0]
        
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, v[1])
        self.price_entry.delete(0, "end")
        self.price_entry.insert(0, str(v[2]).replace("Rs.", ""))
        self.cost_entry.delete(0, "end")
        self.cost_entry.insert(0, str(v[3]).replace("Rs.", ""))
        self.qty_entry.delete(0, "end")
        self.qty_entry.insert(0, v[4])
        self.cat_entry.delete(0, "end")
        self.cat_entry.insert(0, v[5])
    
    def clear_form(self):
        for e in [self.name_entry, self.price_entry, self.cost_entry,
                  self.qty_entry, self.cat_entry, self.min_stock_entry]:
            e.delete(0, "end")
        self.bc_mode.set("auto")
        self.qr_mode.set("auto")
        self.bc_entry.configure(state="normal")
        self.bc_entry.delete(0, "end")
        self.bc_entry.configure(state="disabled")
        self.qr_entry.configure(state="normal")
        self.qr_entry.delete("1.0", "end")
        self.qr_entry.configure(state="disabled")
        self.selected_id = None
        self.tree.selection_remove(self.tree.selection())
    
    def add_product(self):
        name = self.name_entry.get().strip()
        try:
            price = float(self.price_entry.get().strip())
            qty = int(self.qty_entry.get().strip())
            cost = float(self.cost_entry.get().strip() or 0)
            min_stock = int(self.min_stock_entry.get().strip() or 5)
        except ValueError:
            messagebox.showerror("गल्ती", "मूल्य/Qty संख्या!")
            return
        if not name:
            messagebox.showwarning("चेतावनी", "नाम अनिवार्य!")
            return
        
        cat = self.cat_entry.get().strip() or "General"
        bc = self.bc_entry.get().strip() if self.bc_mode.get() == "manual" else None
        qr_data = self.qr_entry.get("1.0", "end").strip() if self.qr_mode.get() == "manual" else None
        
        products = load_products()
        nid = max([p['id'] for p in products], default=0) + 1
        
        p = {
            "id": nid, "name": name, "price": price,
            "cost_price": cost, "quantity": qty,
            "min_stock": min_stock,
            "category": cat,
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "barcode_number": bc if bc else str(nid).zfill(12),
            "qr_content": qr_data,
            "is_custom_barcode": bool(bc),
            "is_custom_qr": bool(qr_data),
            "photo": None
        }
        p["barcode_image"] = generate_barcode(nid, name, bc)
        p["qr_image"] = generate_qr(p, qr_data)
        products.append(p)
        save_products(products)
        
        audit_log("PRODUCT_ADD", f"{name} (ID: {nid})",
                  user=self.current_user['username'])
        
        self.refresh_list()
        self.clear_form()
        messagebox.showinfo("सफल", f"'{name}' Add भयो!")
    
    def update_product(self):
        if not self.selected_id:
            messagebox.showwarning("चेतावनी", "Product छान्नुहोस्!")
            return
        name = self.name_entry.get().strip()
        try:
            price = float(self.price_entry.get().strip())
            qty = int(self.qty_entry.get().strip())
            cost = float(self.cost_entry.get().strip() or 0)
            min_stock = int(self.min_stock_entry.get().strip() or 5)
        except ValueError:
            messagebox.showerror("गल्ती", "संख्या जाँच्नुहोस्!")
            return
        
        cat = self.cat_entry.get().strip() or "General"
        bc = self.bc_entry.get().strip() if self.bc_mode.get() == "manual" else None
        qr_data = self.qr_entry.get("1.0", "end").strip() if self.qr_mode.get() == "manual" else None
        
        products = load_products()
        for p in products:
            if p['id'] == self.selected_id:
                p.update({
                    "name": name, "price": price,
                    "cost_price": cost, "quantity": qty,
                    "min_stock": min_stock, "category": cat
                })
                if bc:
                    p['barcode_number'] = bc
                    p['is_custom_barcode'] = True
                else:
                    p['barcode_number'] = str(p['id']).zfill(12)
                    p['is_custom_barcode'] = False
                if qr_data:
                    p['qr_content'] = qr_data
                    p['is_custom_qr'] = True
                else:
                    p['qr_content'] = None
                    p['is_custom_qr'] = False
                p["barcode_image"] = generate_barcode(p['id'], name, bc)
                p["qr_image"] = generate_qr(p, qr_data)
                break
        save_products(products)
        
        audit_log("PRODUCT_UPDATE", f"{name} (ID: {self.selected_id})",
                  user=self.current_user['username'])
        
        self.refresh_list()
        messagebox.showinfo("सफल", "Update भयो!")
    
    def delete_product(self):
        # Role check
        if self.current_user['role'] == 'cashier':
            messagebox.showerror("गल्ती", "Cashier ले delete गर्न पाउँदैन!")
            return
        
        if not self.selected_id:
            messagebox.showwarning("चेतावनी", "Product छान्नुहोस्!")
            return
        sel = self.tree.selection()
        v = self.tree.item(sel[0])['values']
        if not messagebox.askyesno("पुष्टि", f"'{v[1]}' मेटाउने?"):
            return
        products = [p for p in load_products() if p['id'] != self.selected_id]
        save_products(products)
        
        audit_log("PRODUCT_DELETE", f"{v[1]} (ID: {self.selected_id})",
                  user=self.current_user['username'])
        
        self.refresh_list()
        self.clear_form()
    
    def show_qr(self):
        if not self.selected_id:
            return
        products = load_products()
        p = next((x for x in products if x['id'] == self.selected_id), None)
        if not p or not os.path.exists(p.get('qr_image', '')):
            return
        win = ctk.CTkToplevel(self)
        win.title(f"QR - {p['name']}")
        win.geometry("420x600")
        win.grab_set()
        ctk.CTkLabel(win, text=f"📱 {p['name']}",
                     font=("Arial", 18, "bold")).pack(pady=12)
        if p.get('photo') and os.path.exists(p['photo']):
            try:
                img_p = Image.open(p['photo']).resize((100, 100))
                photo_p = ctk.CTkImage(light_image=img_p, dark_image=img_p,
                                          size=(100, 100))
                ctk.CTkLabel(win, image=photo_p, text="").pack(pady=5)
            except:
                pass
        img = Image.open(p['qr_image']).resize((300, 300))
        photo = ctk.CTkImage(light_image=img, dark_image=img, size=(300, 300))
        ctk.CTkLabel(win, image=photo, text="").pack(pady=8)
        ctk.CTkButton(win, text="🖨️ Print", fg_color="#16a085",
                      height=36, width=120,
                      command=lambda: self.print_image(p['qr_image'])
                      ).pack(pady=8)
        ctk.CTkButton(win, text="बन्द", fg_color="#e74c3c",
                      height=36, width=120, command=win.destroy).pack()
    
    def show_barcode(self):
        if not self.selected_id:
            return
        products = load_products()
        p = next((x for x in products if x['id'] == self.selected_id), None)
        bc = p.get('barcode_image', '') if p else ''
        if bc and not bc.endswith(".png"):
            bc += ".png"
        if not p or not os.path.exists(bc):
            return
        win = ctk.CTkToplevel(self)
        win.title(f"Barcode - {p['name']}")
        win.geometry("580x400")
        win.grab_set()
        ctk.CTkLabel(win, text=f"🏷️ {p['name']}",
                     font=("Arial", 18, "bold")).pack(pady=12)
        img = Image.open(bc).resize((480, 150))
        photo = ctk.CTkImage(light_image=img, dark_image=img, size=(480, 150))
        ctk.CTkLabel(win, image=photo, text="").pack(pady=8)
        ctk.CTkLabel(win, text=f"Number: {p.get('barcode_number', '')}",
                     font=("Arial", 12)).pack()
        ctk.CTkButton(win, text="🖨️ Print", fg_color="#16a085",
                      height=36, width=120,
                      command=lambda: self.print_image(bc)).pack(pady=8)
        ctk.CTkButton(win, text="बन्द", fg_color="#e74c3c",
                      height=36, width=120, command=win.destroy).pack()
    
    def print_image(self, path):
        try:
            os.startfile(path, "print")
            messagebox.showinfo("सफल", "Print पठाइयो!")
        except:
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("गल्ती", str(e))
    
    def print_selected(self):
        if not self.selected_id:
            return
        products = load_products()
        p = next((x for x in products if x['id'] == self.selected_id), None)
        if not p:
            return
        choice = messagebox.askyesnocancel("Print",
            "QR (Yes) / Barcode (No) / दुवै (Cancel)")
        if choice is True:
            self.print_image(p['qr_image'])
        elif choice is False:
            bc = p['barcode_image']
            if not bc.endswith(".png"):
                bc += ".png"
            self.print_image(bc)
        else:
            try:
                os.startfile(p['qr_image'])
                bc = p['barcode_image']
                if not bc.endswith(".png"):
                    bc += ".png"
                os.startfile(bc)
            except:
                pass
    
    def export_csv(self):
        products = load_products()
        if not products:
            return
        fn = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"products_{datetime.now().strftime('%Y%m%d')}.csv")
        if not fn:
            return
        with open(fn, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["ID", "नाम", "मूल्य", "Cost", "Quantity",
                         "Min", "Category", "Barcode"])
            for p in products:
                w.writerow([p['id'], p['name'], p['price'],
                             p.get('cost_price', 0), p['quantity'],
                             p.get('min_stock', 5), p['category'],
                             p.get('barcode_number', '')])
        messagebox.showinfo("सफल", f"CSV: {fn}")
    
    def print_labels(self):
        """Barcode label print गर्ने"""
        if not self.selected_id:
            messagebox.showwarning("चेतावनी", "Product छान्नुहोस्!")
            return
        
        products = load_products()
        p = next((x for x in products if x['id'] == self.selected_id), None)
        if not p:
            return
        
        # Label dialog
        win = ctk.CTkToplevel(self)
        win.title("🏷️ Print Labels")
        win.geometry("420x400")
        win.grab_set()
        
        ctk.CTkLabel(win, text=f"🏷️ Print Labels",
                     font=("Arial", 16, "bold")).pack(pady=15)
        ctk.CTkLabel(win, text=f"Product: {p['name']}",
                     font=("Arial", 12)).pack()
        ctk.CTkLabel(win, text=f"Price: Rs. {p['price']:,.0f}",
                     font=("Arial", 12)).pack()
        
        form = ctk.CTkFrame(win)
        form.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(form, text="कति label चाहिन्छ?",
                     anchor="w", font=("Arial", 12)).pack(fill="x", pady=(5, 2))
        qty_e = ctk.CTkEntry(form, placeholder_text="10", height=32,
                              font=("Arial", 14, "bold"))
        qty_e.pack(fill="x", pady=(0, 10))
        qty_e.insert(0, "10")
        
        ctk.CTkLabel(form, text="Layout:",
                     anchor="w", font=("Arial", 12)).pack(fill="x", pady=(5, 2))
        layout_var = ctk.StringVar(value="2x5")
        ctk.CTkOptionMenu(form, variable=layout_var,
                           values=["1x1", "2x5", "3x8", "4x10"],
                           width=200, height=32).pack(pady=(0, 10))
        
        def do_print():
            try:
                count = int(qty_e.get().strip() or 1)
            except:
                messagebox.showerror("गल्ती", "संख्या!")
                return
            
            label_file = self.generate_label_html(p, count, layout_var.get())
            win.destroy()
            
            if label_file and os.path.exists(label_file):
                try:
                    os.startfile(label_file)
                    messagebox.showinfo("सफल",
                        f"Label खुल्यो!\nCtrl+P थिच्नुहोस्।")
                except Exception as e:
                    messagebox.showerror("गल्ती", str(e))
        
        ctk.CTkButton(win, text="🖨️ Print", height=42,
                      font=("Arial", 13, "bold"), fg_color="#27ae60",
                      command=do_print).pack(pady=10)
    
    def generate_label_html(self, product, count, layout):
        """Label HTML बनाउने"""
        import random
        rand_id = random.randint(1000, 9999)
        fname = os.path.join(LABEL_DIR, f"label_{product['id']}_{rand_id}.html")
        
        # Barcode image to base64
        import base64
        bc_path = product.get('barcode_image', '')
        if bc_path and not bc_path.endswith(".png"):
            bc_path += ".png"
        
        bc_img_tag = ""
        if os.path.exists(bc_path):
            with open(bc_path, "rb") as img_f:
                bc_b64 = base64.b64encode(img_f.read()).decode()
            bc_img_tag = f'<img src="data:image/png;base64,{bc_b64}" style="width:100%;height:auto;">'
        
        labels_html = ""
        for _ in range(count):
            labels_html += f'''
            <div class="label">
                <div class="pname">{product["name"][:20]}</div>
                <div class="price">Rs. {product["price"]:,.0f}</div>
                <div class="barcode">{bc_img_tag}</div>
                <div class="code">{product.get("barcode_number", "")}</div>
            </div>'''
        
        # Layout grid
        cols, rows = layout.split("x")
        cols = int(cols)
        rows = int(rows)
        per_page = cols * rows
        
        html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Labels</title>
<style>
@page {{ size: A4; margin: 5mm; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: Arial, sans-serif; }}
.container {{ display: grid; grid-template-columns: repeat({cols}, 1fr); gap: 2mm; }}
.label {{
    border: 1px dashed #999;
    padding: 2mm;
    text-align: center;
    page-break-inside: avoid;
    height: {int(270/rows)}mm;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}
.pname {{ font-size: 10px; font-weight: bold; }}
.price {{ font-size: 14px; font-weight: bold; color: #e74c3c; }}
.barcode {{ margin: 1mm 0; }}
.code {{ font-size: 8px; font-family: monospace; }}
.btn {{ position: fixed; top: 10px; right: 10px; background: #27ae60; color: white; border: none; padding: 10px 20px; font-size: 14px; border-radius: 5px; cursor: pointer; z-index: 999; }}
.btn2 {{ right: 130px; background: #e74c3c; }}
@media print {{ .btn {{ display: none; }} }}
</style></head><body>
<button class="btn btn2" onclick="window.close()">❌ Close</button>
<button class="btn" onclick="window.print()">🖨️ Print</button>
<div class="container">{labels_html}</div>
</body></html>'''
        
        with open(fname, "w", encoding="utf-8") as f:
            f.write(html)
        return fname
    
    # ==================================================
    # SALE FUNCTIONS
    # ==================================================
    def find_product_by_code(self, code):
        if not code:
            return None
        products = load_products()
        code = code.strip()
        digits = ''.join(filter(str.isdigit, code))
        for p in products:
            if p.get('barcode_number', '') == code:
                return p
            if p.get('barcode_number', '') == digits:
                return p
        if digits:
            try:
                pid = int(digits)
                for p in products:
                    if p['id'] == pid:
                        return p
            except:
                pass
        if len(digits) >= 12:
            last12 = digits[-12:]
            for p in products:
                if p.get('barcode_number', '') == last12:
                    return p
        return None
    
    def on_sale_barcode_enter(self):
        code = self.sale_barcode_entry.get().strip()
        if not code:
            return
        product = self.find_product_by_code(code)
        if not product:
            messagebox.showerror("भेटिएन",
                f"Barcode: {code}\n\nProduct भेटिएन!")
            self.sale_barcode_entry.delete(0, "end")
            return
        if product['quantity'] <= 0:
            messagebox.showerror("गल्ती",
                f"'{product['name']}' stock छैन!")
            self.sale_barcode_entry.delete(0, "end")
            return
        self.sale_product_var.set(
            f"{product['id']}. {product['name']} ({product['quantity']})")
        self.sale_price_label.configure(text=f"Rs. {product['price']}")
        self.sale_stock_label.configure(text=str(product['quantity']))
        self.sale_qty_entry.delete(0, "end")
        self.sale_qty_entry.insert(0, "1")
        self.sale_qty_entry.focus()
        self.sale_qty_entry.select_range(0, "end")
        self.sale_qty_entry.bind("<Return>", lambda e: self.on_sale_qty_enter())
        self.status.configure(
            text=f"✅ {product['name']} | Quantity + Enter")
    
    def on_sale_qty_enter(self):
        choice = self.sale_product_var.get()
        if not choice or choice == "— छान्नुहोस् —":
            return
        try:
            pid = int(choice.split(".")[0])
            qty = int(self.sale_qty_entry.get().strip() or 0)
        except:
            return
        if qty <= 0:
            return
        products = load_products()
        product = next((x for x in products if x['id'] == pid), None)
        if not product:
            return
        cart_qty = sum(i['quantity'] for i in self.sale_cart if i['id'] == pid)
        if product['quantity'] < cart_qty + qty:
            messagebox.showerror("गल्ती", f"Stock अपुग!")
            return
        
        # Line discount
        try:
            line_disc = float(self.sale_line_discount.get().strip() or 0)
        except:
            line_disc = 0
        
        for item in self.sale_cart:
            if item['id'] == pid:
                item['quantity'] += qty
                item['line_discount'] = line_disc
                item['total'] = item['quantity'] * item['unit_price'] - line_disc
                break
        else:
            self.sale_cart.append({
                "id": product['id'], "name": product['name'],
                "quantity": qty, "unit_price": product['price'],
                "line_discount": line_disc,
                "total": product['price'] * qty - line_disc
            })
        
        self.refresh_sale_cart()
        self.sale_barcode_entry.delete(0, "end")
        self.sale_product_var.set("")
        self.sale_qty_entry.delete(0, "end")
        self.sale_line_discount.delete(0, "end")
        self.sale_price_label.configure(text="—")
        self.sale_stock_label.configure(text="—")
        self.sale_barcode_entry.focus()
    
    def on_sale_product_select(self, choice):
        if not choice or choice == "— छान्नुहोस् —":
            return
        try:
            pid = int(choice.split(".")[0])
        except:
            return
        products = load_products()
        p = next((x for x in products if x['id'] == pid), None)
        if p:
            self.sale_price_label.configure(text=f"Rs. {p['price']}")
            self.sale_stock_label.configure(text=str(p['quantity']))
    
    def add_to_sale_cart(self):
        choice = self.sale_product_var.get()
        if not choice or choice == "— छान्नुहोस् —":
            messagebox.showwarning("चेतावनी", "Product छान्नुहोस्!")
            return
        try:
            pid = int(choice.split(".")[0])
            qty = int(self.sale_qty_entry.get().strip() or 0)
            line_disc = float(self.sale_line_discount.get().strip() or 0)
        except:
            messagebox.showerror("गल्ती", "जाँच्नुहोस्!")
            return
        if qty <= 0:
            return
        products = load_products()
        product = next((x for x in products if x['id'] == pid), None)
        if not product:
            return
        cart_qty = sum(i['quantity'] for i in self.sale_cart if i['id'] == pid)
        if product['quantity'] < cart_qty + qty:
            messagebox.showerror("गल्ती", f"Stock अपुग! उपलब्ध: {product['quantity']}")
            return
        for item in self.sale_cart:
            if item['id'] == pid:
                item['quantity'] += qty
                item['line_discount'] = line_disc
                item['total'] = item['quantity'] * item['unit_price'] - line_disc
                break
        else:
            self.sale_cart.append({
                "id": product['id'], "name": product['name'],
                "quantity": qty, "unit_price": product['price'],
                "line_discount": line_disc,
                "total": product['price'] * qty - line_disc            })
        self.sale_qty_entry.delete(0, "end")
        self.sale_line_discount.delete(0, "end")
        self.refresh_sale_cart()
    
    def remove_from_sale_cart(self):
        sel = self.cart_tree.selection()
        if not sel:
            return
        idx = int(self.cart_tree.item(sel[0])['values'][0]) - 1
        if 0 <= idx < len(self.sale_cart):
            self.sale_cart.pop(idx)
            self.refresh_sale_cart()
    
    def clear_sale_cart(self):
        if self.sale_cart and messagebox.askyesno("पुष्टि", "Cart खाली?"):
            self.sale_cart = []
            self.refresh_sale_cart()
    
    def refresh_sale_cart(self):
        for r in self.cart_tree.get_children():
            self.cart_tree.delete(r)
        for i, item in enumerate(self.sale_cart, 1):
            self.cart_tree.insert("", "end", values=(
                i, item['name'], item['quantity'],
                f"Rs. {item['unit_price']:,.0f}",
                f"{item.get('line_discount', 0):,.0f}",
                f"Rs. {item['total']:,.0f}"))
        n = len(self.sale_cart)
        subtotal = sum(x['total'] for x in self.sale_cart)
        self.cart_items_label.configure(text=f"Items: {n}")
        self.cart_total_label.configure(text=f"Rs. {subtotal:,.0f}")
        self.update_sale_totals()
    
    def update_sale_totals(self):
        subtotal = sum(x['total'] for x in self.sale_cart)
        try:
            discount = float(self.sale_discount_entry.get().strip() or 0)
        except:
            discount = 0
        after = subtotal - discount
        vat = after * 13 / 100 if self.sale_vat_var.get() else 0
        
        # Loyalty redemption
        loyalty_disc = 0
        if self.sale_use_loyalty.get() and self.sale_customer_var.get() != "— Walk-in —":
            try:
                cid = int(self.sale_customer_var.get().split(".")[0])
                customers = load_customers()
                c = next((x for x in customers if x['id'] == cid), None)
                if c:
                    points = c.get('loyalty_points', 0)
                    loyalty_disc = min(points, after + vat)  # 1 point = Rs. 1
            except:
                pass
        
        grand = after + vat - loyalty_disc
        if grand < 0:
            grand = 0
        
        try:
            paid = float(self.sale_paid_entry.get().strip() or grand)
        except:
            paid = grand
        due = max(0, grand - paid)
        
        self.sale_subtotal_label.configure(text=f"Rs. {subtotal:,.0f}")
        self.sale_vat_label.configure(text=f"VAT: Rs. {vat:,.0f}")
        self.sale_grand_label.configure(text=f"Rs. {grand:,.0f}")
        self.sale_due_label.configure(text=f"Due: Rs. {due:,.0f}",
                                        text_color="#e74c3c" if due > 0 else "#27ae60")
        
        # Split payment total
        if self.sale_payment_var.get() == "Split":
            self.calc_split()
    
    def apply_percent_discount(self, pct):
        """% discount लागू गर्ने"""
        subtotal = sum(x['total'] for x in self.sale_cart)
        discount = subtotal * pct / 100
        self.sale_discount_entry.delete(0, "end")
        self.sale_discount_entry.insert(0, f"{discount:.0f}")
        self.update_sale_totals()
    
    def on_payment_method_change(self, choice):
        """Payment method परिवर्तन हुँदा"""
        if choice == "Split":
            self.split_frame.pack(fill="x", padx=15, pady=(0, 6))
            self.calc_split()
        else:
            self.split_frame.pack_forget()
    
    def calc_split(self):
        """Split payment calculate गर्ने"""
        total = 0
        payments = []
        for method_var, amt_e in self.split_rows:
            method = method_var.get()
            try:
                amt = float(amt_e.get().strip() or 0)
                if amt > 0 and method:
                    total += amt
                    payments.append({"method": method, "amount": amt})
            except:
                pass
        self.split_payments = payments
        self.split_total_label.configure(text=f"Split: Rs. {total:,.0f}")
        self.sale_paid_entry.delete(0, "end")
        self.sale_paid_entry.insert(0, f"{total:.0f}")
        self.update_sale_totals()
    
    # ==================================================
    # HOLD / PARK SALE
    # ==================================================
    def hold_sale(self):
        """Cart लाई hold गर्ने"""
        if not self.sale_cart:
            messagebox.showwarning("चेतावनी", "Cart खाली!")
            return
        
        # Name dialog
        win = ctk.CTkToplevel(self)
        win.title("⏸️ Hold Sale")
        win.geometry("400x300")
        win.grab_set()
        
        ctk.CTkLabel(win, text="⏸️ Hold Sale",
                     font=("Arial", 16, "bold")).pack(pady=15)
        
        ctk.CTkLabel(win, text="Customer नाम / Reference:",
                     anchor="w", font=("Arial", 12)).pack(fill="x", padx=20)
        name_e = ctk.CTkEntry(win, placeholder_text="जस्तै: Ram",
                                height=35, font=("Arial", 13))
        name_e.pack(fill="x", padx=20, pady=(5, 10))
        
        ctk.CTkLabel(win, text="Remark (optional):",
                     anchor="w", font=("Arial", 11)).pack(fill="x", padx=20)
        remark_e = ctk.CTkEntry(win, height=30)
        remark_e.pack(fill="x", padx=20, pady=(5, 15))
        
        subtotal = sum(x['total'] for x in self.sale_cart)
        ctk.CTkLabel(win, text=f"Total: Rs. {subtotal:,.0f}",
                     font=("Arial", 13, "bold"),
                     text_color="#e67e22").pack()
        
        def do_hold():
            name = name_e.get().strip() or f"Hold-{datetime.now().strftime('%H%M%S')}"
            holds = load_holds()
            hold_id = max([h.get('hold_id', 0) for h in holds], default=0) + 1
            
            holds.append({
                "hold_id": hold_id,
                "name": name,
                "remark": remark_e.get().strip(),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "items": list(self.sale_cart),
                "customer": self.sale_customer_var.get(),
                "subtotal": subtotal,
                "user": self.current_user['username']
            })
            save_holds(holds)
            
            audit_log("HOLD_SALE", f"Hold #{hold_id}: {name}",
                      user=self.current_user['username'])
            
            # Clear cart
            self.sale_cart = []
            self.refresh_sale_cart()
            self.refresh_hold_count()
            win.destroy()
            messagebox.showinfo("सफल", f"Hold गरियो: {name}")
        
        row = ctk.CTkFrame(win, fg_color="transparent")
        row.pack(pady=15)
        ctk.CTkButton(row, text="⏸️ Hold", width=120, height=40,
                      fg_color="#f39c12", font=("Arial", 12, "bold"),
                      command=do_hold).pack(side="left", padx=5)
        ctk.CTkButton(row, text="❌ Cancel", width=120, height=40,
                      fg_color="#95a5a6", font=("Arial", 12, "bold"),
                      command=win.destroy).pack(side="left", padx=5)
        name_e.focus()
    
    def show_hold_list(self):
        """Hold गरिएका sales देखाउने"""
        holds = load_holds()
        if not holds:
            messagebox.showinfo("जानकारी", "कुनै hold छैन!")
            return
        
        win = ctk.CTkToplevel(self)
        win.title("📂 Hold Sales")
        win.geometry("700x500")
        win.grab_set()
        
        ctk.CTkLabel(win, text="📂 Held Sales",
                     font=("Arial", 16, "bold")).pack(pady=15)
        
        cols = ("Hold #", "Name", "Items", "Total", "Date", "User")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=12)
        for c, w in zip(cols, [70, 150, 60, 100, 150, 100]):
            tree.heading(c, text=c)
            tree.column(c, width=w, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        for h in holds:
            tree.insert("", "end", values=(
                h['hold_id'], h['name'], len(h['items']),
                f"Rs. {h['subtotal']:,.0f}", h['date'], h.get('user', '')))
        
        def resume():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("चेतावनी", "Hold छान्नुहोस्!")
                return
            hid = int(tree.item(sel[0])['values'][0])
            
            if self.sale_cart:
                if not messagebox.askyesno("चेतावनी",
                    "Cart मा items छन्। Replace गर्ने?"):
                    return
            
            holds = load_holds()
            hold = next((h for h in holds if h['hold_id'] == hid), None)
            if not hold:
                return
            
            self.sale_cart = list(hold['items'])
            self.sale_customer_var.set(hold.get('customer', '— Walk-in —'))
            
            # Remove from holds
            holds = [h for h in holds if h['hold_id'] != hid]
            save_holds(holds)
            
            audit_log("RESUME_HOLD", f"Hold #{hid}: {hold['name']}",
                      user=self.current_user['username'])
            
            self.refresh_sale_cart()
            self.refresh_hold_count()
            win.destroy()
            messagebox.showinfo("सफल", f"Resume: {hold['name']}")
        
        def delete_hold():
            sel = tree.selection()
            if not sel:
                return
            hid = int(tree.item(sel[0])['values'][0])
            if not messagebox.askyesno("पुष्टि", "Hold मेटाउने?"):
                return
            holds = load_holds()
            holds = [h for h in holds if h['hold_id'] != hid]
            save_holds(holds)
            tree.delete(sel[0])
            self.refresh_hold_count()
        
        btn = ctk.CTkFrame(win, fg_color="transparent")
        btn.pack(pady=10)
        ctk.CTkButton(btn, text="▶️ Resume", width=140, height=38,
                      fg_color="#27ae60", font=("Arial", 12, "bold"),
                      command=resume).pack(side="left", padx=5)
        ctk.CTkButton(btn, text="🗑️ Delete", width=120, height=38,
                      fg_color="#e74c3c", font=("Arial", 12, "bold"),
                      command=delete_hold).pack(side="left", padx=5)
        ctk.CTkButton(btn, text="❌ Close", width=120, height=38,
                      fg_color="#95a5a6", font=("Arial", 12, "bold"),
                      command=win.destroy).pack(side="left", padx=5)
    
    def refresh_hold_count(self):
        holds = load_holds()
        if holds:
            self.hold_count_label.configure(
                text=f"⏸️ {len(holds)} holds")
        else:
            self.hold_count_label.configure(text="")
            # ==================================================
    # ↩️ RETURNS TAB
    # ==================================================
    def build_returns_tab(self):
        main = ctk.CTkFrame(self.tab_returns, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        left = ctk.CTkFrame(main, width=340, corner_radius=8)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        
        ctk.CTkLabel(left, text="↩️ Return / Refund",
                     font=("Arial", 14, "bold")).pack(pady=(15, 10))
        
        ctk.CTkLabel(left, text="Invoice No:", anchor="w",
                     font=("Arial", 11)).pack(fill="x", padx=15)
        self.ret_invoice_entry = ctk.CTkEntry(left,
            placeholder_text="INV-20250115-001", height=32)
        self.ret_invoice_entry.pack(fill="x", padx=15, pady=(0, 6))
        self.ret_invoice_entry.bind("<Return>",
            lambda e: self.load_return_invoice())
        
        ctk.CTkButton(left, text="🔍 Invoice खोज्नुहोस्", height=34,
                      fg_color="#3498db", font=("Arial", 11, "bold"),
                      command=self.load_return_invoice
                      ).pack(fill="x", padx=15, pady=(0, 10))
        
        self.ret_info_label = ctk.CTkLabel(left,
            text="Invoice नम्बर हाल्नुहोस्",
            font=("Arial", 11), text_color="#7f8c8d")
        self.ret_info_label.pack(pady=5)
        
        ctk.CTkLabel(left, text="Product:", anchor="w",
                     font=("Arial", 11)).pack(fill="x", padx=15)
        self.ret_product_var = ctk.StringVar(value="")
        self.ret_product_menu = ctk.CTkOptionMenu(
            left, variable=self.ret_product_var,
            values=["—"], width=310, height=30,
            command=self.on_return_product_select)
        self.ret_product_menu.pack(fill="x", padx=15, pady=(0, 6))
        
        self.ret_max_label = ctk.CTkLabel(left, text="Max: 0",
            font=("Arial", 11), text_color="#7f8c8d")
        self.ret_max_label.pack(pady=2)
        
        ctk.CTkLabel(left, text="Return Qty:", anchor="w",
                     font=("Arial", 11)).pack(fill="x", padx=15)
        self.ret_qty_entry = ctk.CTkEntry(left, placeholder_text="1", height=30)
        self.ret_qty_entry.pack(fill="x", padx=15, pady=(0, 6))
        
        ctk.CTkLabel(left, text="कारण:", anchor="w",
                     font=("Arial", 11)).pack(fill="x", padx=15)
        self.ret_reason = ctk.CTkComboBox(left,
            values=["Defective", "Wrong item", "Customer change mind",
                    "Size issue", "Other"], height=30, width=310)
        self.ret_reason.pack(fill="x", padx=15, pady=(0, 6))
        
        # Refund method
        ctk.CTkLabel(left, text="Refund Method:", anchor="w",
                     font=("Arial", 11)).pack(fill="x", padx=15)
        self.ret_refund_method = ctk.CTkComboBox(left,
            values=["Cash", "Card", "Store Credit", "Exchange"],
            height=30, width=310)
        self.ret_refund_method.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkButton(left, text="↩️ Return गर्नुहोस्", height=42,
                      font=("Arial", 13, "bold"), fg_color="#e74c3c",
                      hover_color="#c0392b",
                      command=self.process_return
                      ).pack(fill="x", padx=15, pady=5)
        
        # RIGHT - Return History
        right = ctk.CTkFrame(main, corner_radius=8)
        right.pack(side="right", fill="both", expand=True)
        
        ctk.CTkLabel(right, text="📋 Return History",
                     font=("Arial", 14, "bold")).pack(pady=(10, 5))
        
        rcols = ("Date", "Invoice", "Product", "Qty", "Amount",
                 "Reason", "Refund", "User")
        self.ret_tree = ttk.Treeview(right, columns=rcols,
            show="headings", height=15)
        for c, w in zip(rcols, [120, 130, 140, 50, 90, 120, 80, 80]):
            self.ret_tree.heading(c, text=c)
            self.ret_tree.column(c, width=w, anchor="center")
        self.ret_tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.return_invoice = None
    
    # ==================================================
    # 💰 UDHAAR TAB
    # ==================================================
    def build_udhaar_tab(self):
        main = ctk.CTkFrame(self.tab_udhaar, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        top = ctk.CTkFrame(main)
        top.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(top, text="💰 Udhaar (Credit) Management",
                     font=("Arial", 15, "bold")).pack(side="left", padx=15)
        
        # Cards
        cards = ctk.CTkFrame(main, fg_color="transparent")
        cards.pack(fill="x", padx=10, pady=5)
        
        self.udh_total_card = self.create_card(cards, "💰 कुल Udhaar",
                                                  "Rs. 0", "#e74c3c")
        self.udh_paid_card = self.create_card(cards, "✅ तिरेको",
                                                 "Rs. 0", "#27ae60")
        self.udh_due_card = self.create_card(cards, "⚠️ बाँकी",
                                                "Rs. 0", "#e67e22")
        self.udh_customers_card = self.create_card(cards, "👥 Customers",
                                                      "0", "#3498db")
        
        # Filter
        flt = ctk.CTkFrame(main)
        flt.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(flt, text="Filter:").pack(side="left", padx=5)
        self.udh_filter = ctk.CTkComboBox(flt,
            values=["All", "Unpaid", "Paid", "Overdue"],
            width=150, height=28,
            command=lambda e: self.refresh_udhaar())
        self.udh_filter.set("Unpaid")
        self.udh_filter.pack(side="left", padx=5)
        
        ctk.CTkButton(flt, text="🔄 Refresh", width=100, height=28,
                      fg_color="#3498db",
                      command=self.refresh_udhaar).pack(side="left", padx=5)
        
        # Tree
        cols = ("Date", "Customer", "Phone", "Invoice",
                "Total", "Paid", "Due", "Days", "Status")
        self.udh_tree = ttk.Treeview(main, columns=cols,
            show="headings", height=13)
        for c, w in zip(cols, [120, 130, 110, 140, 90, 90, 90, 60, 90]):
            self.udh_tree.heading(c, text=c)
            self.udh_tree.column(c, width=w, anchor="center")
        self.udh_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.udh_tree.tag_configure("overdue", background="#fdedec",
                                      foreground="#c0392b")
        self.udh_tree.tag_configure("paid", background="#e8f8f5")
        
        # Payment row
        pay = ctk.CTkFrame(main)
        pay.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(pay, text="💰 Payment जम्मा:",
                     font=("Arial", 12, "bold")).pack(side="left", padx=5)
        self.udh_pay_entry = ctk.CTkEntry(pay,
            placeholder_text="रकम", width=150, height=32,
            font=("Arial", 12))
        self.udh_pay_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(pay, text="💵 Cash", width=100, height=32,
                      fg_color="#27ae60",
                      command=lambda: self.pay_udhaar("Cash")
                      ).pack(side="left", padx=2)
        ctk.CTkButton(pay, text="💳 Card", width=100, height=32,
                      fg_color="#3498db",
                      command=lambda: self.pay_udhaar("Card")
                      ).pack(side="left", padx=2)
        ctk.CTkButton(pay, text="📱 Mobile", width=100, height=32,
                      fg_color="#9b59b6",
                      command=lambda: self.pay_udhaar("Mobile")
                      ).pack(side="left", padx=2)
    
    # ==================================================
    # 🏆 LOYALTY TAB
    # ==================================================
    def build_loyalty_tab(self):
        main = ctk.CTkFrame(self.tab_loyalty, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        top = ctk.CTkFrame(main)
        top.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(top, text="🏆 Loyalty Points",
                     font=("Arial", 15, "bold")).pack(side="left", padx=15)
        
        ctk.CTkButton(top, text="🔄 Refresh", width=100, height=30,
                      fg_color="#3498db",
                      command=self.refresh_loyalty).pack(side="right", padx=5)
        
        # Cards
        cards = ctk.CTkFrame(main, fg_color="transparent")
        cards.pack(fill="x", padx=10, pady=5)
        
        self.loy_total_points = self.create_card(cards, "🏆 Total Points",
                                                    "0", "#9b59b6")
        self.loy_total_customers = self.create_card(cards, "👥 Members",
                                                       "0", "#3498db")
        self.loy_total_value = self.create_card(cards, "💰 Point Value",
                                                   "Rs. 0", "#27ae60")
        self.loy_used = self.create_card(cards, "💸 Used Points",
                                            "0", "#e67e22")
        
        # Tree
        cols = ("ID", "Customer", "Phone", "Points",
                "Total Spent", "Member Since", "Status")
        self.loy_tree = ttk.Treeview(main, columns=cols,
            show="headings", height=15)
        for c, w in zip(cols, [50, 180, 130, 100, 130, 130, 100]):
            self.loy_tree.heading(c, text=c)
            self.loy_tree.column(c, width=w, anchor="center")
        self.loy_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.loy_tree.tag_configure("gold", background="#fff3cd")
        self.loy_tree.tag_configure("silver", background="#ecf0f1")
    
    # ==================================================
    # 📋 HISTORY TAB
    # ==================================================
    def build_history_tab(self):
        main = ctk.CTkFrame(self.tab_history, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        top = ctk.CTkFrame(main)
        top.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(top, text="📋 Transaction History",
                     font=("Arial", 15, "bold")).pack(side="left", padx=15)
        
        ctk.CTkButton(top, text="🔄 Refresh", width=90, height=30,
                      command=self.refresh_history).pack(side="right", padx=5)
        ctk.CTkButton(top, text="💾 CSV", width=90, height=30,
                      fg_color="#8e44ad",
                      command=self.export_history_csv).pack(side="right", padx=5)
        
        # Filter
        flt = ctk.CTkFrame(main)
        flt.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(flt, text="Type:").pack(side="left", padx=5)
        self.hist_filter = ctk.CTkComboBox(flt,
            values=["All", "Sale", "Purchase", "Return"],
            width=150, height=28,
            command=lambda e: self.refresh_history())
        self.hist_filter.set("All")
        self.hist_filter.pack(side="left", padx=5)
        
        # Summary Cards
        cards = ctk.CTkFrame(main, fg_color="transparent")
        cards.pack(fill="x", padx=10, pady=5)
        
        self.card_sales = self.create_card(cards, "📤 Sale",
                                             "Rs. 0", "#27ae60")
        self.card_purchase = self.create_card(cards, "📥 Purchase",
                                                "Rs. 0", "#e74c3c")
        self.card_profit = self.create_card(cards, "💰 Net",
                                              "Rs. 0", "#2980b9")
        self.card_returns = self.create_card(cards, "↩️ Returns",
                                               "Rs. 0", "#e67e22")
        
        # Tree
        cols = ("Type", "Invoice/Date", "Product", "Qty",
                "Amount", "Party", "User")
        self.history_tree = ttk.Treeview(main, columns=cols,
            show="headings", height=13)
        for c, w in zip(cols, [80, 150, 170, 60, 120, 140, 100]):
            self.history_tree.heading(c, text=c)
            self.history_tree.column(c, width=w, anchor="center")
        self.history_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.history_tree.tag_configure("sale", background="#e8f8f5")
        self.history_tree.tag_configure("purchase", background="#fdedec")
        self.history_tree.tag_configure("return", background="#fff3cd")
    
    # ==================================================
    # 📈 REPORTS TAB
    # ==================================================
    def build_reports_tab(self):
        main = ctk.CTkFrame(self.tab_reports, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        top = ctk.CTkFrame(main)
        top.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(top, text="📈 Reports",
                     font=("Arial", 15, "bold")).pack(side="left", padx=15)
        
        ctk.CTkLabel(top, text="Date:", font=("Arial", 11)).pack(side="left", padx=5)
        self.rep_range = ctk.CTkComboBox(top,
            values=["Today", "Last 7 days", "Last 30 days",
                    "Last 90 days", "This Year", "All time"],
            width=150, height=28,
            command=lambda e: self.refresh_reports())
        self.rep_range.set("Last 30 days")
        self.rep_range.pack(side="left", padx=5)
        
        ctk.CTkButton(top, text="🔄", width=50, height=28,
                      command=self.refresh_reports).pack(side="left", padx=5)
        
        ctk.CTkButton(top, text="📊 Export Report", width=140, height=28,
                      fg_color="#8e44ad",
                      command=self.export_report).pack(side="right", padx=5)
        
        # Chart
        self.chart_frame = ctk.CTkFrame(main)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Summary
        self.rep_summary = ctk.CTkTextbox(main, height=140,
            font=("Courier New", 11))
        self.rep_summary.pack(fill="x", padx=10, pady=(0, 10))
    
    # ==================================================
    # 🧾 INVOICES TAB
    # ==================================================
    def build_invoices_tab(self):
        main = ctk.CTkFrame(self.tab_invoices, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        top = ctk.CTkFrame(main)
        top.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(top, text="🧾 Invoices",
                     font=("Arial", 15, "bold")).pack(side="left", padx=15)
        
        ctk.CTkButton(top, text="🔄 Refresh", width=90, height=30,
                      command=self.refresh_invoices).pack(side="right", padx=5)
        ctk.CTkButton(top, text="📂 Folder", width=100, height=30,
                      fg_color="#16a085",
                      command=self.open_invoice_folder).pack(side="right", padx=5)
        
        # Search
        sf = ctk.CTkFrame(main)
        sf.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(sf, text="🔍 Search:", font=("Arial", 11)).pack(side="left", padx=5)
        self.inv_search = ctk.CTkEntry(sf, placeholder_text="Invoice/Party",
                                         height=28)
        self.inv_search.pack(side="left", fill="x", expand=True, padx=5)
        self.inv_search.bind("<KeyRelease>",
            lambda e: self.refresh_invoices())
        
        # Tree
        cols = ("Invoice No", "Type", "Date", "Party", "Items", "Total")
        self.inv_tree = ttk.Treeview(main, columns=cols,
            show="headings", height=13)
        for c, w in zip(cols, [180, 100, 150, 180, 80, 130]):
            self.inv_tree.heading(c, text=c)
            self.inv_tree.column(c, width=w, anchor="center")
        self.inv_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.inv_tree.bind("<Double-1>", self.open_invoice)
        self.inv_tree.tag_configure("sale", background="#e8f8f5")
        self.inv_tree.tag_configure("purchase", background="#fdedec")
        
        # Actions
        act = ctk.CTkFrame(main, fg_color="transparent")
        act.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(act, text="📂 Preview", width=140, height=36,
                      fg_color="#3498db", font=("Arial", 12, "bold"),
                      command=self.open_invoice_selected
                      ).pack(side="left", padx=2)
        ctk.CTkButton(act, text="🖨️ Print", width=120, height=36,
                      fg_color="#27ae60",
                      command=self.print_invoice_selected
                      ).pack(side="left", padx=2)
        ctk.CTkButton(act, text="📄 Thermal TXT", width=140, height=36,
                      fg_color="#e67e22",
                      command=self.print_thermal).pack(side="left", padx=2)
    
    # ==================================================
    # 💵 CASH DRAWER TAB
    # ==================================================
    def build_cash_tab(self):
        main = ctk.CTkFrame(self.tab_cash, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        top = ctk.CTkFrame(main)
        top.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(top, text="💵 Cash Drawer",
                     font=("Arial", 15, "bold")).pack(side="left", padx=15)
        
        self.cash_status_label = ctk.CTkLabel(top, text="",
            font=("Arial", 12, "bold"))
        self.cash_status_label.pack(side="left", padx=15)
        
        # Cards
        cards = ctk.CTkFrame(main, fg_color="transparent")
        cards.pack(fill="x", padx=10, pady=5)
        
        self.cash_opening_card = self.create_card(cards, "🔓 Opening",
                                                     "Rs. 0", "#3498db")
        self.cash_sales_card = self.create_card(cards, "💰 Cash Sales",
                                                   "Rs. 0", "#27ae60")
        self.cash_in_card = self.create_card(cards, "➕ Cash In",
                                                "Rs. 0", "#16a085")
        self.cash_out_card = self.create_card(cards, "➖ Cash Out",
                                                 "Rs. 0", "#e74c3c")
        
        cards2 = ctk.CTkFrame(main, fg_color="transparent")
        cards2.pack(fill="x", padx=10, pady=5)
        
        self.cash_expected_card = self.create_card(cards2, "📊 Expected",
                                                      "Rs. 0", "#9b59b6")
        self.cash_actual_card = self.create_card(cards2, "💵 Actual",
                                                    "Rs. 0", "#e67e22")
        self.cash_diff_card = self.create_card(cards2, "⚠️ Difference",
                                                  "Rs. 0", "#c0392b")
        
        # Buttons
        btn_row = ctk.CTkFrame(main)
        btn_row.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(btn_row, text="➕ Cash In", width=140, height=42,
                      font=("Arial", 12, "bold"), fg_color="#16a085",
                      command=lambda: self.cash_transaction("in")
                      ).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="➖ Cash Out", width=140, height=42,
                      font=("Arial", 12, "bold"), fg_color="#e74c3c",
                      command=lambda: self.cash_transaction("out")
                      ).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="🔒 Day Close", width=160, height=42,
                      font=("Arial", 12, "bold"), fg_color="#c0392b",
                      command=self.day_close_dialog
                      ).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text="📋 View History", width=160, height=42,
                      font=("Arial", 12, "bold"), fg_color="#3498db",
                      command=self.view_cash_history
                      ).pack(side="left", padx=5)
        
        # Today's transactions
        ctk.CTkLabel(main, text="📋 आजका Transactions",
                     font=("Arial", 14, "bold")).pack(pady=(15, 5))
        
        cols = ("Time", "Type", "Amount", "User", "Remark")
        self.cash_tree = ttk.Treeview(main, columns=cols,
            show="headings", height=8)
        for c, w in zip(cols, [130, 100, 130, 120, 250]):
            self.cash_tree.heading(c, text=c)
            self.cash_tree.column(c, width=w, anchor="center")
        self.cash_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.cash_tree.tag_configure("in", background="#e8f8f5")
        self.cash_tree.tag_configure("out", background="#fdedec")
    
    # ==================================================
    # 📝 AUDIT LOG TAB
    # ==================================================
    def build_audit_tab(self):
        main = ctk.CTkFrame(self.tab_audit, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        top = ctk.CTkFrame(main)
        top.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(top, text="📝 Audit Log",
                     font=("Arial", 15, "bold")).pack(side="left", padx=15)
        
        ctk.CTkButton(top, text="🔄 Refresh", width=90, height=30,
                      command=self.refresh_audit).pack(side="right", padx=5)
        ctk.CTkButton(top, text="💾 CSV", width=90, height=30,
                      fg_color="#8e44ad",
                      command=self.export_audit).pack(side="right", padx=5)
        
        # Filter
        flt = ctk.CTkFrame(main)
        flt.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(flt, text="User:").pack(side="left", padx=5)
        self.audit_user_filter = ctk.CTkComboBox(flt,
            values=["All"], width=150, height=28,
            command=lambda e: self.refresh_audit())
        self.audit_user_filter.set("All")
        self.audit_user_filter.pack(side="left", padx=5)
        
        ctk.CTkLabel(flt, text="Action:").pack(side="left", padx=5)
        self.audit_action_filter = ctk.CTkComboBox(flt,
            values=["All", "LOGIN", "LOGOUT", "PRODUCT_ADD",
                    "PRODUCT_UPDATE", "PRODUCT_DELETE", "SALE",
                    "PURCHASE", "RETURN", "HOLD_SALE", "DAY_OPEN",
                    "DAY_CLOSE", "CASH_IN", "CASH_OUT", "PAYMENT"],
            width=180, height=28,
            command=lambda e: self.refresh_audit())
        self.audit_action_filter.set("All")
        self.audit_action_filter.pack(side="left", padx=5)
        
        # Tree
        cols = ("ID", "Date", "User", "Action", "Details")
        self.audit_tree = ttk.Treeview(main, columns=cols,
            show="headings", height=15)
        for c, w in zip(cols, [80, 180, 120, 180, 500]):
            self.audit_tree.heading(c, text=c)
            self.audit_tree.column(c, width=w, anchor="w" if c == "Details" else "center")
        self.audit_tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.audit_count_label = ctk.CTkLabel(main, text="",
            font=("Arial", 10), text_color="#7f8c8d")
        self.audit_count_label.pack(pady=(0, 10))
            # ==================================================
    # RETURNS FUNCTIONS
    # ==================================================
    def load_return_invoice(self):
        inv_no = self.ret_invoice_entry.get().strip()
        if not inv_no:
            messagebox.showwarning("चेतावनी", "Invoice No हाल्नुहोस्!")
            return
        sales = load_sales()
        sale = next((s for s in sales if s.get('invoice_no') == inv_no), None)
        if not sale:
            messagebox.showerror("गल्ती", "Invoice भेटिएन!")
            return
        self.return_invoice = sale
        self.ret_info_label.configure(
            text=f"✅ {sale.get('party_name', '')} | Rs. {sale['total']:,.0f}",
            text_color="#27ae60")
        items = [f"{i+1}. {x['name']} (Qty: {x['quantity']})"
                 for i, x in enumerate(sale['items'])]
        self.ret_product_menu.configure(values=items)
        self.ret_product_var.set(items[0] if items else "")
        self.on_return_product_select(items[0] if items else "")
    
    def on_return_product_select(self, choice):
        if not self.return_invoice or not choice:
            return
        try:
            idx = int(choice.split(".")[0]) - 1
            item = self.return_invoice['items'][idx]
            self.ret_max_label.configure(text=f"Max: {item['quantity']}")
        except:
            pass
    
    def process_return(self):
        if not self.return_invoice:
            messagebox.showwarning("चेतावनी", "Invoice खोज्नुहोस्!")
            return
        choice = self.ret_product_var.get()
        try:
            idx = int(choice.split(".")[0]) - 1
            item = self.return_invoice['items'][idx]
            qty = int(self.ret_qty_entry.get().strip() or 0)
        except:
            messagebox.showerror("गल्ती", "जाँच्नुहोस्!")
            return
        if qty <= 0 or qty > item['quantity']:
            messagebox.showerror("गल्ती", f"Qty 1-{item['quantity']} भित्र!")
            return
        
        reason = self.ret_reason.get()
        refund_method = self.ret_refund_method.get()
        amount = item['unit_price'] * qty
        
        if not messagebox.askyesno("Return",
            f"Return गर्ने?\n{item['name']} x {qty}\nRs. {amount:,.0f}\n"
            f"Refund: {refund_method}"):
            return
        
        # Stock बढाउने
        products = load_products()
        p = next((x for x in products if x['name'] == item['name']), None)
        if p:
            p['quantity'] += qty
            save_products(products)
        
        # Return record
        returns = load_returns()
        returns.append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "invoice_no": self.return_invoice['invoice_no'],
            "product_name": item['name'],
            "quantity": qty,
            "unit_price": item['unit_price'],
            "total": amount,
            "reason": reason,
            "refund_method": refund_method,
            "user": self.current_user['username']
        })
        save_returns(returns)
        
        audit_log("RETURN",
            f"{item['name']} x {qty} = Rs. {amount:,.0f} ({reason})",
            user=self.current_user['username'])
        
        # Cash drawer मा refund
        if refund_method == "Cash":
            cash = load_cash()
            cash.append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "out",
                "amount": amount,
                "user": self.current_user['username'],
                "remark": f"Return Refund: {item['name']}"
            })
            save_cash(cash)
        
        self.refresh_all()
        self.ret_qty_entry.delete(0, "end")
        messagebox.showinfo("सफल",
            f"Return भयो!\nRs. {amount:,.0f} ({refund_method})")
    
    # ==================================================
    # UDHAAR FUNCTIONS
    # ==================================================
    def refresh_udhaar(self):
        for r in self.udh_tree.get_children():
            self.udh_tree.delete(r)
        udhaar = load_udhaar()
        flt = self.udh_filter.get()
        
        total = sum(u['total'] for u in udhaar)
        paid_total = sum(u['paid'] for u in udhaar)
        due_total = sum(u['due'] for u in udhaar)
        customers_count = len(set(u['customer'] for u in udhaar if u['due'] > 0))
        
        self.udh_total_card.configure(text=f"Rs. {total:,.0f}")
        self.udh_paid_card.configure(text=f"Rs. {paid_total:,.0f}")
        self.udh_due_card.configure(text=f"Rs. {due_total:,.0f}")
        self.udh_customers_card.configure(text=f"{customers_count}")
        
        today = datetime.now()
        for u in udhaar:
            status = "✅ Paid" if u['due'] <= 0 else "⚠️ Unpaid"
            tag = "paid" if u['due'] <= 0 else ""
            
            # Days calculation
            try:
                d = datetime.strptime(u['date'][:10], "%Y-%m-%d")
                days = (today - d).days
            except:
                days = 0
            
            # Overdue (30+ days)
            if u['due'] > 0 and days > 30:
                status = "🔴 Overdue"
                tag = "overdue"
            
            if flt == "Unpaid" and u['due'] <= 0:
                continue
            if flt == "Paid" and u['due'] > 0:
                continue
            if flt == "Overdue" and (u['due'] <= 0 or days <= 30):
                continue
            
            self.udh_tree.insert("", "end", tags=(tag,) if tag else (), values=(
                u['date'], u['customer'], u.get('phone', ''),
                u['invoice_no'],
                f"Rs. {u['total']:,.0f}", f"Rs. {u['paid']:,.0f}",
                f"Rs. {u['due']:,.0f}", days, status))
    
    def pay_udhaar(self, method="Cash"):
        sel = self.udh_tree.selection()
        if not sel:
            messagebox.showwarning("चेतावनी", "कुनै छान्नुहोस्!")
            return
        try:
            amt = float(self.udh_pay_entry.get().strip() or 0)
        except:
            messagebox.showerror("गल्ती", "रकम सही हाल्नुहोस्!")
            return
        if amt <= 0:
            return
        
        inv_no = self.udh_tree.item(sel[0])['values'][3]
        udhaar = load_udhaar()
        for u in udhaar:
            if u['invoice_no'] == inv_no:
                u['paid'] += amt
                u['due'] = max(0, u['total'] - u['paid'])
                if u['due'] <= 0:
                    u['status'] = "Paid"
                break
        save_udhaar(udhaar)
        
        audit_log("PAYMENT", f"{inv_no}: Rs. {amt:,.0f} ({method})",
                  user=self.current_user['username'])
        
        # Cash drawer
        if method == "Cash":
            cash = load_cash()
            cash.append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "in",
                "amount": amt,
                "user": self.current_user['username'],
                "remark": f"Udhaar payment: {inv_no}"
            })
            save_cash(cash)
        
        self.refresh_udhaar()
        self.udh_pay_entry.delete(0, "end")
        messagebox.showinfo("सफल", f"Rs. {amt:,.0f} जम्मा भयो! ({method})")
    
    # ==================================================
    # LOYALTY FUNCTIONS
    # ==================================================
    def refresh_loyalty(self):
        for r in self.loy_tree.get_children():
            self.loy_tree.delete(r)
        customers = load_customers()
        sales = load_sales()
        
        total_points = 0
        used_points = 0
        
        for c in customers:
            points = c.get('loyalty_points', 0)
            used = c.get('loyalty_used', 0)
            total_points += points
            used_points += used
            
            # Tier
            total_spent = c.get('total_sales', 0)
            if total_spent >= 100000:
                tier = "🥇 Gold"
                tag = "gold"
            elif total_spent >= 50000:
                tier = "🥈 Silver"
                tag = "silver"
            else:
                tier = "⭐ Regular"
                tag = ""
            
            self.loy_tree.insert("", "end", tags=(tag,) if tag else (), values=(
                c['id'], c['name'], c.get('phone', ''),
                points, f"Rs. {total_spent:,.0f}",
                c.get('date_added', '')[:10], tier))
        
        self.loy_total_points.configure(text=f"{total_points:,}")
        self.loy_total_customers.configure(text=f"{len(customers)}")
        self.loy_total_value.configure(text=f"Rs. {total_points:,.0f}")
        self.loy_used.configure(text=f"{used_points:,}")
    
    # ==================================================
    # HISTORY FUNCTIONS
    # ==================================================
    def refresh_history(self):
        for r in self.history_tree.get_children():
            self.history_tree.delete(r)
        sales = load_sales()
        purchases = load_purchases()
        returns = load_returns()
        
        flt = self.hist_filter.get() if hasattr(self, 'hist_filter') else "All"
        
        combined = []
        for s in sales:
            qty = sum(i['quantity'] for i in s['items'])
            combined.append({
                "type": "📤 Sale", "tag": "sale", "date": s['date'],
                "inv": s.get('invoice_no', ''), "product": f"{len(s['items'])} items",
                "qty": qty, "amount": s['total'],
                "party": s.get('party_name', ''),
                "user": s.get('user', self.current_user['username'])
            })
        for p in purchases:
            qty = sum(i['quantity'] for i in p['items'])
            combined.append({
                "type": "📥 Pur", "tag": "purchase", "date": p['date'],
                "inv": p.get('invoice_no', ''), "product": f"{len(p['items'])} items",
                "qty": qty, "amount": p['total'],
                "party": p.get('party_name', ''),
                "user": p.get('user', self.current_user['username'])
            })
        for r in returns:
            combined.append({
                "type": "↩️ Ret", "tag": "return", "date": r['date'],
                "inv": r.get('invoice_no', ''), "product": r['product_name'],
                "qty": r['quantity'], "amount": r['total'],
                "party": r.get('reason', ''),
                "user": r.get('user', '')
            })
        
        # Filter
        if flt == "Sale":
            combined = [c for c in combined if c['tag'] == 'sale']
        elif flt == "Purchase":
            combined = [c for c in combined if c['tag'] == 'purchase']
        elif flt == "Return":
            combined = [c for c in combined if c['tag'] == 'return']
        
        combined.sort(key=lambda x: x['date'], reverse=True)
        for c in combined[:200]:
            self.history_tree.insert("", "end", tags=(c['tag'],), values=(
                c['type'], c['inv'] or c['date'], c['product'],
                c['qty'], f"Rs. {c['amount']:,.0f}",
                c['party'], c['user']))
        
        ts = sum(s['total'] for s in sales)
        tp = sum(p['total'] for p in purchases)
        tr = sum(r['total'] for r in returns)
        self.card_sales.configure(text=f"Rs. {ts:,.0f}")
        self.card_purchase.configure(text=f"Rs. {tp:,.0f}")
        self.card_profit.configure(text=f"Rs. {ts - tp:,.0f}")
        self.card_returns.configure(text=f"Rs. {tr:,.0f}")
    
    def export_history_csv(self):
        sales = load_sales()
        purchases = load_purchases()
        returns = load_returns()
        fn = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"history_{datetime.now().strftime('%Y%m%d')}.csv")
        if not fn:
            return
        with open(fn, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["Type", "Invoice", "Date", "Party", "Total", "User"])
            for s in sales:
                w.writerow(["Sale", s.get('invoice_no', ''), s['date'],
                             s.get('party_name', ''), s['total'],
                             s.get('user', '')])
            for p in purchases:
                w.writerow(["Purchase", p.get('invoice_no', ''), p['date'],
                             p.get('party_name', ''), p['total'],
                             p.get('user', '')])
            for r in returns:
                w.writerow(["Return", r.get('invoice_no', ''), r['date'],
                             r.get('reason', ''), r['total'],
                             r.get('user', '')])
        messagebox.showinfo("सफल", f"CSV: {fn}")
    
    # ==================================================
    # REPORTS FUNCTIONS
    # ==================================================
    def refresh_reports(self):
        for w in self.chart_frame.winfo_children():
            w.destroy()
        
        days_map = {
            "Today": 1, "Last 7 days": 7, "Last 30 days": 30,
            "Last 90 days": 90, "This Year": 365, "All time": 3650
        }
        days = days_map.get(self.rep_range.get(), 30)
        cutoff = datetime.now() - timedelta(days=days)
        
        all_sales = load_sales()
        all_purchases = load_purchases()
        all_returns = load_returns()
        
        sales = [s for s in all_sales
                 if datetime.strptime(s['date'][:10], "%Y-%m-%d") >= cutoff]
        purchases = [p for p in all_purchases
                     if datetime.strptime(p['date'][:10], "%Y-%m-%d") >= cutoff]
        returns = [r for r in all_returns
                   if datetime.strptime(r['date'][:10], "%Y-%m-%d") >= cutoff]
        
        # Chart - 2 subplots
        fig = Figure(figsize=(12, 5), dpi=80)
        
        # Subplot 1 - Trend
        ax1 = fig.add_subplot(121)
        dates = {}
        for s in sales:
            d = s['date'][:10]
            dates[d] = dates.get(d, {"sale": 0, "purchase": 0})
            dates[d]['sale'] += s['total']
        for p in purchases:
            d = p['date'][:10]
            dates[d] = dates.get(d, {"sale": 0, "purchase": 0})
            dates[d]['purchase'] += p['total']
        
        sorted_dates = sorted(dates.keys())
        if sorted_dates:
            ax1.plot(sorted_dates, [dates[d]['sale'] for d in sorted_dates],
                     'g-o', label='Sales', linewidth=2)
            ax1.plot(sorted_dates, [dates[d]['purchase'] for d in sorted_dates],
                     'r-s', label='Purchases', linewidth=2)
            ax1.legend()
            ax1.set_title("Sale vs Purchase Trend")
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
        else:
            ax1.text(0.5, 0.5, "No data", ha='center', va='center')
            ax1.set_title("Sale vs Purchase Trend")
        
        # Subplot 2 - Top products (bar)
        ax2 = fig.add_subplot(122)
        product_sales = {}
        for s in sales:
            for item in s['items']:
                product_sales[item['name']] = product_sales.get(item['name'], 0) + item['total']
        top = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:8]
        if top:
            names = [n[:12] for n, v in top]
            vals = [v for n, v in top]
            ax2.barh(names, vals, color='#3498db')
            ax2.set_title("Top Products")
            ax2.set_xlabel("Revenue (Rs.)")
        else:
            ax2.text(0.5, 0.5, "No data", ha='center', va='center')
            ax2.set_title("Top Products")
        
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Summary
        ts = sum(s['total'] for s in sales)
        tp = sum(p['total'] for p in purchases)
        tr = sum(r['total'] for r in returns)
        
        # Payment method breakdown
        pm_breakdown = {}
        for s in sales:
            pm = s.get('payment_method', 'Cash')
            pm_breakdown[pm] = pm_breakdown.get(pm, 0) + s['total']
        
        self.rep_summary.delete("1.0", "end")
        text = f"{'='*60}\n"
        text += f"  📊 REPORT - {self.rep_range.get()}\n"
        text += f"{'='*60}\n\n"
        text += f"📤 Total Sales:      Rs. {ts:>15,.0f}\n"
        text += f"📥 Total Purchases:  Rs. {tp:>15,.0f}\n"
        text += f"↩️ Total Returns:    Rs. {tr:>15,.0f}\n"
        text += f"{'─'*60}\n"
        text += f"💰 Net Profit:       Rs. {ts - tp - tr:>15,.0f}\n"
        text += f"📋 Transactions:     {len(sales) + len(purchases):>15}\n"
        text += f"🛒 Items Sold:       {sum(sum(i['quantity'] for i in s['items']) for s in sales):>15}\n\n"
        text += f"💳 Payment Methods:\n"
        for pm, amt in sorted(pm_breakdown.items(), key=lambda x: -x[1]):
            text += f"   • {pm:<15} Rs. {amt:>12,.0f}\n"
        text += f"\n🏆 Top 5 Products:\n"
        for n, v in top[:5]:
            text += f"   • {n:<25} Rs. {v:>10,.0f}\n"
        
        self.rep_summary.insert("1.0", text)
    
    def export_report(self):
        days_map = {
            "Today": 1, "Last 7 days": 7, "Last 30 days": 30,
            "Last 90 days": 90, "This Year": 365, "All time": 3650
        }
        days = days_map.get(self.rep_range.get(), 30)
        cutoff = datetime.now() - timedelta(days=days)
        
        sales = [s for s in load_sales()
                 if datetime.strptime(s['date'][:10], "%Y-%m-%d") >= cutoff]
        
        if not sales:
            messagebox.showinfo("जानकारी", "कुनै sale छैन!")
            return
        
        fn = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"report_{datetime.now().strftime('%Y%m%d')}.csv")
        if not fn:
            return
        
        with open(fn, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["Invoice", "Date", "Customer", "Items",
                         "Subtotal", "Discount", "VAT", "Total", "Payment"])
            for s in sales:
                w.writerow([
                    s.get('invoice_no', ''), s['date'],
                    s.get('party_name', ''),
                    len(s['items']),
                    s['subtotal'], s.get('discount', 0),
                    s.get('vat_amount', 0), s['total'],
                    s.get('payment_method', 'Cash')
                ])
        
        messagebox.showinfo("सफल", f"Report: {fn}")
    
    # ==================================================
    # INVOICES FUNCTIONS
    # ==================================================
    def refresh_invoices(self):
        for r in self.inv_tree.get_children():
            self.inv_tree.delete(r)
        
        search = self.inv_search.get().strip().lower() if hasattr(self, 'inv_search') else ""
        
        for s in load_sales():
            if s.get('invoice_no'):
                if search and search not in s['invoice_no'].lower() and \
                   search not in s.get('party_name', '').lower():
                    continue
                self.inv_tree.insert("", "end", tags=("sale",), values=(
                    s['invoice_no'], "Sale", s['date'],
                    s.get('party_name', ''), len(s.get('items', [])),
                    f"Rs. {s['total']:,.0f}"))
        
        for p in load_purchases():
            if p.get('invoice_no'):
                if search and search not in p['invoice_no'].lower() and \
                   search not in p.get('party_name', '').lower():
                    continue
                self.inv_tree.insert("", "end", tags=("purchase",), values=(
                    p['invoice_no'], "Purchase", p['date'],
                    p.get('party_name', ''), len(p.get('items', [])),
                    f"Rs. {p['total']:,.0f}"))
    
    def open_invoice_folder(self):
        try:
            os.startfile(INVOICE_DIR)
        except Exception as e:
            messagebox.showerror("गल्ती", str(e))
    
    def open_invoice(self, event=None):
        sel = self.inv_tree.selection()
        if not sel:
            return
        inv_no = self.inv_tree.item(sel[0])['values'][0]
        path = os.path.join(INVOICE_DIR, f"{inv_no}.html")
        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("गल्ती", str(e))
        else:
            messagebox.showerror("गल्ती", f"File भेटिएन:\n{path}")
    
    def open_invoice_selected(self):
        self.open_invoice()
    
    def print_invoice_selected(self):
        sel = self.inv_tree.selection()
        if not sel:
            messagebox.showwarning("चेतावनी", "Invoice छान्नुहोस्!")
            return
        inv_no = self.inv_tree.item(sel[0])['values'][0]
        path = os.path.join(INVOICE_DIR, f"{inv_no}.html")
        if os.path.exists(path):
            try:
                os.startfile(path)
                messagebox.showinfo("जानकारी",
                    "Bill browser मा खुल्यो।\n"
                    "Print button थिच्नुहोस्।")
            except Exception as e:
                messagebox.showerror("गल्ती", str(e))
    
    def print_thermal(self):
        sel = self.inv_tree.selection()
        if not sel:
            messagebox.showwarning("चेतावनी", "Invoice छान्नुहोस्!")
            return
        inv_no = self.inv_tree.item(sel[0])['values'][0]
        path = os.path.join(INVOICE_DIR, f"{inv_no}_thermal.txt")
        if os.path.exists(path):
            try:
                os.startfile(path, "print")
                messagebox.showinfo("सफल", "Thermal print पठाइयो!")
            except:
                try:
                    os.startfile(path)
                except Exception as e:
                    messagebox.showerror("गल्ती", str(e))
        else:
            messagebox.showerror("गल्ती", "Thermal receipt भेटिएन!")
    
    # ==================================================
    # CASH DRAWER FUNCTIONS
    # ==================================================
    def cash_transaction(self, ttype):
        """Cash In/Out dialog"""
        win = ctk.CTkToplevel(self)
        win.title(f"💵 Cash {ttype.title()}")
        win.geometry("400x320")
        win.grab_set()
        
        color = "#16a085" if ttype == "in" else "#e74c3c"
        symbol = "➕" if ttype == "in" else "➖"
        
        ctk.CTkLabel(win, text=f"{symbol} Cash {ttype.title()}",
                     font=("Arial", 18, "bold"),
                     text_color=color).pack(pady=15)
        
        form = ctk.CTkFrame(win)
        form.pack(pady=10, padx=25, fill="x")
        
        ctk.CTkLabel(form, text="रकम (Rs.):",
                     anchor="w", font=("Arial", 12, "bold")).pack(fill="x", pady=(5, 2))
        amt_e = ctk.CTkEntry(form, placeholder_text="0",
                              height=40, font=("Arial", 16, "bold"),
                              border_color=color, border_width=2)
        amt_e.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(form, text="कारण / Remark:",
                     anchor="w", font=("Arial", 12)).pack(fill="x", pady=(5, 2))
        reason_e = ctk.CTkEntry(form, placeholder_text="Notes", height=32)
        reason_e.pack(fill="x", pady=(0, 10))
        
        def do_trans():
            try:
                amt = float(amt_e.get().strip() or 0)
            except:
                messagebox.showerror("गल्ती", "रकम!")
                return
            if amt <= 0:
                return
            
            cash = load_cash()
            cash.append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": ttype,
                "amount": amt,
                "user": self.current_user['username'],
                "remark": reason_e.get().strip()
            })
            save_cash(cash)
            
            audit_log(f"CASH_{ttype.upper()}",
                f"Rs. {amt:,.0f} - {reason_e.get().strip()}",
                user=self.current_user['username'])
            
            win.destroy()
            self.refresh_cash()
            messagebox.showinfo("सफल", f"Cash {ttype}: Rs. {amt:,.0f}")
        
        ctk.CTkButton(win, text=f"✅ Confirm",
                      height=42, font=("Arial", 13, "bold"),
                      fg_color=color, command=do_trans).pack(pady=15)
        
        amt_e.focus()
    
    def day_close_dialog(self):
        """दिन बन्द गर्ने"""
        if not self.day_open:
            messagebox.showwarning("चेतावनी", "दिन सुरु भएको छैन!")
            return
        
        # Calculate expected cash
        cash = load_cash()
        today = datetime.now().strftime("%Y-%m-%d")
        today_cash = [c for c in cash if c['date'].startswith(today)]
        
        opening = 0
        cash_in = 0
        cash_out = 0
        cash_sales = 0
        
        for c in today_cash:
            if c['type'] == 'open':
                opening = c['amount']
            elif c['type'] == 'in':
                cash_in += c['amount']
            elif c['type'] == 'out':
                cash_out += c['amount']
        
        # Today's cash sales
        sales = load_sales()
        today_sales = [s for s in sales if s['date'].startswith(today)]
        for s in today_sales:
            if s.get('payment_method') == 'Cash':
                cash_sales += s.get('paid', s['total'])
        
        expected = opening + cash_in - cash_out + cash_sales
        
        win = ctk.CTkToplevel(self)
        win.title("🔒 Day Close")
        win.geometry("450x520")
        win.grab_set()
        win.attributes('-topmost', True)
        
        ctk.CTkLabel(win, text="🔒 Day Close",
                     font=("Arial", 20, "bold"),
                     text_color="#c0392b").pack(pady=15)
        
        # Info box
        info = ctk.CTkFrame(win, fg_color="#f8f9fa", corner_radius=8)
        info.pack(pady=10, padx=20, fill="x")
        
        rows = [
            ("📅 Date", datetime.now().strftime("%Y-%m-%d")),
            ("🔓 Opening Cash", f"Rs. {opening:,.0f}"),
            ("💰 Cash Sales", f"Rs. {cash_sales:,.0f}"),
            ("➕ Cash In", f"Rs. {cash_in:,.0f}"),
            ("➖ Cash Out", f"Rs. {cash_out:,.0f}"),
        ]
        for label, val in rows:
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(row, text=label, font=("Arial", 11),
                         anchor="w", width=180).pack(side="left")
            ctk.CTkLabel(row, text=val, font=("Arial", 11, "bold"),
                         anchor="e").pack(side="right")
        
        # Expected
        exp_row = ctk.CTkFrame(info, fg_color="#e8f8f5", corner_radius=5)
        exp_row.pack(fill="x", padx=10, pady=(8, 10))
        ctk.CTkLabel(exp_row, text="📊 Expected Cash:",
                     font=("Arial", 12, "bold")).pack(side="left", padx=10, pady=8)
        ctk.CTkLabel(exp_row, text=f"Rs. {expected:,.0f}",
                     font=("Arial", 14, "bold"),
                     text_color="#27ae60").pack(side="right", padx=10, pady=8)
        
        # Actual entry
        ctk.CTkLabel(win, text="💵 Actual Cash Count (Rs.):",
                     font=("Arial", 12, "bold")).pack(pady=(15, 5))
        actual_e = ctk.CTkEntry(win, placeholder_text="0", height=42,
                                  font=("Arial", 16, "bold"),
                                  border_color="#c0392b", border_width=2)
        actual_e.pack(fill="x", padx=40, pady=(0, 10))
        actual_e.insert(0, f"{expected:.0f}")
        
        # Difference
        diff_label = ctk.CTkLabel(win, text="Difference: Rs. 0",
                                    font=("Arial", 13, "bold"))
        diff_label.pack(pady=5)
        
        def calc_diff(*args):
            try:
                act = float(actual_e.get().strip() or 0)
                diff = act - expected
                if diff == 0:
                    diff_label.configure(text="Difference: Rs. 0 ✅",
                                          text_color="#27ae60")
                elif diff > 0:
                    diff_label.configure(text=f"Difference: +Rs. {diff:,.0f}",
                                          text_color="#e67e22")
                else:
                    diff_label.configure(text=f"Difference: Rs. {diff:,.0f}",
                                          text_color="#e74c3c")
            except:
                pass
        
        actual_e.bind("<KeyRelease>", calc_diff)
        
        ctk.CTkLabel(win, text="Remark:", font=("Arial", 11)).pack(pady=(10, 3))
        remark_e = ctk.CTkEntry(win, placeholder_text="Notes", height=30)
        remark_e.pack(fill="x", padx=40, pady=(0, 10))
        
        def do_close():
            try:
                actual = float(actual_e.get().strip() or 0)
            except:
                messagebox.showerror("गल्ती", "रकम!")
                return
            
            diff = actual - expected
            
            if not messagebox.askyesno("पुष्टि",
                f"Day Close गर्ने?\n\n"
                f"Expected: Rs. {expected:,.0f}\n"
                f"Actual: Rs. {actual:,.0f}\n"
                f"Difference: Rs. {diff:,.0f}"):
                return
            
            cash = load_cash()
            cash.append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "close",
                "amount": actual,
                "expected": expected,
                "difference": diff,
                "user": self.current_user['username'],
                "remark": remark_e.get().strip()
            })
            save_cash(cash)
            
            audit_log("DAY_CLOSE",
                f"Expected: {expected:,.0f}, Actual: {actual:,.0f}, Diff: {diff:,.0f}",
                user=self.current_user['username'])
            
            self.day_open = False
            self.update_day_indicator()
            win.destroy()
            self.refresh_cash()
            
            messagebox.showinfo("Day Closed",
                f"दिन बन्द भयो!\n"
                f"Difference: Rs. {diff:,.0f}")
        
        ctk.CTkButton(win, text="🔒 Day Close",
                      height=45, font=("Arial", 14, "bold"),
                      fg_color="#c0392b", hover_color="#922b21",
                      command=do_close).pack(pady=15)
        
        actual_e.focus()
        actual_e.select_range(0, "end")
    
    def view_cash_history(self):
        """Cash history देखाउने"""
        cash = load_cash()
        if not cash:
            messagebox.showinfo("जानकारी", "कुनै record छैन!")
            return
        
        win = ctk.CTkToplevel(self)
        win.title("📋 Cash History")
        win.geometry("900x600")
        win.grab_set()
        
        ctk.CTkLabel(win, text="📋 Cash Drawer History",
                     font=("Arial", 16, "bold")).pack(pady=15)
        
        cols = ("Date", "Type", "Amount", "Expected", "Diff", "User", "Remark")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=20)
        for c, w in zip(cols, [140, 80, 110, 110, 100, 100, 200]):
            tree.heading(c, text=c)
            tree.column(c, width=w, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=5)
        tree.tag_configure("in", background="#e8f8f5")
        tree.tag_configure("out", background="#fdedec")
        tree.tag_configure("close", background="#fff3cd")
        
        for c in reversed(cash[-500:]):
            tag = c['type'] if c['type'] in ['in', 'out'] else (
                'close' if c['type'] == 'close' else '')
            tree.insert("", "end", tags=(tag,) if tag else (), values=(
                c['date'], c['type'].upper(), f"Rs. {c['amount']:,.0f}",
                f"Rs. {c.get('expected', 0):,.0f}" if c.get('expected') else '—',
                f"Rs. {c.get('difference', 0):,.0f}" if c.get('difference') else '—',
                c.get('user', ''), c.get('remark', '')[:40]))
        
        ctk.CTkButton(win, text="बन्द", height=38, width=140,
                      fg_color="#e74c3c",
                      command=win.destroy).pack(pady=10)
    
    def refresh_cash(self):
        """Cash tab refresh"""
        cash = load_cash()
        today = datetime.now().strftime("%Y-%m-%d")
        today_cash = [c for c in cash if c['date'].startswith(today)]
        
        opening = 0
        cash_in = 0
        cash_out = 0
        cash_sales = 0
        day_closed = False
        actual = 0
        
        for c in today_cash:
            if c['type'] == 'open':
                opening = c['amount']
            elif c['type'] == 'in':
                cash_in += c['amount']
            elif c['type'] == 'out':
                cash_out += c['amount']
            elif c['type'] == 'close':
                day_closed = True
                actual = c['amount']
        
        sales = load_sales()
        today_sales = [s for s in sales if s['date'].startswith(today)]
        for s in today_sales:
            if s.get('payment_method') == 'Cash':
                cash_sales += s.get('paid', s['total'])
        
        expected = opening + cash_in - cash_out + cash_sales
        
        self.cash_opening_card.configure(text=f"Rs. {opening:,.0f}")
        self.cash_sales_card.configure(text=f"Rs. {cash_sales:,.0f}")
        self.cash_in_card.configure(text=f"Rs. {cash_in:,.0f}")
        self.cash_out_card.configure(text=f"Rs. {cash_out:,.0f}")
        self.cash_expected_card.configure(text=f"Rs. {expected:,.0f}")
        self.cash_actual_card.configure(text=f"Rs. {actual:,.0f}" if day_closed else "—")
        
        diff = actual - expected if day_closed else 0
        self.cash_diff_card.configure(text=f"Rs. {diff:,.0f}" if day_closed else "—",
                                        text_color="#c0392b" if diff < 0 else "#27ae60")
        
        self.cash_status_label.configure(
            text="🟢 DAY OPEN" if self.day_open else "🔴 DAY CLOSED",
            text_color="#27ae60" if self.day_open else "#e74c3c")
        
        # Today's transactions tree
        for r in self.cash_tree.get_children():
            self.cash_tree.delete(r)
        for c in reversed(today_cash):
            tag = c['type'] if c['type'] in ['in', 'out'] else ''
            self.cash_tree.insert("", "end", tags=(tag,) if tag else (), values=(
                c['date'][11:19] if len(c['date']) > 11 else c['date'],
                c['type'].upper(),
                f"Rs. {c['amount']:,.0f}",
                c.get('user', ''),
                c.get('remark', '')[:50]))
    
    # ==================================================
    # AUDIT LOG FUNCTIONS
    # ==================================================
    def refresh_audit(self):
        for r in self.audit_tree.get_children():
            self.audit_tree.delete(r)
        
        logs = load_audit()
        
        # Update user filter
        users = set([l['user'] for l in logs])
        user_options = ["All"] + sorted(list(users))
        self.audit_user_filter.configure(values=user_options)
        
        uflt = self.audit_user_filter.get()
        aflt = self.audit_action_filter.get()
        
        filtered = logs
        if uflt != "All":
            filtered = [l for l in filtered if l['user'] == uflt]
        if aflt != "All":
            filtered = [l for l in filtered if l['action'] == aflt]
        
        # Show latest 500
        for l in reversed(filtered[-500:]):
            self.audit_tree.insert("", "end", values=(
                l.get('id', ''),
                l['date'],
                l['user'],
                l['action'],
                l['details'][:80]))
        
        self.audit_count_label.configure(
            text=f"📊 {len(filtered)} / {len(logs)} entries shown")
    
    def export_audit(self):
        logs = load_audit()
        if not logs:
            messagebox.showinfo("जानकारी", "कुनै log छैन!")
            return
        fn = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"audit_{datetime.now().strftime('%Y%m%d')}.csv")
        if not fn:
            return
        with open(fn, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["ID", "Date", "User", "Action", "Details"])
            for l in logs:
                w.writerow([l.get('id', ''), l['date'],
                             l['user'], l['action'], l['details']])
        messagebox.showinfo("सफल", f"Audit: {fn}")
    
    # ==================================================
    # SALES CHECKOUT
    # ==================================================
    def checkout_sale(self):
        if not self.sale_cart:
            messagebox.showwarning("चेतावनी", "Cart खाली!")
            return
        
        # Stock check
        products = load_products()
        for item in self.sale_cart:
            p = next((x for x in products if x['id'] == item['id']), None)
            if not p or p['quantity'] < item['quantity']:
                messagebox.showerror("गल्ती",
                    f"'{item['name']}' stock अपुग!")
                return
        
        subtotal = sum(x['total'] for x in self.sale_cart)
        try:
            discount = float(self.sale_discount_entry.get().strip() or 0)
        except:
            discount = 0
        
        after = subtotal - discount
        vat = after * 13 / 100 if self.sale_vat_var.get() else 0
        
        # Loyalty redemption
        loyalty_disc = 0
        loyalty_earned = 0
        cust_choice = self.sale_customer_var.get()
        cust = "Walk-in"
        phone = ""
        cid = None
        
        if cust_choice and cust_choice != "— Walk-in —":
            try:
                cid = int(cust_choice.split(".")[0])
                customers = load_customers()
                c = next((x for x in customers if x['id'] == cid), None)
                if c:
                    cust = c['name']
                    phone = c.get('phone', '')
                    if self.sale_use_loyalty.get():
                        loyalty_disc = min(c.get('loyalty_points', 0), after + vat)
            except:
                pass
        
        grand = after + vat - loyalty_disc
        if grand < 0:
            grand = 0
        
        # Payment
        payment_method = self.sale_payment_var.get()
        
        if payment_method == "Split":
            self.calc_split()
            paid = sum(p['amount'] for p in self.split_payments)
            payments = list(self.split_payments)
        else:
            try:
                paid = float(self.sale_paid_entry.get().strip() or grand)
            except:
                paid = grand
            payments = [{"method": payment_method, "amount": paid}]
        
        due = max(0, grand - paid)
        
        if not messagebox.askyesno("Checkout",
            f"Items: {len(self.sale_cart)}\n"
            f"Subtotal: Rs. {subtotal:,.0f}\n"
            f"Discount: Rs. {discount:,.0f}\n"
            f"VAT: Rs. {vat:,.0f}\n"
            f"Loyalty: Rs. {loyalty_disc:,.0f}\n"
            f"─────────────\n"
            f"GRAND: Rs. {grand:,.0f}\n"
            f"Paid: Rs. {paid:,.0f}\n"
            f"Due: Rs. {due:,.0f}\n\n"
            f"Confirm?"):
            return
        
        sales = load_sales()
        inv_no = generate_invoice_number("INV", sales)
        
        # Loyalty earned (1% of total)
        s_settings = load_settings()
        loyalty_pct = s_settings.get('loyalty_percent', 1)
        loyalty_earned = int((grand - loyalty_disc) * loyalty_pct / 100)
        
        sale = {
            "invoice_no": inv_no,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "items": list(self.sale_cart),
            "subtotal": subtotal,
            "discount": discount,
            "vat_amount": vat,
            "loyalty_discount": loyalty_disc,
            "total": grand,
            "paid": paid,
            "due": due,
            "party_name": cust,
            "party_phone": phone,
            "customer_id": cid,
            "payment_method": payment_method,
            "payments": payments,
            "loyalty_earned": loyalty_earned,
            "user": self.current_user['username']
        }
        
        # Stock घटाउने
        for item in self.sale_cart:
            p = next((x for x in products if x['id'] == item['id']), None)
            if p:
                p['quantity'] -= item['quantity']
        
        save_products(products)
        sales.append(sale)
        save_sales(sales)
        
        # Udhaar
        if due > 0:
            udhaar = load_udhaar()
            udhaar.append({
                "invoice_no": inv_no,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "customer": cust,
                "phone": phone,
                "customer_id": cid,
                "total": grand,
                "paid": paid,
                "due": due,
                "status": "Unpaid"
            })
            save_udhaar(udhaar)
        
        # Customer loyalty update
        if cid:
            customers = load_customers()
            for c in customers:
                if c['id'] == cid:
                    c['total_sales'] = c.get('total_sales', 0) + grand
                    if due > 0:
                        c['total_due'] = c.get('total_due', 0) + due
                    
                    # Loyalty points
                    if self.sale_use_loyalty.get() and loyalty_disc > 0:
                        c['loyalty_points'] = max(0, c.get('loyalty_points', 0) - int(loyalty_disc))
                        c['loyalty_used'] = c.get('loyalty_used', 0) + int(loyalty_disc)
                    c['loyalty_points'] = c.get('loyalty_points', 0) + loyalty_earned
                    break
            save_customers(customers)
        
        # Cash drawer for cash payments
        cash_paid = sum(p['amount'] for p in payments if p['method'] == 'Cash')
        if cash_paid > 0:
            cash = load_cash()
            cash.append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "in",
                "amount": cash_paid,
                "user": self.current_user['username'],
                "remark": f"Sale {inv_no}"
            })
            save_cash(cash)
        
        # Invoice
        inv_path = save_invoice_html(sale, is_sale=True)
        thermal_path = save_thermal_receipt(sale, is_sale=True)
        
        audit_log("SALE",
            f"{inv_no}: Rs. {grand:,.0f} ({payment_method})",
            user=self.current_user['username'])
        
        self.refresh_all()
        self.reset_sale_tab()
        
        # Success + print dialog
        msg = f"✅ Sale सफल!\n\n"
        msg += f"Invoice: {inv_no}\n"
        msg += f"Total: Rs. {grand:,.0f}\n"
        if loyalty_earned > 0:
            msg += f"Loyalty: +{loyalty_earned} points\n"
        if due > 0:
            msg += f"⚠️ Due: Rs. {due:,.0f}\n"
        msg += f"\nBill print गर्ने?"
        
        if messagebox.askyesno("Sale Complete", msg):
            try:
                os.startfile(inv_path)
            except:
                pass
    
    def reset_sale_tab(self):
        self.sale_cart = []
        self.split_payments = []
        self.refresh_sale_cart()
        self.sale_product_var.set("")
        self.sale_qty_entry.delete(0, "end")
        self.sale_line_discount.delete(0, "end")
        self.sale_discount_entry.delete(0, "end")
        self.sale_paid_entry.delete(0, "end")
        self.sale_vat_var.set(False)
        self.sale_use_loyalty.set(False)
        self.sale_barcode_entry.delete(0, "end")
        self.sale_customer_var.set("— Walk-in —")
        self.sale_customer_info.configure(text="")
        self.loyalty_label.configure(text="")
        self.split_frame.pack_forget()
        self.sale_payment_var.set("Cash")
        # Clear split rows
        for method_var, amt_e in self.split_rows:
            amt_e.delete(0, "end")
        self.update_sale_totals()
    
    # ==================================================
    # CUSTOMER FUNCTIONS
    # ==================================================
    def refresh_customers_menu(self):
        customers = load_customers()
        if customers:
            options = ["— Walk-in —"] + [
                f"{c['id']}. {c['name']}" for c in customers]
        else:
            options = ["— Walk-in —"]
        self.sale_customer_menu.configure(values=options)
    
    def on_customer_select(self, choice):
        if not choice or choice == "— Walk-in —":
            self.sale_customer_info.configure(text="")
            self.loyalty_label.configure(text="")
            return
        try:
            cid = int(choice.split(".")[0])
        except:
            return
        customers = load_customers()
        cust = next((c for c in customers if c['id'] == cid), None)
        if cust:
            info = []
            if cust.get('phone'):
                info.append(f"📞 {cust['phone']}")
            if cust.get('total_sales'):
                info.append(f"💰 Rs. {cust['total_sales']:,.0f}")
            if cust.get('total_due', 0) > 0:
                info.append(f"⚠️ Due: Rs. {cust['total_due']:,.0f}")
            self.sale_customer_info.configure(
                text="  |  ".join(info) if info else "")
            
            points = cust.get('loyalty_points', 0)
            if points > 0:
                self.loyalty_label.configure(
                    text=f"🏆 {points} pts (= Rs. {points})")
            else:
                self.loyalty_label.configure(text="")
    
    def add_customer_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("➕ नयाँ Customer")
        win.geometry("420x400")
        win.grab_set()
        
        ctk.CTkLabel(win, text="👤 नयाँ Customer",
                     font=("Arial", 16, "bold")).pack(pady=15)
        
        form = ctk.CTkFrame(win)
        form.pack(pady=10, padx=25, fill="x")
        
        ctk.CTkLabel(form, text="नाम *:",
                     anchor="w", font=("Arial", 12)).pack(fill="x", pady=(5, 2))
        name_e = ctk.CTkEntry(form, placeholder_text="Ram Bahadur", height=32)
        name_e.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(form, text="फोन:",
                     anchor="w", font=("Arial", 12)).pack(fill="x", pady=(5, 2))
        phone_e = ctk.CTkEntry(form, placeholder_text="98XXXXXXXX", height=32)
        phone_e.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(form, text="ठेगाना:",
                     anchor="w", font=("Arial", 12)).pack(fill="x", pady=(5, 2))
        addr_e = ctk.CTkEntry(form, placeholder_text="काठमाडौं", height=32)
        addr_e.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(form, text="Email (optional):",
                     anchor="w", font=("Arial", 12)).pack(fill="x", pady=(5, 2))
        email_e = ctk.CTkEntry(form, placeholder_text="email@example.com", height=32)
        email_e.pack(fill="x", pady=(0, 8))
        
        def save_cust():
            name = name_e.get().strip()
            if not name:
                messagebox.showwarning("चेतावनी", "नाम अनिवार्य!")
                return
            
            customers = load_customers()
            phone = phone_e.get().strip()
            
            # Duplicate check
            for c in customers:
                if c['name'].lower() == name.lower() and c.get('phone', '') == phone:
                    messagebox.showwarning("चेतावनी",
                        f"'{name}' ({phone}) पहिले नै छ!")
                    return
            
            new_id = max([c['id'] for c in customers], default=0) + 1
            customer = {
                "id": new_id,
                "name": name,
                "phone": phone,
                "address": addr_e.get().strip(),
                "email": email_e.get().strip(),
                "date_added": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "total_sales": 0,
                "total_due": 0,
                "loyalty_points": 0,
                "loyalty_used": 0
            }
            customers.append(customer)
            save_customers(customers)
            
            audit_log("CUSTOMER_ADD", f"{name} (ID: {new_id})",
                      user=self.current_user['username'])
            
            self.refresh_customers_menu()
            self.sale_customer_var.set(f"{new_id}. {name}")
            self.on_customer_select(f"{new_id}. {name}")
            
            win.destroy()
            messagebox.showinfo("सफल", f"'{name}' थपियो!")
        
        row = ctk.CTkFrame(win, fg_color="transparent")
        row.pack(pady=15)
        ctk.CTkButton(row, text="💾 Save", width=130, height=40,
                      fg_color="#27ae60", font=("Arial", 13, "bold"),
                      command=save_cust).pack(side="left", padx=5)
        ctk.CTkButton(row, text="❌ Cancel", width=130, height=40,
                      fg_color="#e74c3c", font=("Arial", 13, "bold"),
                      command=win.destroy).pack(side="left", padx=5)
        
        name_e.focus()
    
    # ==================================================
    # PURCHASE FUNCTIONS
    # ==================================================
    def toggle_purchase_mode(self):
        if self.pur_mode.get() == "existing":
            self.existing_frame.pack(fill="x", padx=12, pady=(0, 6))
            self.new_product_frame.pack_forget()
        else:
            self.existing_frame.pack_forget()
            self.new_product_frame.pack(fill="x", padx=12, pady=(0, 6))
    
    def toggle_new_bc(self):
        if self.new_bc_mode.get() == "manual":
            self.new_bc_entry.configure(state="normal")
        else:
            self.new_bc_entry.configure(state="disabled")
            self.new_bc_entry.delete(0, "end")
    
    def choose_photo(self):
        path = filedialog.askopenfilename(
            title="Product Photo",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif"),
                        ("All", "*.*")])
        if not path:
            return
        self.photo_path = path
        try:
            img = Image.open(path)
            img.thumbnail((80, 80))
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 80))
            self.photo_preview_label.configure(image=photo, text="")
            self.photo_preview_label.image = photo
        except Exception as e:
            messagebox.showerror("गल्ती", str(e))
            self.photo_path = None
    
    def clear_photo(self):
        self.photo_path = None
        self.photo_preview_label.configure(image="", text="No photo")
        self.photo_preview_label.image = None
    
    def refresh_suppliers_menu(self):
        suppliers = load_suppliers()
        if suppliers:
            options = ["— छान्नुहोस् —"] + [
                f"{s['id']}. {s['name']}" for s in suppliers]
        else:
            options = ["— छान्नुहोस् —"]
        self.pur_supplier_menu.configure(values=options)
    
    def on_supplier_select(self, choice):
        if not choice or choice == "— छान्नुहोस् —":
            self.pur_supplier_info.configure(text="")
            return
        try:
            sid = int(choice.split(".")[0])
        except:
            return
        suppliers = load_suppliers()
        sup = next((s for s in suppliers if s['id'] == sid), None)
        if sup:
            info = []
            if sup.get('phone'):
                info.append(f"📞 {sup['phone']}")
            if sup.get('address'):
                info.append(f"📍 {sup['address']}")
            if sup.get('total_purchases'):
                info.append(f"💰 Rs. {sup['total_purchases']:,.0f}")
            self.pur_supplier_info.configure(
                text="  |  ".join(info) if info else "")
    
    def add_supplier_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("➕ नयाँ Supplier")
        win.geometry("420x440")
        win.grab_set()
        
        ctk.CTkLabel(win, text="🏢 नयाँ Supplier",
                     font=("Arial", 16, "bold")).pack(pady=15)
        
        form = ctk.CTkFrame(win)
        form.pack(pady=10, padx=25, fill="x")
        
        entries = {}
        for label, ph in [("नाम *", "ABC Store"), ("फोन", "98XXXXXXXX"),
                            ("ठेगाना", "काठमाडौं"), ("PAN/VAT", "123456789")]:
            ctk.CTkLabel(form, text=f"{label}:",
                         anchor="w", font=("Arial", 12)).pack(fill="x", pady=(5, 2))
            e = ctk.CTkEntry(form, placeholder_text=ph, height=32)
            e.pack(fill="x", pady=(0, 8))
            entries[label] = e
        
        def save_sup():
            name = entries["नाम *"].get().strip()
            if not name:
                messagebox.showwarning("चेतावनी", "नाम अनिवार्य!")
                return
            
            suppliers = load_suppliers()
            if any(s['name'].lower() == name.lower() for s in suppliers):
                messagebox.showwarning("चेतावनी", f"'{name}' पहिले नै छ!")
                return
            
            new_id = max([s['id'] for s in suppliers], default=0) + 1
            supplier = {
                "id": new_id,
                "name": name,
                "phone": entries["फोन"].get().strip(),
                "address": entries["ठेगाना"].get().strip(),
                "pan": entries["PAN/VAT"].get().strip(),
                "date_added": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "total_purchases": 0
            }
            suppliers.append(supplier)
            save_suppliers(suppliers)
            
            audit_log("SUPPLIER_ADD", f"{name} (ID: {new_id})",
                      user=self.current_user['username'])
            
            self.refresh_suppliers_menu()
            self.pur_supplier_var.set(f"{new_id}. {name}")
            win.destroy()
            messagebox.showinfo("सफल", f"'{name}' थपियो!")
        
        row = ctk.CTkFrame(win, fg_color="transparent")
        row.pack(pady=15)
        ctk.CTkButton(row, text="💾 Save", width=130, height=40,
                      fg_color="#27ae60", font=("Arial", 13, "bold"),
                      command=save_sup).pack(side="left", padx=5)
        ctk.CTkButton(row, text="❌ Cancel", width=130, height=40,
                      fg_color="#e74c3c", font=("Arial", 13, "bold"),
                      command=win.destroy).pack(side="left", padx=5)
    
    def on_purchase_barcode_enter(self):
        code = self.pur_barcode_entry.get().strip()
        if not code:
            return
        product = self.find_product_by_code(code)
        if not product:
            if messagebox.askyesno("भेटिएन",
                f"Barcode: {code}\n\nनयाँ product बनाउने?"):
                self.pur_mode.set("new")
                self.toggle_purchase_mode()
                self.new_bc_mode.set("manual")
                self.toggle_new_bc()
                self.new_bc_entry.delete(0, "end")
                self.new_bc_entry.insert(0,
                    ''.join(filter(str.isdigit, code))[:12])
                self.new_prod_name.focus()
            self.pur_barcode_entry.delete(0, "end")
            return
        self.pur_mode.set("existing")
        self.toggle_purchase_mode()
        self.pur_product_var.set(
            f"{product['id']}. {product['name']} ({product['quantity']})")
        self.pur_price_entry.delete(0, "end")
        self.pur_price_entry.insert(0, str(product.get('cost_price', product['price'])))
        self.pur_qty_entry.delete(0, "end")
        self.pur_qty_entry.insert(0, "1")
        self.pur_qty_entry.focus()
        self.pur_qty_entry.select_range(0, "end")
    
    def on_purchase_qty_enter(self):
        try:
            qty = int(self.pur_qty_entry.get().strip() or 0)
            cost = float(self.pur_price_entry.get().strip() or 0)
        except:
            return
        if qty <= 0 or cost <= 0:
            return
        
        sup_choice = self.pur_supplier_var.get()
        supplier_name = "Unknown"
        supplier_id = None
        if sup_choice and sup_choice != "— छान्नुहोस् —":
            try:
                supplier_id = int(sup_choice.split(".")[0])
                suppliers = load_suppliers()
                sup = next((s for s in suppliers if s['id'] == supplier_id), None)
                if sup:
                    supplier_name = sup['name']
            except:
                pass
        
        if self.pur_mode.get() == "existing":
            choice = self.pur_product_var.get()
            if not choice or choice == "— छान्नुहोस् —":
                return
            try:
                pid = int(choice.split(".")[0])
            except:
                return
            products = load_products()
            product = next((x for x in products if x['id'] == pid), None)
            if not product:
                return
            for item in self.purchase_cart:
                if item['id'] == pid and not item.get('is_new'):
                    item['quantity'] += qty
                    item['total'] = item['quantity'] * item['unit_price']
                    break
            else:
                self.purchase_cart.append({
                    "id": product['id'], "name": product['name'],
                    "quantity": qty, "unit_price": cost,
                    "total": cost * qty, "is_new": False,
                    "supplier": supplier_name, "supplier_id": supplier_id
                })
            pname = product['name']
        else:
            name = self.new_prod_name.get().strip()
            if not name:
                messagebox.showwarning("चेतावनी", "Product नाम!")
                return
            try:
                sale_price = float(self.new_prod_sale_price.get().strip() or 0)
                min_stock = int(self.new_prod_min_stock.get().strip() or 5)
            except:
                return
            if sale_price <= 0:
                messagebox.showwarning("चेतावनी", "Sale Price!")
                return
            cat = self.new_prod_cat.get().strip() or "General"
            bc = self.new_bc_entry.get().strip() if self.new_bc_mode.get() == "manual" else None
            self.purchase_cart.append({
                "id": None, "name": name, "quantity": qty,
                "unit_price": cost, "total": cost * qty,
                "is_new": True, "sale_price": sale_price,
                "min_stock": min_stock,
                "category": cat, "barcode": bc,
                "photo_path": self.photo_path,
                "supplier": supplier_name, "supplier_id": supplier_id
            })
            pname = name
            self.clear_new_product_fields()
        
        self.refresh_purchase_cart()
        self.pur_barcode_entry.delete(0, "end")
        self.pur_product_var.set("")
        self.pur_qty_entry.delete(0, "end")
        self.pur_price_entry.delete(0, "end")
        self.pur_barcode_entry.focus()
    
    def clear_new_product_fields(self):
        self.new_prod_name.delete(0, "end")
        self.new_prod_cat.delete(0, "end")
        self.new_prod_sale_price.delete(0, "end")
        self.new_prod_min_stock.delete(0, "end")
        self.new_bc_mode.set("auto")
        self.toggle_new_bc()
        self.clear_photo()
    
    def add_to_purchase_cart(self):
        self.on_purchase_qty_enter()
    
    def remove_from_purchase_cart(self):
        sel = self.pur_cart_tree.selection()
        if not sel:
            return
        idx = int(self.pur_cart_tree.item(sel[0])['values'][0]) - 1
        if 0 <= idx < len(self.purchase_cart):
            self.purchase_cart.pop(idx)
            self.refresh_purchase_cart()
    
    def clear_purchase_cart(self):
        if self.purchase_cart and messagebox.askyesno("पुष्टि", "Cart खाली?"):
            self.purchase_cart = []
            self.refresh_purchase_cart()
    
    def refresh_purchase_cart(self):
        for r in self.pur_cart_tree.get_children():
            self.pur_cart_tree.delete(r)
        for i, item in enumerate(self.purchase_cart, 1):
            self.pur_cart_tree.insert("", "end", values=(
                i, item['name'], item['quantity'],
                f"Rs. {item['unit_price']:,.0f}",
                f"Rs. {item['total']:,.0f}"))
        n = len(self.purchase_cart)
        subtotal = sum(x['total'] for x in self.purchase_cart)
        self.pur_cart_items.configure(text=f"Items: {n}")
        self.pur_cart_total.configure(text=f"Rs. {subtotal:,.0f}")
        self.update_purchase_totals()
    
    def update_purchase_totals(self):
        subtotal = sum(x['total'] for x in self.purchase_cart)
        try:
            discount = float(self.pur_discount_entry.get().strip() or 0)
        except:
            discount = 0
        grand = subtotal - discount
        self.pur_subtotal_label.configure(text=f"Rs. {subtotal:,.0f}")
        self.pur_grand_label.configure(text=f"Rs. {grand:,.0f}")
    
    def checkout_purchase(self):
        if not self.purchase_cart:
            messagebox.showwarning("चेतावनी", "Cart खाली!")
            return
        subtotal = sum(x['total'] for x in self.purchase_cart)
        try:
            discount = float(self.pur_discount_entry.get().strip() or 0)
        except:
            discount = 0
        grand = subtotal - discount
        
        sup_choice = self.pur_supplier_var.get()
        sup_name = "Unknown"
        sup_phone = ""
        sup_id = None
        if sup_choice and sup_choice != "— छान्नुहोस् —":
            try:
                sup_id = int(sup_choice.split(".")[0])
                suppliers = load_suppliers()
                sup = next((s for s in suppliers if s['id'] == sup_id), None)
                if sup:
                    sup_name = sup['name']
                    sup_phone = sup.get('phone', '')
            except:
                pass
        
        if not messagebox.askyesno("Purchase Confirm",
            f"Items: {len(self.purchase_cart)}\n"
            f"Total: Rs. {grand:,.0f}\n"
            f"Supplier: {sup_name}\n\nConfirm?"):
            return
        
        purchases = load_purchases()
        inv_no = generate_invoice_number("PUR", purchases)
        products = load_products()
        
        for item in self.purchase_cart:
            if item.get('is_new'):
                nid = max([p['id'] for p in products], default=0) + 1
                photo_dest = None
                if item.get('photo_path'):
                    photo_dest = copy_product_photo(item['photo_path'], nid)
                bc_custom = item.get('barcode')
                new_p = {
                    "id": nid, "name": item['name'],
                    "price": item['sale_price'],
                    "cost_price": item['unit_price'],
                    "quantity": item['quantity'],
                    "min_stock": item.get('min_stock', 5),
                    "category": item.get('category', 'General'),
                    "date_added": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "barcode_number": bc_custom if bc_custom else str(nid).zfill(12),
                    "qr_content": None,
                    "is_custom_barcode": bool(bc_custom),
                    "is_custom_qr": False,
                    "photo": photo_dest,
                    "supplier": item.get('supplier', 'Unknown'),
                    "supplier_id": item.get('supplier_id')
                }
                new_p["barcode_image"] = generate_barcode(nid, item['name'], bc_custom)
                new_p["qr_image"] = generate_qr(new_p)
                products.append(new_p)
                item['id'] = nid
            else:
                p = next((x for x in products if x['id'] == item['id']), None)
                if p:
                    p['quantity'] += item['quantity']
                    p['cost_price'] = item['unit_price']
        
        save_products(products)
        
        purchase = {
            "invoice_no": inv_no,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "items": list(self.purchase_cart),
            "subtotal": subtotal,
            "discount": discount,
            "total": grand,
            "party_name": sup_name,
            "party_phone": sup_phone,
            "supplier_id": sup_id,
            "vat_amount": 0,
            "user": self.current_user['username']
        }
        purchases.append(purchase)
        save_purchases(purchases)
        
        if sup_id:
            suppliers = load_suppliers()
            for s in suppliers:
                if s['id'] == sup_id:
                    s['total_purchases'] = s.get('total_purchases', 0) + grand
                    break
            save_suppliers(suppliers)
        
        # Cash drawer (पैसा गयो)
        cash = load_cash()
        cash.append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "out",
            "amount": grand,
            "user": self.current_user['username'],
            "remark": f"Purchase {inv_no}"
        })
        save_cash(cash)
        
        inv_path = save_invoice_html(purchase, is_sale=False)
        save_thermal_receipt(purchase, is_sale=False)
        
        audit_log("PURCHASE", f"{inv_no}: Rs. {grand:,.0f}",
                  user=self.current_user['username'])
        
        self.refresh_all()
        self.reset_purchase_tab()
        
        if messagebox.askyesno("✅ Purchase!",
            f"Invoice: {inv_no}\nTotal: Rs. {grand:,.0f}\n\nBill खोल्ने?"):
            try:
                os.startfile(inv_path)
            except:
                pass
    
    def reset_purchase_tab(self):
        self.purchase_cart = []
        self.refresh_purchase_cart()
        self.pur_mode.set("existing")
        self.toggle_purchase_mode()
        self.pur_product_var.set("")
        self.pur_price_entry.delete(0, "end")
        self.pur_qty_entry.delete(0, "end")
        self.pur_discount_entry.delete(0, "end")
        self.pur_barcode_entry.delete(0, "end")
        self.clear_new_product_fields()
        self.update_purchase_totals()
    
    # ==================================================
    # USERS TAB
    # ==================================================
    def build_users_tab(self):
        main = ctk.CTkFrame(self.tab_users, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        top = ctk.CTkFrame(main)
        top.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(top, text="👥 User Management",
                     font=("Arial", 15, "bold")).pack(side="left", padx=15)
        
        # Only admin can access
        if self.current_user['role'] != 'admin':
            ctk.CTkLabel(main, text="🔒 Only Admin can access",
                         font=("Arial", 16, "bold"),
                         text_color="#e74c3c").pack(pady=50)
            return
        
        ctk.CTkButton(top, text="➕ नयाँ User", width=140, height=30,
                      fg_color="#27ae60",
                      command=self.add_user_dialog).pack(side="right", padx=5)
        ctk.CTkButton(top, text="🔄 Refresh", width=100, height=30,
                      command=self.refresh_users).pack(side="right", padx=5)
        
        # Users list
        cols = ("ID", "Username", "Full Name", "Role",
                "Status", "Created", "Last Login")
        self.users_tree = ttk.Treeview(main, columns=cols,
            show="headings", height=13)
        for c, w in zip(cols, [50, 130, 180, 100, 90, 140, 150]):
            self.users_tree.heading(c, text=c)
            self.users_tree.column(c, width=w, anchor="center")
        self.users_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.users_tree.tag_configure("inactive", background="#fdedec")
        
        # Actions
        act = ctk.CTkFrame(main, fg_color="transparent")
        act.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(act, text="🔑 Reset Password", width=160, height=36,
                      fg_color="#f39c12",
                      command=self.reset_password_dialog
                      ).pack(side="left", padx=2)
        ctk.CTkButton(act, text="🚫 Activate/Deactivate", width=180, height=36,
                      fg_color="#3498db",
                      command=self.toggle_user_active
                      ).pack(side="left", padx=2)
        ctk.CTkButton(act, text="🗑️ Delete", width=120, height=36,
                      fg_color="#e74c3c",
                      command=self.delete_user
                      ).pack(side="left", padx=2)
    
    def refresh_users(self):
        for r in self.users_tree.get_children():
            self.users_tree.delete(r)
        users = load_users()
        for u in users:
            tag = "inactive" if not u.get('active', True) else ""
            self.users_tree.insert("", "end", tags=(tag,) if tag else (), values=(
                u['id'], u['username'], u['full_name'], u['role'].upper(),
                "✅ Active" if u.get('active', True) else "❌ Inactive",
                u.get('created', '')[:10], u.get('last_login', '—')))
    
    def add_user_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("➕ नयाँ User")
        win.geometry("420x480")
        win.grab_set()
        
        ctk.CTkLabel(win, text="👤 नयाँ User",
                     font=("Arial", 16, "bold")).pack(pady=15)
        
        form = ctk.CTkFrame(win)
        form.pack(pady=10, padx=25, fill="x")
        
        ctk.CTkLabel(form, text="Username *:",
                     anchor="w", font=("Arial", 12)).pack(fill="x", pady=(5, 2))
        uname_e = ctk.CTkEntry(form, placeholder_text="username", height=32)
        uname_e.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(form, text="Full Name *:",
                     anchor="w", font=("Arial", 12)).pack(fill="x", pady=(5, 2))
        fname_e = ctk.CTkEntry(form, placeholder_text="Full Name", height=32)
        fname_e.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(form, text="Password *:",
                     anchor="w", font=("Arial", 12)).pack(fill="x", pady=(5, 2))
        pass_e = ctk.CTkEntry(form, placeholder_text="••••••",
                                height=32, show="•")
        pass_e.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(form, text="Role *:",
                     anchor="w", font=("Arial", 12)).pack(fill="x", pady=(5, 2))
        role_var = ctk.StringVar(value="cashier")
        ctk.CTkOptionMenu(form, variable=role_var,
                           values=["cashier", "manager", "admin"],
                           width=200, height=32).pack(pady=(0, 10))
        
        def save():
            uname = uname_e.get().strip()
            fname = fname_e.get().strip()
            pwd = pass_e.get().strip()
            role = role_var.get()
            
            if not uname or not fname or not pwd:
                messagebox.showwarning("चेतावनी", "सबै field भर्नुहोस्!")
                return
            
            users = load_users()
            if any(u['username'].lower() == uname.lower() for u in users):
                messagebox.showwarning("चेतावनी", "Username पहिले नै छ!")
                return
            
            new_id = max([u['id'] for u in users], default=0) + 1
            users.append({
                "id": new_id,
                "username": uname,
                "password": hash_password(pwd),
                "full_name": fname,
                "role": role,
                "active": True,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            save_users(users)
            
            audit_log("USER_ADD", f"{uname} ({role})",
                      user=self.current_user['username'])
            
            win.destroy()
            self.refresh_users()
            messagebox.showinfo("सफल", f"'{uname}' थपियो!")
        
        ctk.CTkButton(win, text="💾 Save", height=42,
                      fg_color="#27ae60", font=("Arial", 13, "bold"),
                      command=save).pack(pady=15)
        uname_e.focus()
    
    def reset_password_dialog(self):
        sel = self.users_tree.selection()
        if not sel:
            messagebox.showwarning("चेतावनी", "User छान्नुहोस्!")
            return
        uid = int(self.users_tree.item(sel[0])['values'][0])
        
        win = ctk.CTkToplevel(self)
        win.title("🔑 Reset Password")
        win.geometry("400x280")
        win.grab_set()
        
        ctk.CTkLabel(win, text="🔑 Reset Password",
                     font=("Arial", 16, "bold")).pack(pady=15)
        
        ctk.CTkLabel(win, text="नयाँ Password:",
                     font=("Arial", 12)).pack(pady=(10, 5))
        pwd_e = ctk.CTkEntry(win, placeholder_text="••••••",
                               height=38, show="•")
        pwd_e.pack(fill="x", padx=40, pady=(0, 10))
        
        def do_reset():
            pwd = pwd_e.get().strip()
            if not pwd:
                return
            users = load_users()
            for u in users:
                if u['id'] == uid:
                    u['password'] = hash_password(pwd)
                    break
            save_users(users)
            audit_log("PASSWORD_RESET", f"User ID: {uid}",
                      user=self.current_user['username'])
            win.destroy()
            messagebox.showinfo("सफल", "Password reset भयो!")
        
        ctk.CTkButton(win, text="💾 Save", height=40,
                      fg_color="#27ae60", font=("Arial", 12, "bold"),
                      command=do_reset).pack(pady=15)
        pwd_e.focus()
    
    def toggle_user_active(self):
        sel = self.users_tree.selection()
        if not sel:
            return
        uid = int(self.users_tree.item(sel[0])['values'][0])
        
        if uid == self.current_user['id']:
            messagebox.showerror("गल्ती", "आफ्नै account deactivate गर्न सकिँदैन!")
            return
        
        users = load_users()
        for u in users:
            if u['id'] == uid:
                u['active'] = not u.get('active', True)
                break
        save_users(users)
        self.refresh_users()
    
    def delete_user(self):
        sel = self.users_tree.selection()
        if not sel:
            return
        uid = int(self.users_tree.item(sel[0])['values'][0])
        
        if uid == self.current_user['id']:
            messagebox.showerror("गल्ती", "आफ्नै account delete गर्न सकिँदैन!")
            return
        
        if not messagebox.askyesno("पुष्टि", "User delete गर्ने?"):
            return
        
        users = [u for u in load_users() if u['id'] != uid]
        save_users(users)
        self.refresh_users()
    
    # ==================================================
    # BACKUP TAB
    # ==================================================
    def build_backup_tab(self):
        main = ctk.CTkFrame(self.tab_backup, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        ctk.CTkLabel(main, text="☁️ Backup Management",
                     font=("Arial", 18, "bold")).pack(pady=20)
        
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text="💾 अहिले Backup बनाउने",
                      width=250, height=48,
                      font=("Arial", 13, "bold"), fg_color="#27ae60",
                      command=self.make_backup).pack(pady=5)
        ctk.CTkButton(btn_frame, text="📂 Backup Folder खोल्ने",
                      width=250, height=42,
                      font=("Arial", 12), fg_color="#3498db",
                      command=self.open_backup_folder).pack(pady=5)
        ctk.CTkButton(btn_frame, text="📊 Storage Info",
                      width=250, height=42,
                      font=("Arial", 12), fg_color="#9b59b6",
                      command=self.show_storage_info).pack(pady=5)
        
        ctk.CTkLabel(main, text="📁 Available Backups:",
                     font=("Arial", 14, "bold")).pack(pady=(20, 5))
        
        self.backup_list = ctk.CTkScrollableFrame(main,
            width=700, height=400)
        self.backup_list.pack(pady=10, padx=20, fill="both", expand=True)
        self.refresh_backup_list()
    
    def make_backup(self):
        path = auto_backup()
        audit_log("BACKUP", f"Backup created: {path}",
                  user=self.current_user['username'])
        messagebox.showinfo("सफल", f"Backup बन्यो:\n{path}")
        self.refresh_backup_list()
    
    def open_backup_folder(self):
        try:
            os.startfile(BACKUP_DIR)
        except Exception as e:
            messagebox.showerror("गल्ती", str(e))
    
    def show_storage_info(self):
        try:
            total, used, free = shutil.disk_usage(APP_DIR)
            data_size = sum(
                os.path.getsize(os.path.join(APP_DIR, f))
                for f in os.listdir(APP_DIR)
                if os.path.isfile(os.path.join(APP_DIR, f))
            )
            
            win = ctk.CTkToplevel(self)
            win.title("📊 Storage Info")
            win.geometry("420x400")
            win.grab_set()
            
            ctk.CTkLabel(win, text="📊 Storage Information",
                         font=("Arial", 16, "bold")).pack(pady=15)
            
            info = ctk.CTkFrame(win)
            info.pack(pady=10, padx=20, fill="x")
            
            rows = [
                ("📁 App Folder", APP_DIR.split("\\")[-1]),
                ("💾 Total Disk", f"{total/(1024**3):.1f} GB"),
                ("📊 Used", f"{used/(1024**3):.1f} GB"),
                ("🆓 Free", f"{free/(1024**3):.1f} GB"),
                ("📄 Data Size", f"{data_size/(1024**2):.2f} MB"),
                ("📦 Products", f"{len(load_products())} items"),
                ("📤 Sales", f"{len(load_sales())} records"),
                ("📥 Purchases", f"{len(load_purchases())} records"),
                ("🧾 Invoices", f"{len(os.listdir(INVOICE_DIR))} files"),
                ("📝 Audit Logs", f"{len(load_audit())} entries"),
            ]
            
            for label, value in rows:
                row = ctk.CTkFrame(info, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=3)
                ctk.CTkLabel(row, text=label, font=("Arial", 11),
                             anchor="w", width=180).pack(side="left")
                ctk.CTkLabel(row, text=value, font=("Arial", 11, "bold"),
                             anchor="e").pack(side="right")
            
            ctk.CTkButton(win, text="बन्द", height=38,
                          fg_color="#e74c3c",
                          command=win.destroy).pack(pady=15)
        except Exception as e:
            messagebox.showerror("गल्ती", str(e))
    
    def refresh_backup_list(self):
        for w in self.backup_list.winfo_children():
            w.destroy()
        if not os.path.exists(BACKUP_DIR):
            return
        backups = sorted(
            [d for d in os.listdir(BACKUP_DIR) if d.startswith("backup_")],
            reverse=True)
        
        if not backups:
            ctk.CTkLabel(self.backup_list, text="कुनै backup छैन",
                         font=("Arial", 11),
                         text_color="#7f8c8d").pack(pady=20)
            return
        
        for b in backups[:30]:
            path = os.path.join(BACKUP_DIR, b)
            try:
                size = sum(os.path.getsize(os.path.join(path, f))
                           for f in os.listdir(path))
                size_str = f"{size/1024:.1f} KB"
            except:
                size_str = "—"
            
            row = ctk.CTkFrame(self.backup_list, fg_color="#f8f9fa",
                                corner_radius=6)
            row.pack(fill="x", pady=3, padx=5)
            
            ctk.CTkLabel(row, text=f"📁 {b}",
                         font=("Arial", 11)).pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(row, text=size_str,
                         font=("Arial", 10),
                         text_color="#7f8c8d").pack(side="left", padx=5)
            
            ctk.CTkButton(row, text="📂 खोल्ने", width=90, height=28,
                          fg_color="#3498db", font=("Arial", 10),
                          command=lambda p=path: os.startfile(p)
                          ).pack(side="right", padx=5)
            ctk.CTkButton(row, text="↩️ Restore", width=90, height=28,
                          fg_color="#f39c12", font=("Arial", 10),
                          command=lambda p=path: self.restore_backup(p)
                          ).pack(side="right", padx=2)
    
    def restore_backup(self, backup_path):
        if not messagebox.askyesno("⚠️ Warning",
            "Restore गर्दा हालको data replace हुनेछ!\n\n"
            "Continue?"):
            return
        if not messagebox.askyesno("⚠️ Final Confirm",
            "के तपाईं पक्का हुनुहुन्छ?\n"
            "यो action undo गर्न सकिँदैन!"):
            return
        
        try:
            files = [DATA_FILE, SALES_FILE, PURCHASES_FILE, RETURNS_FILE,
                     UDHAAR_FILE, SUPPLIERS_FILE, CUSTOMERS_FILE,
                     USERS_FILE, CASH_FILE, HOLD_FILE, LOYALTY_FILE]
            for f in files:
                src = os.path.join(backup_path, os.path.basename(f))
                if os.path.exists(src):
                    shutil.copy(src, f)
            
            audit_log("RESTORE", f"From: {backup_path}",
                      user=self.current_user['username'])
            
            messagebox.showinfo("सफल", "Restore भयो!\nApp restart गर्नुहोस्।")
            self.refresh_all()
        except Exception as e:
            messagebox.showerror("गल्ती", str(e))
    
    # ==================================================
    # SETTINGS TAB
    # ==================================================
    def build_settings_tab(self):
        main = ctk.CTkScrollableFrame(self.tab_settings, fg_color="transparent")
        main.pack(fill="both", expand=True)
        
        ctk.CTkLabel(main, text="⚙️ Settings",
                     font=("Arial", 18, "bold")).pack(pady=15)
        
        form = ctk.CTkFrame(main)
        form.pack(pady=10, padx=30, fill="x")
        
        s = load_settings()
        
        ctk.CTkLabel(form, text="🏪 Business Info",
                     font=("Arial", 13, "bold"),
                     text_color="#3498db").grid(row=0, column=0, columnspan=2,
                                                  pady=(10, 5), sticky="w", padx=10)
        
        fields = [
            ("Business Name:", "set_biz_name", s.get('business_name', '')),
            ("Address:", "set_addr", s.get('address', '')),
            ("Phone:", "set_phone", s.get('phone', '')),
            ("VAT Number:", "set_vat", s.get('vat_number', '')),
        ]
        for i, (label, attr, val) in enumerate(fields):
            ctk.CTkLabel(form, text=label, font=("Arial", 12),
                         anchor="w").grid(row=i+1, column=0,
                                            padx=10, pady=6, sticky="w")
            e = ctk.CTkEntry(form, width=350, height=30)
            e.insert(0, val)
            e.grid(row=i+1, column=1, padx=10, pady=6)
            setattr(self, attr, e)
        
        ctk.CTkLabel(form, text="💰 VAT Settings",
                     font=("Arial", 13, "bold"),
                     text_color="#3498db").grid(row=5, column=0, columnspan=2,
                                                  pady=(15, 5), sticky="w", padx=10)
        
        ctk.CTkLabel(form, text="VAT %:", font=("Arial", 12),
                     anchor="w").grid(row=6, column=0, padx=10, pady=6, sticky="w")
        self.set_vat_pct = ctk.CTkEntry(form, width=350, height=30)
        self.set_vat_pct.insert(0, str(s.get('vat_percent', 13)))
        self.set_vat_pct.grid(row=6, column=1, padx=10, pady=6)
        
        ctk.CTkLabel(form, text="🏆 Loyalty %:", font=("Arial", 12),
                     anchor="w").grid(row=7, column=0, padx=10, pady=6, sticky="w")
        self.set_loyalty = ctk.CTkEntry(form, width=350, height=30)
        self.set_loyalty.insert(0, str(s.get('loyalty_percent', 1)))
        self.set_loyalty.grid(row=7, column=1, padx=10, pady=6)
        
        ctk.CTkLabel(form, text="⚠️ Low Stock Threshold:",
                     font=("Arial", 12), anchor="w").grid(row=8, column=0,
                                                            padx=10, pady=6, sticky="w")
        self.set_low_stock = ctk.CTkEntry(form, width=350, height=30)
        self.set_low_stock.insert(0, str(s.get('low_stock_threshold', 5)))
        self.set_low_stock.grid(row=8, column=1, padx=10, pady=6)
        
        ctk.CTkLabel(form, text="🖨️ Printer",
                     font=("Arial", 13, "bold"),
                     text_color="#3498db").grid(row=9, column=0, columnspan=2,
                                                  pady=(15, 5), sticky="w", padx=10)
        
        ctk.CTkLabel(form, text="Printer Width:",
                     font=("Arial", 12), anchor="w").grid(row=10, column=0,
                                                            padx=10, pady=6, sticky="w")
        self.set_printer = ctk.CTkComboBox(form, values=["80", "58"],
                                             width=350, height=30)
        self.set_printer.set(s.get('printer_width', '80'))
        self.set_printer.grid(row=10, column=1, padx=10, pady=6)
        
        ctk.CTkButton(main, text="💾 Save Settings",
                      width=250, height=48,
                      font=("Arial", 13, "bold"),
                      fg_color="#27ae60", hover_color="#219150",
                      command=self.save_settings_ui).pack(pady=20)
        
        # Info box
        info = ctk.CTkFrame(main, fg_color="#e8f8f5",
                             corner_radius=8)
        info.pack(pady=10, padx=30, fill="x")
        
        ctk.CTkLabel(info, text="📌 System Information",
                     font=("Arial", 13, "bold")).pack(pady=(10, 5))
        
        stats = f"""Version: 2.0 (Full POS)
Total Users: {len(load_users())}
Total Products: {len(load_products())}
Total Customers: {len(load_customers())}
Total Suppliers: {len(load_suppliers())}
Total Sales: {len(load_sales())}
Total Purchases: {len(load_purchases())}
Audit Logs: {len(load_audit())}
"""
        ctk.CTkLabel(info, text=stats, font=("Courier New", 11),
                     justify="left").pack(padx=15, pady=(5, 15))
    
    def save_settings_ui(self):
        try:
            vat = float(self.set_vat_pct.get().strip() or 13)
            loyalty = float(self.set_loyalty.get().strip() or 1)
            low_stock = int(self.set_low_stock.get().strip() or 5)
        except:
            vat = 13
            loyalty = 1
            low_stock = 5
        
        s = {
            "business_name": self.set_biz_name.get().strip() or "मेरो पसल",
            "address": self.set_addr.get().strip(),
            "phone": self.set_phone.get().strip(),
            "vat_number": self.set_vat.get().strip(),
            "vat_percent": vat,
            "loyalty_percent": loyalty,
            "low_stock_threshold": low_stock,
            "printer_width": self.set_printer.get(),
            "currency": "Rs."
        }
        save_settings(s)
        
        audit_log("SETTINGS_UPDATE", "Settings saved",
                  user=self.current_user['username'])
        
        messagebox.showinfo("सफल", "Settings save भयो!")
    
    # ==================================================
    # CAMERA FUNCTIONS
    # ==================================================
    def scan_for_sale(self):
        self.scan_target = "sale"
        self.open_camera()
    
    def scan_for_purchase(self):
        self.scan_target = "purchase"
        self.open_camera()
    
    def open_camera(self):
        if not CAMERA_AVAILABLE:
            messagebox.showerror("गल्ती", "pip install opencv-python")
            return
        if self.camera_window and self.camera_window.winfo_exists():
            self.camera_window.focus()
            return
        
        self.camera_window = ctk.CTkToplevel(self)
        self.camera_window.title("📷 Scanner")
        self.camera_window.geometry("640x580")
        self.camera_window.grab_set()
        
        hint, color = "📷 Scan", "#e67e22"
        if self.scan_target == "sale":
            hint, color = "📤 SALE scan", "#27ae60"
        elif self.scan_target == "purchase":
            hint, color = "📥 PURCHASE scan", "#e74c3c"
        
        ctk.CTkLabel(self.camera_window, text=hint,
                     font=("Arial", 16, "bold"),
                     text_color=color).pack(pady=12)
        
        self.video_label = ctk.CTkLabel(self.camera_window, text="",
                                          width=580, height=380,
                                          fg_color="#000000",
                                          corner_radius=8)
        self.video_label.pack(pady=10)
        
        self.scan_status = ctk.CTkLabel(self.camera_window, text="🔍 खोज्दै...",
                                         font=("Arial", 12))
        self.scan_status.pack(pady=5)
        
        ctk.CTkButton(self.camera_window, text="❌ बन्द",
                      fg_color="#e74c3c", height=38, width=160,
                      command=self.close_camera).pack(pady=10)
        
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("गल्ती", "Camera खोल्न सकिएन!")
            self.close_camera()
            return
        self.qr_detector = cv2.QRCodeDetector()
        self.scan_active = True
        self.update_camera()
    
    def update_camera(self):
        if not self.scan_active or not hasattr(self, 'cap') or self.cap is None:
            return
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            try:
                data, bbox, _ = self.qr_detector.detectAndDecode(frame)
                if data:
                    self.handle_scan_result(data)
                    self.scan_active = False
                    return
            except:
                pass
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(rgb).resize((580, 380))
            photo = ctk.CTkImage(light_image=pil, dark_image=pil,
                                    size=(580, 380))
            self.video_label.configure(image=photo)
            self.video_label.image = photo
        if self.scan_active and self.camera_window and \
           self.camera_window.winfo_exists():
            self.camera_window.after(30, self.update_camera)
    
    def handle_scan_result(self, data):
        self.close_camera()
        product = self.find_product_by_code(data)
        if not product:
            products = load_products()
            for p in products:
                if p.get('qr_content') and p['qr_content'] in data:
                    product = p
                    break
                if f"ID: {p['id']}" in data:
                    product = p
                    break
        if not product:
            messagebox.showinfo("भेटिएन", f"Data:\n{data[:100]}")
            return
        if self.scan_target == "sale":
            self.scan_result_to_sale(product)
        elif self.scan_target == "purchase":
            self.scan_result_to_purchase(product)
        else:
            self.select_product_in_tree(product)
    
    def select_product_in_tree(self, product):
        self.tabs.set("📦 Products")
        for item in self.tree.get_children():
            v = self.tree.item(item)['values']
            if v[0] == product['id']:
                self.tree.selection_set(item)
                self.tree.focus(item)
                break
    
    def scan_result_to_sale(self, product):
        if product['quantity'] <= 0:
            messagebox.showerror("गल्ती", f"'{product['name']}' stock छैन!")
            return
        self.tabs.set("📤 Sales")
        self.sale_product_var.set(
            f"{product['id']}. {product['name']} ({product['quantity']})")
        self.sale_price_label.configure(text=f"Rs. {product['price']}")
        self.sale_stock_label.configure(text=str(product['quantity']))
        self.sale_qty_entry.delete(0, "end")
        self.sale_qty_entry.insert(0, "1")
        self.sale_qty_entry.focus()
        self.sale_qty_entry.select_range(0, "end")
        self.sale_qty_entry.bind("<Return>", lambda e: self.on_sale_qty_enter())
    
    def scan_result_to_purchase(self, product):
        self.tabs.set("📥 Purchases")
        self.pur_mode.set("existing")
        self.toggle_purchase_mode()
        self.pur_product_var.set(
            f"{product['id']}. {product['name']} ({product['quantity']})")
        self.pur_price_entry.delete(0, "end")
        self.pur_price_entry.insert(0, str(product.get('cost_price', product['price'])))
        self.pur_qty_entry.delete(0, "end")
        self.pur_qty_entry.insert(0, "1")
        self.pur_qty_entry.focus()
        self.pur_qty_entry.bind("<Return>", lambda e: self.on_purchase_qty_enter())
    
    def close_camera(self):
        self.scan_active = False
        if hasattr(self, 'cap') and self.cap is not None:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None
        if self.camera_window and self.camera_window.winfo_exists():
            self.camera_window.destroy()
        self.after(500, lambda: setattr(self, 'scan_target', None))
    
    # ==================================================
    # REFRESH ALL
    # ==================================================
    def refresh_all(self):
        try:
            self.refresh_dashboard()
            self.refresh_list()
            self.refresh_sale_cart()
            self.refresh_purchase_cart()
            self.refresh_returns()
            self.refresh_udhaar()
            self.refresh_loyalty()
            self.refresh_history()
            self.refresh_reports()
            self.refresh_invoices()
            self.refresh_cash()
            self.refresh_audit()
            self.refresh_users()
            self.refresh_suppliers_menu()
            self.refresh_customers_menu()
            self.refresh_hold_count()
            self.update_day_indicator()
        except Exception as e:
            print(f"Refresh error: {e}")
    
    def refresh_returns(self):
        for r in self.ret_tree.get_children():
            self.ret_tree.delete(r)
        for r in load_returns():
            self.ret_tree.insert("", "end", values=(
                r['date'], r.get('invoice_no', ''), r['product_name'],
                r['quantity'], f"Rs. {r['total']:,.0f}",
                r.get('reason', ''), r.get('refund_method', ''),
                r.get('user', '')))


# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    app = POSApp()
    app.mainloop()
