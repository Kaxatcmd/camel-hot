# 🎧 DJ Harmonic Analyzer v2.0 - GUI Edition

Uma aplicação Python com **interface gráfica** que analisa sua música, detecta tonalidades e BPM, e organiza sua biblioteca para mixagem harmônica profissional como feita por DJs!

## 🚀 Instalação Rápida

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar o programa (vai abrir a interface gráfica)
python main.py
```

## 📖 Como Usar

### 1️⃣ **Analisar uma Música Individual**

1. Abra a aba "🔍 Analisar"
2. Clique em "Procurar" para selecionar um arquivo MP3/WAV/FLAC
3. Clique em "🎵 Analisar Música"
4. Veja os resultados:
   - **Tonalidade**: Ex: "C Major" (Tom Maior em Dó)
   - **Camelot**: Ex: "8B" (notação DJ)
   - **BPM**: Batidas por minuto
   - **Duração**: Tempo total em segundos

### 2️⃣ **Organizar Sua Biblioteca Completa**

1. Abra a aba "📂 Organizar"
2. Selecione a pasta com suas músicas (entrada)
3. Selecione onde salvar os arquivos organizados (saída)
4. Escolha: Copiar ou Mover (cuidado: move remove originals!)
5. Clique "⚙️ Organizar Biblioteca"
6. Resultado: Pasta organizada em subpastas por tonalidade
   - `output_audio/8A/` → Todas as músicas em A Minor
   - `output_audio/8B/` → Todas as músicas em C# Major
   - etc...

### 3️⃣ **Criar Playlist Harmônica**

1. Abra a aba "📝 Playlist"
2. Selecione pasta com as músicas
3. Defina o nome do arquivo (ex: `minha_mix.m3u`)
4. **(Opcional)** Configure filtros:
   - Tonalidade Camelot (ex: 8A)
   - Intervalo de BPM (ex: 120-130)
   - Limite de músicas (ex: 50)
5. Clique "📝 Criar Playlist"
6. Abra o arquivo `.m3u` em seu player de DJ favorito!

### 4️⃣ **Verificar Compatibilidade de Chaves**

1. Abra a aba "✅ Compatibilidade"
2. Selecione uma tonalidade Camelot (ex: 8A)
3. Clique "🔍 Ver Compatibilidade"
4. Veja todas as chaves que harmonizam bem!

## 🎼 O Sistema Camelot Explicado

É como um **relógio musical** para DJs:

```
        12B    1B    2B
     11B    ════    3B
   10B   A Minor  ════   4B
     9B   (12A)   5B
        8B    7B    6B

         8A    7A    6A
       9A   (12B)   5A
     10A  E Major  ════   4A
       11A  (7B)   3A
         12A   1A    2A
```

- **Números**: 1-12 (as 12 notas musicais)
- **A**: Tom Menor (som triste/escuro)
- **B**: Tom Maior (som alegre/brilhante)

**Exemplo de compatibilidade com 8A:**
- ✅ 8A (mesma chave)
- ✅ 8B (maior relativo)
- ✅ 7A (um passo para trás)
- ✅ 9A (um passo para frente)
- ✅ 7B, 9B (relativos dos adjacentes)

## 📁 Estrutura do Projeto (v2.0)

```
App_projeto/
├── main.py                    → Arquivo principal (GUI)
├── requirements.txt           → Dependências
│
├── gui/                       → Novo diretório com GUI
│   ├── __init__.py
│   └── main_window.py         → Implementação da interface
│
├── audio_analysis/            → Análise de áudio (inalterado)
│   ├── __init__.py
│   └── key_detection.py       → Detecção de tonalidade e BPM
│
├── file_manager/              → Gerenciamento de arquivos (inalterado)
│   ├── __init__.py
│   └── organizaer.py          → Organizar e criar playlists
│
└── utils/                     → Funções auxiliares (inalterado)
    ├── __init__.py
    └── camelot_map.py         → Mapeamento de tonalidades
```

## 🔧 Requisitos do Sistema

- **Python**: 3.7+
- **Bibliotecas**:
  - `librosa` - Análise de áudio
  - `PySimpleGUI` - Interface gráfica
  - Dependências automaticamente instaladas

## 🎯 Formatos de Áudio Suportados

✅ MP3  
✅ WAV  
✅ FLAC  
✅ OGG  
✅ M4A  
✅ AIFF

## 💡 Dicas de Uso

### Para Iniciantes
1. Comece analisando uma música individual
2. Veja qual tonalidade e BPM ela tem
3. Use a aba "Compatibilidade" para aprender quais chaves combinam
4. Organize sua biblioteca pequena primeiro para praticar

### Para DJs Experientes
1. Use "Organizar" na sua biblioteca completa
2. Crie playlists específicas por tonalidade
3. Use filtros de BPM para sets mais consistentes
4. Combine com seu software de DJ favorito

### Troubleshooting

**Problema**: Arquivo não é analisado
- **Solução**: Certifique-se que é um formato suportado e tem qualidade boa

**Problema**: Organizar demora muito
- **Solução**: Isso é normal! Análise de áudio é processante. Paciência!

**Problema**: Tonalidade detectada está errada
- **Solução**: Às vezes a detecção não é perfeita. Você pode editar manualmente ou ignorar

## 📝 Exemplo: Workflow Completo

```
1. Você tem 100 músicas em Downloads/
2. Clica em "Organizar" → Input: Downloads/ → Output: MusicaOrganizada/
3. O programa analisa todas (leva uns minutos)
4. Resultado: MusicaOrganizada/ tem pastas 1A, 1B, 2A, 2B... 8A, 8B... etc
5. Você quer fazer uma mix em 8A com BPM 120-130
6. Vai em "Playlist" → Input: MusicaOrganizada/ → Tonalidade: 8A → BPM: 120-130
7. Cria lista.m3u com 20 músicas que combinam perfeitamente
8. Abre em seu DJ software → Happy mixing! 🎧
```

## 📞 Suporte

Se algo não funcionar:

1. Verifique se `librosa` e `PySimpleGUI` estão instalados
2. Tente com um arquivo diferente
3. Verifique a qualidade do áudio
4. Reinstale as dependências: `pip install -r requirements.txt --upgrade`

## 📊 Mudanças da v1.0 para v2.0

| Aspecto | v1.0 (CLI) | v2.0 (GUI) |
|---------|-----------|-----------|
| Interface | Linha de comando | Janelas gráficas |
| Entrada | Digitação | Cliques em botões |
| Saída | Texto | Visualização formatada |
| Facilidade | Iniciantes: difícil | Iniciantes: fácil |
| Potência | Alta flexibilidade | Mais intuitivo |

---

🎧 **Aproveite e boa mixagem!** 🎧

Desenvolvido com ❤️ para DJs e produtores musicais
