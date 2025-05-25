import os
import re
from object_tracker import DelphiMemoryAnalyzer
import pyparsing as pp
from typing import List, Dict, Any

def extract_methods_from_file(file_content):
    lines = file_content.splitlines(True)
    impl_index = None
    # Encontra a linha "implementation"
    for idx, line in enumerate(lines):
        if re.match(r'^\s*implementation\b', line, flags=re.IGNORECASE):
            impl_index = idx
            break
    if impl_index is None:
        return []
    
    results = []
    in_method = False
    method = None
    body_lines = []
    depth = 0
    in_curly = False
    in_paren_star = False
    
    i = impl_index + 1
    while i < len(lines):
        line = lines[i]
        
        if not in_method:
            # Detecta novo cabeçalho de procedure/function
            if re.match(r'^\s*(procedure|function)\b', line, flags=re.IGNORECASE):
                header_lines = [line]
                j = i
                # Acumula linhas até encontrar ';' que fecha o cabeçalho
                while True:
                    last = header_lines[-1]
                    # Remove comentários para verificar ';'
                    no_comments = re.sub(r'{[^}]*}', '', last)
                    no_comments = re.sub(r'\(\*.*?\*\)', '', no_comments)
                    no_comments = re.sub(r'//.*', '', no_comments)
                    if ';' in no_comments:
                        break
                    j += 1
                    if j >= len(lines):
                        break
                    header_lines.append(lines[j])
                
                header_text = ''.join(header_lines).strip()
                m2 = re.match(r'^\s*(procedure|function)\s+([\w.]+)', header_text, flags=re.IGNORECASE)
                if not m2:
                    i = j + 1
                    continue
                m_type = m2.group(1).lower()
                name = m2.group(2)
                rest = header_text[m2.end():]
                
                # Extrai argumentos (texto entre parênteses, sem parênteses)
                args = ""
                idx_paren = rest.find('(')
                if idx_paren != -1:
                    balance = 1
                    k = idx_paren + 1
                    while k < len(rest) and balance > 0:
                        if rest[k] == '(':
                            balance += 1
                        elif rest[k] == ')':
                            balance -= 1
                        k += 1
                    if balance == 0:
                        args = rest[idx_paren+1:k-1].strip()
                    else:
                        args = rest[idx_paren+1:].strip()
                
                # Inicia novo método
                method = {
                    'type': m_type,
                    'name': name,
                    'args': args,
                    'body': '',
                    'has_finally': False,
                    'line': i
                }
                in_method = True
                body_lines = header_lines.copy()
                depth = 0
                i = j
        
        else:
            # Adiciona linha ao corpo do método
            body_lines.append(line)
            code_line = ''
            p = 0
            # Remove comentários e literais para contagem de blocos
            while p < len(line):
                if in_curly:
                    end_idx = line.find('}', p)
                    if end_idx == -1:
                        p = len(line)
                    else:
                        in_curly = False
                        p = end_idx + 1
                    continue
                if in_paren_star:
                    end_idx = line.find('*)', p)
                    if end_idx == -1:
                        p = len(line)
                    else:
                        in_paren_star = False
                        p = end_idx + 2
                    continue
                if line.startswith('//', p):
                    break
                if line.startswith('{', p):
                    in_curly = True
                    p += 1
                    continue
                if line.startswith('(*', p):
                    in_paren_star = True
                    p += 2
                    continue
                if line[p] == "'":
                    # pula literais de string (considerando acentuação de Pascal)
                    p += 1
                    while p < len(line):
                        if line[p] == "'":
                            p += 1
                            if p < len(line) and line[p] == "'":
                                p += 1
                                continue
                            break
                        p += 1
                    continue
                code_line += line[p]
                p += 1
            
            # Atualiza profundidade de blocos conforme tokens
            tokens = re.findall(r'\b(begin|case|record|try|end)\b', code_line, flags=re.IGNORECASE)
            closed_method = False
            for token in tokens:
                tok = token.lower()
                if tok in ('begin', 'case', 'record', 'try'):
                    depth += 1
                elif tok == 'end':
                    if depth == 0:
                        closed_method = True
                        break
                    else:
                        depth -= 1
                        if depth == 0:
                            closed_method = True
                            break
                if closed_method:
                    break
            
            # Se atingiu o fim do método, finaliza
            if closed_method:
                method['body'] = ''.join(body_lines)
                # Detecta bloco finally (fora de comentários)
                body_text = ''.join(body_lines)
                stripped = re.sub(r'{[^}]*}', '', body_text)
                stripped = re.sub(r'\(\*.*?\*\)', '', stripped)
                stripped = re.sub(r'//.*', '', stripped)
                if re.search(r'\bfinally\b', stripped, flags=re.IGNORECASE):
                    method['has_finally'] = True
                results.append(method)
                in_method = False
                method = None
                body_lines = []
                depth = 0
        
        i += 1
    
    return results

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
                    'method_line': method['line'] + 1,
                    'object_name': obj['name'],
                    'object_type': obj['type'],
                    'line': absolute_line + 1,  # Linha absoluta no arquivo
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