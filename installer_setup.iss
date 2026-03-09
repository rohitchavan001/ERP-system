; ERP-System Professional Installer Script
; Creates a Windows installer like Microsoft software

#define MyAppName "ERP-System"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "ERP-System"
#define MyAppExeName "ERP-System.exe"

[Setup]
; Basic Information
AppId={{8F9A2B3C-4D5E-6F7A-8B9C-0D1E2F3A4B5C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
OutputDir=installer_output
OutputBaseFilename=ERP-System-Setup
SetupIconFile=
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

; User can choose installation directory
DisableDirPage=no
DisableProgramGroupPage=no

; Modern UI
WizardImageFile=compiler:WizModernImage-IS.bmp
WizardSmallImageFile=compiler:WizModernSmallImage-IS.bmp

; Uninstall
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable and all files from dist\ERP-System
Source: "dist\ERP-System\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Dirs]
; Create data directories in AppData for user data (survives uninstall/reinstall)
Name: "{userappdata}\ERP_System"; Permissions: users-full
Name: "{userappdata}\ERP_System\database"; Permissions: users-full
Name: "{userappdata}\ERP_System\aadhaar_images"; Permissions: users-full
Name: "{userappdata}\ERP_System\student_cards"; Permissions: users-full
Name: "{userappdata}\ERP_System\logs"; Permissions: users-full

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Desktop shortcut (if user selected)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; Quick Launch shortcut (if user selected)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Option to launch after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  DataDirPage: TInputDirWizardPage;

procedure InitializeWizard;
begin
  { Create custom page for data directory selection }
  DataDirPage := CreateInputDirPage(wpSelectDir,
    'Select Data Storage Location', 
    'Where should ERP-System store your data?',
    'Student data, photos, and ID cards will be stored here.' + #13#10 + 
    'This location is separate from the program files, so your data is safe during updates.' + #13#10#13#10 +
    'Recommended: Keep the default location (AppData folder)',
    False, '');
  DataDirPage.Add('');
  DataDirPage.Values[0] := ExpandConstant('{userappdata}\ERP_System');
end;

function GetDataDir(Param: String): String;
begin
  Result := DataDirPage.Values[0];
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  DataDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    DataDir := DataDirPage.Values[0];
    
    { Create data directories }
    if not DirExists(DataDir) then
      CreateDir(DataDir);
    if not DirExists(DataDir + '\database') then
      CreateDir(DataDir + '\database');
    if not DirExists(DataDir + '\aadhaar_images') then
      CreateDir(DataDir + '\aadhaar_images');
    if not DirExists(DataDir + '\student_cards') then
      CreateDir(DataDir + '\student_cards');
    if not DirExists(DataDir + '\logs') then
      CreateDir(DataDir + '\logs');
      
    { Save data directory path to config file }
    SaveStringToFile(ExpandConstant('{app}\data_path.txt'), DataDir, False);
  end;
end;

[UninstallDelete]
; Clean up config file on uninstall (but preserve user data)
Type: files; Name: "{app}\data_path.txt"

[Messages]
WelcomeLabel1=Welcome to [name] Setup
WelcomeLabel2=This will install [name/ver] on your computer.%n%nERP-System is a complete Student Management System with:%n%n• Student Registration%n• QR Code & ID Card Generation%n• Dashboard & Analytics%n• Renewal System%n• Expiry Notifications%n%nYour data will be stored safely and will not be lost during updates.
FinishedLabel=Setup has finished installing [name] on your computer.%n%nDefault Login:%nUsername: admin%nPassword: 1234
