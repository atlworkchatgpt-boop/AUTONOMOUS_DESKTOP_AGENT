#define MyAppName "Autonomous AI"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Shreyansh Ray"

[Setup]
AppId={{A8F2D7B1-5C9A-4A91-B3F0-ADA2026A0001}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\Autonomous AI
DefaultGroupName=Autonomous AI

OutputDir=output
OutputBaseFilename=AutonomousAI_Setup

Compression=lzma
SolidCompression=yes
WizardStyle=modern

PrivilegesRequired=lowest

[Files]
Source: "..\installer\dist\AutonomousAI\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Autonomous AI"; Filename: "{app}\AutonomousAI\AutonomousAI.exe"
Name: "{commondesktop}\Autonomous AI"; Filename: "{app}\AutonomousAI\AutonomousAI.exe"

[Run]
Filename: "{app}\AutonomousAI\AutonomousAI.exe"; Description: "Launch Autonomous AI"; Flags: nowait postinstall skipifsilent
