import os
import re
from object_tracker import DelphiMemoryAnalyzer

def extract_methods_from_file(file_content):
    """
    Extrai todos os métodos de um arquivo Delphi
    
    Args:
        file_content (str): Conteúdo do arquivo
        
    Returns:
        list: Lista de dicionários com informações sobre os métodos
    """
    methods = []
    
    # Regex melhorada para capturar métodos completos com blocos try-finally
    method_pattern = re.compile(
        r'(procedure|function)\s+(\w+(?:\.\w+)?)(\s*\(.*?\))?\s*(?::\s*\w+)?;' # Declaração
        r'(?:.*?)'          # Qualquer coisa entre declaração e implementação
        r'(begin.*?end;)',  # Implementação (de begin até end;)
        re.DOTALL | re.IGNORECASE
    )
    
    for match in method_pattern.finditer(file_content):
        method_type = match.group(1).lower()  # procedure ou function
        method_name = match.group(2)
        method_args = match.group(3) or ""
        method_body = match.group(0)  # Método completo
        
        # Calcular linha no arquivo
        line_num = file_content[:match.start()].count('\n') + 1
        
        # Verificar se tem try-finally
        has_finally = bool(re.search(r'\btry\b.*?\bfinally\b', method_body, re.DOTALL | re.IGNORECASE))
        
        methods.append({
            'type': method_type,
            'name': method_name,
            'args': method_args,
            'body': method_body,
            'has_finally': has_finally,
            'line': line_num
        })
    
    return methods

def analyze_pas_file(file_path, log_callback=None, debug=False):
    """
    Analisa um arquivo .pas para encontrar objetos não liberados
    
    Args:
        file_path (str): Caminho do arquivo .pas
        log_callback (callable, optional): Função para log
        debug (bool): Modo de depuração
        
    Returns:
        list: Lista de objetos não liberados
    """
    if log_callback:
        log_callback(f"Analisando: {os.path.basename(file_path)}")
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            file_content = f.read()
    except Exception as e:
        if log_callback:
            log_callback(f"Erro ao ler {file_path}: {str(e)}")
        return []
    
    # Extrair métodos
    methods = extract_methods_from_file(file_content)
    
    if debug and log_callback:
        log_callback(f"Encontrados {len(methods)} métodos em {os.path.basename(file_path)}")
        
        methods_with_finally = [m['name'] for m in methods if m['has_finally']]
        if methods_with_finally:
            log_callback(f"Métodos com finally: {', '.join(methods_with_finally)}")
    
    # Criar analisador
    analyzer = DelphiMemoryAnalyzer(debug)
    unreleased_objects = []
    
    # Analisar cada método
    for method in methods:
        results = analyzer.find_unreleased_objects(method['body'], method['name'])
        
        if results:
            for obj in results:
                # Calcular a linha absoluta do objeto no arquivo
                method_start_line = method['line']
                object_relative_line = obj['line']
                
                # A linha absoluta é a linha do início do método + a linha relativa do objeto
                # Subtraímos 1 pois a linha relativa já conta o início do método
                absolute_line = method_start_line + object_relative_line - 1
                
                unreleased_objects.append({
                    'file': file_path,
                    'file_name': os.path.basename(file_path),
                    'method_type': method['type'],
                    'method_name': method['name'],
                    'method_line': method['line'],
                    'object_name': obj['name'],
                    'object_type': obj['type'],
                    'line': absolute_line,  # Linha absoluta no arquivo
                    'relative_line': object_relative_line,  # Mantemos a linha relativa também
                    'initialization': obj['initialization']
                })
                
                if debug and log_callback:
                    log_callback(f"Objeto {obj['name']} não liberado em {method['name']} (linha {absolute_line})")
    
    # Resumo
    if log_callback:
        if unreleased_objects:
            log_callback(f"Encontrados {len(unreleased_objects)} objetos não liberados em {os.path.basename(file_path)}")
        else:
            log_callback(f"Nenhum objeto não liberado em {os.path.basename(file_path)}")
    
    return unreleased_objects

def analyze_pas_files(pas_files, log_callback=None, progress_callback=None):
    """
    Analisa múltiplos arquivos .pas
    
    Args:
        pas_files (list): Lista de caminhos para arquivos .pas
        log_callback (callable, optional): Função para log
        progress_callback (callable, optional): Função para atualizar progresso
        
    Returns:
        list: Lista de objetos não liberados
    """
    all_results = []
    total_files = len(pas_files)
    
    # Analisar cada arquivo
    for i, file_path in enumerate(pas_files):
        # Log de progresso
        if log_callback:
            log_callback(f"Analisando arquivo {i+1}/{total_files}: {os.path.basename(file_path)}")
        
        # Analisar arquivo
        results = analyze_pas_file(file_path, log_callback)
        all_results.extend(results)
        
        # Atualizar progresso
        if progress_callback:
            progress_callback((i + 1) / total_files * 100)
    
    # Resumo final
    if log_callback:
        log_callback(f"Análise concluída. Encontrados {len(all_results)} objetos não liberados em {total_files} arquivos.")
    
    return all_results 