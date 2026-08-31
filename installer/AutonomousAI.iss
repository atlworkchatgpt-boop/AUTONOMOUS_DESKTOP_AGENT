#define MyAppName "Autonomous AI"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Shreyansh Ray"

[Setup]

AppId={{7D4B9F7B-ADA1-4F75-9A31-8C5D2A1F0001}}

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

Source: "..\installer\dist\AutonomousAI\*";
DestDir: "{app}";
Flags: recursesubdirs ignoreversion

Source: "..\START_AUTONOMOUS_AI.bat";
DestDir: "{app}";
Flags: ignoreversion

[Icons]

Name: "{group}\Autonomous AI";
Filename: "{app}\AutonomousAI.exe"

Name: "{commondesktop}\Autonomous AI";
Filename: "{app}\AutonomousAI.exe"

[Run]

Filename: "{app}\AutonomousAI.exe";
Description: "Launch Autonomous AI";
Flags: nowait postinstall skipifsilent

