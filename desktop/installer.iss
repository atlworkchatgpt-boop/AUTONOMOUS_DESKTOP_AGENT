[Setup]
AppName=Autonomous Desktop AI
AppVersion=1.0
DefaultDirName={autopf}\Autonomous Desktop AI
DefaultGroupName=Autonomous Desktop AI
OutputDir=dist
OutputBaseFilename=AutonomousAI_Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\AutonomousAI\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\Autonomous Desktop AI"; Filename: "{app}\AutonomousAI.exe"
Name: "{commondesktop}\Autonomous Desktop AI"; Filename: "{app}\AutonomousAI.exe"
