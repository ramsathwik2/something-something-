; ───────────────────────────────────────────────
;  Taskbar Kitten ♥ — Gift Edition Installer
;  Made with ♥ for you — modern, warm & gift-beautiful
;  Wizard images: wizard.bmp (164x314) + wizard_small.bmp (55x55)
;  Generated via Pillow from assets\sprites\frame_4.png
; ───────────────────────────────────────────────
#define MyAppName "Madhu"
#define MyAppNameLong "Madhu — Taskbar Kitten ♥"
#define MyAppVersion "1.0"
#define MyAppPublisher "KITTY — with ♥"
#define MyAppPublisherURL "https://github.com"
#define MyAppExeName "Kitty.exe"
#define MyAppComments "A little gift full of purrs, warmth & love ♡ — for Madhu"
#define MyAppCopyright "Made with ♥ for Madhu — 2026"

[Setup]
AppId={{KITTY-TASKBAR-PET-2026-MADHU}}
AppName={#MyAppName}
AppVerName={#MyAppNameLong} {#MyAppVersion}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppPublisherURL}
AppSupportURL={#MyAppPublisherURL}
AppComments={#MyAppComments}
AppCopyright={#MyAppCopyright}
VersionInfoDescription=Madhu — Taskbar Kitten ♥ — Gift Edition
VersionInfoCopyright={#MyAppCopyright}
VersionInfoProductName={#MyAppNameLong}
VersionInfoVersion={#MyAppVersion}
AppUpdatesURL={#MyAppPublisherURL}
DefaultDirName={autopf}\Madhu
DefaultGroupName={#MyAppNameLong}
AllowNoIcons=yes
OutputDir=..
OutputBaseFilename=KittySetup
SetupIconFile=kitty.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppNameLong}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
WizardImageFile=wizard.bmp
WizardSmallImageFile=wizard_small.bmp
WizardImageStretch=no
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=no
CloseApplications=yes
RestartApplications=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ShowLanguageDialog=no
WindowVisible=no
BackSolid=no
; Gift palette (used in [Code] + wizard BMPs):
;  top #FFF8FA / mid #FFD1DC / bottom #FF8AA2 / accent #FF6B8A / cream #FFF5EF
UsePreviousAppDir=yes
DirExistsWarning=auto

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; ── Gift-style messages ──
[Messages]
english.WelcomeLabel1=Welcome to [name] — A Little Gift Full of Purrs! ♥
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nA tiny kitten will soon keep your taskbar warm and loved — made with ♥ just for you, Madhu. No whiskers harmed, just pure coziness!%n%n✨ Click Next to unwrap your gift, or Cancel to gently close this little box.
english.FinishedHeadingLabel=Your gift is ready, Madhu! ♥  Thank you for installing [name]
english.FinishedLabel=[name] has been installed.%n%nYour new taskbar kitten is already stretching and waiting to say hello!%n%n♡ Click Finish to meet your purr-friend. May it bring tiny smiles every day — with love, KITTY.
english.ClickFinish=Finish ♥
english.SetupWindowTitle={#MyAppNameLong} — Gift Setup ♥
english.BeveledLabel= ♡  with love for Madhu  ♡

[CustomMessages]
english.WelcomeGift=Unwrapping your purr-gift...
english.LaunchGift=Meet your kitten now!

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut ♡"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Launch at startup (kitten greets you at boot) ♥"; GroupDescription: "Startup & Love:"; Flags: unchecked

[Files]
Source: "..\dist\Kitty\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppNameLong}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppNameLong}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppNameLong}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "MadhuKitten"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppNameLong, '&', '&&')}}"; Flags: nowait postinstall skipifsilent unchecked

; ── Custom colors & gift polish ──
[Code]
procedure InitializeWizard;
begin
  // Gift palette — soft modern pinks, keep compile-safe
  WizardForm.Color := $FAF8FF; // #FFF8FA (BGR)
  WizardForm.WelcomeLabel1.Font.Color := $5541A5; // #A54155 rose
  WizardForm.WelcomeLabel2.Font.Color := $61417A; // deeper rose
  WizardForm.WelcomeLabel1.Font.Style := [fsBold];
  WizardForm.WelcomeLabel1.Font.Size := 12;
  WizardForm.WelcomeLabel2.Font.Size := 9;

  WizardForm.FinishedHeadingLabel.Font.Color := $5541A5;
  WizardForm.FinishedHeadingLabel.Font.Style := [fsBold];
  WizardForm.FinishedHeadingLabel.Font.Size := 12;
  WizardForm.FinishedLabel.Font.Color := $61417A;

  // Header labels for modern wizard
  WizardForm.PageDescriptionLabel.Font.Color := $61417A;
  WizardForm.PageNameLabel.Font.Color := $5541A5;
  WizardForm.PageNameLabel.Font.Style := [fsBold];

  // Beveled label gift text already set via [Messages], ensure center
  WizardForm.BeveledLabel.Font.Color := $C08FA0;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  // Keep gift warmth on every page
  if CurPageID = wpWelcome then
    WizardForm.WelcomeLabel1.Caption := 'Welcome to Madhu ♥ — Your Taskbar Kitten';
  if CurPageID = wpFinished then
    WizardForm.FinishedHeadingLabel.Caption := 'Your gift is ready, Madhu! ♥';
end;
