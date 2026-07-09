; ============================================================
;  CAMEL-HOT — Inno Setup Script
;  Gera: dist\CamelHot_Setup.exe
;  Compilar: ISCC.exe build_windows\setup.iss
; ============================================================

#define AppName    "CAMEL-HOT"
#define AppVersion "2.1.0"
#define AppPublisher "Kaxatcmd"
#define AppExeName "CamelHot.exe"
#define AppURL     "https://github.com/Kaxatcmd/camel-hot"

[Setup]
AppId={{A3F2C8D1-7B4E-4F9A-B621-0D3E5C8F2A71}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\CamelHot
DefaultGroupName={#AppName}
AllowNoIcons=yes
; Requer elevação (instala em Arquivos de Programas)
PrivilegesRequired=admin
; Output
OutputDir=..\dist
OutputBaseFilename=CamelHot_Setup
; Compressão máxima
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
; Aparência
WizardStyle=modern
WizardResizable=no
; Ícone do instalador (usa o mesmo ícone da app se existir)
SetupIconFile=..\assets\camel_hot.ico
; Imagem de boas-vindas/conclusão (painel esquerdo — 410×797 px)
WizardImageFile=..\assets\installer_sidebar.png
WizardImageStretch=yes
; Imagem de cabeçalho nas páginas internas (55×58 px)
WizardSmallImageFile=..\assets\installer_header.png
; Versão Windows mínima: 10
MinVersion=10.0
; Arquitectura
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[CustomMessages]
english.WelcomeLabel1=Welcome to CAMEL-HOT Setup
english.WelcomeLabel2=CAMEL-HOT is a Harmonic Music Analyzer for DJs.%n%nIt detects key and BPM of your tracks and organizes them using the Camelot Wheel system for perfect harmonic mixing.%n%nThis wizard will guide you through the installation.
english.FinishedLabel=CAMEL-HOT has been successfully installed on your computer.%n%nClick Finish to close the Setup.
portuguese.WelcomeLabel1=Bem-vindo ao instalador do CAMEL-HOT
portuguese.WelcomeLabel2=O CAMEL-HOT e um Analisador Harmonico de Musica para DJs.%n%nDetecta o tom e o BPM das tuas faixas e organiza-as usando o sistema Camelot Wheel para misturas harmonicas perfeitas.%n%nEste assistente vai guiar-te atraves da instalacao.
portuguese.FinishedLabel=O CAMEL-HOT foi instalado com sucesso no teu computador.%n%nClica em Concluir para fechar o assistente.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Conteúdo do build PyInstaller
Source: "..\dist\CamelHot\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Nota: não usar "Flags: ignoreversion" para ficheiros de sistema

[Icons]
; Menu Iniciar
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Comment: "Harmonic Music Analyzer para DJs"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
; Desktop (opcional — confirmado pelo utilizador na tarefa acima)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; Comment: "Harmonic Music Analyzer para DJs"
; Quick Launch (Windows XP/Vista)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunchicon

[Run]
; Opção de lançar a app após instalar
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Limpar ficheiros gerados pela app durante o uso
Type: filesandordirs; Name: "{app}\logs"

[Code]
// Verificar se o utilizador tem Windows 10 ou superior
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsWin64 then begin
    MsgBox('CAMELOT-HOT requires a 64-bit version of Windows 10 or later.', mbError, MB_OK);
    Result := False;
  end;
end;
