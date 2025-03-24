"""
Detector de vazamentos de memória para código Delphi
Usa pyparsing para análise de texto avançada
"""

import re
import pyparsing as pp
from collections import defaultdict

class DelphiMemoryAnalyzer:
    """Analisador de código Delphi para detectar objetos não liberados"""
    
    def __init__(self, debug=False):
        """
        Inicializar o analisador
        Args:
            debug (bool): Ativar mensagens de depuração
        """
        self.debug = debug
        self.objects = {}
        self.unreleased = []
    
    def find_unreleased_objects(self, method_code, method_name):
        """
        Encontra objetos não liberados em um método Delphi
        
        Args:
            method_code (str): O código do método
            method_name (str): Nome do método (para referência)
            
        Returns:
            list: Lista de objetos não liberados
        """
        # Limpar estado
        self.objects = {}
        self.unreleased = []
        
        # 1. Extrair bloco 'finally' se existir
        finally_block = self._extract_finally_block(method_code)
        
        # 2. Encontrar declarações de objetos
        self._find_object_declarations(method_code)
        
        # 3. Encontrar uso de objetos
        self._find_object_usage(method_code)
        
        # 4. Encontrar liberações (primeiro no 'finally', depois no código geral)
        self._find_object_releases(finally_block, True)
        self._find_object_releases(method_code, False)
        
        # 5. Identificar objetos não liberados
        return self._get_unreleased_objects()
    
    def _debug_print(self, message):
        """Imprime mensagem de depuração se o modo debug estiver ativado"""
        if self.debug:
            print(f"DEBUG: {message}")
    
    def _extract_finally_block(self, code):
        """Extrai o bloco 'finally' do código"""
        finally_match = re.search(r'finally\b(.*?)(?=\bend\b)', code, re.IGNORECASE | re.DOTALL)
        if finally_match:
            return finally_match.group(1)
        return ""
    
    def _find_object_declarations(self, code):
        """
        Encontra declarações de objetos no código
        
        Formato:
        var
          obj1, obj2: TClassName;
          obj3: TOutraClasse;
        """
        # Encontrar seção 'var'
        var_match = re.search(r'\bvar\b(.*?)\bbegin\b', code, re.IGNORECASE | re.DOTALL)
        if not var_match:
            self._debug_print("Nenhuma seção 'var' encontrada")
            return
        
        var_section = var_match.group(1)
        line_offset = code[:var_match.start()].count('\n') + 1
        
        # Analisar declarações de variáveis
        for line_num, line in enumerate(var_section.split('\n')):
            line = line.strip()
            if not line or ':' not in line:
                continue
            
            # Extrair variáveis e tipo
            try:
                vars_part, type_part = line.split(':', 1)
                type_name = type_part.strip().rstrip(';').strip()
                
                # Verificar se é objeto (começa com T)
                if not (type_name.startswith('T') or type_name.startswith('I')):
                    continue
                
                # Processar variáveis
                for var_name in [v.strip() for v in vars_part.split(',')]:
                    if var_name:
                        self.objects[var_name] = {
                            'type': type_name,
                            'line': line_offset + line_num,
                            'used': False,
                            'freed': False
                        }
                        self._debug_print(f"Objeto encontrado: {var_name}: {type_name}")
            except Exception as e:
                self._debug_print(f"Erro ao processar linha '{line}': {str(e)}")
    
    def _find_object_usage(self, code):
        """Detecta uso dos objetos declarados"""
        for obj_name in self.objects:
            # Padrões para uso de objeto
            if any([
                re.search(fr'{re.escape(obj_name)}\s*:=', code),             # Atribuição
                re.search(fr'{re.escape(obj_name)}\.', code),                # Chamada de método
                re.search(fr'\(\s*{re.escape(obj_name)}', code),             # Parâmetro
                re.search(fr',\s*{re.escape(obj_name)}\s*[,\)]', code)       # Parâmetro intermediário
            ]):
                self.objects[obj_name]['used'] = True
                self._debug_print(f"Objeto em uso: {obj_name}")
    
    def _find_object_releases(self, code, is_finally=False):
        """
        Detecta liberação de objetos
        
        Args:
            code (str): Código a analisar
            is_finally (bool): Se está analisando um bloco finally
        """
        if not code:
            return
        
        context = "bloco finally" if is_finally else "código geral"
        
        for obj_name, obj_info in self.objects.items():
            # Pular se já foi marcado como liberado
            if obj_info['freed']:
                continue
            
            # Padrões de liberação
            if any([
                # FreeAndNil sem espaços extras
                re.search(fr'FreeAndNil\({re.escape(obj_name)}\)', code, re.IGNORECASE),
                # FreeAndNil com espaços
                re.search(fr'FreeAndNil\s*\(\s*{re.escape(obj_name)}\s*\)', code, re.IGNORECASE),
                # Método Free
                re.search(fr'{re.escape(obj_name)}\.Free\b', code, re.IGNORECASE),
                # Outros métodos de liberação
                re.search(fr'{re.escape(obj_name)}\.DisposeOf\b', code, re.IGNORECASE),
                re.search(fr'{re.escape(obj_name)}\.Release\b', code, re.IGNORECASE),
                re.search(fr'{re.escape(obj_name)}\.Destroy\b', code, re.IGNORECASE),
                # Free como função
                re.search(fr'Free\s*\(\s*{re.escape(obj_name)}\s*\)', code, re.IGNORECASE)
            ]):
                self.objects[obj_name]['freed'] = True
                self._debug_print(f"Objeto liberado: {obj_name} ({context})")
    
    def _get_unreleased_objects(self):
        """Retorna lista de objetos usados mas não liberados"""
        unreleased = []
        
        for obj_name, obj_info in self.objects.items():
            if obj_info['used'] and not obj_info['freed']:
                self._debug_print(f"AVISO: Objeto não liberado: {obj_name}")
                unreleased.append({
                    'name': obj_name,
                    'type': obj_info['type'],
                    'line': obj_info['line'],
                    'initialization': f"{obj_name} ({obj_info['type']})"
                })
        
        return unreleased

# Função de compatibilidade para o código existente
def find_unreleased_objects(method_code, method_name, debug=False):
    """
    Função de compatibilidade com a interface anterior
    
    Args:
        method_code (str): Código do método
        method_name (str): Nome do método
        debug (bool): Ativar depuração
        
    Returns:
        list: Objetos não liberados
    """
    analyzer = DelphiMemoryAnalyzer(debug)
    return analyzer.find_unreleased_objects(method_code, method_name) 