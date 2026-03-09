import os, sqlite3, tkinter as tk, sys
from tkinter import ttk, messagebox, filedialog, font
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from tkcalendar import DateEntry
from PIL import Image, ImageTk, ImageDraw, ImageFilter
from shutil import copyfile
import math
import csv
from features_qr import generate_student_card, generate_student_qr
import logging
import traceback
import threading
import subprocess

# ================= AUTO-START API SERVER =================
def start_api_server():
    """Start API server in background for mobile sync"""
    try:
        api_path = os.path.join(os.path.dirname(__file__), 'api', 'server.py')
        if os.path.exists(api_path):
            # Start API server in background
            subprocess.Popen([sys.executable, api_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            logger.info("API server started for mobile sync")
    except Exception as e:
        logger.warning(f"Could not start API server: {e}")

# Start API server in background thread
threading.Thread(target=start_api_server, daemon=True).start()

# ================= ERROR LOGGING SETUP =================
# Create logs directory
LOG_DIR = os.path.join(os.environ.get('APPDATA', '.'), 'ERP_System', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'error_log.txt')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("="*50)
logger.info("ERP-System Started")
logger.info(f"Version: 1.0.0")
logger.info(f"Python: {sys.version}")
logger.info(f"Platform: {sys.platform}")
logger.info("="*50)

# ================= CONFIG =================
ADMIN_USER = "admin"
ADMIN_PASS = "1234"

# Modern Color Palette
COLORS = {
    'primary': '#6366F1',
    'primary_light': '#818CF8',
    'secondary': '#10B981',
    'success': '#22C55E',
    'warning': '#F97316',
    'danger': '#EF4444',
    'info': '#3B82F6',
    'white': '#FFFFFF',
    'gray_100': '#F3F4F6',
    'gray_200': '#E5E7EB',
    'gray_300': '#D1D5DB',
    'gray_400': '#9CA3AF',
    'gray_500': '#6B7280',
    'gray_600': '#4B5563',
    'gray_700': '#374151',
    'gray_800': '#1F2937',
}

# Determine if running as exe or script
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    BASE_DIR = os.path.dirname(sys.executable)
    
    # Check if installer created a data path config
    data_path_file = os.path.join(BASE_DIR, 'data_path.txt')
    if os.path.exists(data_path_file):
        try:
            with open(data_path_file, 'r') as f:
                APP_DATA_DIR = f.read().strip()
        except:
            APP_DATA_DIR = os.path.join(os.environ['APPDATA'], 'ERP_System')
    else:
        # Fallback to AppData
        APP_DATA_DIR = os.path.join(os.environ['APPDATA'], 'ERP_System')
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DATA_DIR = BASE_DIR

# Create data directories in AppData (persistent location)
os.makedirs(APP_DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(APP_DATA_DIR, "library.db")
IMAGE_DIR = os.path.join(APP_DATA_DIR, "aadhaar_images")
os.makedirs(IMAGE_DIR, exist_ok=True)

# Initialize database if it doesn't exist
def init_database():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            middle_name TEXT,
            surname TEXT,
            name TEXT NOT NULL,
            mobile TEXT NOT NULL UNIQUE,
            parents_mobile TEXT,
            email TEXT,
            aadhaar_no TEXT,
            address TEXT,
            course TEXT,
            gender TEXT,
            date_of_birth TEXT,
            admission_date TEXT,
            duration_months INTEGER,
            expiry_date TEXT,
            fees_paid REAL DEFAULT 0,
            aadhaar_image TEXT,
            application_for TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        conn.close()

# Initialize database on startup
init_database()

aadhaar_temp = None
preview_img = None

def db():
    return sqlite3.connect(DB_PATH)

def center(win, w, h):
    win.update_idletasks()
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = (screen_w - w) // 2
    y = (screen_h - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

def lighten_color(color, factor=0.2):
    color = color.lstrip('#')
    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    lighter = tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)
    return f"#{lighter[0]:02x}{lighter[1]:02x}{lighter[2]:02x}"

# ================= MENU PAGE =================
def open_menu():
    login.destroy()
    menu_page()

def open_main():
    menu_win.destroy()
    main_ui()

def open_qr_module():
    menu_win.destroy()
    qr_id_ui()

def open_dashboard():
    menu_win.destroy()
    dashboard_ui()

def open_reminder():
    menu_win.destroy()
    reminder_ui()

def check_login():
    u = user_e.get().strip()
    p = pass_e.get().strip()

    if not u or not p:
        messagebox.showwarning("Missing Information", "Please enter both username and password")
        return

    if u == ADMIN_USER and p == ADMIN_PASS:
        open_menu()
    else:
        messagebox.showerror("Authentication Failed", "Invalid credentials. Please try again.")

# Create login window
login = tk.Tk()
login.title("ERP-System - Authentication Portal")
login.configure(bg=COLORS['primary'])
center(login, 650, 750)  # Larger login window
login.resizable(False, False)

# Main container with better padding
main_container = tk.Frame(login, bg=COLORS['white'], padx=50, pady=40)  # Increased padding
main_container.pack(fill='both', expand=True, padx=25, pady=25)  # Increased margins

# Header
header_frame = tk.Frame(main_container, bg=COLORS['white'])
header_frame.pack(fill='x', pady=(0, 30))

tk.Label(header_frame, text="📚", font=('Segoe UI Emoji', 48), 
         bg=COLORS['white'], fg=COLORS['primary']).pack()

tk.Label(header_frame, text="ERP-System", 
         font=('Segoe UI', 28, 'bold'), 
         bg=COLORS['white'], fg=COLORS['gray_800']).pack()

tk.Label(header_frame, text="Next-Generation Library Management", 
         font=('Segoe UI', 12), 
         bg=COLORS['white'], fg=COLORS['gray_500']).pack(pady=(5, 0))

# Login form
form_container = tk.Frame(main_container, bg=COLORS['white'])
form_container.pack(fill='x', pady=20)

tk.Label(form_container, text="Welcome Back", 
         font=('Segoe UI', 20, 'bold'), 
         bg=COLORS['white'], fg=COLORS['gray_800']).pack()

tk.Label(form_container, text="Sign in to your account to continue", 
         font=('Segoe UI', 11), 
         bg=COLORS['white'], fg=COLORS['gray_500']).pack(pady=(5, 30))

# Username field with improved styling
username_container = tk.Frame(form_container, bg=COLORS['white'])
username_container.pack(fill='x', pady=(0, 20))

tk.Label(username_container, text="👤 Username", 
         font=('Segoe UI', 12, 'bold'), 
         bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 8))

user_e = tk.Entry(username_container, font=('Segoe UI', 16), 
                 relief='solid', bd=2, bg='white',
                 highlightthickness=3, highlightcolor=COLORS['primary'],
                 highlightbackground=COLORS['gray_300'], width=35)
user_e.pack(fill='x', ipady=20)  # Larger input field

# Password field with improved styling
password_container = tk.Frame(form_container, bg=COLORS['white'])
password_container.pack(fill='x', pady=(0, 30))

tk.Label(password_container, text="🔒 Password", 
         font=('Segoe UI', 12, 'bold'), 
         bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 8))

pass_e = tk.Entry(password_container, show="*", font=('Segoe UI', 16), 
                 relief='solid', bd=2, bg='white',
                 highlightthickness=3, highlightcolor=COLORS['primary'],
                 highlightbackground=COLORS['gray_300'], width=35)
pass_e.pack(fill='x', ipady=20)  # Larger input field

# Login button - Simple and guaranteed to work
button_container = tk.Frame(form_container, bg=COLORS['white'])
button_container.pack(pady=(30, 0))

# Create a simple, visible button
login_button = tk.Button(button_container, 
                        text="LOGIN", 
                        command=check_login,
                        bg='blue', 
                        fg='white',
                        font=('Arial', 14, 'bold'),
                        width=15,
                        height=2)
login_button.pack()

# Also create a text-based backup
login_text = tk.Label(button_container, 
                     text="Click here to login", 
                     bg=COLORS['white'], 
                     fg='blue',
                     font=('Arial', 12, 'underline'),
                     cursor='hand2')
login_text.pack(pady=(10, 0))
login_text.bind("<Button-1>", lambda e: check_login())

# Simple login info
login_info = tk.Frame(form_container, bg=COLORS['white'])
login_info.pack(pady=(20, 0))

tk.Label(login_info, text="admin / 1234", 
         font=('Segoe UI', 10), 
         bg=COLORS['white'], fg=COLORS['gray_400']).pack()

# Bind Enter key
login.bind('<Return>', lambda e: check_login())
user_e.bind('<Return>', lambda e: check_login())
pass_e.bind('<Return>', lambda e: check_login())

user_e.focus()

# ================= MENU PAGE =================
def menu_page():
    global menu_win
    
    menu_win = tk.Tk()
    menu_win.title("ERP-System - Dashboard")
    menu_win.configure(bg='#0F172A')  # Dark blue background
    menu_win.state('zoomed')
    menu_win.resizable(True, True)

    # Top Navigation Bar
    navbar = tk.Frame(menu_win, bg='#1E293B', height=70)
    navbar.pack(fill='x')
    navbar.pack_propagate(False)

    nav_content = tk.Frame(navbar, bg='#1E293B')
    nav_content.pack(fill='both', expand=True, padx=40, pady=15)

    # Logo and Brand
    brand_frame = tk.Frame(nav_content, bg='#1E293B')
    brand_frame.pack(side='left')
    
    tk.Label(brand_frame, text="⚡", 
             font=('Segoe UI Emoji', 32), 
             bg='#1E293B', fg='#60A5FA').pack(side='left', padx=(0, 10))
    
    tk.Label(brand_frame, text="ERP-System", 
             font=('Segoe UI', 22, 'bold'), 
             bg='#1E293B', fg='white').pack(side='left')

    # User Info
    user_frame = tk.Frame(nav_content, bg='#1E293B')
    user_frame.pack(side='right')
    
    tk.Label(user_frame, text="Admin", 
             font=('Segoe UI', 13, 'bold'), 
             bg='#1E293B', fg='white').pack(side='left', padx=(0, 10))
    
    tk.Label(user_frame, text="●", 
             font=('Segoe UI', 20), 
             bg='#1E293B', fg='#10B981').pack(side='left')

    # Main Container
    main_container = tk.Frame(menu_win, bg='#0F172A')
    main_container.pack(fill='both', expand=True, padx=60, pady=40)

    # Page Title
    title_section = tk.Frame(main_container, bg='#0F172A')
    title_section.pack(fill='x', pady=(0, 40))
    
    tk.Label(title_section, text="Dashboard", 
             font=('Segoe UI', 42, 'bold'), 
             bg='#0F172A', fg='white').pack(anchor='w')
    
    tk.Label(title_section, text="Select a module to continue", 
             font=('Segoe UI', 16), 
             bg='#0F172A', fg='#94A3B8').pack(anchor='w', pady=(5, 0))

    # Cards Container
    cards_frame = tk.Frame(main_container, bg='#0F172A')
    cards_frame.pack(fill='both', expand=True)
    
    # Configure grid
    for i in range(2):
        cards_frame.grid_columnconfigure(i, weight=1, uniform="card")
        cards_frame.grid_rowconfigure(i, weight=1, uniform="card")

    # Module Data
    modules = [
        {
            'name': 'Student Registration',
            'desc': 'Add and manage student records',
            'icon': '👥',
            'gradient_start': '#6366F1',
            'gradient_end': '#8B5CF6',
            'stats': 'Quick Access',
            'row': 0, 'col': 0,
            'action': open_main
        },
        {
            'name': 'Analytics Dashboard',
            'desc': 'View reports and statistics',
            'icon': '📈',
            'gradient_start': '#10B981',
            'gradient_end': '#059669',
            'stats': 'Real-time Data',
            'row': 0, 'col': 1,
            'action': open_dashboard
        },
        {
            'name': 'ID Card Generator',
            'desc': 'Create student ID cards',
            'icon': '🎴',
            'gradient_start': '#3B82F6',
            'gradient_end': '#2563EB',
            'stats': 'With QR Codes',
            'row': 1, 'col': 0,
            'action': open_qr_module
        },
        {
            'name': 'Notifications',
            'desc': 'Manage expiry alerts',
            'icon': '🔔',
            'gradient_start': '#F59E0B',
            'gradient_end': '#D97706',
            'stats': 'Auto Reminders',
            'row': 1, 'col': 1,
            'action': open_reminder
        }
    ]

    # Create Cards
    for module in modules:
        # Card Container
        card_outer = tk.Frame(cards_frame, bg='#0F172A')
        card_outer.grid(row=module['row'], column=module['col'], 
                       padx=20, pady=20, sticky='nsew')
        
        # Card with gradient effect (simulated with colored frame)
        card = tk.Frame(card_outer, bg='#1E293B', relief='flat', bd=0, cursor='hand2')
        card.pack(fill='both', expand=True)
        
        # Gradient bar at top
        gradient_bar = tk.Frame(card, bg=module['gradient_start'], height=6)
        gradient_bar.pack(fill='x')
        
        # Card Content
        content = tk.Frame(card, bg='#1E293B')
        content.pack(fill='both', expand=True, padx=25, pady=25)
        
        # Icon Section
        icon_frame = tk.Frame(content, bg='#1E293B')
        icon_frame.pack(anchor='w', pady=(0, 15))
        
        # Icon with gradient background
        icon_bg = tk.Frame(icon_frame, bg=module['gradient_start'], 
                          width=70, height=70)
        icon_bg.pack()
        icon_bg.pack_propagate(False)
        
        tk.Label(icon_bg, text=module['icon'], 
                font=('Segoe UI Emoji', 35), 
                bg=module['gradient_start'], fg='white').place(relx=0.5, rely=0.5, anchor='center')
        
        # Module Name
        tk.Label(content, text=module['name'], 
                font=('Segoe UI', 18, 'bold'), 
                bg='#1E293B', fg='white', wraplength=300, justify='left').pack(anchor='w', pady=(0, 6))
        
        # Description
        tk.Label(content, text=module['desc'], 
                font=('Segoe UI', 11), 
                bg='#1E293B', fg='#94A3B8', wraplength=300, justify='left').pack(anchor='w', pady=(0, 15))
        
        # Stats Badge
        badge = tk.Frame(content, bg='#0F172A')
        badge.pack(anchor='w', pady=(0, 15))
        
        tk.Label(badge, text=module['stats'], 
                font=('Segoe UI', 10, 'bold'), 
                bg='#0F172A', fg='#60A5FA',
                padx=10, pady=5).pack()
        
        # Action Button
        btn = tk.Button(content, text="Open Module →", 
                       command=module['action'],
                       bg=module['gradient_start'], fg='white',
                       font=('Segoe UI', 12, 'bold'),
                       relief='flat', bd=0, cursor='hand2',
                       padx=20, pady=10,
                       activebackground=module['gradient_end'],
                       activeforeground='white')
        btn.pack(anchor='w')
        
        # Click event only (hover effects removed)
        def on_click(e, cmd=module['action']):
            cmd()
        
        # Bind click event
        for widget in [card, content, icon_frame]:
            widget.bind('<Button-1>', on_click)

    # Bottom Status Bar
    status_bar = tk.Frame(menu_win, bg='#1E293B', height=50)
    status_bar.pack(fill='x', side='bottom')
    status_bar.pack_propagate(False)
    
    status_content = tk.Frame(status_bar, bg='#1E293B')
    status_content.pack(fill='both', expand=True, padx=40, pady=12)
    
    tk.Label(status_content, text="© 2024 ERP-System", 
             font=('Segoe UI', 10), 
             bg='#1E293B', fg='#64748B').pack(side='left')
    
    tk.Label(status_content, text="Version 1.0.0 • All Systems Operational", 
             font=('Segoe UI', 10), 
             bg='#1E293B', fg='#64748B').pack(side='right')

    menu_win.mainloop()

# ================= EXPIRY NOTIFICATION & REMINDER UI =================
def reminder_ui():
    reminder_win = tk.Tk()
    reminder_win.title("ERP-System - Expiry Notifications & Reminders")
    reminder_win.configure(bg=COLORS['gray_100'])
    reminder_win.state('zoomed')  # Fullscreen on Windows
    
    # Header
    header = tk.Frame(reminder_win, bg=COLORS['warning'], height=80)
    header.pack(fill='x')
    header.pack_propagate(False)
    
    header_content = tk.Frame(header, bg=COLORS['warning'])
    header_content.pack(fill='both', expand=True, padx=30, pady=15)
    
    tk.Label(header_content, text="📧 Expiry Notifications & Reminders", 
             font=('Segoe UI', 20, 'bold'), 
             bg=COLORS['warning'], fg='white').pack(side='left')
    
    back_btn = tk.Button(header_content, text="← Back to Menu", 
                        command=lambda: [reminder_win.destroy(), menu_page()],
                        bg='white', fg=COLORS['warning'],
                        font=('Segoe UI', 11, 'bold'),
                        relief='flat', bd=0, cursor='hand2',
                        padx=20, pady=10)
    back_btn.pack(side='right')
    
    # Main content
    content = tk.Frame(reminder_win, bg=COLORS['gray_100'])
    content.pack(fill='both', expand=True, padx=30, pady=30)
    
    # Top section - Notification summary
    summary_frame = tk.Frame(content, bg='white', padx=30, pady=25)
    summary_frame.pack(fill='x', pady=(0, 20))
    
    tk.Label(summary_frame, text="📊 Notification Summary", 
             font=('Segoe UI', 18, 'bold'),
             bg='white', fg=COLORS['gray_800']).pack(anchor='w', pady=(0, 20))
    
    # Get notification counts
    def get_notification_counts():
        try:
            con = db()
            cur = con.cursor()
            today = datetime.today().date()
            
            # Expired today
            cur.execute("SELECT COUNT(*) FROM students WHERE expiry_date = ?", 
                       (today.strftime("%Y-%m-%d"),))
            expired_today = cur.fetchone()[0]
            
            # Expiring in 3 days
            three_days = (today + timedelta(days=3)).strftime("%Y-%m-%d")
            cur.execute("SELECT COUNT(*) FROM students WHERE expiry_date BETWEEN ? AND ?", 
                       (today.strftime("%Y-%m-%d"), three_days))
            expiring_3days = cur.fetchone()[0]
            
            # Expiring in 7 days
            seven_days = (today + timedelta(days=7)).strftime("%Y-%m-%d")
            cur.execute("SELECT COUNT(*) FROM students WHERE expiry_date BETWEEN ? AND ?", 
                       (today.strftime("%Y-%m-%d"), seven_days))
            expiring_7days = cur.fetchone()[0]
            
            # Already expired
            cur.execute("SELECT COUNT(*) FROM students WHERE expiry_date < ?", 
                       (today.strftime("%Y-%m-%d"),))
            already_expired = cur.fetchone()[0]
            
            con.close()
            return {
                'expired_today': expired_today,
                'expiring_3days': expiring_3days,
                'expiring_7days': expiring_7days,
                'already_expired': already_expired
            }
        except:
            return {
                'expired_today': 0,
                'expiring_3days': 0,
                'expiring_7days': 0,
                'already_expired': 0
            }
    
    counts = get_notification_counts()
    
    # Summary cards
    summary_cards_frame = tk.Frame(summary_frame, bg='white')
    summary_cards_frame.pack(fill='x', pady=(0, 10))
    
    for i in range(4):
        summary_cards_frame.grid_columnconfigure(i, weight=1, uniform="summary")
    
    summary_data = [
        {'title': 'Expired Today', 'value': counts['expired_today'], 'icon': '🔴', 'color': COLORS['danger']},
        {'title': 'Expiring in 3 Days', 'value': counts['expiring_3days'], 'icon': '🟠', 'color': COLORS['warning']},
        {'title': 'Expiring in 7 Days', 'value': counts['expiring_7days'], 'icon': '🟡', 'color': COLORS['info']},
        {'title': 'Already Expired', 'value': counts['already_expired'], 'icon': '❌', 'color': COLORS['gray_600']}
    ]
    
    for idx, card in enumerate(summary_data):
        card_frame = tk.Frame(summary_cards_frame, bg=COLORS['gray_100'], relief='solid', bd=1)
        card_frame.grid(row=0, column=idx, padx=8, pady=5, sticky='nsew', ipadx=10, ipady=10)
        
        inner = tk.Frame(card_frame, bg=COLORS['gray_100'])
        inner.pack(fill='both', expand=True, padx=15, pady=15)
        
        tk.Label(inner, text=card['icon'], 
                font=('Segoe UI Emoji', 28), 
                bg=COLORS['gray_100']).pack(pady=(0, 5))
        
        tk.Label(inner, text=str(card['value']), 
                font=('Segoe UI', 22, 'bold'), 
                bg=COLORS['gray_100'], fg=card['color']).pack(pady=(5, 5))
        
        tk.Label(inner, text=card['title'], 
                font=('Segoe UI', 10), 
                bg=COLORS['gray_100'], fg=COLORS['gray_600']).pack(pady=(5, 0))
    
    # Main content area
    main_content = tk.Frame(content, bg=COLORS['gray_100'])
    main_content.pack(fill='both', expand=True, pady=(20, 0))
    
    main_content.grid_columnconfigure(0, weight=2)
    main_content.grid_columnconfigure(1, weight=1)
    main_content.grid_rowconfigure(0, weight=1)
    
    # Left panel - Students list with filters
    left_panel = tk.Frame(main_content, bg='white', padx=20, pady=20)
    left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 15))
    
    tk.Label(left_panel, text="📋 Students Requiring Notification", 
             font=('Segoe UI', 16, 'bold'),
             bg='white', fg=COLORS['gray_800']).pack(anchor='w', pady=(0, 15))
    
    # Filter buttons
    filter_frame = tk.Frame(left_panel, bg='white')
    filter_frame.pack(fill='x', pady=(0, 15))
    
    tk.Label(filter_frame, text="Filter by:", 
             font=('Segoe UI', 11, 'bold'),
             bg='white', fg=COLORS['gray_700']).pack(side='left', padx=(0, 10))
    
    filter_var = tk.StringVar(value="ALL")
    
    filter_options = [
        ("All", "ALL", COLORS['primary']),
        ("Expired Today", "TODAY", COLORS['danger']),
        ("3 Days", "3DAYS", COLORS['warning']),
        ("7 Days", "7DAYS", COLORS['info']),
        ("Already Expired", "EXPIRED", COLORS['gray_600'])
    ]
    
    for text, value, color in filter_options:
        btn = tk.Radiobutton(filter_frame, text=text, variable=filter_var, value=value,
                            font=('Segoe UI', 10), bg='white', 
                            activebackground='white', relief='flat',
                            selectcolor=color, cursor='hand2')
        btn.pack(side='left', padx=5)
    
    # Students table
    table_frame = tk.Frame(left_panel, bg='white')
    table_frame.pack(fill='both', expand=True, pady=(10, 0))
    
    cols = ("Name", "Mobile", "Expiry Date", "Days Left", "Status")
    students_tree = ttk.Treeview(table_frame, columns=cols, show="headings", 
                                height=18, style='Modern.Treeview')
    
    students_tree.column("Name", width=180, anchor="w")
    students_tree.column("Mobile", width=110, anchor="center")
    students_tree.column("Expiry Date", width=100, anchor="center")
    students_tree.column("Days Left", width=80, anchor="center")
    students_tree.column("Status", width=120, anchor="center")
    
    for c in cols:
        students_tree.heading(c, text=c)
    
    scroll = ttk.Scrollbar(table_frame, orient="vertical", command=students_tree.yview)
    students_tree.configure(yscrollcommand=scroll.set)
    
    students_tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    
    # Right panel - Notification actions
    right_panel = tk.Frame(main_content, bg='white', padx=25, pady=25)
    right_panel.grid(row=0, column=1, sticky='nsew', padx=(15, 0))
    
    tk.Label(right_panel, text="📱 Notification Actions", 
             font=('Segoe UI', 16, 'bold'),
             bg='white', fg=COLORS['gray_800']).pack(anchor='w', pady=(0, 20))
    
    # Selected student info
    selected_frame = tk.Frame(right_panel, bg=COLORS['gray_100'], relief='solid', bd=1)
    selected_frame.pack(fill='x', pady=(0, 20))
    
    selected_inner = tk.Frame(selected_frame, bg=COLORS['gray_100'])
    selected_inner.pack(fill='both', expand=True, padx=15, pady=15)
    
    tk.Label(selected_inner, text="Selected Student", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['gray_100'], fg=COLORS['gray_700']).pack(anchor='w')
    
    selected_info = tk.Label(selected_inner, text="No student selected\n\nSelect a student from the list", 
                            font=('Segoe UI', 11),
                            bg=COLORS['gray_100'], fg=COLORS['gray_600'],
                            justify='left')
    selected_info.pack(anchor='w', pady=(10, 0))
    
    # Notification template
    template_frame = tk.Frame(right_panel, bg='white')
    template_frame.pack(fill='both', expand=True, pady=(0, 20))
    
    tk.Label(template_frame, text="📝 Notification Message", 
             font=('Segoe UI', 12, 'bold'),
             bg='white', fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 10))
    
    message_text = tk.Text(template_frame, font=('Segoe UI', 10), height=12,
                          relief='solid', bd=1, bg='white', wrap='word')
    message_text.pack(fill='both', expand=True)
    message_text.insert("1.0", "Dear [Student Name],\n\n"
                              "This is a reminder that your library membership is expiring soon.\n\n"
                              "Expiry Date: [Expiry Date]\n"
                              "Days Remaining: [Days Left]\n\n"
                              "Please renew your membership to continue enjoying our services.\n\n"
                              "Contact: [Mobile Number]\n\n"
                              "Thank you,\nERP-System Team")
    
    # Action buttons
    action_frame = tk.Frame(right_panel, bg='white')
    action_frame.pack(fill='x')
    
    # Store current selection
    current_selection = {'student': None}
    
    def load_students(filter_type="ALL"):
        try:
            con = db()
            cur = con.cursor()
            today = datetime.today().date()
            
            if filter_type == "TODAY":
                cur.execute("""
                    SELECT name, mobile, expiry_date 
                    FROM students 
                    WHERE expiry_date = ?
                    ORDER BY expiry_date
                """, (today.strftime("%Y-%m-%d"),))
            elif filter_type == "3DAYS":
                three_days = (today + timedelta(days=3)).strftime("%Y-%m-%d")
                cur.execute("""
                    SELECT name, mobile, expiry_date 
                    FROM students 
                    WHERE expiry_date BETWEEN ? AND ?
                    ORDER BY expiry_date
                """, (today.strftime("%Y-%m-%d"), three_days))
            elif filter_type == "7DAYS":
                seven_days = (today + timedelta(days=7)).strftime("%Y-%m-%d")
                cur.execute("""
                    SELECT name, mobile, expiry_date 
                    FROM students 
                    WHERE expiry_date BETWEEN ? AND ?
                    ORDER BY expiry_date
                """, (today.strftime("%Y-%m-%d"), seven_days))
            elif filter_type == "EXPIRED":
                cur.execute("""
                    SELECT name, mobile, expiry_date 
                    FROM students 
                    WHERE expiry_date < ?
                    ORDER BY expiry_date DESC
                """, (today.strftime("%Y-%m-%d"),))
            else:  # ALL
                seven_days = (today + timedelta(days=7)).strftime("%Y-%m-%d")
                cur.execute("""
                    SELECT name, mobile, expiry_date 
                    FROM students 
                    WHERE expiry_date <= ?
                    ORDER BY expiry_date
                """, (seven_days,))
            
            rows = cur.fetchall()
            con.close()
            
            students_tree.delete(*students_tree.get_children())
            
            for row in rows:
                exp_date = datetime.strptime(row[2], "%Y-%m-%d").date()
                days_left = (exp_date - today).days
                exp_str = exp_date.strftime("%b %d, %Y")
                
                if days_left < 0:
                    status = "🔴 Expired"
                    days_str = f"{abs(days_left)} ago"
                elif days_left == 0:
                    status = "🔴 Today"
                    days_str = "0"
                elif days_left <= 3:
                    status = "🟠 Critical"
                    days_str = str(days_left)
                elif days_left <= 7:
                    status = "🟡 Warning"
                    days_str = str(days_left)
                else:
                    status = "🟢 Active"
                    days_str = str(days_left)
                
                students_tree.insert("", "end", values=(row[0], row[1], exp_str, days_str, status))
        except Exception as e:
            messagebox.showerror("Error", f"Could not load students:\n{str(e)}")
    
    def on_student_select(event):
        selection = students_tree.focus()
        if not selection:
            return
        
        values = students_tree.item(selection)["values"]
        current_selection['student'] = {
            'name': values[0],
            'mobile': values[1],
            'expiry': values[2],
            'days_left': values[3]
        }
        
        selected_info.config(
            text=f"Name: {values[0]}\nMobile: {values[1]}\nExpiry: {values[2]}\nDays Left: {values[3]}"
        )
        
        # Update message template
        message = message_text.get("1.0", tk.END)
        message = message.replace("[Student Name]", values[0])
        message = message.replace("[Expiry Date]", values[2])
        message = message.replace("[Days Left]", str(values[3]))
        message = message.replace("[Mobile Number]", values[1])
        message_text.delete("1.0", tk.END)
        message_text.insert("1.0", message)
    
    def copy_message():
        if not current_selection['student']:
            messagebox.showwarning("No Selection", "Please select a student first!")
            return
        
        message = message_text.get("1.0", tk.END).strip()
        try:
            reminder_win.clipboard_clear()
            reminder_win.clipboard_append(message)
            reminder_win.update()  # Force clipboard update
            messagebox.showinfo("✅ Copied", 
                              f"Message copied to clipboard!\n\n"
                              f"You can now paste it in WhatsApp, SMS, or Email app.\n\n"
                              f"Student: {current_selection['student']['name']}\n"
                              f"Mobile: {current_selection['student']['mobile']}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not copy to clipboard:\n{str(e)}")
    
    def copy_all_contacts():
        items = students_tree.get_children()
        if not items:
            messagebox.showwarning("No Data", "No students to copy!")
            return
        
        contacts = []
        for item in items:
            values = students_tree.item(item)["values"]
            contacts.append(f"{values[0]}: {values[1]}")
        
        contact_text = "\n".join(contacts)
        try:
            reminder_win.clipboard_clear()
            reminder_win.clipboard_append(contact_text)
            reminder_win.update()  # Force clipboard update
            messagebox.showinfo("✅ Copied", 
                              f"All {len(contacts)} contacts copied to clipboard!\n\n"
                              f"You can now paste them in your messaging app.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not copy to clipboard:\n{str(e)}")
        reminder_win.clipboard_append(contact_text)
        messagebox.showinfo("✅ Copied", 
                          f"All {len(contacts)} contacts copied to clipboard!\n\n"
                          f"You can now paste them in your messaging app.")
    
    def export_notifications():
        items = students_tree.get_children()
        if not items:
            messagebox.showwarning("No Data", "No students to export!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Notification List",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"Expiry_Notifications_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Name', 'Mobile', 'Expiry Date', 'Days Left', 'Status'])
                    
                    for item in items:
                        values = students_tree.item(item)["values"]
                        writer.writerow(values)
                
                messagebox.showinfo("✅ Success", f"Notification list exported!\n\nFile: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not export:\n{str(e)}")
    
    copy_btn = tk.Button(action_frame, text="📋 Copy Message", 
                        command=copy_message,
                        bg=COLORS['info'], fg='white',
                        font=('Segoe UI', 11, 'bold'),
                        relief='flat', cursor='hand2',
                        padx=20, pady=12)
    copy_btn.pack(fill='x', pady=(0, 10))
    
    copy_all_btn = tk.Button(action_frame, text="📱 Copy All Contacts", 
                            command=copy_all_contacts,
                            bg=COLORS['secondary'], fg='white',
                            font=('Segoe UI', 11, 'bold'),
                            relief='flat', cursor='hand2',
                            padx=20, pady=12)
    copy_all_btn.pack(fill='x', pady=(0, 10))
    
    export_btn = tk.Button(action_frame, text="📊 Export List", 
                          command=export_notifications,
                          bg=COLORS['primary'], fg='white',
                          font=('Segoe UI', 11, 'bold'),
                          relief='flat', cursor='hand2',
                          padx=20, pady=12)
    export_btn.pack(fill='x')
    
    # Bind events
    students_tree.bind("<<TreeviewSelect>>", on_student_select)
    filter_var.trace('w', lambda *args: load_students(filter_var.get()))
    
    # Load initial data
    load_students("ALL")
    
    reminder_win.mainloop()

# ================= DASHBOARD & ANALYTICS UI =================
def dashboard_ui():
    dash_win = tk.Tk()
    dash_win.title("ERP-System - Dashboard & Analytics")
    dash_win.configure(bg=COLORS['gray_100'])
    dash_win.state('zoomed')  # Fullscreen on Windows
    
    # Header
    header = tk.Frame(dash_win, bg=COLORS['secondary'], height=80)
    header.pack(fill='x')
    header.pack_propagate(False)
    
    header_content = tk.Frame(header, bg=COLORS['secondary'])
    header_content.pack(fill='both', expand=True, padx=30, pady=15)
    
    tk.Label(header_content, text="📊 Dashboard & Analytics", 
             font=('Segoe UI', 20, 'bold'), 
             bg=COLORS['secondary'], fg='white').pack(side='left')
    
    current_time = datetime.now().strftime('%B %d, %Y • %I:%M %p')
    tk.Label(header_content, text=f"🕐 {current_time}", 
             font=('Segoe UI', 12), 
             bg=COLORS['secondary'], fg='white').pack(side='left', padx=(30, 0))
    
    back_btn = tk.Button(header_content, text="← Back to Menu", 
                        command=lambda: [dash_win.destroy(), menu_page()],
                        bg='white', fg=COLORS['secondary'],
                        font=('Segoe UI', 11, 'bold'),
                        relief='flat', bd=0, cursor='hand2',
                        padx=20, pady=10)
    back_btn.pack(side='right')
    
    # Main content
    content = tk.Frame(dash_win, bg=COLORS['gray_100'])
    content.pack(fill='both', expand=True, padx=30, pady=30)
    
    # Get statistics from database
    def get_stats():
        try:
            con = db()
            cur = con.cursor()
            
            # Total students
            cur.execute("SELECT COUNT(*) FROM students")
            total_students = cur.fetchone()[0]
            
            # Active students
            today = datetime.today().strftime("%Y-%m-%d")
            cur.execute("SELECT COUNT(*) FROM students WHERE expiry_date >= ?", (today,))
            active_students = cur.fetchone()[0]
            
            # Expired students
            cur.execute("SELECT COUNT(*) FROM students WHERE expiry_date < ?", (today,))
            expired_students = cur.fetchone()[0]
            
            # Expiring soon (within 7 days)
            week_end = (datetime.today() + timedelta(days=7)).strftime("%Y-%m-%d")
            cur.execute("SELECT COUNT(*) FROM students WHERE expiry_date BETWEEN ? AND ?", 
                       (today, week_end))
            expiring_soon = cur.fetchone()[0]
            
            # New registrations this month
            month_start = datetime.today().replace(day=1).strftime("%Y-%m-%d")
            cur.execute("SELECT COUNT(*) FROM students WHERE admission_date >= ?", (month_start,))
            new_this_month = cur.fetchone()[0]
            
            # Total fees collected
            cur.execute("SELECT SUM(fees_paid) FROM students")
            total_fees = cur.fetchone()[0] or 0
            
            con.close()
            
            return {
                'total': total_students,
                'active': active_students,
                'expired': expired_students,
                'expiring_soon': expiring_soon,
                'new_month': new_this_month,
                'total_fees': total_fees
            }
        except Exception as e:
            messagebox.showerror("Error", f"Could not load statistics:\n{str(e)}")
            return {
                'total': 0, 'active': 0, 'expired': 0, 
                'expiring_soon': 0, 'new_month': 0, 'total_fees': 0
            }
    
    stats = get_stats()
    
    # Statistics cards container
    stats_container = tk.Frame(content, bg=COLORS['gray_100'])
    stats_container.pack(fill='x', pady=(0, 30))
    
    # Configure grid
    for i in range(6):
        stats_container.grid_columnconfigure(i, weight=1, uniform="stats")
    
    # Statistics cards data
    stat_cards = [
        {
            'title': 'Total Students',
            'value': stats['total'],
            'icon': '👥',
            'color': COLORS['primary'],
            'col': 0
        },
        {
            'title': 'Active Members',
            'value': stats['active'],
            'icon': '✅',
            'color': COLORS['success'],
            'col': 1
        },
        {
            'title': 'Expired',
            'value': stats['expired'],
            'icon': '❌',
            'color': COLORS['danger'],
            'col': 2
        },
        {
            'title': 'Expiring Soon',
            'value': stats['expiring_soon'],
            'icon': '⚠️',
            'color': COLORS['warning'],
            'col': 3
        },
        {
            'title': 'New This Month',
            'value': stats['new_month'],
            'icon': '🆕',
            'color': COLORS['info'],
            'col': 4
        },
        {
            'title': 'Total Fees',
            'value': f"₹{stats['total_fees']:.2f}",
            'icon': '💰',
            'color': COLORS['secondary'],
            'col': 5
        }
    ]
    
    # Create stat cards
    for card in stat_cards:
        card_frame = tk.Frame(stats_container, bg='white', relief='solid', bd=1)
        card_frame.grid(row=0, column=card['col'], padx=10, pady=10, sticky='nsew')
        
        inner = tk.Frame(card_frame, bg='white')
        inner.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Icon
        tk.Label(inner, text=card['icon'], 
                font=('Segoe UI Emoji', 32), 
                bg='white').pack()
        
        # Value
        tk.Label(inner, text=str(card['value']), 
                font=('Segoe UI', 24, 'bold'), 
                bg='white', fg=card['color']).pack(pady=(5, 0))
        
        # Title
        tk.Label(inner, text=card['title'], 
                font=('Segoe UI', 11), 
                bg='white', fg=COLORS['gray_600']).pack()
    
    # Charts and details section
    details_container = tk.Frame(content, bg=COLORS['gray_100'])
    details_container.pack(fill='both', expand=True)
    
    details_container.grid_columnconfigure(0, weight=1)
    details_container.grid_columnconfigure(1, weight=1)
    details_container.grid_rowconfigure(0, weight=1)
    
    # Left panel - Recent registrations
    left_detail = tk.Frame(details_container, bg='white', padx=20, pady=20)
    left_detail.grid(row=0, column=0, sticky='nsew', padx=(0, 15))
    
    tk.Label(left_detail, text="📋 Recent Registrations", 
             font=('Segoe UI', 16, 'bold'),
             bg='white', fg=COLORS['gray_800']).pack(anchor='w', pady=(0, 15))
    
    # Recent registrations table
    recent_frame = tk.Frame(left_detail, bg='white')
    recent_frame.pack(fill='both', expand=True)
    
    recent_cols = ("Name", "Mobile", "Date", "Status")
    recent_tree = ttk.Treeview(recent_frame, columns=recent_cols, show="headings", 
                              height=15, style='Modern.Treeview')
    
    recent_tree.column("Name", width=150, anchor="w")
    recent_tree.column("Mobile", width=100, anchor="center")
    recent_tree.column("Date", width=100, anchor="center")
    recent_tree.column("Status", width=100, anchor="center")
    
    for c in recent_cols:
        recent_tree.heading(c, text=c)
    
    recent_scroll = ttk.Scrollbar(recent_frame, orient="vertical", command=recent_tree.yview)
    recent_tree.configure(yscrollcommand=recent_scroll.set)
    
    recent_tree.pack(side="left", fill="both", expand=True)
    recent_scroll.pack(side="right", fill="y")
    
    # Load recent registrations
    try:
        con = db()
        cur = con.cursor()
        cur.execute("""
            SELECT name, mobile, admission_date, expiry_date 
            FROM students 
            ORDER BY admission_date DESC 
            LIMIT 20
        """)
        rows = cur.fetchall()
        con.close()
        
        today = datetime.today().strftime("%Y-%m-%d")
        for row in rows:
            adm_date = datetime.strptime(row[2], "%Y-%m-%d").strftime("%b %d")
            status = "🟢 Active" if row[3] >= today else "🔴 Expired"
            recent_tree.insert("", "end", values=(row[0], row[1], adm_date, status))
    except:
        pass
    
    # Right panel - Expiring soon
    right_detail = tk.Frame(details_container, bg='white', padx=20, pady=20)
    right_detail.grid(row=0, column=1, sticky='nsew', padx=(15, 0))
    
    tk.Label(right_detail, text="⚠️ Expiring Soon (Next 7 Days)", 
             font=('Segoe UI', 16, 'bold'),
             bg='white', fg=COLORS['gray_800']).pack(anchor='w', pady=(0, 15))
    
    # Expiring soon table
    expiring_frame = tk.Frame(right_detail, bg='white')
    expiring_frame.pack(fill='both', expand=True)
    
    expiring_cols = ("Name", "Mobile", "Expiry", "Days Left")
    expiring_tree = ttk.Treeview(expiring_frame, columns=expiring_cols, show="headings", 
                                height=15, style='Modern.Treeview')
    
    expiring_tree.column("Name", width=150, anchor="w")
    expiring_tree.column("Mobile", width=100, anchor="center")
    expiring_tree.column("Expiry", width=100, anchor="center")
    expiring_tree.column("Days Left", width=80, anchor="center")
    
    for c in expiring_cols:
        expiring_tree.heading(c, text=c)
    
    expiring_scroll = ttk.Scrollbar(expiring_frame, orient="vertical", command=expiring_tree.yview)
    expiring_tree.configure(yscrollcommand=expiring_scroll.set)
    
    expiring_tree.pack(side="left", fill="both", expand=True)
    expiring_scroll.pack(side="right", fill="y")
    
    # Load expiring soon
    try:
        con = db()
        cur = con.cursor()
        today = datetime.today().date()
        week_end = today + timedelta(days=7)
        cur.execute("""
            SELECT name, mobile, expiry_date 
            FROM students 
            WHERE expiry_date BETWEEN ? AND ?
            ORDER BY expiry_date ASC
        """, (today.strftime("%Y-%m-%d"), week_end.strftime("%Y-%m-%d")))
        rows = cur.fetchall()
        con.close()
        
        for row in rows:
            exp_date = datetime.strptime(row[2], "%Y-%m-%d")
            days_left = (exp_date.date() - today).days
            exp_str = exp_date.strftime("%b %d")
            expiring_tree.insert("", "end", values=(row[0], row[1], exp_str, f"{days_left} days"))
    except:
        pass
    
    # Action buttons at bottom
    action_frame = tk.Frame(content, bg=COLORS['gray_100'])
    action_frame.pack(fill='x', pady=(20, 0))
    
    btn_container = tk.Frame(action_frame, bg=COLORS['gray_100'])
    btn_container.pack()
    
    refresh_btn = tk.Button(btn_container, text="🔄 Refresh Data", 
                           command=lambda: [dash_win.destroy(), dashboard_ui()],
                           bg=COLORS['info'], fg='white',
                           font=('Segoe UI', 12, 'bold'),
                           relief='flat', cursor='hand2',
                           padx=30, pady=15)
    refresh_btn.pack(side='left', padx=10)
    
    export_btn = tk.Button(btn_container, text="📊 Export Report", 
                          command=lambda: export_dashboard_report(stats),
                          bg=COLORS['primary'], fg='white',
                          font=('Segoe UI', 12, 'bold'),
                          relief='flat', cursor='hand2',
                          padx=30, pady=15)
    export_btn.pack(side='left', padx=10)
    
    dash_win.mainloop()

def export_dashboard_report(stats):
    """Export dashboard statistics to CSV"""
    try:
        file_path = filedialog.asksaveasfilename(
            title="Save Dashboard Report",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"Dashboard_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if file_path:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(['ERP-System - Dashboard Report'])
                writer.writerow([f'Generated: {datetime.now().strftime("%B %d, %Y %I:%M %p")}'])
                writer.writerow([])
                
                # Write statistics
                writer.writerow(['Metric', 'Value'])
                writer.writerow(['Total Students', stats['total']])
                writer.writerow(['Active Members', stats['active']])
                writer.writerow(['Expired Members', stats['expired']])
                writer.writerow(['Expiring Soon (7 days)', stats['expiring_soon']])
                writer.writerow(['New This Month', stats['new_month']])
                writer.writerow(['Total Fees Collected', f"₹{stats['total_fees']:.2f}"])
                
            messagebox.showinfo("Success", f"Dashboard report exported successfully!\n\nFile: {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Could not export report:\n{str(e)}")

# ================= QR & ID GENERATE UI =================
def qr_id_ui():
    qr_win = tk.Tk()
    qr_win.title("ERP-System - QR & ID Card Generator")
    qr_win.configure(bg=COLORS['gray_100'])
    qr_win.state('zoomed')  # Fullscreen on Windows
    
    # Header
    header = tk.Frame(qr_win, bg=COLORS['info'], height=80)
    header.pack(fill='x')
    header.pack_propagate(False)
    
    header_content = tk.Frame(header, bg=COLORS['info'])
    header_content.pack(fill='both', expand=True, padx=30, pady=15)
    
    tk.Label(header_content, text="🎫 QR & ID Card Generator", 
             font=('Segoe UI', 20, 'bold'), 
             bg=COLORS['info'], fg='white').pack(side='left')
    
    back_btn = tk.Button(header_content, text="← Back to Menu", 
                        command=lambda: [qr_win.destroy(), menu_page()],
                        bg='white', fg=COLORS['info'],
                        font=('Segoe UI', 11, 'bold'),
                        relief='flat', bd=0, cursor='hand2',
                        padx=20, pady=10)
    back_btn.pack(side='right')
    
    # Main content
    content = tk.Frame(qr_win, bg=COLORS['gray_100'])
    content.pack(fill='both', expand=True, padx=30, pady=30)
    
    # Left panel - Student list
    left_panel = tk.Frame(content, bg='white', padx=20, pady=20)
    left_panel.pack(side='left', fill='both', expand=True, padx=(0, 15))
    
    tk.Label(left_panel, text="📋 Select Student", 
             font=('Segoe UI', 18, 'bold'),
             bg='white', fg=COLORS['gray_800']).pack(anchor='w', pady=(0, 20))
    
    # Search
    search_frame = tk.Frame(left_panel, bg='white')
    search_frame.pack(fill='x', pady=(0, 15))
    
    search_entry = tk.Entry(search_frame, font=('Segoe UI', 12),
                           relief='solid', bd=1, bg='white')
    search_entry.pack(side='left', fill='x', expand=True, ipady=8, padx=(0, 10))
    
    search_btn = tk.Button(search_frame, text="🔍 Search", 
                          bg=COLORS['info'], fg='white',
                          font=('Segoe UI', 10, 'bold'),
                          relief='flat', cursor='hand2',
                          padx=15, pady=8)
    search_btn.pack(side='left')
    
    # Student table
    table_frame = tk.Frame(left_panel, bg='white')
    table_frame.pack(fill='both', expand=True)
    
    cols = ("ID", "Name", "Mobile", "Expiry")
    student_tree = ttk.Treeview(table_frame, columns=cols, show="headings", 
                               height=20, style='Modern.Treeview')
    
    student_tree.column("ID", width=50, anchor="center")
    student_tree.column("Name", width=200, anchor="w")
    student_tree.column("Mobile", width=120, anchor="center")
    student_tree.column("Expiry", width=100, anchor="center")
    
    for c in cols:
        student_tree.heading(c, text=c)
    
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=student_tree.yview)
    student_tree.configure(yscrollcommand=scrollbar.set)
    
    student_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Right panel - Card preview and generation
    right_panel = tk.Frame(content, bg='white', padx=30, pady=30)
    right_panel.pack(side='right', fill='both', expand=True, padx=(15, 0))
    
    tk.Label(right_panel, text="🎫 ID Card Preview", 
             font=('Segoe UI', 18, 'bold'),
             bg='white', fg=COLORS['gray_800']).pack(anchor='w', pady=(0, 20))
    
    # Preview area
    preview_frame = tk.Frame(right_panel, bg=COLORS['gray_100'], 
                            relief='solid', bd=2, width=600, height=400)
    preview_frame.pack(pady=20)
    preview_frame.pack_propagate(False)
    
    preview_label = tk.Label(preview_frame, 
                            text="Select a student from the list\nto generate their ID card",
                            font=('Segoe UI', 14),
                            bg=COLORS['gray_100'], 
                            fg=COLORS['gray_500'])
    preview_label.pack(expand=True)
    
    # Create ID Card button - directly below preview
    create_card_btn = tk.Button(right_panel, text="🎫 CREATE ID CARD", 
                               command=lambda: create_and_save_card(),
                               bg=COLORS['success'], fg='white',
                               font=('Segoe UI', 14, 'bold'),
                               relief='flat', cursor='hand2',
                               padx=40, pady=18, state='disabled')
    create_card_btn.pack(fill='x', pady=(10, 20))
    
    # Selected student info
    info_frame = tk.Frame(right_panel, bg='white')
    info_frame.pack(fill='x', pady=20)
    
    selected_info = tk.Label(info_frame, text="No student selected", 
                            font=('Segoe UI', 12),
                            bg='white', fg=COLORS['gray_600'])
    selected_info.pack()
    
    # Action buttons
    btn_frame = tk.Frame(right_panel, bg='white')
    btn_frame.pack(pady=20)
    
    generate_btn = tk.Button(btn_frame, text="🎫 Generate ID Card", 
                            command=lambda: generate_card(),
                            bg=COLORS['success'], fg='white',
                            font=('Segoe UI', 12, 'bold'),
                            relief='flat', cursor='hand2',
                            padx=30, pady=15, state='disabled')
    generate_btn.pack(fill='x', pady=(0, 10))
    
    save_btn = tk.Button(btn_frame, text="💾 Save Card to File", 
                        command=lambda: save_card(),
                        bg=COLORS['primary'], fg='white',
                        font=('Segoe UI', 12, 'bold'),
                        relief='flat', cursor='hand2',
                        padx=30, pady=15, state='disabled')
    save_btn.pack(fill='x', pady=(0, 10))
    
    # View QR Code button
    view_qr_btn = tk.Button(btn_frame, text="🔍 View QR Code (Large)", 
                           command=lambda: view_qr_code(),
                           bg=COLORS['info'], fg='white',
                           font=('Segoe UI', 12, 'bold'),
                           relief='flat', cursor='hand2',
                           padx=30, pady=15, state='disabled')
    view_qr_btn.pack(fill='x', pady=(0, 10))
    
    # Additional info label
    info_label = tk.Label(btn_frame, 
                         text="💡 Tip: Select a student, click Generate,\nthen Save to export the card",
                         font=('Segoe UI', 9),
                         bg='white', fg=COLORS['gray_600'],
                         justify='center')
    info_label.pack(pady=(10, 0))
    
    # Variables to store current selection
    current_student = {'data': None, 'card_path': None}
    
    def create_and_save_card():
        """Create ID card and automatically save it to folder"""
        if not current_student['data']:
            messagebox.showwarning("No Selection", "Please select a student first!")
            return
        
        try:
            # Create output directory
            cards_dir = os.path.join(APP_DATA_DIR, "student_cards")
            os.makedirs(cards_dir, exist_ok=True)
            
            # Prepare student data for card generation
            student_info = {
                'id': current_student['data']['id'],
                'name': current_student['data']['name'],
                'mobile': current_student['data']['mobile'],
                'course': current_student['data'].get('course', 'N/A'),
                'expiry': current_student['data']['expiry']
            }
            
            # Generate card filename
            output_path = os.path.join(cards_dir, f"card_{current_student['data']['mobile']}.png")
            
            # Call the generate_student_card function from features_qr
            generate_student_card(
                student_info,
                current_student['data']['photo_path'],
                output_path
            )
            
            current_student['card_path'] = output_path
            
            # Display preview
            card_img = Image.open(output_path)
            card_img = card_img.resize((600, 400), Image.Resampling.LANCZOS)
            card_photo = ImageTk.PhotoImage(card_img)
            preview_label.config(image=card_photo, text="")
            preview_label.image = card_photo
            
            # Enable save button
            save_btn.config(state='normal')
            view_qr_btn.config(state='normal')
            
            # Show success message with file location
            messagebox.showinfo("✅ ID Card Created!", 
                              f"ID card created and saved successfully!\n\n"
                              f"Student: {current_student['data']['name']}\n"
                              f"Mobile: {current_student['data']['mobile']}\n\n"
                              f"📁 Saved to:\n{output_path}\n\n"
                              f"✓ Card is ready to print or share!")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror("❌ Error", 
                               f"Could not create ID card:\n\n{str(e)}\n\n"
                               f"Details:\n{error_details}")
    
    def view_qr_code():
        """Display QR code in a larger window for easy scanning"""
        if not current_student['card_path']:
            messagebox.showwarning("No QR Code", "Please create an ID card first!")
            return
        
        qr_path = current_student['card_path'].replace('.png', '_qr.png')
        
        if not os.path.exists(qr_path):
            messagebox.showerror("Error", "QR code file not found!")
            return
        
        # Create QR viewer window
        qr_viewer = tk.Toplevel(qr_win)
        qr_viewer.title("QR Code Viewer - Scan Me!")
        qr_viewer.configure(bg='white')
        qr_viewer.geometry("500x600")
        qr_viewer.resizable(False, False)
        
        # Center the window
        qr_viewer.update_idletasks()
        x = (qr_viewer.winfo_screenwidth() // 2) - (500 // 2)
        y = (qr_viewer.winfo_screenheight() // 2) - (600 // 2)
        qr_viewer.geometry(f"500x600+{x}+{y}")
        
        # Header
        header = tk.Frame(qr_viewer, bg=COLORS['info'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="📱 Scan QR Code", 
                font=('Segoe UI', 20, 'bold'),
                bg=COLORS['info'], fg='white').pack(expand=True)
        
        # Content
        content = tk.Frame(qr_viewer, bg='white')
        content.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Student info
        tk.Label(content, text=f"Student: {current_student['data']['name']}", 
                font=('Segoe UI', 14, 'bold'),
                bg='white', fg=COLORS['gray_800']).pack(pady=(0, 5))
        
        tk.Label(content, text=f"Mobile: {current_student['data']['mobile']}", 
                font=('Segoe UI', 12),
                bg='white', fg=COLORS['gray_600']).pack(pady=(0, 20))
        
        # Large QR code
        try:
            qr_img = Image.open(qr_path)
            qr_img = qr_img.resize((350, 350), Image.Resampling.LANCZOS)
            qr_photo = ImageTk.PhotoImage(qr_img)
            
            qr_label = tk.Label(content, image=qr_photo, bg='white')
            qr_label.image = qr_photo
            qr_label.pack(pady=20)
        except Exception as e:
            tk.Label(content, text=f"Error loading QR code:\n{str(e)}", 
                    font=('Segoe UI', 12),
                    bg='white', fg='red').pack()
        
        # Instructions
        instructions = tk.Label(content, 
                               text="📱 Use any QR scanner app to scan this code\n"
                                    "The QR code contains student information",
                               font=('Segoe UI', 11),
                               bg='white', fg=COLORS['gray_600'],
                               justify='center')
        instructions.pack(pady=(10, 0))
        
        # Close button
        close_btn = tk.Button(content, text="Close", 
                             command=qr_viewer.destroy,
                             bg=COLORS['gray_600'], fg='white',
                             font=('Segoe UI', 11, 'bold'),
                             relief='flat', cursor='hand2',
                             padx=30, pady=10)
        close_btn.pack(pady=(20, 0))
    
    def load_students():
        try:
            con = db()
            cur = con.cursor()
            cur.execute("SELECT id, name, mobile, expiry_date FROM students ORDER BY name")
            rows = cur.fetchall()
            con.close()
            
            student_tree.delete(*student_tree.get_children())
            for row in rows:
                exp_date = datetime.strptime(row[3], "%Y-%m-%d").strftime("%b %d, %Y")
                student_tree.insert("", "end", values=(row[0], row[1], row[2], exp_date))
        except Exception as e:
            messagebox.showerror("Error", f"Could not load students:\n{str(e)}")
    
    def on_student_select(event):
        selection = student_tree.focus()
        if not selection:
            return
        
        values = student_tree.item(selection)["values"]
        student_id = values[0]
        
        try:
            con = db()
            cur = con.cursor()
            cur.execute("SELECT * FROM students WHERE id=?", (student_id,))
            row = cur.fetchone()
            con.close()
            
            if row:
                current_student['data'] = {
                    'id': row[0],
                    'name': row[4],
                    'mobile': row[5],
                    'course': row[10],
                    'expiry': datetime.strptime(row[15], "%Y-%m-%d").strftime("%B %d, %Y"),
                    'photo_path': row[17] if row[17] and os.path.exists(row[17]) else None
                }
                
                selected_info.config(
                    text=f"Selected: {current_student['data']['name']} | {current_student['data']['mobile']}"
                )
                create_card_btn.config(state='normal')
                generate_btn.config(state='normal')
        except Exception as e:
            messagebox.showerror("Error", f"Could not load student details:\n{str(e)}")
    
    def generate_card():
        if not current_student['data']:
            messagebox.showwarning("No Selection", "Please select a student first!")
            return
        
        try:
            # Create output directory
            cards_dir = os.path.join(APP_DATA_DIR, "student_cards")
            os.makedirs(cards_dir, exist_ok=True)
            
            # Prepare student data for card generation
            student_info = {
                'id': current_student['data']['id'],
                'name': current_student['data']['name'],
                'mobile': current_student['data']['mobile'],
                'course': current_student['data'].get('course', 'N/A'),
                'expiry': current_student['data']['expiry']
            }
            
            # Generate card
            output_path = os.path.join(cards_dir, f"card_{current_student['data']['mobile']}.png")
            
            # Call the generate_student_card function from features_qr
            generate_student_card(
                student_info,
                current_student['data']['photo_path'],
                output_path
            )
            
            current_student['card_path'] = output_path
            
            # Display preview
            card_img = Image.open(output_path)
            card_img = card_img.resize((600, 400), Image.Resampling.LANCZOS)
            card_photo = ImageTk.PhotoImage(card_img)
            preview_label.config(image=card_photo, text="")
            preview_label.image = card_photo
            
            save_btn.config(state='normal')
            view_qr_btn.config(state='normal')
            messagebox.showinfo("✅ Success", 
                              f"ID card generated successfully!\n\n"
                              f"Student: {current_student['data']['name']}\n"
                              f"Saved to: {output_path}")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror("❌ Error", 
                               f"Could not generate card:\n\n{str(e)}\n\n"
                               f"Details:\n{error_details}")
    
    def save_card():
        if not current_student['card_path']:
            messagebox.showwarning("No Card", "Please generate a card first!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save ID Card",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialfile=f"IDCard_{current_student['data']['name'].replace(' ', '_')}.png"
        )
        
        if file_path:
            try:
                copyfile(current_student['card_path'], file_path)
                messagebox.showinfo("✅ Success", f"ID card saved successfully!\n\nLocation: {file_path}")
            except Exception as e:
                messagebox.showerror("❌ Error", f"Could not save card:\n{str(e)}")
    
    def search_students():
        query = search_entry.get().strip()
        if not query:
            load_students()
            return
        
        try:
            con = db()
            cur = con.cursor()
            q = f"%{query}%"
            cur.execute("""
                SELECT id, name, mobile, expiry_date FROM students 
                WHERE name LIKE ? OR mobile LIKE ?
                ORDER BY name
            """, (q, q))
            rows = cur.fetchall()
            con.close()
            
            student_tree.delete(*student_tree.get_children())
            for row in rows:
                exp_date = datetime.strptime(row[3], "%Y-%m-%d").strftime("%b %d, %Y")
                student_tree.insert("", "end", values=(row[0], row[1], row[2], exp_date))
        except Exception as e:
            messagebox.showerror("Error", f"Search failed:\n{str(e)}")
    
    # Bind events
    student_tree.bind("<<TreeviewSelect>>", on_student_select)
    search_btn.config(command=search_students)
    search_entry.bind('<Return>', lambda e: search_students())
    
    # Load students
    load_students()
    
    qr_win.mainloop()

# ================= MAIN UI =================
def main_ui():
    global name_e, mobile_e, address_e, course_e, ad_date, dur, fees_e
    global img_box, tree, preview_label, preview_img, aadhaar_temp
    global first_name_e, middle_name_e, surname_e, dob_e, gender_e
    global parents_mob_e, email_e, aadhaar_e, application_e, expiry_date_e
    global dur_var

    root = tk.Tk()
    root.title("ERP-System - Student Management Dashboard")
    root.configure(bg=COLORS['gray_100'])
    root.state('zoomed')  # Fullscreen on Windows

    # Configure ttk styles
    style = ttk.Style()
    style.theme_use('clam')
    
    style.configure('Modern.Treeview', 
                   background=COLORS['white'], 
                   foreground=COLORS['gray_700'],
                   rowheight=35, 
                   fieldbackground=COLORS['white'])
    
    style.configure('Modern.Treeview.Heading', 
                   background=COLORS['primary'], 
                   foreground='white', 
                   font=('Segoe UI', 11, 'bold'))

    # Main container
    main_container = tk.Frame(root, bg=COLORS['gray_100'])
    main_container.pack(fill='both', expand=True)

    # Navigation bar
    nav_bar = tk.Frame(main_container, bg=COLORS['primary'], height=80)
    nav_bar.pack(fill='x')
    nav_bar.pack_propagate(False)

    nav_content = tk.Frame(nav_bar, bg=COLORS['primary'])
    nav_content.pack(fill='both', expand=True, padx=30, pady=15)

    # Left side - Logo
    tk.Label(nav_content, text="📚 ERP-System", 
             font=('Segoe UI', 20, 'bold'), 
             bg=COLORS['primary'], fg='white').pack(side='left')

    # Right side - Back button and user info
    right_nav = tk.Frame(nav_content, bg=COLORS['primary'])
    right_nav.pack(side='right')
    
    # Back to Main button
    back_btn = tk.Button(right_nav, text="← Back to Main", 
                        command=lambda: [root.destroy(), menu_page()],
                        bg='white', fg=COLORS['primary'],
                        font=('Segoe UI', 11, 'bold'),
                        relief='flat', bd=0, cursor='hand2',
                        padx=20, pady=8)
    back_btn.pack(side='left', padx=(0, 20))
    
    # User info
    current_time = datetime.now().strftime('%B %d, %Y • %I:%M %p')
    tk.Label(right_nav, text=f"👤 Admin • {current_time}", 
             font=('Segoe UI', 11), 
             bg=COLORS['primary'], fg='white').pack(side='left')

    # Content area
    content_area = tk.Frame(main_container, bg=COLORS['gray_100'])
    content_area.pack(fill='both', expand=True, padx=20, pady=20)

    # Create panels with registration form taking maximum width
    panels_container = tk.Frame(content_area, bg=COLORS['gray_100'])
    panels_container.pack(fill='both', expand=True)
    
    # Give nearly full width to registration form
    panels_container.grid_columnconfigure(0, weight=9)  # Left column (form) - 90% width
    panels_container.grid_columnconfigure(1, weight=1)  # Right column (records) - 10% width
    panels_container.grid_rowconfigure(0, weight=1)
    
    # Left panel (form) - 90% width with maximum padding
    left_panel = tk.Frame(panels_container, bg=COLORS['white'], padx=50, pady=45)
    left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 25))
    
    # Right panel (records) - 10% width, very compact
    right_panel = tk.Frame(panels_container, bg=COLORS['white'], padx=10, pady=15)
    right_panel.grid(row=0, column=1, sticky='nsew', padx=(25, 0))

    # ================= REGISTRATION FORM =================
    
    # Form header
    form_header = tk.Frame(left_panel, bg=COLORS['primary'], height=60)
    form_header.pack(fill='x', pady=(0, 30))
    form_header.pack_propagate(False)

    tk.Label(form_header, text="REGISTRATION FORM",
             font=('Segoe UI', 16, 'bold'),
             bg=COLORS['primary'], fg='white').pack(expand=True)

    # Form content container - Working scrollable registration form
    canvas = tk.Canvas(left_panel, bg=COLORS['white'], highlightthickness=0)
    scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
    form_container = tk.Frame(canvas, bg=COLORS['white'])
    
    # Configure canvas window properly
    canvas_window = canvas.create_window((0, 0), window=form_container, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Update scroll region when form content changes
    def configure_scroll_region(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        # Also update canvas window width to match canvas width
        canvas_width = canvas.winfo_width()
        if canvas_width > 1:
            canvas.itemconfig(canvas_window, width=canvas_width)
    
    # Bind configuration events
    form_container.bind("<Configure>", configure_scroll_region)
    canvas.bind("<Configure>", configure_scroll_region)
    
    # Pack canvas and scrollbar with increased spacing
    canvas.pack(side="left", fill="both", expand=True, padx=(0, 10))
    scrollbar.pack(side="right", fill="y", padx=(10, 10), pady=(10, 10))
    
    # Working mousewheel scrolling
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    # Bind mousewheel events properly
    def bind_mousewheel(event):
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        # For Linux compatibility
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
    
    def unbind_mousewheel(event):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")
    
    # Bind when mouse enters/leaves canvas
    canvas.bind('<Enter>', bind_mousewheel)
    canvas.bind('<Leave>', unbind_mousewheel)
    
    # Also bind to form container for better coverage
    form_container.bind('<Enter>', bind_mousewheel)
    form_container.bind('<Leave>', unbind_mousewheel)
    
    # Initialize scroll region immediately
    configure_scroll_region()

    # APPLICATION FOR SECTION
    app_section = tk.Frame(form_container, bg=COLORS['white'])
    app_section.pack(fill='x', pady=(0, 25))

    # Application for and Photo row
    app_photo_row = tk.Frame(app_section, bg=COLORS['white'])
    app_photo_row.pack(fill='x')

    # Left side - Application for (65% width)
    app_left = tk.Frame(app_photo_row, bg=COLORS['white'])
    app_left.pack(side='left', fill='both', expand=True, padx=(0, 25))

    tk.Label(app_left, text="APPLICATION FOR :", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 8))

    application_e = tk.Entry(app_left, font=('Segoe UI', 12),
                            relief='solid', bd=1, bg=COLORS['white'],
                            highlightthickness=2, highlightcolor=COLORS['primary'])
    application_e.pack(fill='x', ipady=12)

    # Right side - Photo (35% width)
    photo_frame = tk.Frame(app_photo_row, bg=COLORS['white'])
    photo_frame.pack(side='right')

    photo_container = tk.Frame(photo_frame, bg=COLORS['gray_100'], 
                              relief='solid', bd=2, width=160, height=130)
    photo_container.pack()
    photo_container.pack_propagate(False)

    img_box = tk.Label(photo_container, text="PHOTO\n\nClick to\nUpload",
                       font=('Segoe UI', 11, 'bold'),
                       bg=COLORS['gray_100'], 
                       fg=COLORS['gray_600'], 
                       cursor='hand2',
                       justify='center')
    img_box.pack(fill='both', expand=True)

    def upload_img():
        global aadhaar_temp, preview_img
        f = filedialog.askopenfilename(
            title="Select Student Photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff")])
        if not f:
            return
        aadhaar_temp = f
        try:
            img = Image.open(f)
            img = img.resize((156, 126), Image.Resampling.LANCZOS)
            preview_img = ImageTk.PhotoImage(img)
            img_box.config(image=preview_img, text="")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image: {str(e)}")

    img_box.bind("<Button-1>", lambda e: upload_img())

    # SUBSCRIPTION DURATION
    duration_section = tk.Frame(form_container, bg=COLORS['white'])
    duration_section.pack(fill='x', pady=(0, 25))

    tk.Label(duration_section, text="SUBSCRIPTION DURATION :", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 12))

    dur_check_frame = tk.Frame(duration_section, bg=COLORS['white'])
    dur_check_frame.pack(fill='x')

    dur_var = tk.StringVar(value="1")
    
    dur_1_cb = tk.Checkbutton(dur_check_frame, text="☐ 1 Month", variable=dur_var, onvalue="1",
                             font=('Segoe UI', 12), bg=COLORS['white'], 
                             activebackground=COLORS['white'], relief='flat')
    dur_1_cb.pack(side='left', padx=(0, 60))

    dur_3_cb = tk.Checkbutton(dur_check_frame, text="☐ 3 Months", variable=dur_var, onvalue="3",
                             font=('Segoe UI', 12), bg=COLORS['white'],
                             activebackground=COLORS['white'], relief='flat')
    dur_3_cb.pack(side='left')

    # PERSONAL DETAILS HEADER
    personal_header = tk.Frame(form_container, bg=COLORS['primary'], height=55)
    personal_header.pack(fill='x', pady=(15, 25))
    personal_header.pack_propagate(False)

    tk.Label(personal_header, text="PERSONAL DETAILS",
             font=('Segoe UI', 15, 'bold'),
             bg=COLORS['primary'], fg='white').pack(expand=True)

    # FULL NAME SECTION
    name_section = tk.Frame(form_container, bg=COLORS['white'])
    name_section.pack(fill='x', pady=(0, 20))

    tk.Label(name_section, text="FULL NAME", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 10))

    # Name fields row
    name_fields = tk.Frame(name_section, bg=COLORS['white'])
    name_fields.pack(fill='x')

    # First name
    first_name_frame = tk.Frame(name_fields, bg=COLORS['white'])
    first_name_frame.pack(side='left', fill='x', expand=True, padx=(0, 12))
    
    tk.Label(first_name_frame, text="FIRST NAME", 
             font=('Segoe UI', 10), bg=COLORS['white'], fg=COLORS['gray_500']).pack(anchor='w', pady=(0, 6))
    
    first_name_e = tk.Entry(first_name_frame, font=('Segoe UI', 11),
                           relief='solid', bd=1, bg=COLORS['white'],
                           highlightthickness=2, highlightcolor=COLORS['primary'])
    first_name_e.pack(fill='x', ipady=10)

    # Middle name
    middle_name_frame = tk.Frame(name_fields, bg=COLORS['white'])
    middle_name_frame.pack(side='left', fill='x', expand=True, padx=12)
    
    tk.Label(middle_name_frame, text="MIDDLE NAME", 
             font=('Segoe UI', 10), bg=COLORS['white'], fg=COLORS['gray_500']).pack(anchor='w', pady=(0, 6))
    
    middle_name_e = tk.Entry(middle_name_frame, font=('Segoe UI', 11),
                            relief='solid', bd=1, bg=COLORS['white'],
                            highlightthickness=2, highlightcolor=COLORS['primary'])
    middle_name_e.pack(fill='x', ipady=10)

    # Surname
    surname_frame = tk.Frame(name_fields, bg=COLORS['white'])
    surname_frame.pack(side='left', fill='x', expand=True, padx=(12, 0))
    
    tk.Label(surname_frame, text="SURNAME", 
             font=('Segoe UI', 10), bg=COLORS['white'], fg=COLORS['gray_500']).pack(anchor='w', pady=(0, 6))
    
    surname_e = tk.Entry(surname_frame, font=('Segoe UI', 11),
                        relief='solid', bd=1, bg=COLORS['white'],
                        highlightthickness=2, highlightcolor=COLORS['primary'])
    surname_e.pack(fill='x', ipady=10)

    # DOB AND GENDER ROW
    dob_gender_row = tk.Frame(form_container, bg=COLORS['white'])
    dob_gender_row.pack(fill='x', pady=(0, 20))

    # Date of birth
    dob_frame = tk.Frame(dob_gender_row, bg=COLORS['white'])
    dob_frame.pack(side='left', fill='x', expand=True, padx=(0, 20))
    
    tk.Label(dob_frame, text="DATE OF BIRTH", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 8))
    
    dob_e = DateEntry(dob_frame, width=15, date_pattern="dd/mm/yyyy",
                     font=('Segoe UI', 11), relief='solid', bd=1,
                     highlightthickness=2, highlightcolor=COLORS['primary'])
    dob_e.pack(fill='x', ipady=10)

    # Gender
    gender_frame = tk.Frame(dob_gender_row, bg=COLORS['white'])
    gender_frame.pack(side='right', fill='x', expand=True, padx=(20, 0))
    
    tk.Label(gender_frame, text="GENDER", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 8))
    
    gender_e = ttk.Combobox(gender_frame, values=["Male", "Female", "Other"], 
                           state="readonly", font=('Segoe UI', 11))
    gender_e.pack(fill='x', ipady=10)

    # MOBILE NUMBERS ROW
    mobile_row = tk.Frame(form_container, bg=COLORS['white'])
    mobile_row.pack(fill='x', pady=(0, 20))

    # Student mobile
    student_mob_frame = tk.Frame(mobile_row, bg=COLORS['white'])
    student_mob_frame.pack(side='left', fill='x', expand=True, padx=(0, 20))
    
    tk.Label(student_mob_frame, text="STUDENT MOB", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 8))
    
    mobile_e = tk.Entry(student_mob_frame, font=('Segoe UI', 11),
                       relief='solid', bd=1, bg=COLORS['white'],
                       highlightthickness=2, highlightcolor=COLORS['primary'])
    mobile_e.pack(fill='x', ipady=10)

    # Parents mobile
    parents_mob_frame = tk.Frame(mobile_row, bg=COLORS['white'])
    parents_mob_frame.pack(side='right', fill='x', expand=True, padx=(20, 0))
    
    tk.Label(parents_mob_frame, text="PARENTS MOB", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 8))
    
    parents_mob_e = tk.Entry(parents_mob_frame, font=('Segoe UI', 11),
                            relief='solid', bd=1, bg=COLORS['white'],
                            highlightthickness=2, highlightcolor=COLORS['primary'])
    parents_mob_e.pack(fill='x', ipady=10)

    # EMAIL ADDRESS
    email_frame = tk.Frame(form_container, bg=COLORS['white'])
    email_frame.pack(fill='x', pady=(0, 20))
    
    tk.Label(email_frame, text="EMAIL ADDRESS", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 8))
    
    email_e = tk.Entry(email_frame, font=('Segoe UI', 11),
                      relief='solid', bd=1, bg=COLORS['white'],
                      highlightthickness=2, highlightcolor=COLORS['primary'])
    email_e.pack(fill='x', ipady=10)

    # AADHAAR NUMBER
    aadhaar_frame = tk.Frame(form_container, bg=COLORS['white'])
    aadhaar_frame.pack(fill='x', pady=(0, 20))
    
    tk.Label(aadhaar_frame, text="AADHAAR NO", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 8))
    
    aadhaar_e = tk.Entry(aadhaar_frame, font=('Segoe UI', 11),
                        relief='solid', bd=1, bg=COLORS['white'],
                        highlightthickness=2, highlightcolor=COLORS['primary'])
    aadhaar_e.pack(fill='x', ipady=10)

    # ADDRESS
    address_frame = tk.Frame(form_container, bg=COLORS['white'])
    address_frame.pack(fill='x', pady=(0, 20))
    
    tk.Label(address_frame, text="ADDRESS", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 8))
    
    address_text = tk.Text(address_frame, font=('Segoe UI', 11), height=3,
                          relief='solid', bd=1, bg=COLORS['white'],
                          highlightthickness=2, highlightcolor=COLORS['primary'])
    address_text.pack(fill='x')

    # DATE FIELDS ROW
    dates_row = tk.Frame(form_container, bg=COLORS['white'])
    dates_row.pack(fill='x', pady=(0, 25))

    # Date of joining
    joining_frame = tk.Frame(dates_row, bg=COLORS['white'])
    joining_frame.pack(side='left', fill='x', expand=True, padx=(0, 20))
    
    tk.Label(joining_frame, text="DATE OF JOINING", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 8))
    
    ad_date = DateEntry(joining_frame, width=15, date_pattern="dd/mm/yyyy",
                       font=('Segoe UI', 11), relief='solid', bd=1,
                       highlightthickness=2, highlightcolor=COLORS['primary'])
    ad_date.pack(fill='x', ipady=10)

    # Date of expiration
    expiry_frame = tk.Frame(dates_row, bg=COLORS['white'])
    expiry_frame.pack(side='right', fill='x', expand=True, padx=(20, 0))
    
    tk.Label(expiry_frame, text="DATE OF EXPIRATION", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 8))
    
    expiry_date_e = tk.Entry(expiry_frame, font=('Segoe UI', 11),
                            relief='solid', bd=1, bg=COLORS['gray_100'],
                            state='readonly', fg=COLORS['gray_600'])
    expiry_date_e.pack(fill='x', ipady=10)

    # Auto-calculate expiry date
    def update_expiry_date(*args):
        try:
            joining_date = ad_date.get_date()
            duration = int(dur_var.get())
            expiry_date = joining_date + relativedelta(months=duration)
            expiry_date_e.config(state='normal')
            expiry_date_e.delete(0, tk.END)
            expiry_date_e.insert(0, expiry_date.strftime("%d/%m/%Y"))
            expiry_date_e.config(state='readonly')
        except:
            pass

    ad_date.bind("<<DateEntrySelected>>", update_expiry_date)
    dur_var.trace('w', update_expiry_date)
    
    # Initialize expiry date immediately
    update_expiry_date()

    # FEES SECTION
    fees_frame = tk.Frame(form_container, bg=COLORS['white'])
    fees_frame.pack(fill='x', pady=(0, 25))
    
    tk.Label(fees_frame, text="FEES PAID (₹)", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 8))
    
    fees_e = tk.Entry(fees_frame, font=('Segoe UI', 11),
                     relief='solid', bd=1, bg=COLORS['white'],
                     highlightthickness=2, highlightcolor=COLORS['primary'])
    fees_e.pack(fill='x', ipady=10)
    fees_e.insert(0, "0")  # Default value

    # ACTION BUTTONS
    actions_frame = tk.Frame(form_container, bg=COLORS['white'])
    actions_frame.pack(fill='x', pady=(25, 0))

    def clear_form():
        global aadhaar_temp
        first_name_e.delete(0, tk.END)
        middle_name_e.delete(0, tk.END)
        surname_e.delete(0, tk.END)
        mobile_e.delete(0, tk.END)
        parents_mob_e.delete(0, tk.END)
        email_e.delete(0, tk.END)
        aadhaar_e.delete(0, tk.END)
        fees_e.delete(0, tk.END)
        fees_e.insert(0, "0")
        application_e.delete(0, tk.END)
        address_text.delete("1.0", tk.END)
        gender_e.set("")
        dur_var.set("1")
        img_box.config(image="", text="PHOTO\n\nClick to\nUpload")
        aadhaar_temp = None
        update_expiry_date()

    btn_container = tk.Frame(actions_frame, bg=COLORS['white'])
    btn_container.pack(pady=20)

    # Save button
    save_btn = tk.Button(btn_container, text="💾 SAVE STUDENT", 
                        command=lambda: save_student(clear_form),
                        bg=COLORS['success'], fg='white',
                        font=('Segoe UI', 12, 'bold'),
                        relief='flat', bd=0, cursor='hand2',
                        padx=30, pady=15)
    save_btn.pack(side='left', padx=(0, 25))

    # Clear button
    clear_btn = tk.Button(btn_container, text="�️ CLEAR FORM", 
                         command=clear_form,
                         bg=COLORS['warning'], fg='white',
                         font=('Segoe UI', 12, 'bold'),
                         relief='flat', bd=0, cursor='hand2',
                         padx=30, pady=15)
    clear_btn.pack(side='left')

    # Add hover effects
    def on_save_enter(e):
        save_btn.config(bg=lighten_color(COLORS['success']))
    def on_save_leave(e):
        save_btn.config(bg=COLORS['success'])
    def on_clear_enter(e):
        clear_btn.config(bg=lighten_color(COLORS['warning']))
    def on_clear_leave(e):
        clear_btn.config(bg=COLORS['warning'])

    save_btn.bind("<Enter>", on_save_enter)
    save_btn.bind("<Leave>", on_save_leave)
    clear_btn.bind("<Enter>", on_clear_enter)
    clear_btn.bind("<Leave>", on_clear_leave)

    # ================= RIGHT PANEL - STUDENT RECORDS =================
    
    # Records header
    records_header = tk.Frame(right_panel, bg=COLORS['white'])
    records_header.pack(fill='x', pady=(0, 20))

    tk.Label(records_header, text="👥 Student Records", 
             font=('Segoe UI', 18, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_800']).pack(anchor='w')

    tk.Label(records_header, text="Manage and view all registered students", 
             font=('Segoe UI', 11),
             bg=COLORS['white'], fg=COLORS['gray_500']).pack(anchor='w', pady=(5, 0))

    # Search section
    search_frame = tk.Frame(right_panel, bg=COLORS['white'])
    search_frame.pack(fill='x', pady=(0, 15))

    tk.Label(search_frame, text="🔍", font=('Segoe UI', 14),
             bg=COLORS['white'], fg=COLORS['gray_500']).pack(side='left', padx=(0, 10))

    search_e = tk.Entry(search_frame, width=30, font=('Segoe UI', 11),
                       relief='solid', bd=1, bg=COLORS['white'],
                       highlightthickness=2, highlightcolor=COLORS['primary'])
    search_e.pack(side="left", ipady=8, padx=(0, 10))

    search_btn = tk.Button(search_frame, text="Search", 
                          command=lambda: search_student(search_e),
                          bg=COLORS['info'], fg='white',
                          font=('Segoe UI', 10, 'bold'),
                          relief='flat', bd=0, cursor='hand2',
                          padx=15, pady=8)
    search_btn.pack(side="left")

    # Define renew_student function
    def renew_student():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ No Selection", "Please select a student!")
            return

        item = tree.item(selected[0])
        values = item['values']
        student_name = values[0]
        mobile_no = values[1]

        # Dialog
        win = tk.Toplevel(root)
        win.title("Renew Student")
        win.geometry("500x600")
        win.configure(bg='white')
        center(win, 500, 600)
        win.grab_set()

        # Header
        hdr = tk.Frame(win, bg='#2563eb', height=70)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🔄 Renew Student", font=('Segoe UI', 16, 'bold'), bg='#2563eb', fg='white').pack(pady=20)

        # Content
        content = tk.Frame(win, bg='white')
        content.pack(fill='both', expand=True, padx=25, pady=20)

        # Info
        tk.Label(content, text=f"Student: {student_name}", font=('Segoe UI', 12, 'bold'), bg='white').pack(anchor='w', pady=5)
        tk.Label(content, text=f"Mobile: {mobile_no}", font=('Segoe UI', 10), bg='white', fg='gray').pack(anchor='w', pady=(0,20))

        # Duration
        tk.Label(content, text="Duration:", font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(0,10))
        dur_var = tk.StringVar(value="1")
        for txt, val in [("1 Month", "1"), ("3 Months", "3"), ("6 Months", "6"), ("12 Months", "12")]:
            tk.Radiobutton(content, text=txt, variable=dur_var, value=val, font=('Segoe UI', 10), bg='white').pack(anchor='w', pady=3)

        # Fees
        tk.Label(content, text="Fees (₹):", font=('Segoe UI', 11, 'bold'), bg='white').pack(anchor='w', pady=(20,10))
        fees_e = tk.Entry(content, font=('Segoe UI', 12), relief='solid', bd=2)
        fees_e.pack(fill='x', ipady=10, pady=(0,30))
        fees_e.insert(0, "0")
        fees_e.focus()

        # Process
        def do_renew():
            try:
                fees = float(fees_e.get() or "0")
                if fees < 0:
                    messagebox.showerror("Error", "Invalid fees!")
                    return
                con = db()
                cur = con.cursor()
                cur.execute("SELECT * FROM students WHERE mobile=?", (mobile_no,))
                st = cur.fetchone()
                if not st:
                    messagebox.showerror("Error", "Student not found!")
                    con.close()
                    return
                
                # Handle date parsing - st[14] is expiry_date
                expiry_str = st[14]
                if isinstance(expiry_str, str):
                    exp = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                elif isinstance(expiry_str, datetime):
                    exp = expiry_str.date()
                elif hasattr(expiry_str, 'date'):
                    exp = expiry_str.date()
                else:
                    exp = datetime.now().date()
                
                today = datetime.now().date()
                start = max(exp, today)
                new_exp = start + relativedelta(months=int(dur_var.get()))
                cur.execute("UPDATE students SET expiry_date=?, fees_paid=fees_paid+?, duration_months=? WHERE mobile=?",
                           (new_exp.strftime("%Y-%m-%d"), fees, int(dur_var.get()), mobile_no))
                con.commit()
                con.close()
                load_all()
                messagebox.showinfo("Success", f"Renewed!\nExpiry: {new_exp.strftime('%d/%m/%Y')}\nFees: ₹{fees}")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Renewal failed: {str(e)}")

        # Buttons
        btn_f = tk.Frame(content, bg='white')
        btn_f.pack(fill='x', pady=(20,0))
        tk.Button(btn_f, text="✅ SUBMIT", command=do_renew, bg='#10b981', fg='white', font=('Segoe UI', 12, 'bold'), relief='raised', bd=2, padx=25, pady=10).pack(side='left', expand=True, fill='x', padx=(0,5))
        tk.Button(btn_f, text="❌ CANCEL", command=win.destroy, bg='#ef4444', fg='white', font=('Segoe UI', 12, 'bold'), relief='raised', bd=2, padx=25, pady=10).pack(side='left', expand=True, fill='x', padx=(5,0))



    # Filter buttons
    filter_container = tk.Frame(right_panel, bg=COLORS['white'])
    filter_container.pack(fill='x', pady=(0, 15))

    tk.Label(filter_container, text="📊 Quick Filters", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 10))

    filter_buttons_frame = tk.Frame(filter_container, bg=COLORS['white'])
    filter_buttons_frame.pack(fill='x')

    # Define delete_student function
    def delete_student():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ No Selection", "Please select a student to delete!")
            return
        
        item = tree.item(selected[0])
        values = item['values']
        student_name = values[0]
        mobile_no = values[1]
        
        # Confirm deletion
        confirm = messagebox.askyesno("⚠️ Confirm Delete", 
                                     f"Are you sure you want to delete this student?\n\n"
                                     f"Name: {student_name}\n"
                                     f"Mobile: {mobile_no}\n\n"
                                     f"This action cannot be undone!")
        
        if not confirm:
            return
        
        try:
            con = db()
            cur = con.cursor()
            cur.execute("DELETE FROM students WHERE mobile=?", (mobile_no,))
            con.commit()
            con.close()
            
            # Refresh the table
            load_all()
            
            messagebox.showinfo("✅ Success", 
                              f"Student deleted successfully!\n\n"
                              f"Name: {student_name}\n"
                              f"Mobile: {mobile_no}")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Could not delete student:\n\n{str(e)}")

    filter_buttons = [
        ("🗑️ Delete", "DELETE", COLORS['danger']),  # Replaced Today with Delete
        ("📆 Week", "WEEK", COLORS['info']),
        ("🗓️ Month", "MONTH", COLORS['secondary']),
        ("✅ Active", "ACTIVE", COLORS['success']),
        ("❌ Expired", "EXPIRED", COLORS['danger']),
        ("🔄 Renew", "RENEW", "#8B5CF6"),  # Purple color for renewal
        ("📊 Extract List", "EXTRACT", COLORS['primary'])
    ]

    for text, mode, color in filter_buttons:
        if mode == "EXTRACT":
            btn = tk.Button(filter_buttons_frame, text=text, 
                           command=extract_to_excel,
                           bg=color, fg='white',
                           font=('Segoe UI', 9, 'bold'),
                           relief='flat', bd=0, cursor='hand2',
                           padx=12, pady=6)
        elif mode == "RENEW":
            btn = tk.Button(filter_buttons_frame, text=text, 
                           command=lambda: renew_student(),
                           bg=color, fg='white',
                           font=('Segoe UI', 9, 'bold'),
                           relief='flat', bd=0, cursor='hand2',
                           padx=12, pady=6)
        elif mode == "DELETE":
            btn = tk.Button(filter_buttons_frame, text=text, 
                           command=lambda: delete_student(),
                           bg=color, fg='white',
                           font=('Segoe UI', 9, 'bold'),
                           relief='flat', bd=0, cursor='hand2',
                           padx=12, pady=6)
        else:
            btn = tk.Button(filter_buttons_frame, text=text, 
                           command=lambda m=mode: filter_data(m),
                           bg=color, fg='white',
                           font=('Segoe UI', 9, 'bold'),
                           relief='flat', bd=0, cursor='hand2',
                           padx=12, pady=6)
        btn.pack(side="left", padx=(0, 8))

    # Student table
    table_container = tk.Frame(right_panel, bg=COLORS['white'])
    table_container.pack(fill="both", expand=True, pady=10)

    tk.Label(table_container, text="📋 Student List", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w', pady=(0, 10))

    table_frame = tk.Frame(table_container, bg=COLORS['white'])
    table_frame.pack(fill="both", expand=True)

    cols = ("Name", "Mobile", "Course", "Expiry", "Status")
    tree = ttk.Treeview(table_frame, columns=cols, show="headings", 
                       height=15, style='Modern.Treeview')
    
    tree.column("Name", width=180, anchor="w")
    tree.column("Mobile", width=120, anchor="center")
    tree.column("Course", width=150, anchor="w")
    tree.column("Expiry", width=100, anchor="center")
    tree.column("Status", width=100, anchor="center")

    for c in cols:
        tree.heading(c, text=c)

    scrollbar_tree = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar_tree.set)
    
    tree.pack(side="left", fill="both", expand=True)
    scrollbar_tree.pack(side="right", fill="y")

    # Preview section
    preview_container = tk.Frame(right_panel, bg=COLORS['white'])
    preview_container.pack(fill='x', pady=(15, 0))

    tk.Label(preview_container, text="🖼️ Photo Preview", 
             font=('Segoe UI', 12, 'bold'),
             bg=COLORS['white'], fg=COLORS['gray_700']).pack(anchor='w')

    preview_label = tk.Label(preview_container, 
                            text="Select a student\nto view photo",
                            width=25, height=8, 
                            font=('Segoe UI', 10),
                            relief="solid", bd=1, 
                            bg=COLORS['gray_100'], 
                            fg=COLORS['gray_500'])
    preview_label.pack(pady=10)

    tree.bind("<<TreeviewSelect>>", on_select)

    # COMPATIBILITY WRAPPERS
    class NameEntry:
        def get(self):
            first = first_name_e.get().strip()
            middle = middle_name_e.get().strip()
            last = surname_e.get().strip()
            return f"{first} {middle} {last}".strip()
        def delete(self, start, end):
            first_name_e.delete(0, tk.END)
            middle_name_e.delete(0, tk.END)
            surname_e.delete(0, tk.END)
        def focus(self):
            first_name_e.focus()

    name_e = NameEntry()

    class TextWrapper:
        def __init__(self, text_widget):
            self.widget = text_widget
        def get(self):
            return self.widget.get("1.0", tk.END).strip()
        def delete(self, start, end):
            self.widget.delete("1.0", tk.END)
        def focus(self):
            self.widget.focus()

    class EntryWrapper:
        def __init__(self, entry_widget):
            self.widget = entry_widget
        def get(self):
            return self.widget.get()
        def delete(self, start, end):
            self.widget.delete(start, end)
        def focus(self):
            self.widget.focus()

    # Wrap widgets for compatibility
    course_e = EntryWrapper(application_e)
    address_e = TextWrapper(address_text)
    
    # Create hidden fees field for compatibility
    fees_hidden = tk.Entry(form_container)
    fees_hidden.pack_forget()
    fees_e = EntryWrapper(fees_hidden)

    # Duration wrapper
    class DurationEntry:
        def get(self):
            return f"{dur_var.get()} Month{'s' if dur_var.get() != '1' else ''}"
        def set(self, value):
            dur_var.set(value.split()[0])

    dur = DurationEntry()
    
    load_all()
    
    def auto_refresh():
        load_all()
        root.after(60000, auto_refresh)  # Reduced from 30 seconds to 60 seconds
    
    root.after(60000, auto_refresh)  # Reduced from 30 seconds to 60 seconds
    
    root.mainloop()

# ================= LOGIC FUNCTIONS =================
def save_student(clear_cb):
    # Get values from form fields
    first_name = first_name_e.get().strip()
    middle_name = middle_name_e.get().strip()
    surname = surname_e.get().strip()
    full_name = f"{first_name} {middle_name} {surname}".strip()
    
    mobile_val = mobile_e.get().strip()
    parents_mobile = parents_mob_e.get().strip()
    email = email_e.get().strip()
    aadhaar_no = aadhaar_e.get().strip()
    gender = gender_e.get()
    dob = dob_e.get_date()
    application_for = application_e.get().strip()
    address_val = address_e.get()
    fees_val = fees_e.get().strip()
    
    # Validation
    if not full_name:
        messagebox.showerror("❌ Validation Error", 
                           "Student name is required!\n\nPlease enter at least the first name.")
        first_name_e.focus()
        return
    
    if not mobile_val:
        messagebox.showerror("❌ Validation Error", 
                           "Mobile number is required!\n\nPlease enter a valid 10-digit mobile number.")
        mobile_e.focus()
        return
    
    if len(mobile_val) != 10 or not mobile_val.isdigit():
        messagebox.showerror("❌ Validation Error", 
                           "Invalid mobile number format!\n\nPlease enter exactly 10 digits.")
        mobile_e.focus()
        return
    
    if not application_for:
        messagebox.showerror("❌ Validation Error", 
                           "Application for is required!\n\nPlease enter what the application is for.")
        application_e.focus()
        return
    
    # Validate fees
    try:
        fees_paid = float(fees_val) if fees_val else 0.0
        if fees_paid < 0:
            messagebox.showerror("❌ Validation Error", 
                               "Fees cannot be negative!\n\nPlease enter a valid amount.")
            fees_e.focus()
            return
    except ValueError:
        messagebox.showerror("❌ Validation Error", 
                           "Invalid fees amount!\n\nPlease enter a valid number.")
        fees_e.focus()
        return

    duration_months = int(dur_var.get())
    adm = ad_date.get_date()
    exp = adm + relativedelta(months=duration_months)
    img_path = ""

    if aadhaar_temp:
        img_path = os.path.join(IMAGE_DIR, f"{mobile_val}.jpg")
        try:
            copyfile(aadhaar_temp, img_path)
        except Exception as e:
            messagebox.showerror("❌ Error", f"Could not save image:\n\n{str(e)}")
            return

    try:
        con = db()
        cur = con.cursor()
        cur.execute("""
        INSERT INTO students
        (first_name, middle_name, surname, name, mobile, parents_mobile, email, 
         aadhaar_no, address, course, gender, date_of_birth, admission_date,
         duration_months, expiry_date, fees_paid, aadhaar_image, application_for)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            first_name, middle_name, surname, full_name, mobile_val, parents_mobile,
            email, aadhaar_no, address_val, application_for, gender, 
            dob.strftime("%Y-%m-%d"), adm.strftime("%Y-%m-%d"),
            duration_months, exp.strftime("%Y-%m-%d"), fees_paid, img_path, application_for
        ))
        con.commit()
        con.close()
        
        # Refresh the table BEFORE clearing the form to ensure data is visible
        load_all()
        
        # Find and select the newly added student in the tree
        for item in tree.get_children():
            if tree.item(item)["values"][1] == mobile_val:  # Match by mobile number
                tree.selection_set(item)
                tree.see(item)  # Scroll to make it visible
                tree.focus(item)
                break
        
        # Show success message
        messagebox.showinfo("✅ Success", 
                          f"Student registered successfully!\n\n"
                          f"Name: {full_name}\n"
                          f"Mobile: {mobile_val}\n"
                          f"Application: {application_for}\n"
                          f"Expiry: {exp.strftime('%B %d, %Y')}\n\n"
                          f"✓ Data saved to database\n"
                          f"✓ Record visible in student list")
        
        # Clear form AFTER showing success message
        clear_cb()
        
    except sqlite3.IntegrityError:
        messagebox.showerror("❌ Duplicate Entry", 
                           f"A student with mobile number {mobile_val} already exists!\n\n"
                           "Please use a different mobile number.")
    except Exception as e:
        messagebox.showerror("❌ Database Error", f"Could not save student:\n\n{str(e)}")

def populate(rows):
    # Clear existing items
    tree.delete(*tree.get_children())
    
    today = datetime.today().strftime("%Y-%m-%d")
    
    for i, s in enumerate(rows):
        if len(s) >= 16:  # Check if we have enough columns
            if s[15] < today:  # expiry_date column
                status = "🔴 Expired"
                status_color = 'expired'
            else:
                days_left = (datetime.strptime(s[15], "%Y-%m-%d") - datetime.today()).days
                if days_left <= 7:
                    status = "🟡 Expiring Soon"
                    status_color = 'warning'
                else:
                    status = "🟢 Active"
                    status_color = 'active'
            
            exp_date = datetime.strptime(s[15], "%Y-%m-%d").strftime("%b %d, %Y")
            
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            tree.insert("", "end", 
                       values=(s[4], s[5], s[10], exp_date, status),
                       tags=(tag, status_color))
    
    # Configure tags for styling
    tree.tag_configure('evenrow', background='#f8f9fa')
    tree.tag_configure('oddrow', background='white')
    tree.tag_configure('active', foreground=COLORS['success'])
    tree.tag_configure('warning', foreground=COLORS['warning'])
    tree.tag_configure('expired', foreground=COLORS['danger'])
    
    # Force update the tree widget
    tree.update_idletasks()

def load_all():
    try:
        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM students ORDER BY expiry_date DESC")
        rows = cur.fetchall()
        con.close()
        
        # Always populate the table, even if empty
        populate(rows)
        
        # Update the tree to ensure it's refreshed
        if 'tree' in globals():
            tree.update_idletasks()
            
    except Exception as e:
        messagebox.showerror("❌ Database Error", f"Could not load students:\n\n{str(e)}")

def search_student(e):
    query = e.get().strip()
    if not query:
        load_all()
        return
    
    try:
        q = f"%{query}%"
        con = db()
        cur = con.cursor()
        cur.execute("""
            SELECT * FROM students 
            WHERE name LIKE ? OR mobile LIKE ? OR course LIKE ? OR address LIKE ?
            ORDER BY expiry_date DESC
        """, (q, q, q, q))
        rows = cur.fetchall()
        populate(rows)
        con.close()
        
        if not rows:
            messagebox.showinfo("🔍 Search Results", 
                              f"No students found matching '{query}'.\n\n"
                              "Try searching with different keywords.")
    except Exception as e:
        messagebox.showerror("❌ Search Error", f"Search failed:\n\n{str(e)}")

def filter_data(mode):
    today = datetime.today().date()
    
    try:
        con = db()
        cur = con.cursor()

        if mode == "TODAY":
            cur.execute("SELECT * FROM students WHERE expiry_date=? ORDER BY name", (today,))
        elif mode == "WEEK":
            week_end = today + timedelta(days=7)
            cur.execute("SELECT * FROM students WHERE expiry_date BETWEEN ? AND ? ORDER BY expiry_date", 
                       (today, week_end))
        elif mode == "MONTH":
            month_end = today + relativedelta(months=1)
            cur.execute("SELECT * FROM students WHERE expiry_date BETWEEN ? AND ? ORDER BY expiry_date", 
                       (today, month_end))
        elif mode == "ACTIVE":
            cur.execute("SELECT * FROM students WHERE expiry_date>=? ORDER BY expiry_date DESC", (today,))
        else:  # EXPIRED
            cur.execute("SELECT * FROM students WHERE expiry_date<? ORDER BY expiry_date DESC", (today,))

        rows = cur.fetchall()
        populate(rows)
        con.close()
         
    except Exception as e:
        messagebox.showerror("❌ Filter Error", f"Filter failed:\n\n{str(e)}")

def extract_to_excel():
    """Extract all student data to CSV format (Excel compatible)"""
    try:
        # Get all student data from database
        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM students ORDER BY name")
        rows = cur.fetchall()
        con.close()
        
        if not rows:
            messagebox.showinfo("📊 Export Info", "No student data found to export.")
            return
        
        # Define column headers
        columns = [
            'ID', 'First Name', 'Middle Name', 'Surname', 'Full Name', 'Mobile', 
            'Parents Mobile', 'Email', 'Aadhaar No', 'Address', 'Course/Application', 
            'Gender', 'Date of Birth', 'Admission Date', 'Duration (Months)', 
            'Expiry Date', 'Fees Paid', 'Photo Path', 'Application For', 'Created At'
        ]
        
        # Ask user where to save the file
        file_path = filedialog.asksaveasfilename(
            title="Save Student Data (Excel Compatible)",
            defaultextension=".csv",
            filetypes=[("CSV files (Excel compatible)", "*.csv"), ("All files", "*.*")],
            initialfile=f"Student_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            confirmoverwrite=True
        )
        
        if file_path:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers
                writer.writerow(columns)
                
                # Write data rows with formatted dates
                for row in rows:
                    formatted_row = list(row)
                    # Format date columns (indices 12, 13, 15, 19 based on column order)
                    date_indices = [12, 13, 15, 19]  # Date of Birth, Admission Date, Expiry Date, Created At
                    for idx in date_indices:
                        if idx < len(formatted_row) and formatted_row[idx]:
                            try:
                                # Try different date formats
                                date_str = str(formatted_row[idx])
                                if '-' in date_str:
                                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                                    formatted_row[idx] = date_obj.strftime('%d/%m/%Y')
                            except:
                                pass  # Keep original format if parsing fails
                    
                    writer.writerow(formatted_row)
            
            messagebox.showinfo("✅ Export Successful", 
                              f"Student data exported successfully!\n\n"
                              f"File saved: {file_path}\n"
                              f"Total records: {len(rows)}\n\n"
                              f"📝 Note: CSV file opens perfectly in Excel!")
        
    except Exception as e:
        messagebox.showerror("❌ Export Error", f"Failed to export data:\n\n{str(e)}")

def on_select(_):
    global preview_img
    sel = tree.focus()
    if not sel:
        return

    try:
        mobile = tree.item(sel)["values"][1]
        con = db()
        cur = con.cursor()
        cur.execute("SELECT name, aadhaar_image FROM students WHERE mobile=?", (mobile,))
        row = cur.fetchone()
        con.close()

        if row and row[1] and os.path.exists(row[1]):
            img = Image.open(row[1])
            img = img.resize((180, 180), Image.Resampling.LANCZOS)
            
            mask = Image.new('L', (180, 180), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 180, 180), fill=255)
            
            img.putalpha(mask)
            preview_img = ImageTk.PhotoImage(img)
            
            if 'preview_label' in globals():
                preview_label.config(image=preview_img, text="")
        else: 
            if 'preview_label' in globals():
                preview_label.config(text="📷\n\nNo photo\navailable", image="")
                
    except Exception as e:
        if 'preview_label' in globals():
            preview_label.config(text="❌\n\nError loading\nphoto", image="")

login.mainloop()
