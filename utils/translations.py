"""
Translations Module - Multi-language Support for DJ Harmonic Analyzer

Supports: English (ENG), Portuguese (PT), Spanish (ES)
The translation system manages all UI text in the application.

Usage:
    from utils.translations import Translator
    translator = Translator(language='ENG')  # or 'PT', 'ES'
    text = translator.get('key_name')
    
    # To change language at runtime:
    translator.set_language('PT')
    
    # Or get a new translator instance:
    translator = Translator(language='PT')
"""

class Translator:
    """Manages translations for the DJ Harmonic Analyzer application"""
    
    # Translation dictionary: key -> {language -> translation}
    TRANSLATIONS = {
        # Window titles and main UI
        'window_title': {
            'ENG': 'CAMEL-HOT - Harmonic Music Analyzer',
            'PT': 'CAMEL-HOT - Analisador de Música Harmônica',
            'ES': 'CAMEL-HOT - Analizador de Música Armónica'
        },
        'subtitle': {
            'ENG': 'Harmonic Music Analyzer',
            'PT': 'Analisador de Música Harmônica',
            'ES': 'Analizador de Música Armónica'
        },
        'tagline': {
            'ENG': 'Mix by Harmony, Not by Chance',
            'PT': 'Misture por Harmonia, Não por Acaso',
            'ES': 'Mezcla por Armonía, No por Casualidad'
        },
        'footer_text': {
            'ENG': "Design for DJ's and Electronic Music Producers.",
            'PT': "Design para DJs e Produtores de Música Eletrônica.",
            'ES': "Diseño para DJs y Productores de Música Electrónica."
        },
        
        # Tab names
        'tab_analyze': {
            'ENG': 'Analyze',
            'PT': 'Analisar',
            'ES': 'Analizar'
        },
        'tab_organize': {
            'ENG': 'Organize',
            'PT': 'Organizar',
            'ES': 'Organizar'
        },
        'tab_playlist': {
            'ENG': 'Playlist',
            'PT': 'Playlist',
            'ES': 'Lista de Reproducción'
        },
        'tab_compatibility': {
            'ENG': 'Compatibility',
            'PT': 'Compatibilidade',
            'ES': 'Compatibilidad'
        },
        'tab_about': {
            'ENG': 'About',
            'PT': 'Sobre',
            'ES': 'Acerca de'
        },
        'tab_tips': {
            'ENG': 'Tips',
            'PT': 'Dicas',
            'ES': 'Consejos'
        },
        
        # Buttons
        'btn_browse': {
            'ENG': 'Browse',
            'PT': 'Procurar',
            'ES': 'Examinar'
        },
        'btn_analyze_track': {
            'ENG': 'Analyze Track',
            'PT': 'Analisar Faixa',
            'ES': 'Analizar Pista'
        },
        'btn_clear': {
            'ENG': 'Clear',
            'PT': 'Limpar',
            'ES': 'Limpiar'
        },
        'btn_organize_library': {
            'ENG': 'Organize Library',
            'PT': 'Organizar Biblioteca',
            'ES': 'Organizar Biblioteca'
        },
        'btn_create_playlist': {
            'ENG': 'Create Playlist',
            'PT': 'Criar Playlist',
            'ES': 'Crear Lista de Reproducción'
        },
        'btn_check_compatibility': {
            'ENG': 'Check Compatibility',
            'PT': 'Verificar Compatibilidade',
            'ES': 'Verificar Compatibilidad'
        },
        'btn_exit': {
            'ENG': 'Exit',
            'PT': 'Sair',
            'ES': 'Salir'
        },
        
        # Analyze Tab
        'analyze_title': {
            'ENG': 'Analyze Individual Track',
            'PT': 'Analisar Faixa Individual',
            'ES': 'Analizar Pista Individual'
        },
        'label_select_file': {
            'ENG': 'Select file:',
            'PT': 'Selecione arquivo:',
            'ES': 'Seleccionar archivo:'
        },
        'placeholder_audio_file': {
            'ENG': 'Choose an audio file...',
            'PT': 'Escolha um arquivo de áudio...',
            'ES': 'Elige un archivo de audio...'
        },
        'label_results': {
            'ENG': 'Results:',
            'PT': 'Resultados:',
            'ES': 'Resultados:'
        },
        
        # Organize Tab
        'organize_title': {
            'ENG': 'Organize Music Library',
            'PT': 'Organizar Biblioteca de Música',
            'ES': 'Organizar Biblioteca de Música'
        },
        'label_input_folder': {
            'ENG': 'Input folder:',
            'PT': 'Pasta de entrada:',
            'ES': 'Carpeta de entrada:'
        },
        'placeholder_music_source': {
            'ENG': 'Choose music source folder...',
            'PT': 'Escolha pasta de origem da música...',
            'ES': 'Elige carpeta de origen de música...'
        },
        'label_output_folder': {
            'ENG': 'Output folder:',
            'PT': 'Pasta de saída:',
            'ES': 'Carpeta de salida:'
        },
        'placeholder_destination': {
            'ENG': 'Choose destination folder...',
            'PT': 'Escolha pasta de destino...',
            'ES': 'Elige carpeta de destino...'
        },
        'checkbox_move_files': {
            'ENG': 'Move files (instead of copying)',
            'PT': 'Mover arquivos (ao invés de copiar)',
            'ES': 'Mover archivos (en lugar de copiar)'
        },
        'warning_move_files': {
            'ENG': '⚠️  Warning: Original files will be moved!',
            'PT': '⚠️  Aviso: Os arquivos originais serão movidos!',
            'ES': '⚠️  Advertencia: ¡Los archivos originales se moverán!'
        },
        'label_progress': {
            'ENG': 'Progress:',
            'PT': 'Progresso:',
            'ES': 'Progreso:'
        },
        
        # Playlist Tab
        'playlist_title': {
            'ENG': 'Create Harmonic Playlist',
            'PT': 'Criar Playlist Harmônica',
            'ES': 'Crear Lista de Reproducción Armónica'
        },
        'label_playlist_mode': {
            'ENG': 'Playlist Mode:',
            'PT': 'Modo de Playlist:',
            'ES': 'Modo de Lista de Reproducción:'
        },
        'mode_simple_harmonic': {
            'ENG': 'Simple Harmonic',
            'PT': 'Harmônico Simples',
            'ES': 'Armónico Simple'
        },
        'mode_harmonic_sequence': {
            'ENG': 'Harmonic Sequence',
            'PT': 'Sequência Harmônica',
            'ES': 'Secuencia Armónica'
        },
        'mode_key_transition': {
            'ENG': 'Key Transition',
            'PT': 'Transição de Tom',
            'ES': 'Transición de Tonalidad'
        },
        'mode_camelot_zone': {
            'ENG': 'Camelot Zone',
            'PT': 'Zona Camelot',
            'ES': 'Zona Camelot'
        },
        'label_music_folder': {
            'ENG': 'Music folder:',
            'PT': 'Pasta de música:',
            'ES': 'Carpeta de música:'
        },
        'placeholder_select_music': {
            'ENG': 'Select music folder...',
            'PT': 'Selecione pasta de música...',
            'ES': 'Selecciona carpeta de música...'
        },
        'label_playlist_filename': {
            'ENG': 'Playlist filename:',
            'PT': 'Nome do arquivo playlist:',
            'ES': 'Nombre de archivo de lista:'
        },
        'label_options': {
            'ENG': 'Options (depends on mode):',
            'PT': 'Opções (depende do modo):',
            'ES': 'Opciones (depende del modo):'
        },
        'label_camelot_key': {
            'ENG': 'Camelot Key:',
            'PT': 'Tom Camelot:',
            'ES': 'Tonalidad Camelot:'
        },
        'label_sequence_start': {
            'ENG': 'Sequence Start:',
            'PT': 'Início da Sequência:',
            'ES': 'Inicio de Secuencia:'
        },
        'label_direction': {
            'ENG': 'Direction:',
            'PT': 'Direção:',
            'ES': 'Dirección:'
        },
        'label_transition_end': {
            'ENG': 'Transition End:',
            'PT': 'Fim da Transição:',
            'ES': 'Fin de Transición:'
        },
        'label_min_bpm': {
            'ENG': 'Min BPM:',
            'PT': 'BPM Mín:',
            'ES': 'BPM Mín:'
        },
        'label_max_bpm': {
            'ENG': 'Max BPM:',
            'PT': 'BPM Máx:',
            'ES': 'BPM Máx:'
        },
        
        # Compatibility Tab
        'compatibility_title': {
            'ENG': 'Check Key Compatibility',
            'PT': 'Verificar Compatibilidade de Tom',
            'ES': 'Verificar Compatibilidad de Tonalidad'
        },
        'label_key1': {
            'ENG': 'Key 1:',
            'PT': 'Tom 1:',
            'ES': 'Tonalidad 1:'
        },
        'label_key2': {
            'ENG': 'Key 2:',
            'PT': 'Tom 2:',
            'ES': 'Tonalidad 2:'
        },
        'label_compatibility_result': {
            'ENG': 'Compatible:',
            'PT': 'Compatível:',
            'ES': 'Compatible:'
        },
        'yes': {
            'ENG': 'Yes',
            'PT': 'Sim',
            'ES': 'Sí'
        },
        'no': {
            'ENG': 'No',
            'PT': 'Não',
            'ES': 'No'
        },
        
        # About Tab
        'about_title': {
            'ENG': 'About CAMEL-HOT',
            'PT': 'Sobre CAMEL-HOT',
            'ES': 'Acerca de CAMEL-HOT'
        },
        'about_description': {
            'ENG': 'CAMEL-HOT is a professional tool for DJ and electronic music producers to analyze music keys, BPM, and organize their libraries using harmonic mixing principles.',
            'PT': 'CAMEL-HOT é uma ferramenta profissional para DJs e produtores de música eletrônica analisarem tons, BPM e organizarem suas bibliotecas usando princípios de mistura harmônica.',
            'ES': 'CAMEL-HOT es una herramienta profesional para DJs y productores de música electrónica para analizar tonalidades, BPM y organizar sus bibliotecas usando principios de mezcla armónica.'
        },
        'about_features': {
            'ENG': 'Key Features:\n• Automatic key and BPM detection\n• Camelot notation system\n• Library organization\n• Harmonic mixing playlists\n• Compatible key checking',
            'PT': 'Recursos Principais:\n• Detecção automática de tom e BPM\n• Sistema de notação Camelot\n• Organização de biblioteca\n• Playlists de mistura harmônica\n• Verificação de compatibilidade de tom',
            'ES': 'Características Principales:\n• Detección automática de tonalidad y BPM\n• Sistema de notación Camelot\n• Organización de biblioteca\n• Listas de mezcla armónica\n• Verificación de compatibilidad de tonalidad'
        },
        'about_version': {
            'ENG': 'Version: 1.0',
            'PT': 'Versão: 1.0',
            'ES': 'Versión: 1.0'
        },
        
        # Tips Tab
        'tips_title': {
            'ENG': 'DJ Tips',
            'PT': 'Dicas de DJ',
            'ES': 'Consejos de DJ'
        },
        'tips_subtitle': {
            'ENG': 'Tip of the Moment',
            'PT': 'Dica do Momento',
            'ES': 'Consejo del Momento'
        },
        'btn_next_tip': {
            'ENG': 'Next Tip',
            'PT': 'Próxima Dica',
            'ES': 'Siguiente Consejo'
        },
        'tips_subtitle_desc': {
            'ENG': 'Learn harmonic mixing and DJ preparation tips',
            'PT': 'Aprenda dicas de mistura harmônica e preparação de DJ',
            'ES': 'Aprende consejos de mezcla armónica y preparación de DJ'
        },
        
        # Messages and dialogs
        'msg_file_not_selected': {
            'ENG': 'Please select an audio file first.',
            'PT': 'Por favor, selecione um arquivo de áudio primeiro.',
            'ES': 'Por favor, selecciona un archivo de audio primero.'
        },
        'msg_analyzing': {
            'ENG': 'Analyzing audio file...',
            'PT': 'Analisando arquivo de áudio...',
            'ES': 'Analizando archivo de audio...'
        },
        'msg_analysis_complete': {
            'ENG': 'Analysis complete!',
            'PT': 'Análise concluída!',
            'ES': '¡Análisis completado!'
        },
        'msg_error': {
            'ENG': 'Error',
            'PT': 'Erro',
            'ES': 'Error'
        },
        'msg_success': {
            'ENG': 'Success',
            'PT': 'Sucesso',
            'ES': 'Éxito'
        },
        'msg_no_input_folder': {
            'ENG': 'Please select input folder.',
            'PT': 'Por favor, selecione a pasta de entrada.',
            'ES': 'Por favor, selecciona la carpeta de entrada.'
        },
        'msg_no_output_folder': {
            'ENG': 'Please select output folder.',
            'PT': 'Por favor, selecione a pasta de saída.',
            'ES': 'Por favor, selecciona la carpeta de salida.'
        },
        'msg_no_music_folder': {
            'ENG': 'Please select a music folder.',
            'PT': 'Por favor, selecione uma pasta de música.',
            'ES': 'Por favor, selecciona una carpeta de música.'
        },
        'msg_playlist_created': {
            'ENG': 'Playlist created successfully!',
            'PT': 'Playlist criada com sucesso!',
            'ES': '¡Lista de reproducción creada con éxito!'
        },
        'msg_confirm_move': {
            'ENG': 'This will move all files. Continue?',
            'PT': 'Isto irá mover todos os arquivos. Continuar?',
            'ES': 'Esto moverá todos los archivos. ¿Continuar?'
        },
        
        # Results display
        'result_key': {
            'ENG': 'Key',
            'PT': 'Tom',
            'ES': 'Tonalidad'
        },
        'result_camelot': {
            'ENG': 'Camelot',
            'PT': 'Camelot',
            'ES': 'Camelot'
        },
        'result_bpm': {
            'ENG': 'BPM',
            'PT': 'BPM',
            'ES': 'BPM'
        },
        'result_duration': {
            'ENG': 'Duration',
            'PT': 'Duração',
            'ES': 'Duración'
        },
        'result_confidence': {
            'ENG': 'Confidence',
            'PT': 'Confiança',
            'ES': 'Confianza'
        },
        'result_file': {
            'ENG': 'File',
            'PT': 'Arquivo',
            'ES': 'Archivo'
        },
        
        # Language selector
        'label_language': {
            'ENG': 'Language:',
            'PT': 'Idioma:',
            'ES': 'Idioma:'
        },
        'lang_english': {
            'ENG': 'English',
            'PT': 'Inglês',
            'ES': 'Inglés'
        },
        'lang_portuguese': {
            'ENG': 'Portuguese',
            'PT': 'Português',
            'ES': 'Portugués'
        },
        'lang_spanish': {
            'ENG': 'Spanish',
            'PT': 'Espanhol',
            'ES': 'Español'
        },
    }
    
    def __init__(self, language='ENG'):
        """
        Initialize translator with specified language.
        
        Args:
            language (str): Language code - 'ENG', 'PT', or 'ES'
        
        Raises:
            ValueError: If language code is not supported
        """
        self.supported_languages = ['ENG', 'PT', 'ES']
        if language not in self.supported_languages:
            raise ValueError(f"Unsupported language: {language}. Supported: {self.supported_languages}")
        self.current_language = language
    
    def set_language(self, language):
        """
        Change the current language.
        
        Args:
            language (str): Language code - 'ENG', 'PT', or 'ES'
        
        Raises:
            ValueError: If language code is not supported
        """
        if language not in self.supported_languages:
            raise ValueError(f"Unsupported language: {language}. Supported: {self.supported_languages}")
        self.current_language = language
    
    def get(self, key):
        """
        Get translated text for a given key.
        
        Args:
            key (str): Translation key
        
        Returns:
            str: Translated text in the current language, or the key itself if not found
        """
        if key not in self.TRANSLATIONS:
            return key  # Return key if translation not found
        
        translations = self.TRANSLATIONS[key]
        if self.current_language not in translations:
            return translations.get('ENG', key)  # Fallback to English
        
        return translations[self.current_language]
    
    def get_all_languages(self):
        """Get list of supported language codes"""
        return self.supported_languages.copy()
    
    def get_current_language(self):
        """Get current active language code"""
        return self.current_language


# Global translator instance (optional - for convenience)
_global_translator = None


def get_translator(language='ENG'):
    """
    Get a translator instance.
    
    Args:
        language (str): Language code - 'ENG', 'PT', or 'ES'
    
    Returns:
        Translator: Translator instance
    """
    return Translator(language)


def set_global_translator(language='ENG'):
    """
    Set the global translator instance.
    
    Args:
        language (str): Language code - 'ENG', 'PT', or 'ES'
    """
    global _global_translator
    _global_translator = Translator(language)
    return _global_translator


def global_translate(key):
    """
    Translate using the global translator instance.
    
    Args:
        key (str): Translation key
    
    Returns:
        str: Translated text
    """
    global _global_translator
    if _global_translator is None:
        _global_translator = Translator('ENG')
    return _global_translator.get(key)


def global_set_language(language):
    """
    Change language in the global translator instance.
    
    Args:
        language (str): Language code - 'ENG', 'PT', or 'ES'
    """
    global _global_translator
    if _global_translator is None:
        _global_translator = Translator(language)
    else:
        _global_translator.set_language(language)
