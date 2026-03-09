# 🚀 ERP System - Complete Setup Guide

## 📦 What You Get

- **Desktop EXE** - Windows application with built-in API server
- **Mobile APK** - Android app that syncs with desktop
- **Auto-sync** - Works on same WiFi or different networks

## 🔨 Build Everything

**Run this once:**
```bash
BUILD_ALL.bat
```

This creates:
- `dist/ERP-System.exe` - Desktop installer
- `mobile/bin/*.apk` - Mobile app

## 💻 Desktop Setup (Windows PC)

1. **Run** `dist/ERP-System.exe`
2. **Desktop app opens** - API server starts automatically
3. **Find your IP** - Open Command Prompt:
   ```bash
   ipconfig
   ```
   Look for "IPv4 Address" (e.g., 192.168.1.50)

## 📱 Mobile Setup (Android Phone)

1. **Install APK** on phone
2. **Open app** - Login: admin/1234
3. **Configure connection:**
   - Tap ⋮ menu → Settings
   - Enter PC IP: `192.168.1.50`
   - Tap "TEST CONNECTION"
   - Tap "SAVE"
4. **Check status** - Should show "● Connected"

## 🌐 Connection Options

### Same WiFi (Easiest)
- Both devices on same WiFi
- Mobile uses PC's IP address
- Data syncs automatically

### Different Networks (Internet)
1. **On PC:** Install ngrok from https://ngrok.com
2. **Run:**
   ```bash
   ngrok http 8000
   ```
3. **Copy URL** (e.g., abc123.ngrok.io)
4. **Mobile:** Settings → Enter ngrok URL → Save
5. **Works anywhere!**

## ✨ Features

**Desktop:**
- Full student management
- ID card generation
- Reports and exports
- Database management

**Mobile:**
- Add/edit students
- Search & filter
- Renew memberships
- Generate ID cards
- Works offline

**Sync:**
- Real-time data sync
- Same database
- Changes appear instantly
- Works on WiFi or internet

## 🔧 Troubleshooting

**Mobile shows "○ Offline":**
- Check desktop app is running
- Verify IP address (ipconfig)
- Test in browser: http://IP:8000/health
- Check firewall allows port 8000

**Can't build APK:**
- Use GitHub Actions (automatic)
- Push code: `git push origin main`
- Download from Actions tab

**Desktop EXE not working:**
- Run as administrator
- Check antivirus isn't blocking
- Install Visual C++ Redistributable

---

**That's it! Desktop EXE + Mobile APK working together.** 🎉

## 🌐 Connecting Mobile to Desktop

### On Desktop (PC):
1. Start the API server: `python api/server.py`
2. Note the message showing your IP address
3. Keep the server running

### On Mobile App:
1. Open the app and login
2. Tap the ⚙️ (Settings) icon in the top-right
3. Enter your PC's IP address (e.g., `192.168.1.50`)
4. Tap "TEST CONNECTION" to verify
5. If successful, tap "SAVE CONFIGURATION"
6. Return to student list - you should see "● Connected to Desktop"

### Network Requirements:
- Both devices must be on the same Wi-Fi network
- Desktop firewall must allow port 8000
- API server must be running on desktop

## ✨ New Features

### 1. Enhanced Student List
- **Card-based layout** - Each student in a clean card
- **Search bar** - Type to filter by name or mobile
- **Student count** - See total students at a glance
- **Connection status** - Green dot = synced, Orange = offline

### 2. Improved Student Details
- **Rich information display** - Course, mobile, expiry, fees
- **Quick actions** - Generate ID card or renew membership
- **Visual feedback** - Emoji icons for better UX

### 3. Better Add Student Form
- **Field validation** - Required fields marked with *
- **Input helpers** - Icons and hints for each field
- **Mobile validation** - Ensures 10-digit numbers
- **Auto-calculations** - Expiry date computed automatically

### 4. Network Settings
- **Connection testing** - Test before saving
- **Visual guides** - Step-by-step instructions
- **Status feedback** - Clear success/error messages

### 5. Responsive Design
- **Proper spacing** - Uses dp units for consistency
- **Smooth scrolling** - All screens scroll properly
- **Loading indicators** - Spinners during operations
- **Async operations** - Non-blocking network calls

## 🎨 UI Improvements

### Color Scheme
- **Primary:** Blue (0.2, 0.5, 0.9) - Professional and modern
- **Background:** Light gray (0.93, 0.94, 0.96) - Easy on eyes
- **Cards:** White with subtle shadows - Clean separation
- **Text:** Proper hierarchy with Primary/Secondary/Hint colors

### Typography
- **Headers:** H4-H6 for titles
- **Body:** Subtitle1 for names, Caption for details
- **Consistency:** All text properly sized and colored

### Spacing
- **Padding:** dp(16-24) for comfortable touch targets
- **Spacing:** dp(8-16) between elements
- **Heights:** dp(52-56) for buttons, dp(56) for text fields

### Icons & Emojis
- **Visual communication:** 📚 📱 📅 💰 for quick recognition
- **Status indicators:** ● ○ ✅ ❌ ⚠️ for feedback
- **Material icons:** account, phone, book, calendar, etc.

## 🔄 Sync Behavior

### When Connected (Green Dot):
- All operations sync to desktop immediately
- Student list fetched from desktop database
- Changes visible on both desktop and mobile
- Real-time updates

### When Offline (Orange Dot):
- Full functionality maintained locally
- Data stored in mobile's SQLite database
- Manual sync when connection restored
- No data loss

## 📱 Screen-by-Screen Guide

### Login Screen
- Modern card-based design with logo
- Auto-filled credentials for quick testing
- Clean, professional appearance

### Students Dashboard
- **Top Bar:** Title, Settings, Refresh buttons
- **Status Bar:** Connection status + student count
- **Search Bar:** Type to filter students instantly
- **Student Cards:** Tap any card to view details
- **FAB Button:** Blue + button to add new student

### Student Details Dialog
- **Information:** Name, course, mobile, expiry, fees
- **Actions:**
  - **ID CARD:** Generate student ID with QR code
  - **RENEW:** Extend membership by X months
  - **CLOSE:** Return to list

### Add Student Screen
- **Required Fields:** Name*, Mobile* (marked with asterisk)
- **Optional Fields:** Course, photo path
- **Auto-filled:** Admission date (today), Duration (1 month)
- **Validation:** Mobile must be 10 digits
- **Action:** REGISTER STUDENT button at bottom

### Settings Screen
- **Network Config Card:** IP address input with test button
- **Info Card:** Step-by-step connection guide
- **Actions:** Test connection, Save configuration

## 🛠️ Technical Details

### Architecture
```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Mobile    │◄───────►│  REST API   │◄───────►│   Desktop   │
│     App     │  HTTP   │   Server    │  SQLite │     App     │
└─────────────┘         └─────────────┘         └─────────────┘
      │                                                 │
      ▼                                                 ▼
┌─────────────┐                                 ┌─────────────┐
│   Local     │                                 │   Shared    │
│   SQLite    │                                 │   SQLite    │
└─────────────┘                                 └─────────────┘
```

### Key Technologies
- **KivyMD:** Material Design framework for Python
- **FastAPI:** Modern REST API framework
- **SQLite:** Lightweight database
- **Threading:** Non-blocking network operations
- **Requests:** HTTP client for API calls

### Data Flow
1. **User Action** → Mobile UI
2. **API Call** → REST endpoint (if connected)
3. **Database Update** → SQLite (local or shared)
4. **Response** → Update UI with feedback
5. **Fallback** → Local storage if offline

## 🐛 Troubleshooting

### Mobile App Won't Start
```bash
# Check dependencies
cd mobile
pip install -r requirements.txt

# Try running with verbose output
python main.py
```

### API Server Won't Start
```bash
# Check dependencies
cd api
pip install -r requirements.txt

# Check if port 8000 is available
netstat -an | findstr :8000

# Try different port
uvicorn server:app --host 0.0.0.0 --port 8001
```

### Connection Issues
1. **Check same network:** Both devices on same Wi-Fi
2. **Check firewall:** Allow port 8000 on desktop
3. **Check IP address:** Use `ipconfig` on Windows
4. **Test connection:** Use "TEST CONNECTION" in settings
5. **Check API logs:** Look for errors in API terminal

### Search Not Working
- Make sure you're typing in the search field
- Search is case-insensitive
- Searches both name and mobile fields
- Clear search to see all students

### Students Not Syncing
1. Check connection status (should be green dot)
2. Verify API server is running
3. Test connection in settings
4. Check API server logs for errors
5. Try refreshing the student list

## 📊 Performance Tips

### For Best Performance:
- Keep student list under 1000 records for smooth scrolling
- Use search to filter large lists
- Close unused dialogs
- Restart app if it becomes sluggish

### Network Optimization:
- Use local Wi-Fi (not mobile hotspot) for best speed
- Keep devices close to router
- Minimize network traffic during sync

## 🎓 Usage Examples

### Example 1: Add New Student
1. Tap the blue + button
2. Fill in Name: "John Doe"
3. Fill in Mobile: "9876543210"
4. Fill in Course: "Python Programming"
5. Adjust Duration if needed (default 1 month)
6. Tap "REGISTER STUDENT"
7. See success message and return to list

### Example 2: Renew Membership
1. Tap on student card
2. Tap "RENEW" button
3. Enter number of months (e.g., 3)
4. Tap "RENEW" to confirm
5. See updated expiry date

### Example 3: Generate ID Card
1. Tap on student card
2. Tap "ID CARD" button
3. Card generated with QR code
4. Saved to student_cards folder

### Example 4: Search Students
1. Tap search bar at top
2. Type student name or mobile
3. List filters in real-time
4. Clear search to see all

## 🔐 Security Notes

- Default credentials are for testing only
- Change admin password in production
- API has no authentication (local network only)
- Don't expose API server to internet
- Keep mobile app on trusted devices only

## 📈 Future Enhancements

Planned features for next version:
- [ ] Camera integration for student photos
- [ ] Biometric authentication
- [ ] Push notifications for expiring memberships
- [ ] Batch student import/export
- [ ] Advanced filtering (by course, expiry date)
- [ ] Attendance tracking
- [ ] Fee payment history
- [ ] Reports and analytics
- [ ] Dark mode support
- [ ] Multi-language support

## 📞 Support

For issues or questions:
1. Check this guide first
2. Review error messages in console
3. Check API server logs
4. Verify network connectivity
5. Restart all services

## 📝 Changelog

### Version 2.0 (Current)
- ✨ Complete UI redesign with Material Design
- 🔍 Added real-time search functionality
- 🌐 Improved desktop sync with connection testing
- ⚡ Async operations with loading indicators
- 📊 Live status and statistics display
- 🎨 Enhanced visual feedback with emojis
- 📱 Better form validation
- 🔄 Threaded network operations
- 📏 Responsive design with dp units
- 🎯 Improved user experience throughout

### Version 1.0
- Basic student management
- Simple list view
- Basic sync functionality
- Minimal UI

---

**Enjoy the improved ERP Mobile App! 🎉**
