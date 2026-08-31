#define MyAppName "Autonomous AI"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Shreyansh Ray"

[Setup]
AppId={{A0B1C2D3-E4F5-4678-9012-AUTONOMOUSAI}}
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

[Files]
Source: "..\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Autonomous AI"; Filename: "{app}\START_AUTONOMOUS_AI.bat"
Name: "{commondesktop}\Autonomous AI"; Filename: "{app}\START_AUTONOMOUS_AI.bat"

[Run]
Filename: "{app}\START_AUTONOMOUS_AI.bat"; Description: "Launch Autonomous AI"; Flags: postinstall nowait skipifsilent
