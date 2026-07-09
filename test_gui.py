"""
Test Script - Verificar se a GUI PyQt5 funciona corretamente

Este script testa se todos os imports funcionam e se a GUI pode ser iniciada.
"""

import sys
from pathlib import Path

def test_imports():
    """Teste 1: Verificar se todos os imports funcionam"""
    print("=" * 60)
    print("TEST 1: Verificando imports...")
    print("=" * 60)
    
    try:
        print("✓ Importando PyQt5...", end=" ")
        from PyQt5.QtWidgets import QApplication
        print("OK")
        
        print("✓ Importando gui.main_window...", end=" ")
        from gui.main_window import DJAnalyzerGUI
        print("OK")
        
        print("✓ Importando audio_analysis...", end=" ")
        from audio_analysis.key_detection import analyze_track
        print("OK")
        
        print("✓ Importando file_manager...", end=" ")
        from gui.file_manager.organizer import find_audio_files
        print("OK")
        
        print("✓ Importando utils...", end=" ")
        from utils.camelot_map import CAMELOT_MAP, get_compatible_keys
        print("OK")
        
        print("\n✅ Todos os imports funcionam!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        return False
        
        print("✓ Importando audio_analysis...", end=" ")
        from audio_analysis.key_detection import analyze_track
        print("OK")
        
        print("✓ Importando file_manager...", end=" ")
        from gui.file_manager.organizer import find_audio_files
        print("OK")
        
        print("✓ Importando utils...", end=" ")
        from utils.camelot_map import CAMELOT_MAP, get_compatible_keys
        print("OK")
        
        print("\n✅ Todos os imports funcionam!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        return False


def test_data_structures():
    """Teste 2: Verificar se estruturas de dados existem"""
    print("\n" + "=" * 60)
    print("TEST 2: Verificando estruturas de dados...")
    print("=" * 60)
    
    try:
        from utils.camelot_map import CAMELOT_MAP, RELATIVE_KEYS
        
        print(f"✓ CAMELOT_MAP tem {len(CAMELOT_MAP)} entradas", end=" ")
        assert len(CAMELOT_MAP) > 0
        print("OK")
        
        print(f"✓ RELATIVE_KEYS tem {len(RELATIVE_KEYS)} entradas", end=" ")
        assert len(RELATIVE_KEYS) > 0
        print("OK")
        
        print("✓ Testando get_camelot_key()...", end=" ")
        from utils.camelot_map import get_camelot_key
        result = get_camelot_key("C Major")
        assert result == "8B", f"Esperado 8B, recebido {result}"
        print(f"OK (C Major = {result})")
        
        print("✓ Testando get_compatible_keys()...", end=" ")
        from utils.camelot_map import get_compatible_keys
        compat = get_compatible_keys("8A")
        assert len(compat) > 0, "get_compatible_keys retornou lista vazia"
        print(f"OK ({len(compat)} chaves compatíveis)")
        
        print("\n✅ Estruturas de dados OK!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        return False


def test_gui_creation():
    """Teste 3: Verificar se GUI pode ser criada (sem exibir)"""
    print("\n" + "=" * 60)
    print("TEST 3: Criando instância da GUI...")
    print("=" * 60)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from gui.main_window import DJAnalyzerGUI
        
        print("✓ Criando aplicação Qt...", end=" ")
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        print("OK")
        
        print("✓ Criando objeto DJAnalyzerGUI...", end=" ")
        gui = DJAnalyzerGUI()
        print("OK")
        
        print("✓ GUI foi criada com sucesso!", end=" ")
        assert gui is not None
        print("OK")
        
        print("✓ Verificando widgets principais...", end=" ")
        assert hasattr(gui, 'analyze_file_input')
        assert hasattr(gui, 'org_input')
        assert hasattr(gui, 'pl_input')
        print("OK")
        
        print("\n✅ GUI pode ser criada e está funcional!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Executar todos os testes"""
    print("\n")
    print("🧪 DJ HARMONIC ANALYZER - TESTE DE FUNCIONALIDADE")
    print("🧪 Version 2.0 GUI Edition (PyQt5)\n")
    
    results = []
    
    # Executar testes
    results.append(("Imports", test_imports()))
    results.append(("Estruturas de Dados", test_data_structures()))
    results.append(("GUI Creation", test_gui_creation()))
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{test_name:.<40} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print("=" * 60)
    print(f"TOTAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n✅ TUDO FUNCIONA! Pronto para usar!")
        print("\nExecute: python main.py")
        return 0
    else:
        print("\n❌ Alguns testes falharam. Verifique os erros acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
