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
        self.debug = True
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
        
        # 1. Extrair todos os blocos 'finally' se existirem
        finally_blocks = self._extract_all_finally_blocks(method_code)
        
        # 2. Encontrar declarações de objetos
        self._find_object_declarations(method_code)
        
        # 3. Encontrar uso de objetos
        self._find_object_usage(method_code)
        
        # 4. Encontrar liberações (em todos os 'finally', depois no código geral)
        for finally_block in finally_blocks:
            self._find_object_releases(finally_block, True)
        self._find_object_releases(method_code, False)
        
        # 5. Identificar objetos não liberados
        return self._get_unreleased_objects()
    
    def _debug_print(self, message):
        """Imprime mensagem de depuração se o modo debug estiver ativado"""
        if self.debug:
            print(f"DEBUG: {message}")
    
    def _extract_all_finally_blocks(self, code):
        """Extrai todos os blocos 'finally' do código, considerando aninhamento de try-finally"""
        blocks = []
        pattern = re.compile(r'\btry\b', re.IGNORECASE)
        pos = 0
        while True:
            try_match = pattern.search(code, pos)
            if not try_match:
                break
            start = try_match.end()
            finally_match = re.search(r'\bfinally\b', code[start:], re.IGNORECASE)
            if not finally_match:
                break
            finally_start = start + finally_match.end()
            block = code[finally_start:]
            begin_count = 0
            end_pos = 0
            for m in re.finditer(r'\bbegin\b|\bend\b', block, re.IGNORECASE):
                if m.group(0).lower() == 'begin':
                    begin_count += 1
                else:
                    if begin_count == 0:
                        end_pos = m.end()
                        break
                    else:
                        begin_count -= 1
            if end_pos == 0:
                end_match = re.search(r'\bend\b', block, re.IGNORECASE)
                if end_match:
                    end_pos = end_match.end()
                else:
                    end_pos = len(block)
            blocks.append(block[:end_pos])
            pos = finally_start + end_pos
        return blocks
    
    def _find_object_declarations(self, code):
        """
        Encontra declarações de objetos no código

        Formato:
        var
        obj1, obj2: TClassName;
        obj3: TOutraClasse;
        """
        # Lista de tipos primitivos/comuns do Delphi
        COMMON_TYPES = {
            'integer', 'string', 'double', 'real', 'boolean', 'byte', 'word', 'char', 'currency',
            'smallint', 'longint', 'int64', 'single', 'extended', 'pchar', 'ansistring', 'widestring',
            'shortstring', 'cardinal', 'variant', 'pointer', 'dword', 'qword', 'tdate', 'tdatetime'
        }
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
                type_name = type_part.strip().rstrip(';').strip().lower()
                if type_name in COMMON_TYPES:
                    continue  # Ignora tipos comuns do Delphi
                if not (type_name.startswith('t') or type_name.startswith('i')):
                    continue  # Mantém checagem para classes customizadas
                for var_name in [v.strip() for v in vars_part.split(',')]:
                    if var_name:
                        self.objects[var_name] = {
                            'type': type_part.strip().rstrip(';').strip(),
                            'line': line_offset + line_num,
                            'used': False,
                            'freed': False
                        }
                        self._debug_print(f"Objeto encontrado: {var_name}: {type_part.strip().rstrip(';').strip()}")
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
            if obj_info['freed']:
                continue
            # Padrões de liberação (mais robusto)
            patterns = [
                fr'FreeAndNil\s*\(\s*{re.escape(obj_name)}\s*\)',
                fr'{re.escape(obj_name)}\s*\.\s*Free\b',
                fr'{re.escape(obj_name)}\s*\.\s*DisposeOf\b',
                fr'{re.escape(obj_name)}\s*\.\s*Release\b',
                fr'{re.escape(obj_name)}\s*\.\s*Destroy\b',
                fr'Free\s*\(\s*{re.escape(obj_name)}\s*\)'
            ]
            for pat in patterns:
                if re.search(pat, code, re.IGNORECASE):
                    self.objects[obj_name]['freed'] = True
                    self._debug_print(f"Objeto liberado: {obj_name} ({context})")
                    break
    
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

def extract_methods_from_file(file_content):
    """
    Extrai todos os métodos de um arquivo Delphi, respeitando aninhamento de begin/end,
    e considera apenas métodos abaixo da seção 'implementation'.
    """
    # Só pega o trecho após 'implementation'
    implementation_match = re.search(r'\\bimplementation\\b', file_content, re.IGNORECASE)
    if implementation_match:
        file_content = file_content[implementation_match.end():]
    # ... resto do código igual ... 