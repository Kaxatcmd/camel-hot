"""
DJ Tips Module - Educational content and tips for harmonic mixing

Provides a collection of DJ preparation and harmonic mixing tips
that are randomly displayed to help users improve their mixing skills.
"""

import random

class DJTipsManager:
    """Manages DJ tips display with intelligent rotation"""
    
    # Tips in English
    TIPS_ENG = [
        "🎵 Mix within the same Camelot number for the smoothest transitions.",
        "⚡ Move +1 or -1 on the Camelot wheel to increase energy gradually.",
        "😊 Switch between major (B) and minor (A) of the same number for emotional contrast.",
        "📊 Check energy levels, not only BPM, when planning a set.",
        "🎚️ Use breakdowns to perform key changes without jarring your audience.",
        "🎼 Keys 6A and 8A are harmonic 'hubs' – compatible with many others.",
        "⏱️ BPM compatibility matters more than exact key matching in fast sets.",
        "🔄 A ±1 semitone shift often sounds better than a full octave jump.",
        "🎧 Test your transitions before your performance – there are no second chances!",
        "📈 Build your DJ set like a story: beginning, climax, and resolution.",
        "🌀 The Camelot wheel works because it's based on harmonic relationships.",
        "💡 Spring reversals: go from 8B back to 8A for dramatic energy drops.",
        "🎯 Organize your library by Camelot code to find compatible tracks instantly.",
        "🔊 Mixing in key doesn't guarantee a great transition – musicality always wins.",
        "⭐ The +1/-1 rule on the wheel gives you 4 easy compatible keys for any track.",
        "🎬 Use visualization: imagine the emotional journey your audience will experience.",
        "🔍 Analyze tracks offline to make better choices in your next session.",
        "🌟 Practice transitions during rehearsal, not during the actual performance.",
        "📱 Keep detailed notes on successful track pairings for future reference.",
        "🎪 Remember: harmonic mixing is a tool, not the law – context is everything!",
        "📚 Understanding Camelot Wheel notation improves your harmonic mixing accuracy.",
        "✅ Always check key compatibility before mixing tracks to ensure smooth blending.",
        "🎚️ BPM matching is crucial for seamless beat blending and audience flow.",
        "🔥 Energy levels affect track selection – build your set with dynamic peaks and valleys.",
        "🔗 Use the Compatibility tab to identify tracks that work exceptionally well together.",
        "📂 Create themed playlists by musical key for faster track selection during live sets.",
        "💻 Professional DJ software uses advanced harmonic analysis for competitive advantage.",
        "🎶 Groove and rhythm characteristics help maintain audience engagement throughout.",
        "📊 Analyzing BPM trends helps understand artist production style and energy patterns.",
        "🎛️ Organize your music library by key to master harmonic mixing techniques faster.",
        "🎲 Tips appear randomly – refresh often to discover new mixing advice and insights.",
    ]
    
    # Tips in Portuguese
    TIPS_PT = [
        "🎵 Misture dentro do mesmo número Camelot para as transições mais suaves.",
        "⚡ Mova +1 ou -1 na roda Camelot para aumentar a energia gradualmente.",
        "😊 Alterne entre maior (B) e menor (A) do mesmo número para contraste emocional.",
        "📊 Verifique os níveis de energia, não apenas BPM, ao planejar um set.",
        "🎚️ Use breakdowns para fazer mudanças de tom sem jarring do público.",
        "🎼 Os tons 6A e 8A são 'hubs' harmônicos – compatíveis com muitos outros.",
        "⏱️ A compatibilidade de BPM importa mais que a correspondência exata de tom em sets rápidos.",
        "🔄 Uma mudança de ±1 semitom geralmente soa melhor que um salto de oitava completo.",
        "🎧 Teste suas transições antes da sua performance – não há segundas chances!",
        "📈 Construa seu DJ set como uma história: começo, clímax e resolução.",
        "🌀 A roda Camelot funciona porque é baseada em relações harmônicas.",
        "💡 Reversões de primavera: volte de 8B para 8A para quedas dramáticas de energia.",
        "🎯 Organize sua biblioteca por código Camelot para encontrar faixas compatíveis instantaneamente.",
        "🔊 Misturar em tom não garante uma transição ótima – musicalidade sempre vence.",
        "⭐ A regra +1/-1 na roda oferece 4 tons fáceis e compatíveis para qualquer faixa.",
        "🎬 Use visualização: imagine a jornada emocional do seu público.",
        "🔍 Analise faixas offline para fazer melhores escolhas na próxima sessão.",
        "🌟 Pratique transições durante ensaios, não durante a performance real.",
        "📱 Mantenha anotações detalhadas de associações de faixas bem-sucedidas.",
        "🎪 Lembre-se: mistura harmônica é uma ferramenta, não uma lei – contexto é tudo!",
        "📚 Compreender a notação da Roda Camelot melhora sua precisão na mistura harmônica.",
        "✅ Sempre verifique a compatibilidade de tom antes de misturar faixas para suavidade.",
        "🎚️ Sincronização de BPM é crucial para fusão de batidas perfeita e fluxo da audiência.",
        "🔥 Níveis de energia afetam seleção de faixas – construa seu set com picos dinâmicos.",
        "🔗 Use a aba Compatibilidade para identificar faixas que funcionam excepcionalmente bem.",
        "📂 Crie playlists temáticas por tom musical para seleção mais rápida durante apresentações.",
        "💻 Software profissional de DJ usa análise harmônica avançada para vantagem competitiva.",
        "🎶 Características de groove ajudam manter envolvimento da audiência ao longo do tempo.",
        "📊 Analisar tendências de BPM ajuda entender estilo de produção e padrões de energia.",
        "🎛️ Organize sua biblioteca por tom para dominar técnicas de mistura harmônica rápido.",
        "🎲 Dicas aparecem aleatoriamente – atualize frequentemente para descobrir novos conselhos.",
    ]
    
    # Tips in Spanish
    TIPS_ES = [
        "🎵 Mezcla dentro del mismo número Camelot para las transiciones más suaves.",
        "⚡ Muévete +1 o -1 en la rueda Camelot para aumentar la energía gradualmente.",
        "😊 Alterna entre mayor (B) y menor (A) del mismo número para contraste emocional.",
        "📊 Verifica los niveles de energía, no solo BPM, al planificar tu set.",
        "🎚️ Usa breakdowns para hacer cambios de tonalidad sin sorprender a tu público.",
        "🎼 Las tonalidades 6A y 8A son 'hubs' armónicos – compatibles con muchas otras.",
        "⏱️ La compatibilidad de BPM importa más que la coincidencia exacta de tonalidad en sets rápidos.",
        "🔄 Un cambio de ±1 semitono generalmente suena mejor que un salto de octava completo.",
        "🎧 Prueba tus transiciones antes de tu presentación – ¡no hay segundas oportunidades!",
        "📈 Construye tu set de DJ como una historia: principio, clímax y resolución.",
        "🌀 La rueda Camelot funciona porque se basa en relaciones armónicas.",
        "💡 Reversiones de primavera: vuelve de 8B a 8A para caídas dramáticas de energía.",
        "🎯 Organiza tu biblioteca por código Camelot para encontrar pistas compatibles al instante.",
        "🔊 Mezclar en tonalidad no garantiza una transición excelente – ¡la musicalidad siempre gana!",
        "⭐ La regla +1/-1 en la rueda te da 4 tonalidades fáciles y compatibles para cualquier pista.",
        "🎬 Usa visualización: imagina el viaje emocional de tu público.",
        "🔍 Analiza pistas sin conexión para tomar mejores decisiones en tu próxima sesión.",
        "🌟 Practica transiciones durante ensayos, no durante la presentación real.",
        "📱 Mantén notas detalladas de asociaciones de pistas exitosas para referencia futura.",
        "🎪 Recuerda: la mezcla armónica es una herramienta, no una ley – ¡el contexto es todo!",
        "📚 Entender la notación de la Rueda Camelot mejora tu precisión en mezcla armónica.",
        "✅ Siempre verifica la compatibilidad de tonalidad antes de mezclar pistas para suavidad.",
        "🎚️ La sincronización de BPM es crucial para fusión de ritmo perfecta y flujo de audiencia.",
        "🔥 Los niveles de energía afectan selección de pistas – construye tu set con picos dinámicos.",
        "🔗 Usa la pestaña Compatibilidad para identificar pistas que funcionan excepcionalmente bien.",
        "📂 Crea listas de reproducción temáticas por tonalidad para selección más rápida en vivo.",
        "💻 El software profesional de DJ usa análisis armónico avanzado para ventaja competitiva.",
        "🎶 Las características de groove ayudan mantener engagement de la audiencia todo el tiempo.",
        "📊 Analizar tendencias de BPM ayuda entender estilo de producción y patrones de energía.",
        "🎛️ Organiza tu biblioteca por tonalidad para dominar técnicas de mezcla armónica rápido.",
        "🎲 Los consejos aparecen aleatoriamente – refresca frecuentemente para nuevas recomendaciones.",
    ]
    
    def __init__(self, language='ENG'):
        """Initialize the tips manager"""
        self.language = language
        self.last_tip_index = -1
        self._update_tips()
    
    def _update_tips(self):
        """Update tips based on current language"""
        if self.language == 'PT':
            self.tips = self.TIPS_PT
        elif self.language == 'ES':
            self.tips = self.TIPS_ES
        else:
            self.tips = self.TIPS_ENG
    
    def set_language(self, language):
        """Change language and update tips"""
        self.language = language
        self._update_tips()
        self.last_tip_index = -1
    
    def get_random_tip(self):
        """
        Get a random tip that's different from the last one shown.
        
        Returns:
            str: A random DJ tip
        """
        available_indices = [i for i in range(len(self.tips)) if i != self.last_tip_index]
        
        if not available_indices:
            available_indices = list(range(len(self.tips)))
        
        self.last_tip_index = random.choice(available_indices)
        return self.tips[self.last_tip_index]
    
    def get_all_tips(self):
        """Get all available tips"""
        return self.tips.copy()
    
    def get_tip_count(self):
        """Get total number of tips"""
        return len(self.tips)
    
    def get_last_tip_index(self):
        """Get the index of the last tip shown (1-based for display)"""
        return self.last_tip_index + 1
