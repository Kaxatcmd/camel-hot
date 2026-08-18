# Como fazer build do CAMEL-HOT

Guia completo para gerar os instaladores standalone para Windows, macOS e Linux.  
O resultado final é uma aplicação que **não requer Python instalado** na máquina do utilizador final.

---

## Pré-requisitos

### Todos os sistemas — gerar os ícones primeiro

```bash
pip install Pillow          # uma vez
python3 tools/generate_icons.py
```

Este comando cria todos os assets necessários em `assets/`:
- `camel_hot.ico` — Windows
- `camel_hot.icns` — macOS (apenas em macOS via `iconutil`)
- `camel_hot_512.png` — Linux
- `installer_sidebar.png` / `installer_header.png` — imagens de branding do instalador Windows

> **Nota macOS:** O `camel_hot.icns` é gerado apenas quando o script corre em macOS.  
> Para os outros sistemas, o `.icns` deve ser pré-gerado e incluído no repositório.

### Windows

| Ferramenta | Versão mínima | Link de download |
|---|---|---|
| Python | 3.10+ | https://www.python.org/downloads/ |
| pip | (incluído com Python) | — |
| Pillow | qualquer | `pip install Pillow` |
| PyInstaller | 6.0+ | `pip install pyinstaller` |
| VLC Media Player | 3.0+ | https://www.videolan.org/vlc/download-windows.html |
| Inno Setup | 6.x | https://jrsoftware.org/isdl.php |

> **Nota:** O Python e o pip devem estar no PATH do sistema.  
> Durante a instalação do Python, marca "Add Python to PATH".

### macOS

| Ferramenta | Versão mínima | Instalação |
|---|---|---|
| Python | 3.10+ | https://www.python.org/downloads/macos/ ou `brew install python` |
| Pillow | qualquer | `pip install Pillow` |
| PyInstaller | 6.0+ | `pip install pyinstaller` |
| Homebrew | qualquer | https://brew.sh |
| create-dmg | qualquer | `brew install create-dmg` |
| VLC Media Player | 3.0+ | `brew install --cask vlc` ou https://www.videolan.org/vlc/download-macosx.html |

O bundle suporta macOS 10.15 ou posterior. Gere em Apple Silicon para `arm64`,
em Intel para `x86_64`, ou use `ARCH=universal2` com dependências universais.

### Linux

| Ferramenta | Versão mínima | Instalação |
|---|---|---|
| Python | 3.10+ | `sudo apt-get install python3 python3-pip` |
| Pillow | qualquer | `pip3 install Pillow` |
| PyInstaller | 6.0+ | `pip3 install pyinstaller` |
| VLC + libvlc-dev | 3.0+ | `sudo apt-get install vlc libvlc-dev` |
| libfuse2 | qualquer | `sudo apt-get install libfuse2` |
| curl | qualquer | `sudo apt-get install curl` |

---

## Passos Windows (ordem exacta)

### 1. Gerar ícones

```bat
python tools\generate_icons.py
```

### 2. Copiar bibliotecas nativas do VLC

```bat
build_windows\get_vlc_libs.bat
```

Copia `libvlc.dll`, `libvlccore.dll` e `plugins/` para `vlc_libs/`.  
Sem este passo, a reprodução de áudio não funcionará.

### 3. Fazer o build

```bat
build_windows\build.bat
```

O script:
1. Gera os ícones automaticamente
2. Verifica/instala o PyInstaller
3. Limpa o `dist/` anterior
4. Corre `pyinstaller camel_hot.spec --clean --noconfirm`
5. Se o Inno Setup estiver instalado, gera automaticamente o instalador

### 4. Output

| Ficheiro | Descrição |
|---|---|
| `dist\CamelHot\` | Pasta com a app (pode ser distribuída directamente como zip) |
| `dist\CamelHot_Setup.exe` | Instalador completo com branding (requer Inno Setup) |

---

## Passos macOS (ordem exacta)

### 1. Gerar ícones (inclui .icns via iconutil)

```bash
python3 tools/generate_icons.py
```

### 2. Copiar bibliotecas nativas do VLC

```bash
bash build_macos/get_vlc_libs.sh
```

Copia `libvlc.dylib`, `libvlccore.dylib` e `plugins/` de `/Applications/VLC.app` para `vlc_libs/`.

### 3. Fazer o build

```bash
bash build_macos/build.sh
```

O script gera os ícones, corre o PyInstaller, executa o smoke test de análise e
cria o `.dmg` com `create-dmg`. Para uma release pública assinada e notarizada:

```bash
export MACOS_CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"
export APPLE_ID="release@example.com"
export APPLE_TEAM_ID="TEAMID"
export APPLE_APP_PASSWORD="app-specific-password"
ARCH=universal2 bash build_macos/build.sh
```

### 4. Output

| Ficheiro | Descrição |
|---|---|
| `dist/CamelHot.app` | Bundle macOS (pode ser copiado para /Applications directamente) |
| `dist/CamelHot.dmg` | Imagem de disco para distribuição |

---

## Passos Linux (ordem exacta)

### 1. Gerar ícones

```bash
python3 tools/generate_icons.py
```

### 2. Copiar bibliotecas nativas do VLC

```bash
bash build_linux/get_vlc_libs.sh
```

Copia `libvlc.so`, `libvlccore.so` e `plugins/` para `vlc_libs/`.

### 3. Fazer o build

```bash
bash build_linux/build.sh
```

O script:
1. Gera os ícones
2. Verifica/instala o PyInstaller
3. Corre `pyinstaller camel_hot.spec --clean --noconfirm`
4. Monta o AppDir com `.desktop` e ícone PNG
5. Descarrega o `appimagetool` (automaticamente, uma vez)
6. Empacota tudo como AppImage

### 4. Output

| Ficheiro | Descrição |
|---|---|
| `dist/CamelHot-x86_64.AppImage` | AppImage portátil (corre em qualquer Linux x86_64 moderno) |

### 5. Executar o AppImage

```bash
chmod +x dist/CamelHot-x86_64.AppImage
./dist/CamelHot-x86_64.AppImage
```

---

## Build automático via GitHub Actions (releases)

O repositório inclui `.github/workflows/release.yml` que automatiza o build
para os três sistemas operativos.

### Como criar uma release

```bash
git tag v2.0.0
git push origin v2.0.0
```

A pipeline corre automaticamente e:
1. Compila para Windows, macOS e Linux em paralelo
2. Executa `--smoke-test` no executável congelado em cada plataforma
3. Exige assinatura e notarização macOS para releases por tag
4. Cria uma GitHub Release com os três artefactos

Configure os secrets `MACOS_CODESIGN_IDENTITY`, `APPLE_ID`, `APPLE_TEAM_ID` e
`APPLE_APP_PASSWORD` antes de publicar uma tag. Um disparo manual pode produzir
um DMG não assinado apenas para testes internos.

### Artefactos por plataforma

| Job | Runner | Output |
|---|---|---|
| `build-windows` | `windows-latest` | `CamelHot_Setup.exe` |
| `build-macos` | `macos-latest` | `CamelHot.dmg` |
| `build-linux` | `ubuntu-22.04` | `CamelHot-x86_64.AppImage` |

### Trigger manual

Podes activar a pipeline manualmente via GitHub Actions → "Release Build" → "Run workflow".

---

## Testar o build

### Windows
- Instalar `CamelHot_Setup.exe` numa **VM Windows 10/11 limpa** (sem Python instalado)
- Verificar que o branding aparece no instalador (logo no painel esquerdo)
- Verificar que a app abre e consegue analisar um ficheiro de áudio
- Verificar que o VLC reproduz o áudio
- Executar `dist\CamelHot\CamelHot.exe --smoke-test` antes de criar o instalador

### macOS
- Copiar `CamelHot.dmg` para outro Mac (diferente do Mac de build)
- Abrir o `.dmg`, arrastar para `/Applications`, lançar
- Verificar assinatura e Gatekeeper: `spctl --assess --type execute --verbose=4 /Applications/CamelHot.app`
- Executar `dist/CamelHot.app/Contents/MacOS/CamelHot --smoke-test`

### Linux
- Copiar o `.AppImage` para outra máquina Linux (sem Python instalado)
- `chmod +x CamelHot-x86_64.AppImage && ./CamelHot-x86_64.AppImage`
- `APPIMAGE_EXTRACT_AND_RUN=1 ./CamelHot-x86_64.AppImage --smoke-test`

---

## Tamanho esperado

| Ficheiro | Tamanho estimado |
|---|---|
| `CamelHot_Setup.exe` | ~300–400 MB |
| `CamelHot.dmg` | ~300–400 MB |
| `CamelHot-x86_64.AppImage` | ~350–450 MB |

O tamanho elevado deve-se ao bundling de Python, librosa, NumPy/SciPy e VLC.

---

## Estrutura dos ficheiros de build

```
camel-hot/
├── tools/
│   └── generate_icons.py       ← Gerador de ícones e assets do instalador
├── assets/
│   ├── camel_mascot.png        ← Imagem fonte (1536×1024)
│   ├── camel_hot.ico           ← Ícone Windows (gerado)
│   ├── camel_hot.icns          ← Ícone macOS (gerado em macOS)
│   ├── camel_hot_512.png       ← Ícone Linux 512×512 (gerado)
│   ├── camel_hot.desktop       ← Metadados app Linux (para AppImage)
│   ├── installer_sidebar.png   ← Imagem de branding do instalador 410×797 (gerada)
│   └── installer_header.png    ← Cabeçalho do instalador 55×58 (gerado)
├── camel_hot.spec              ← Configuração do PyInstaller
├── vlc_libs/                   ← Libs VLC copiadas pelos scripts get_vlc_libs
├── build_windows/
│   ├── build.bat               ← Script de build Windows
│   ├── get_vlc_libs.bat        ← Copia libs VLC (Windows)
│   └── setup.iss               ← Script Inno Setup (instalador com branding)
├── build_macos/
│   ├── build.sh                ← Script de build macOS
│   └── get_vlc_libs.sh         ← Copia libs VLC (macOS)
├── build_linux/
│   ├── build.sh                ← Script de build Linux (AppImage)
│   └── get_vlc_libs.sh         ← Copia libs VLC (Linux)
├── .github/workflows/
│   ├── ci.yml                  ← CI: testes em push/PR
│   └── release.yml             ← Release: builds de distribuição em tags v*
└── dist/                       ← Output gerado (ignorado pelo git)
    ├── CamelHot/               ← Windows: pasta da app
    ├── CamelHot_Setup.exe      ← Windows: instalador
    ├── CamelHot.app            ← macOS: bundle
    ├── CamelHot.dmg            ← macOS: imagem de disco
    └── CamelHot-x86_64.AppImage ← Linux: AppImage portátil
```

---

## Troubleshooting comum

### librosa não encontra ficheiros de áudio
- Verificar os `hiddenimports` no `camel_hot.spec`
- Adicionar qualquer módulo em falta e repetir o build

### VLC não reproduz áudio na app compilada
- Confirmar que o script `get_vlc_libs` da plataforma foi corrido **antes** do build
- Verificar que `vlc_libs/plugins/` existe e tem conteúdo
- Confirmar que o VLC instalado tem a mesma arquitectura (64-bit) da app

### App não arranca no macOS ("app danificada")
- Confirmar que a release foi assinada e notarizada com `spctl --assess --type execute --verbose=4 /Applications/CamelHot.app`
- Não distribua um DMG sem assinatura/notarização; configure os secrets de release indicados acima e volte a gerar o artefacto.

### App não arranca no Windows ("DLL não encontrada")
- Instalar os Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Verificar que todas as DLLs do VLC estão em `dist\CamelHot\`

### AppImage não abre no Linux
- Confirmar que `libfuse2` está instalado: `sudo apt-get install libfuse2`
- Confirmar que o ficheiro tem permissão de execução: `chmod +x CamelHot-x86_64.AppImage`

### Build falha com "ModuleNotFoundError"
- Verificar que o ambiente Python de build tem todas as dependências:
  ```
  pip install -r requirements.txt
  ```

### Ícone não aparece na app
- Correr `python3 tools/generate_icons.py` para regenerar os ícones
- Os ficheiros gerados (`camel_hot.ico`, etc.) devem existir em `assets/` antes do build

---

## Assinatura de código (distribuição pública)

Para distribuição pública sem avisos de segurança:

- **Windows:** Assinar `CamelHot.exe` com um certificado Code Signing (EV ou OV)
- **macOS:** Assinar com Apple Developer ID + Notarização (`xcrun notarytool`)

O build macOS executa estes passos quando as variáveis de ambiente de assinatura
estão configuradas. Releases de tag falham deliberadamente sem essas credenciais.

