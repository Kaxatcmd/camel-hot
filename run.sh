#!/bin/bash
# Script para iniciar rapidamente a aplicação

# Verificar se virtualenv está ativado
if [ -z "$VIRTUAL_ENV" ]; then
    echo "🔧 Ativando virtualenv..."
    source venv/bin/activate
fi

# Verificar se dependências estão instaladas
echo "📦 Verificando dependências..."
pip install -q -r requirements.txt 2>/dev/null

# Executar testes rápidos
echo "🧪 Executando testes..."
python test_gui.py

# Se testes passarem, executar aplicação
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Tudo OK! Iniciando DJ Harmonic Analyzer..."
    echo ""
    python main.py
else
    echo "❌ Testes falharam. Verifique os erros acima."
    exit 1
fi
