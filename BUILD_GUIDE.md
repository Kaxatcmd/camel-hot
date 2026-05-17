# Como fazer build do CAMEL-HOT

Guia completo para gerar os instaladores standalone para Windows e macOS.  
O resultado final é uma aplicação que **não requer Python instalado** na máquina do utilizador final.

---

## Pré-requisitos

### Windows

| Ferramenta | Versão mínima | Link de download |
|---|---|---|
| Python | 3.10+ | https://www.python.org/downloads/ |
| pip | (incluído com Python) | — |
| PyInstaller | 6.0+ | `pip install pyinstaller` |
| VLC Media Player | 3.0+ | https://www.videolan.org/vlc/download-windows.html |
| Inno Setup | 6.x | https://jrsoftware.org/isdl.php |

> **Nota:** O Python e o pip devem estar no PATH do sistema.  
> Durante a instalação do Python, marca "Add Python to PATH".

### macOS

| Ferramenta | Versão mínima | Instalação |
|---|---|---|
| Python | 3.10+ | https://www.python.org/downloads/macos/ ou `brew install python` |
| PyInstaller | 6.0+ | `pip install pyinstaller` |
| Homebrew | qualquer | https://brew.sh |
| create-dmg | qualquer | `brew install create-dmg` |
| VLC Media Player | 3.0+ | `brew install --cask vlc` ou https://www.videolan.org/vlc/download-macosx.html |

---

## Passos Windows (ordem exacta)

### 1. Copiar bibliotecas nativas do VLC

```bat
build_windows\get_vlc_libs.bat
```

Este script localiza o VLC instalado e copia `libvlc.dll`, `libvlccore.dll` e a pasta `plugins/` para `vlc_libs/`.  
Sem este passo, a reprodução de áudio não funcionará na app compilada.

### 2. Fazer o build

```bat
build_windows\build.bat
```

O script:
1. Verifica/instala o PyInstaller
2. Limpa o `dist/` anterior
3. Corre `pyinstaller camel_hot.spec --clean --noconfirm`
4. Se o Inno Setup estiver instalado, gera automaticamente o instalador

### 3. Output

| Ficheiro | Descrição |
|---|---|
| `dist\CamelHot\` | Pasta com a app (pode ser distribuída diretamente como zip) |
| `dist\CamelHot_Setup.exe` | Instalador completo (requer Inno Setup no passo 2) |

---

## Passos macOS (ordem exacta)

### 1. Copiar bibliotecas nativas do VLC

```bash
bash build_macos/get_vlc_libs.sh
```

Copia `libvlc.dylib`, `libvlccore.dylib` e `plugins/` de `/Applications/VLC.app` para `vlc_libs/`.

### 2. Fazer o build

```bash
bash build_macos/build.sh
```

O script corre o PyInstaller e depois cria a imagem `.dmg` com o `create-dmg`.

### 3. Output

| Ficheiro | Descrição |
|---|---|
| `dist/CamelHot.app` | Bundle macOS (pode ser copiado para /Applications directamente) |
| `dist/CamelHot.dmg` | Imagem de disco para distribuição |

---

## Testar o build

### Windows
- Instalar `CamelHot_Setup.exe` numa **VM Windows 10/11 limpa** (sem Python instalado)
- Verificar que a app abre e consegue analisar um ficheiro de áudio
- Verificar que o VLC reproduz o áudio (requer que os `vlc_libs/` tenham sido incluídos)

### macOS
- Copiar `CamelHot.dmg` para outro Mac (diferente do Mac de build)
- Abrir o `.dmg`, arrastar para `/Applications`, lançar
- Se aparecer aviso de segurança: **Preferências do Sistema → Segurança e Privacidade → Permitir**
- Para apps não assinadas via Terminal: `xattr -dr com.apple.quarantine /Applications/CamelHot.app`

---

## Tamanho esperado

| Ficheiro | Tamanho estimado |
|---|---|
| `CamelHot_Setup.exe` | ~300–400 MB |
| `CamelHot.dmg` | ~300–400 MB |

O tamanho elevado deve-se ao bundling de Python, librosa, NumPy/SciPy e VLC.

---

## Estrutura dos ficheiros de build

```
camel-hot/
├── camel_hot.spec              ← Configuração do PyInstaller
├── vlc_libs/                   ← Libs VLC copiadas pelos scripts get_vlc_libs
│   ├── libvlc.dll / libvlc.dylib
│   ├── libvlccore.dll / libvlccore.dylib
│   └── plugins/
├── build_windows/
│   ├── build.bat               ← Script de build Windows
│   ├── get_vlc_libs.bat        ← Copia libs VLC (Windows)
│   └── setup.iss               ← Script Inno Setup (instalador)
├── build_macos/
│   ├── build.sh                ← Script de build macOS
│   └── get_vlc_libs.sh         ← Copia libs VLC (macOS)
└── dist/                       ← Output gerado (ignorado pelo git)
    ├── CamelHot/               ← Windows: pasta da app
    ├── CamelHot_Setup.exe      ← Windows: instalador
    ├── CamelHot.app            ← macOS: bundle
    └── CamelHot.dmg            ← macOS: imagem de disco
```

---

## Troubleshooting comum

### librosa não encontra ficheiros de áudio
- Verificar os `hiddenimports` no `camel_hot.spec`
- Adicionar qualquer módulo em falta e repetir o build

### VLC não reproduz áudio na app compilada
- Confirmar que `build_windows/get_vlc_libs.bat` (ou `build_macos/get_vlc_libs.sh`) foi corrido **antes** do build
- Verificar que `vlc_libs/plugins/` existe e tem conteúdo
- Confirmar que o VLC instalado no sistema de build tem a mesma arquitectura (64-bit) da app

### App não arranca no macOS ("app danificada")
- Correr no Terminal: `xattr -dr com.apple.quarantine /Applications/CamelHot.app`
- Ou: **Preferências do Sistema → Segurança e Privacidade → Permitir mesmo assim**

### App não arranca no Windows ("DLL não encontrada")
- Instalar os Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Verificar que todas as DLLs do VLC estão em `dist\CamelHot\`

### Build falha com "ModuleNotFoundError" durante a análise
- Verificar que o ambiente Python de build tem todas as dependências instaladas:
  ```
  pip install -r requirements.txt
  ```
- Correr o build dentro do venv usado para o desenvolvimento

### Ícone não aparece na app
- Criar `assets/camel_hot.ico` (Windows, 256×256px, formato ICO)
- Criar `assets/camel_hot.icns` (macOS, formato ICNS)
- O `camel_hot.spec` usa-os automaticamente se existirem

---

## Assinatura de código (distribuição pública)

Para distribuição pública sem avisos de segurança:

- **Windows:** Assinar `CamelHot.exe` com um certificado Code Signing (EV ou OV)
- **macOS:** Assinar com Apple Developer ID + Notarização (`xcrun notarytool`)

Estes passos estão fora do âmbito deste guia mas são necessários para distribuição na App Store ou via download directo sem avisos do Gatekeeper/SmartScreen.
