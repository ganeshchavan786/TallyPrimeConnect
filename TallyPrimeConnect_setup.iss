; Inno Setup Script for TallyPrime Connect App
; SEE THE INNO SETUP DOCUMENTATION FOR DETAILS!

#define MyAppName "TallyPrime Connect App"
#define MyAppVersion "1.1.0"  // <-- !! UPDATE Your Final App Version !!
#define MyAppPublisher "Your Company or Name" // <-- !! UPDATE Publisher !!
#define MyAppURL "https://your-website.com" // <-- !! UPDATE URL (Optional) !!
#define MyAppExeName "TallyPrimeConnectApp.exe" // Matches PyInstaller output name
#define SourceBuildDir "dist\TallyPrimeConnectApp" // Relative path to PyInstaller output
#define MyAppIcon "assets\logo.ico"            // Relative path to app icon for setup
#define LicenseFileName "LICENSE.txt"          // Optional: Create and specify License File name
#define OutputDir "Release"                   // Subdirectory for the final setup file

[Setup]
; Unique AppId is CRUCIAL for uninstall/updates. Generate a new one!
AppId={{NEW-GUID-HERE} ; <-- !! GENERATE a new GUID from https://www.guidgenerator.com/ !!
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation Directories
DefaultDirName={autopf}\{#MyAppName} ; Install in "C:\Program Files\TallyPrime Connect App"
DefaultGroupName={#MyAppName} ; Start Menu Folder Name
DisableProgramGroupPage=yes ; Keep Start Menu simple

; Installation Options & Appearance
AllowNoIcons=yes ; Allow user to skip shortcut creation
LicenseFile={#LicenseFileName} ; Uncomment or set if you have a LICENSE.txt/.rtf
OutputBaseFilename=TallyPrimeConnectApp-{#MyAppVersion}-setup ; Setup file name
OutputDir={#OutputDir} ; Where to save the setup.exe
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin ; Need admin for Program Files, registry, uninstaller
; Ensure architecture matches your Python/PyInstaller build (usually x64)
ArchitecturesInstallIn64BitMode=x64
; Use the same icon for setup and uninstaller display
SetupIconFile={#MyAppIcon}
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

; --- Code Signing (Optional but Recommended) ---
; If you have a certificate:
; SignTool=YourSignToolPath $p ; Use $p for prompt or specify parameters below
; Example SignTool parameters:
; SignTool=signtool sign /f "C:\Path\To\Your\certificate.pfx" /p YourPassword /t http://timestamp.comodoca.com/authenticode /v $f
; SignedUninstaller=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Optional Tasks for the user during installation
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
; Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 0,6.1 ; Deprecated

[Files]
; Copy ALL files and subdirectories from the PyInstaller output directory to the installation directory ({app})
Source: "{#SourceBuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: This copies the default config files too. The app will create .db and .log inside the installed {app}\config folder.

[Icons]
; Start Menu Shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIcon}"
; Desktop Shortcut (only if task selected)
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppIcon}"
; Quick Launch Shortcut (only if task selected - deprecated)
; Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon; IconFilename: "{app}\{#MyAppIcon}"
; Uninstaller entry in Start Menu
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; IconFilename: "{app}\{#MyAppIcon}"

[Run]
; Option to launch the application after setup completes
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent unchecked

[UninstallDelete]
; Clean up during uninstall - Remove the entire application directory
Type: filesandordirs; Name: "{app}"

; Optional: Remove specific registry keys if created during install
; Type: registry; Root: HKLM; Subkey: "Software\YourCompany\{#MyAppName}"

[Registry]
; Optional: Example - Write install path to registry (useful for other apps or diagnostics)
; Root: HKLM; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekeyifempty
; Ensure Uninstall information has the correct install location
; Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#AppId}_is1"; ValueType: string; ValueName: "InstallLocation"; ValueData: "{app}"; Flags: uninsdeletevalue

; --- Custom Pascal Script Code ---
[Code]
// Function to check minimum RAM
function CheckMemory(MinMB: Integer): Boolean;
var
  MemInfo: TMemoryStatus;
begin
  MemInfo.dwLength := SizeOf(MemInfo);
  GlobalMemoryStatus(MemInfo);
  Result := (MemInfo.ullTotalPhys div 1024 div 1024) >= MinMB;
  if not Result then
    MsgBox(Format('This program requires at least %d MB of RAM. Your system has %d MB.', [MinMB, MemInfo.ullTotalPhys div 1024 div 1024]), mbError, MB_OK);
end;

// Function to check minimum disk space on the installation drive
function CheckDiskSpace(MinMB: Integer): Boolean;
var
  FreeBytes, TotalBytes, TotalFreeBytes: Int64;
  Drive: String;
begin
  Drive := ExpandConstant('{drive:{app}}'); // Check drive where app will be installed
  if GetDiskFreeSpaceEx(Drive, FreeBytes, TotalBytes, TotalFreeBytes) then
  begin
    Result := (FreeBytes div 1024 div 1024) >= MinMB;
    if not Result then
      MsgBox(Format('Setup requires at least %d MB of free space on drive %s. You have %d MB available.', [MinMB, Drive, FreeBytes div 1024 div 1024]), mbError, MB_OK);
  end else begin // Failed to get disk space (network drive? permissions?)
    Log(Format('Could not check disk space on drive %s.', [Drive]));
    Result := True; // Allow install to proceed, or set to False to block
  end;
end;

// --- Main Initialization Check ---
function InitializeSetup(): Boolean;
begin
  // --- Pre-Checks ---
  // Check OS Version (Windows 7 = 6.1, Windows 8 = 6.2, Windows 10/11 = 10.0+)
  // Inno Setup handles basic version checks better with MinVersion directive if needed,
  // but explicit check can give custom message. Let's assume Win 7+ support.
  // if GetWindowsVersion < $06010000 then begin... end;

  // Check Minimum RAM (e.g., 512 MB) - Adjust as needed!
  if not CheckMemory(512) then // <-- !! ADJUST RAM REQUIREMENT !!
  begin
    Result := False; Exit; // Stop setup if check fails
  end;

  // Check Minimum Disk Space (e.g., 250 MB) - Estimate based on PyInstaller output size
  if not CheckDiskSpace(250) then // <-- !! ADJUST DISK SPACE REQUIREMENT !!
  begin
    Result := False; Exit; // Stop setup if check fails
  end;

  // --- Dependency Checks (Placeholders - Customize if needed) ---
  // Example: Check for a specific file indicating another required app
  // if not FileExists(ExpandConstant('{pf}\Common Files\SomeDependency\required.dll')) then
  // begin
  //   MsgBox('This application requires [Dependency Name] to be installed.', mbError, MB_OK);
  //   Result := False; Exit;
  // end;
  // Example: Check for .NET (Requires ISPP or custom functions usually)
  // if not IsDotNetInstalled(...) then ... Result := False; Exit;

  // If all checks pass
  Log('System pre-checks passed.');
  Result := True;
end;