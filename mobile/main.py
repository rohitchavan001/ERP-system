import os
import sys
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.button import MDRaisedButton, MDFloatingActionButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.list import MDList, ThreeLineListItem, IconLeftWidget, TwoLineAvatarIconListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.card import MDCard
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.chip import MDChip
from kivy.metrics import dp
from kivy.clock import Clock
import requests
import json
import threading

# Allow importing shared QR features from the desktop app
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
try:
    from features_qr import generate_student_card
except Exception:
    generate_student_card = None

# Offline data paths
def get_data_dir():
    try:
        from kivy.utils import platform
        if platform == 'android':
            from android.storage import app_storage_path
            return os.path.join(app_storage_path(), "data")
    except ImportError:
        pass
    
    # Fallback for desktop/dev
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "data")

DATA_DIR = get_data_dir()
IMG_DIR = os.path.join(DATA_DIR, "aadhaar_images")
CARDS_DIR = os.path.join(DATA_DIR, "student_cards")
DB_PATH = os.path.join(DATA_DIR, "library.db")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")

def get_base_url():
    env_url = os.environ.get("ERP_MOBILE_API")
    if env_url:
        return env_url
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
                return data.get("base_url") or "http://127.0.0.1:8000"
        except Exception:
            pass
    return "http://127.0.0.1:8000"

def set_base_url(url):
    try:
        if not url.startswith("http"):
            url = f"http://{url}"
        if ":" not in url.replace("http://", "").replace("https://", ""):
            url = f"{url}:8000"
        with open(CONFIG_PATH, "w") as f:
            json.dump({"base_url": url}, f)
        return True
    except Exception:
        return False

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(CARDS_DIR, exist_ok=True)

# Database schema (kept compatible with desktop app)
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
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

def add_student(student):
    try:
        r = requests.post(f"{get_base_url()}/students", json=student, timeout=3)
        if r.status_code in (200, 201):
            return r.json()
    except Exception:
        pass
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO students (first_name, middle_name, surname, name, mobile, parents_mobile, email, aadhaar_no, address, course, gender, date_of_birth, admission_date, duration_months, expiry_date, fees_paid, aadhaar_image, application_for) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (student.get("first_name"), student.get("middle_name"), student.get("surname"), student["name"], student["mobile"], student.get("parents_mobile"), student.get("email"), student.get("aadhaar_no"), student.get("address"), student.get("course"), student.get("gender"), student.get("date_of_birth"), student.get("admission_date"), student.get("duration_months"), student.get("expiry_date"), float(student.get("fees_paid") or 0), student.get("aadhaar_image"), student.get("application_for")))
    conn.commit()
    conn.close()

def list_students():
    try:
        r = requests.get(f"{get_base_url()}/students", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, mobile, course, expiry_date, aadhaar_image FROM students ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "mobile": r[2], "course": r[3], "expiry": r[4], "aadhaar_image": r[5]} for r in rows]

def compute_expiry(admission_date_str, duration_months):
    try:
        dt = datetime.strptime(admission_date_str, "%Y-%m-%d")
        exp = dt + relativedelta(months=int(duration_months or 0))
        return exp.strftime("%Y-%m-%d")
    except Exception:
        return admission_date_str

def renew_student_remote(student_id, months):
    try:
        r = requests.post(f"{get_base_url()}/students/{student_id}/renew", json={"months": months}, timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT admission_date, duration_months FROM students WHERE id=?", (student_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    admission_date, duration_months = row
    new_duration = int(duration_months or 0) + int(months)
    new_expiry = compute_expiry(admission_date, new_duration)
    c.execute("UPDATE students SET duration_months=?, expiry_date=? WHERE id=?", (new_duration, new_expiry, student_id))
    conn.commit()
    conn.close()
    return {"expiry_date": new_expiry, "duration_months": new_duration}

class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "login"
        
        # Main layout with gradient-like background
        layout = MDFloatLayout(md_bg_color=(0.93, 0.94, 0.96, 1))
        
        # Logo/Header area
        header_box = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(120),
            pos_hint={"center_x": 0.5, "top": 0.85},
            spacing=dp(8)
        )
        
        header_box.add_widget(MDLabel(
            text="📚",
            font_style="H2",
            halign="center",
            size_hint_y=None,
            height=dp(60)
        ))
        
        header_box.add_widget(MDLabel(
            text="ERP System",
            font_style="H4",
            halign="center",
            theme_text_color="Primary",
            bold=True
        ))
        
        header_box.add_widget(MDLabel(
            text="Student Management Portal",
            font_style="Caption",
            halign="center",
            theme_text_color="Secondary"
        ))
        
        layout.add_widget(header_box)
        
        # Login Card with improved styling
        card = MDCard(
            orientation="vertical",
            padding=dp(28),
            spacing=dp(20),
            size_hint=(None, None),
            width=dp(320),
            height=dp(340),
            pos_hint={"center_x": 0.5, "center_y": 0.42},
            elevation=4,
            radius=[dp(16), dp(16), dp(16), dp(16)],
            md_bg_color=(1, 1, 1, 1)
        )
        
        card.add_widget(MDLabel(
            text="Sign In",
            font_style="H6",
            halign="left",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(32)
        ))
        
        self.user = MDTextField(
            hint_text="Username",
            text="admin",
            mode="rectangle",
            icon_left="account",
            size_hint_y=None,
            height=dp(56)
        )
        self.passw = MDTextField(
            hint_text="Password",
            password=True,
            text="1234",
            mode="rectangle",
            icon_left="lock",
            size_hint_y=None,
            height=dp(56)
        )
        
        card.add_widget(self.user)
        card.add_widget(self.passw)
        
        btn = MDRaisedButton(
            text="SIGN IN",
            size_hint=(1, None),
            height=dp(52),
            on_release=self.do_login,
            md_bg_color=(0.2, 0.5, 0.9, 1),
            elevation=2
        )
        card.add_widget(btn)
        
        # Footer
        footer = MDLabel(
            text="v2.0 • Secure Access",
            font_style="Caption",
            halign="center",
            theme_text_color="Hint",
            pos_hint={"center_x": 0.5, "y": 0.05}
        )
        
        layout.add_widget(card)
        layout.add_widget(footer)
        self.add_widget(layout)

    def do_login(self, *_):
        if self.user.text.strip() == "admin" and self.passw.text.strip() == "1234":
            self.manager.current = "students"
        else:
            Snackbar(text="❌ Invalid credentials", duration=2).open()

class StudentsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "students"
        self.is_loading = False
        self.filter_course = None  # Current filter
        
        # Main FloatLayout to allow overlapping FAB
        self.layout = MDFloatLayout(md_bg_color=(0.93, 0.94, 0.96, 1))
        
        # Header Box - Responsive height
        header = MDBoxLayout(orientation="vertical", pos_hint={"top": 1}, size_hint=(1, None), height=dp(160))
        
        # Toolbar with responsive title
        self.toolbar = MDTopAppBar(
            title="Students",
            md_bg_color=(0.2, 0.5, 0.9, 1),
            elevation=4,
            specific_text_color=(1, 1, 1, 1)
        )
        
        # Create dropdown menu for settings
        self.menu_items = [
            {
                "text": "Settings",
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.menu_callback("settings"),
            },
            {
                "text": "Refresh",
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.menu_callback("refresh"),
            },
            {
                "text": "About",
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.menu_callback("about"),
            },
        ]
        
        self.toolbar.right_action_items = [
            ["dots-vertical", lambda x: self.open_menu(x)]
        ]
        
        header.add_widget(self.toolbar)

        # Enhanced status and search bar
        info_bar = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(80),
            padding=(dp(12), dp(8)),
            md_bg_color=(1, 1, 1, 1),
            spacing=dp(8)
        )
        
        # Status row
        status_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
        self.status_label = MDLabel(
            text="● Checking...",
            theme_text_color="Hint",
            font_style="Caption",
            size_hint_x=0.6
        )
        status_row.add_widget(self.status_label)
        
        self.count_label = MDLabel(
            text="0 students",
            theme_text_color="Secondary",
            font_style="Caption",
            halign="right",
            size_hint_x=0.4
        )
        status_row.add_widget(self.count_label)
        info_bar.add_widget(status_row)
        
        # Search and filter row
        search_row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        
        self.search_field = MDTextField(
            hint_text="Search...",
            mode="rectangle",
            size_hint=(0.75, None),
            height=dp(44),
            font_size="14sp"
        )
        self.search_field.bind(text=self.on_search)
        search_row.add_widget(self.search_field)
        
        # Filter button
        filter_btn = MDIconButton(
            icon="filter-variant",
            theme_text_color="Custom",
            text_color=(0.2, 0.5, 0.9, 1),
            size_hint=(0.25, None),
            height=dp(44),
            on_release=self.open_filter_menu
        )
        search_row.add_widget(filter_btn)
        
        info_bar.add_widget(search_row)
        header.add_widget(info_bar)
        
        self.layout.add_widget(header)

        # Filter chips container
        self.filter_container = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=0,  # Hidden by default
            padding=(dp(12), 0),
            spacing=dp(8),
            pos_hint={"top": 0.68}
        )
        self.layout.add_widget(self.filter_container)

        # Scrollable List area with loading indicator
        list_container = MDFloatLayout(
            pos_hint={"top": 0.68},
            size_hint=(1, 0.68)
        )
        
        self.scroll = MDScrollView()
        self.list = MDList(padding=dp(12), spacing=dp(8))
        self.scroll.add_widget(self.list)
        list_container.add_widget(self.scroll)
        
        # Loading spinner
        self.spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(46), dp(46)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            active=False
        )
        list_container.add_widget(self.spinner)
        
        self.layout.add_widget(list_container)

        # Responsive FAB positioning
        fab = MDFloatingActionButton(
            icon="plus",
            md_bg_color=(0.2, 0.5, 0.9, 1),
            pos_hint={"right": 0.92, "y": 0.04},
            elevation=8
        )
        fab.bind(on_release=lambda *_: self.manager.get_screen("add").reset_and_open())
        self.layout.add_widget(fab)
        
        self.add_widget(self.layout)
        self.all_students = []
        self.filtered_students = []
        
        # Initialize menu
        self.menu = None

    def open_menu(self, button):
        """Open dropdown menu"""
        if not self.menu:
            self.menu = MDDropdownMenu(
                caller=button,
                items=self.menu_items,
                width_mult=3,
            )
        self.menu.open()

    def menu_callback(self, action):
        """Handle menu actions"""
        self.menu.dismiss()
        if action == "settings":
            self.open_settings()
        elif action == "refresh":
            self.refresh()
        elif action == "about":
            self.show_about()

    def show_about(self):
        """Show about dialog"""
        about_dlg = MDDialog(
            title="ERP Mobile v2.0",
            text="Modern student management system\n\n✨ Features:\n• Real-time sync\n• Offline support\n• Search & filter\n• ID card generation\n\n© 2026 ERP System",
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: about_dlg.dismiss(),
                    md_bg_color=(0.2, 0.5, 0.9, 1)
                )
            ]
        )
        about_dlg.open()

    def open_filter_menu(self, button):
        """Open filter menu with course options"""
        # Get unique courses from all students
        courses = set()
        for s in self.all_students:
            if s.get('course'):
                courses.add(s['course'])
        
        filter_items = [
            {
                "text": "All Courses",
                "viewclass": "OneLineListItem",
                "on_release": lambda: self.apply_filter(None),
            }
        ]
        
        for course in sorted(courses):
            filter_items.append({
                "text": course,
                "viewclass": "OneLineListItem",
                "on_release": lambda c=course: self.apply_filter(c),
            })
        
        if not courses:
            filter_items.append({
                "text": "No courses available",
                "viewclass": "OneLineListItem",
                "on_release": lambda: None,
            })
        
        filter_menu = MDDropdownMenu(
            caller=button,
            items=filter_items,
            width_mult=4,
        )
        filter_menu.open()

    def apply_filter(self, course):
        """Apply course filter"""
        self.filter_course = course
        
        # Update filter chip display
        self.filter_container.clear_widgets()
        if course:
            self.filter_container.height = dp(48)
            chip = MDChip(
                text=f"📚 {course}",
                icon_right="close-circle",
                on_release=lambda x: self.clear_filter(),
                md_bg_color=(0.85, 0.9, 1, 1),
                text_color=(0.2, 0.5, 0.9, 1)
            )
            self.filter_container.add_widget(chip)
            
            # Adjust list position
            self.layout.children[1].pos_hint = {"top": 0.62}
        else:
            self.filter_container.height = 0
            self.layout.children[1].pos_hint = {"top": 0.68}
        
        # Reapply search with new filter
        self.on_search(self.search_field, self.search_field.text)

    def clear_filter(self):
        """Clear active filter"""
        self.apply_filter(None)

    def on_pre_enter(self, *_):
        self.check_connection()
        self.refresh()

    def on_search(self, instance, value):
        """Filter students based on search text and active filter"""
        search_text = value.lower().strip()
        
        # Start with all students
        filtered = self.all_students
        
        # Apply course filter if active
        if self.filter_course:
            filtered = [s for s in filtered if s.get('course') == self.filter_course]
        
        # Apply search filter
        if search_text:
            filtered = [s for s in filtered 
                       if search_text in s['name'].lower() or search_text in s['mobile']]
        
        self.filtered_students = filtered
        self.display_students(filtered)

    def refresh(self):
        """Refresh student list with loading indicator"""
        if self.is_loading:
            return
            
        self.is_loading = True
        self.spinner.active = True
        self.list.clear_widgets()
        
        def fetch_data():
            students = list_students()
            Clock.schedule_once(lambda dt: self.on_data_loaded(students), 0)
        
        threading.Thread(target=fetch_data, daemon=True).start()

    def on_data_loaded(self, students):
        """Handle loaded data on main thread"""
        self.spinner.active = False
        self.is_loading = False
        self.all_students = students
        self.count_label.text = f"{len(students)} student{'s' if len(students) != 1 else ''}"
        self.display_students(students)

    def display_students(self, students):
        """Display filtered student list"""
        self.list.clear_widgets()
        
        if not students:
            empty_card = MDCard(
                orientation="vertical",
                padding=dp(24),
                size_hint=(1, None),
                height=dp(120),
                radius=[dp(12), dp(12), dp(12), dp(12)],
                md_bg_color=(1, 1, 1, 1)
            )
            empty_card.add_widget(MDLabel(
                text="📋",
                font_style="H4",
                halign="center",
                size_hint_y=None,
                height=dp(40)
            ))
            empty_card.add_widget(MDLabel(
                text="No students found" if not self.filter_course else f"No students in {self.filter_course}",
                halign="center",
                theme_text_color="Secondary",
                font_style="Body1"
            ))
            self.list.add_widget(empty_card)
            return
            
        for s in students:
            # Create responsive card for each student
            card = MDCard(
                orientation="vertical",
                padding=dp(14),
                size_hint=(1, None),
                height=dp(96),
                radius=[dp(12), dp(12), dp(12), dp(12)],
                md_bg_color=(1, 1, 1, 1),
                elevation=1
            )
            
            # Student info with responsive text
            info_box = MDBoxLayout(orientation="vertical", spacing=dp(3))
            
            name_label = MDLabel(
                text=f"[b]{s['name']}[/b]",
                markup=True,
                font_style="Subtitle1",
                theme_text_color="Primary",
                size_hint_y=None,
                height=dp(22)
            )
            
            course_label = MDLabel(
                text=f"📚 {s['course'] or 'No course'}",
                font_style="Caption",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(18)
            )
            
            details_label = MDLabel(
                text=f"📱 {s['mobile']}",
                font_style="Caption",
                theme_text_color="Hint",
                size_hint_y=None,
                height=dp(18)
            )
            
            expiry_label = MDLabel(
                text=f"📅 Exp: {s['expiry']}",
                font_style="Caption",
                theme_text_color="Hint",
                size_hint_y=None,
                height=dp(18)
            )
            
            info_box.add_widget(name_label)
            info_box.add_widget(course_label)
            info_box.add_widget(details_label)
            info_box.add_widget(expiry_label)
            
            card.add_widget(info_box)
            card.bind(on_release=lambda _, sid=s['id']: self.open_student(sid))
            self.list.add_widget(card)

    def check_connection(self):
        """Check API connection status"""
        def check():
            try:
                r = requests.get(f"{get_base_url()}/health", timeout=2)
                if r.status_code == 200:
                    Clock.schedule_once(lambda dt: self.update_status(True), 0)
                    return
            except Exception:
                pass
            Clock.schedule_once(lambda dt: self.update_status(False), 0)
        
        threading.Thread(target=check, daemon=True).start()

    def update_status(self, connected):
        """Update connection status on main thread"""
        if connected:
            self.status_label.text = "● Connected"
            self.status_label.theme_text_color = "Custom"
            self.status_label.text_color = (0.1, 0.7, 0.3, 1)
        else:
            self.status_label.text = "○ Offline"
            self.status_label.theme_text_color = "Custom"
            self.status_label.text_color = (0.9, 0.5, 0.1, 1)

    def open_settings(self):
        self.manager.get_screen("settings").load_current()
        self.manager.current = "settings"

    def open_student(self, student_id):
        """Open student details dialog with enhanced UI"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, name, mobile, course, expiry_date, aadhaar_image, fees_paid FROM students WHERE id=?", (student_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            Snackbar(text="❌ Student not found", duration=2).open()
            return
            
        student = {
            "id": row[0],
            "name": row[1],
            "mobile": row[2],
            "course": row[3],
            "expiry": row[4],
            "fees": row[6] or 0
        }
        photo = row[5]

        def do_card(*_):
            if generate_student_card:
                out = os.path.join(CARDS_DIR, f"card_{student['id']}.png")
                try:
                    generate_student_card(student, photo, out)
                    Snackbar(text="✅ ID Card generated", duration=2).open()
                except Exception as e:
                    Snackbar(text=f"❌ Error: {str(e)[:50]}", duration=3).open()
            else:
                Snackbar(text="⚠️ Card generator unavailable", duration=2).open()
            dlg.dismiss()

        def do_renew(*_):
            months_field = MDTextField(
                hint_text="Months to add",
                text="1",
                input_filter="int",
                mode="rectangle",
                size_hint_y=None,
                height=dp(56)
            )
            
            def go_renew(*_):
                try:
                    months = int(months_field.text.strip() or "1")
                except Exception:
                    months = 1
                
                inner_dlg.dismiss()
                
                def renew_task():
                    res = renew_student_remote(student["id"], months)
                    if res:
                        Clock.schedule_once(lambda dt: on_renew_success(res), 0)
                    else:
                        Clock.schedule_once(lambda dt: Snackbar(text="❌ Renewal failed", duration=2).open(), 0)
                
                def on_renew_success(res):
                    Snackbar(text=f"✅ Renewed! New expiry: {res.get('expiry_date')}", duration=3).open()
                    self.refresh()
                    dlg.dismiss()
                
                threading.Thread(target=renew_task, daemon=True).start()

            inner_dlg = MDDialog(
                title="Renew Membership",
                type="custom",
                content_cls=MDBoxLayout(
                    orientation="vertical",
                    children=[months_field],
                    size_hint=(1, None),
                    height=dp(80),
                    padding=dp(16)
                ),
                buttons=[
                    MDFlatButton(text="CANCEL", on_release=lambda x: inner_dlg.dismiss()),
                    MDRaisedButton(
                        text="RENEW",
                        on_release=go_renew,
                        md_bg_color=(0.2, 0.5, 0.9, 1)
                    )
                ]
            )
            inner_dlg.open()

        dlg = MDDialog(
            title=student["name"],
            text=f"📚 Course: {student['course'] or 'N/A'}\n📱 Mobile: {student['mobile']}\n📅 Expiry: {student['expiry']}\n💰 Fees: ₹{student['fees']:.2f}",
            buttons=[
                MDFlatButton(text="CLOSE", on_release=lambda x: dlg.dismiss()),
                MDRaisedButton(text="ID CARD", on_release=do_card, md_bg_color=(0.3, 0.6, 0.3, 1)),
                MDRaisedButton(text="RENEW", on_release=do_renew, md_bg_color=(0.2, 0.5, 0.9, 1))
            ]
        )
        dlg.open()

class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "settings"
        
        layout = MDBoxLayout(orientation="vertical", md_bg_color=(0.93, 0.94, 0.96, 1))
        
        toolbar = MDTopAppBar(
            title="Settings",
            md_bg_color=(0.2, 0.5, 0.9, 1),
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            specific_text_color=(1, 1, 1, 1)
        )
        layout.add_widget(toolbar)
        
        # Scrollable content
        scroll = MDScrollView()
        content = MDBoxLayout(orientation="vertical", padding=dp(20), spacing=dp(16), size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        
        # Connection Settings Card
        conn_card = MDCard(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(12),
            size_hint=(1, None),
            height=dp(280),
            radius=[dp(12), dp(12), dp(12), dp(12)],
            md_bg_color=(1, 1, 1, 1)
        )
        
        conn_card.add_widget(MDLabel(
            text="🌐 Network Configuration",
            font_style="Subtitle1",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(32)
        ))
        
        conn_card.add_widget(MDLabel(
            text="Connect to your desktop ERP system over Wi-Fi for real-time sync.",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(40)
        ))
        
        self.base_e = MDTextField(
            hint_text="Desktop IP Address",
            helper_text="Example: 192.168.1.50 (port 8000 auto-added)",
            helper_text_mode="persistent",
            mode="rectangle",
            size_hint_y=None,
            height=dp(64)
        )
        conn_card.add_widget(self.base_e)
        
        test_btn = MDFlatButton(
            text="TEST CONNECTION",
            size_hint=(1, None),
            height=dp(44),
            on_release=self.test_connection
        )
        conn_card.add_widget(test_btn)
        
        content.add_widget(conn_card)
        
        # Info Card
        info_card = MDCard(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(8),
            size_hint=(1, None),
            height=dp(160),
            radius=[dp(12), dp(12), dp(12), dp(12)],
            md_bg_color=(0.95, 0.97, 1, 1)
        )
        
        info_card.add_widget(MDLabel(
            text="ℹ️ How to Connect",
            font_style="Subtitle2",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(28)
        ))
        
        info_card.add_widget(MDLabel(
            text="1. Ensure desktop app is running\n2. Both devices on same Wi-Fi\n3. Enter desktop's IP address\n4. Test and save configuration",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(80)
        ))
        
        content.add_widget(info_card)
        
        # Save button
        save_btn = MDRaisedButton(
            text="SAVE CONFIGURATION",
            size_hint=(1, None),
            height=dp(52),
            on_release=self.save,
            md_bg_color=(0.2, 0.5, 0.9, 1)
        )
        content.add_widget(save_btn)
        
        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def load_current(self):
        url = get_base_url().replace("http://", "").replace(":8000", "")
        self.base_e.text = url

    def test_connection(self, *_):
        """Test connection to desktop"""
        url = self.base_e.text.strip()
        if not url:
            Snackbar(text="⚠️ Please enter IP address", duration=2).open()
            return
        
        def test():
            try:
                test_url = url if url.startswith("http") else f"http://{url}"
                if ":" not in test_url.replace("http://", "").replace("https://", ""):
                    test_url = f"{test_url}:8000"
                
                r = requests.get(f"{test_url}/health", timeout=3)
                if r.status_code == 200:
                    Clock.schedule_once(lambda dt: Snackbar(text="✅ Connection successful!", duration=2).open(), 0)
                else:
                    Clock.schedule_once(lambda dt: Snackbar(text="❌ Server responded with error", duration=2).open(), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: Snackbar(text=f"❌ Connection failed", duration=2).open(), 0)
        
        threading.Thread(target=test, daemon=True).start()

    def save(self, *_):
        url = self.base_e.text.strip()
        if not url:
            Snackbar(text="⚠️ IP Address required", duration=2).open()
            return
            
        ok = set_base_url(url)
        if ok:
            Snackbar(text="✅ Settings saved", duration=2).open()
            self.go_back()
        else:
            Snackbar(text="❌ Failed to save", duration=2).open()

    def go_back(self):
        self.manager.current = "students"

class AddStudentScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "add"
        
        layout = MDBoxLayout(orientation="vertical", md_bg_color=(0.93, 0.94, 0.96, 1))
        
        toolbar = MDTopAppBar(
            title="New Student",
            md_bg_color=(0.2, 0.5, 0.9, 1),
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            specific_text_color=(1, 1, 1, 1)
        )
        layout.add_widget(toolbar)

        # Form area with ScrollView
        scroll = MDScrollView()
        form = MDBoxLayout(orientation="vertical", spacing=dp(14), padding=dp(20), size_hint_y=None)
        form.bind(minimum_height=form.setter('height'))
        
        # Form fields with improved styling
        self.name_e = MDTextField(
            hint_text="Full Name *",
            mode="rectangle",
            icon_left="account",
            size_hint_y=None,
            height=dp(56)
        )
        self.mobile_e = MDTextField(
            hint_text="Mobile Number *",
            mode="rectangle",
            icon_left="phone",
            input_filter="int",
            max_text_length=10,
            size_hint_y=None,
            height=dp(56)
        )
        self.course_e = MDTextField(
            hint_text="Course Name",
            mode="rectangle",
            icon_left="book-open-variant",
            size_hint_y=None,
            height=dp(56)
        )
        self.admission_e = MDTextField(
            hint_text="Admission Date (YYYY-MM-DD)",
            mode="rectangle",
            icon_left="calendar",
            text=datetime.now().strftime("%Y-%m-%d"),
            size_hint_y=None,
            height=dp(56)
        )
        self.duration_e = MDTextField(
            hint_text="Duration (months)",
            mode="rectangle",
            icon_left="clock-outline",
            text="1",
            input_filter="int",
            size_hint_y=None,
            height=dp(56)
        )
        self.fees_e = MDTextField(
            hint_text="Fees Amount (₹)",
            mode="rectangle",
            icon_left="currency-inr",
            text="0",
            input_filter="float",
            size_hint_y=None,
            height=dp(56)
        )
        self.photo_e = MDTextField(
            hint_text="Photo Path (optional)",
            mode="rectangle",
            icon_left="image",
            size_hint_y=None,
            height=dp(56)
        )
        
        form.add_widget(MDLabel(
            text="* Required fields",
            font_style="Caption",
            theme_text_color="Hint",
            size_hint_y=None,
            height=dp(24)
        ))
        
        form.add_widget(self.name_e)
        form.add_widget(self.mobile_e)
        form.add_widget(self.course_e)
        form.add_widget(self.admission_e)
        form.add_widget(self.duration_e)
        form.add_widget(self.fees_e)
        form.add_widget(self.photo_e)
        
        # Bottom Buttons
        btn_box = MDBoxLayout(orientation="vertical", padding=(0, dp(20)), size_hint_y=None, height=dp(80))
        save_btn = MDRaisedButton(
            text="REGISTER STUDENT",
            size_hint=(1, None),
            height=dp(56),
            on_release=self.save_student,
            md_bg_color=(0.2, 0.5, 0.9, 1),
            elevation=2
        )
        btn_box.add_widget(save_btn)
        form.add_widget(btn_box)
        
        scroll.add_widget(form)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def go_back(self):
        self.manager.current = "students"

    def reset_and_open(self):
        self.name_e.text = ""
        self.mobile_e.text = ""
        self.course_e.text = ""
        self.admission_e.text = datetime.now().strftime("%Y-%m-%d")
        self.duration_e.text = "1"
        self.fees_e.text = "0"
        self.photo_e.text = ""
        self.manager.current = "add"

    def save_student(self, *_):
        name = self.name_e.text.strip()
        mobile = self.mobile_e.text.strip()
        course = self.course_e.text.strip()
        admission = self.admission_e.text.strip()
        duration = self.duration_e.text.strip()
        fees = self.fees_e.text.strip()
        photo = self.photo_e.text.strip() or None

        if not name or not mobile:
            Snackbar(text="⚠️ Name and Mobile are required", duration=2).open()
            return
        
        if len(mobile) != 10:
            Snackbar(text="⚠️ Mobile must be 10 digits", duration=2).open()
            return

        expiry = compute_expiry(admission, duration or "0")
        
        def save_task():
            try:
                add_student({
                    "first_name": None,
                    "middle_name": None,
                    "surname": None,
                    "name": name,
                    "mobile": mobile,
                    "parents_mobile": None,
                    "email": None,
                    "aadhaar_no": None,
                    "address": None,
                    "course": course or None,
                    "gender": None,
                    "date_of_birth": None,
                    "admission_date": admission,
                    "duration_months": int(duration or "0"),
                    "expiry_date": expiry,
                    "fees_paid": float(fees or "0"),
                    "aadhaar_image": photo,
                    "application_for": None,
                })
                Clock.schedule_once(lambda dt: self.on_save_success(), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: Snackbar(text=f"❌ Error: {str(e)[:50]}", duration=3).open(), 0)
        
        threading.Thread(target=save_task, daemon=True).start()

    def on_save_success(self):
        Snackbar(text="✅ Student registered successfully", duration=2).open()
        self.manager.get_screen("students").refresh()
        self.manager.current = "students"

class ERPMobileApp(MDApp):
    def build(self):
        init_db()
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "700"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.theme_style = "Light"
        self.title = "ERP Mobile"
        
        sm = MDScreenManager()
        sm.add_widget(LoginScreen())
        sm.add_widget(StudentsScreen())
        sm.add_widget(SettingsScreen())
        sm.add_widget(AddStudentScreen())
        return sm

if __name__ == "__main__":
    ERPMobileApp().run()

