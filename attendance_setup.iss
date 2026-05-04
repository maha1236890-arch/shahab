; attendance_setup.iss  —  Inno Setup Script
; يُنتج مثبّت Windows احترافي لنظام الحضور والغياب

#define AppName "شهاب"
#define AppVersion "2.0.0"
#define AppPublisher "MGG Software"
#define AppExeName "attendance.exe"
#define AppId "{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\AttendanceSystem
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=attendance_setup_v{#AppVersion}
; SolidCompression=yes
Compression=lzma2/ultra64
WizardStyle=modern
SetupIconFile=static\img\icon.ico
PrivilegesRequired=admin
CloseApplications=yes
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "إنشاء أيقونة على سطح المكتب"; GroupDescription: "أيقونات إضافية:";

[Files]
; نسخ مجلد البناء كاملاً
Source: "dist\attendance\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\إلغاء التثبيت"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "تشغيل البرنامج الآن"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; حذف قاعدة البيانات عند إلغاء التثبيت (اختياري — احذف هذا السطر لحفظ البيانات)
; Type: filesandordirs; Name: "{app}\attendance.db"
