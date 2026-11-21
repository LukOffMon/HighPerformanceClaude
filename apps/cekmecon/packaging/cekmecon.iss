; Inno Setup 6 script for the Windows installer of Toilet Bamboo Paper Çekmecón.
; Built by packaging/build.py (defines AppVersion, SrcDir, IconFile). Per-user install, no admin rights.
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{6F1B3C2A-7E44-4C1D-9B0E-CEC0B4AB0001}
AppName=Çekmecón
AppVerName=Toilet Bamboo Paper Çekmecón {#AppVersion}
AppVersion={#AppVersion}
AppPublisher=LukOffMon
AppPublisherURL=https://lukoffmon.github.io/HighPerformanceClaude/cekmecon/
DefaultDirName={localappdata}\Programs\Cekmecon
DefaultGroupName=Çekmecón
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=Cekmecon-Setup-Windows
SetupIconFile={#IconFile}
UninstallDisplayIcon={app}\Cekmecon.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#SrcDir}\Cekmecon.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SrcDir}\cekmecon-cli.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Çekmecón"; Filename: "{app}\Cekmecon.exe"
Name: "{autodesktop}\Çekmecón"; Filename: "{app}\Cekmecon.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Cekmecon.exe"; Description: "{cm:LaunchProgram,Çekmecón}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\cekmecon-cli.exe"; Parameters: "disconnect"; Flags: runhidden; RunOnceId: "DisconnectClaude"
