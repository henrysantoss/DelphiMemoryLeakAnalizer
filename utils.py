import os
import re

def is_delphi_unit(file_path):
    """
    Verifica se um arquivo é uma unidade Delphi
    
    Args:
        file_path (str): Caminho do arquivo
        
    Returns:
        bool: True se for uma unidade Delphi, False caso contrário
    """
    if not os.path.isfile(file_path):
        return False
        
    if not file_path.lower().endswith('.pas'):
        return False
        
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(1000)  # Ler apenas o início do arquivo
            
        # Verificar se começa com a palavra-chave 'unit'
        return bool(re.search(r'^\s*unit\s+\w+;', content, re.IGNORECASE | re.MULTILINE))
    except:
        return False

def find_function_definition(function_name, file_contents):
    """
    Procura a definição de uma função em todos os arquivos
    
    Args:
        function_name (str): Nome da função
        file_contents (dict): Dicionário {arquivo: conteúdo}
        
    Returns:
        tuple: (arquivo, linha) onde a função é definida ou (None, None)
    """
    # Padrão para encontrar a declaração da função
    pattern = re.compile(fr'function\s+{function_name}\s*\(.*?\)', re.IGNORECASE | re.DOTALL)
    
    for file_path, content in file_contents.items():
        match = pattern.search(content)
        if match:
            # Calcular o número da linha
            line_num = content[:match.start()].count('\n') + 1
            return file_path, line_num
    
    return None, None

def is_system_unit(unit_name):
    """
    Verifica se uma unidade é do sistema (RTL, VCL, etc.)
    
    Args:
        unit_name (str): Nome da unidade
        
    Returns:
        bool: True se for uma unidade do sistema, False caso contrário
    """
    system_prefixes = [
        'System', 'Vcl', 'Winapi', 'Data', 'FireDAC', 'DBX',
        'Datasnap', 'IdHTTP', 'REST', 'XML', 'FMX', 'IOUtils'
    ]
    
    for prefix in system_prefixes:
        if unit_name.startswith(prefix + '.'):
            return True
    
    system_units = [
        'Windows', 'SysUtils', 'Classes', 'Graphics', 'Controls',
        'Forms', 'Dialogs', 'StdCtrls', 'ExtCtrls', 'ComCtrls',
        'DB', 'DBClient', 'Provider', 'Variants', 'StrUtils',
        'Registry', 'IniFiles', 'DateUtils', 'Math', 'Types'
    ]
    
    return unit_name in system_units

def extract_unit_name(file_path):
    """
    Extrai o nome da unidade de um arquivo .pas
    
    Args:
        file_path (str): Caminho do arquivo
        
    Returns:
        str: Nome da unidade ou None
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(1000)  # Ler apenas o início do arquivo
            
        # Extrair o nome da unidade
        unit_match = re.search(r'^\s*unit\s+(\w+);', content, re.IGNORECASE | re.MULTILINE)
        if unit_match:
            return unit_match.group(1)
    except:
        pass
        
    return os.path.splitext(os.path.basename(file_path))[0]

def extract_method_info(content, line_num):
    """
    Extrai informações sobre o método/procedimento que contém a linha especificada
    
    Args:
        content (str): Conteúdo do arquivo
        line_num (int): Número da linha
        
    Returns:
        tuple: (nome_método, linha_início, linha_fim)
    """
    lines = content.split('\n')
    
    # Encontrar início do método (procurar para trás a partir da linha)
    start_line = line_num
    while start_line > 0:
        line = lines[start_line - 1]  # Ajuste para índice base-0
        
        # Procurar por declaração de procedimento/função
        if re.search(r'^\s*(procedure|function)\s+\w+', line, re.IGNORECASE):
            break
            
        start_line -= 1
    
    if start_line == 0:
        return None, None, None
        
    # Extrair nome do método
    method_line = lines[start_line - 1]
    method_match = re.search(r'^\s*(procedure|function)\s+(\w+)', method_line, re.IGNORECASE)
    if not method_match:
        return None, None, None
        
    method_name = method_match.group(2)
    
    # Encontrar fim do método (procurar para frente a partir da linha)
    end_line = line_num
    begin_count = 0
    end_count = 0
    
    # Contar blocos begin/end para identificar o final do método
    for i in range(start_line - 1, len(lines)):
        line = lines[i].lower()
        
        # Ignorar comentários de linha
        line = re.sub(r'//.*$', '', line)
        
        # Contar begins e ends
        if 'begin' in line and not 'end' in line:
            begin_count += 1
        elif 'end;' in line and not 'begin' in line:
            end_count += 1
            
            # Se temos um end; e é balanceado, encontramos o final
            if end_count >= begin_count and begin_count > 0:
                end_line = i + 1  # Converter de volta para índice base-1
                break
    
    return method_name, start_line, end_line 