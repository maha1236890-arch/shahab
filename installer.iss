; Inno Setup Script - نظام إدارة الموظفين
; يُنشئ مثبّت ويندوز مع اختصار سطح المكتب وقائمة Start

#define AppName "نظام إدارة الموظفين"
#define AppVersion "3.0"
#define AppPublisher "شهاب"
#define AppExeName "نظام_إدارة_الموظفين.exe"
#define AppId "{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://github.com/maha1236890-arch/shahab
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=installer_output
OutputBaseFilename=تثبيت_نظام_الموظفين_v3
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; دعم العربية
ShowLanguageDialog=no
; أيقونة المثبّت
SetupIconFile=app_icon.ico
; لا يحتاج صلاحيات مشرف
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; إظهار اتفاقية ترخيص (اختياري - احذف السطرين التاليين إذا لا تريد)
; LicenseFile=LICENSE.txt

[Languages]
Name: "arabic"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "إنشاء اختصار على سطح المكتب"; GroupDescription: "اختصارات إضافية:"
Name: "startmenuicon"; Description: "إضافة إلى قائمة ابدأ"; GroupDescription: "اختصارات إضافية:"

[Files]
; الملف التنفيذي الرئيسي
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; اختصار قائمة Start
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\إزالة {#AppName}"; Filename: "{uninstallexe}"

; اختصار سطح المكتب (فقط إذا اختار المستخدم)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; تشغيل التطبيق بعد التثبيت (اختياري)
Filename: "{app}\{#AppExeName}"; Description: "تشغيل {#AppName} الآن"; Flags: nowait postinstall skipifsilent
