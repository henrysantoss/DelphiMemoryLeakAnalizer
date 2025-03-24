import os
import re
import xml.etree.ElementTree as ET

def get_pas_files_from_dproj(dproj_path):
    """
    Extrai os caminhos de arquivos .pas referenciados em um arquivo .dproj do Delphi.
    
    Args:
        dproj_path (str): Caminho para o arquivo .dproj
        
    Returns:
        list: Lista de caminhos completos para arquivos .pas
    """
    # Verificar se o arquivo existe
    if not os.path.isfile(dproj_path):
        raise FileNotFoundError(f"Arquivo .dproj não encontrado: {dproj_path}")
    
    project_dir = os.path.dirname(dproj_path)
    
    try:
        # Analisar o arquivo XML
        tree = ET.parse(dproj_path)
        root = tree.getroot()
        
        # Namespace usado nos arquivos .dproj (pode variar, mas geralmente é esse)
        ns = {'ns': 'http://schemas.microsoft.com/developer/msbuild/2003'}
        
        # Procurar por arquivos DCU (que correspondem aos .pas)
        pas_files = []
        
        # Buscar elementos DCCReference, que contêm referências a arquivos .pas
        for dcc_ref in root.findall('.//ns:DCCReference', ns):
            if 'Include' in dcc_ref.attrib:
                pas_path = dcc_ref.attrib['Include']
                
                # Converter para caminho absoluto se for relativo
                if not os.path.isabs(pas_path):
                    pas_path = os.path.normpath(os.path.join(project_dir, pas_path))
                
                # Verificar se o arquivo existe e tem a extensão .pas
                if os.path.isfile(pas_path) and pas_path.lower().endswith('.pas'):
                    pas_files.append(pas_path)
        
        # Buscar também unidades no arquivo .dpr (que pode não estar explicitamente no .dproj)
        dpr_files = [f for f in os.listdir(project_dir) if f.lower().endswith('.dpr')]
        for dpr_file in dpr_files:
            dpr_path = os.path.join(project_dir, dpr_file)
            pas_files.extend(get_units_from_dpr(dpr_path, project_dir))
        
        # Remover duplicatas
        return list(set(pas_files))
    
    except ET.ParseError as e:
        raise ValueError(f"Erro ao analisar o arquivo .dproj: {str(e)}")

def get_units_from_dpr(dpr_path, project_dir):
    """
    Extrai nomes de unidades do bloco 'uses' em um arquivo .dpr
    
    Args:
        dpr_path (str): Caminho para o arquivo .dpr
        project_dir (str): Diretório do projeto
        
    Returns:
        list: Lista de caminhos completos para arquivos .pas
    """
    pas_files = []
    
    try:
        with open(dpr_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Procurar o bloco uses
        uses_match = re.search(r'uses\s+(.*?);', content, re.DOTALL)
        if uses_match:
            uses_block = uses_match.group(1)
            
            # Remover comentários
            uses_block = re.sub(r'{.*?}', '', uses_block)
            uses_block = re.sub(r'//.*?$', '', uses_block, flags=re.MULTILINE)
            
            # Extrair nomes de unidades
            units = [u.strip() for u in uses_block.replace('\n', '').split(',')]
            
            # Para cada unidade, tentar encontrar o arquivo .pas correspondente
            for unit in units:
                # Ignorar unidades do sistema ou vazias
                if not unit or unit.startswith('System.') or unit.startswith('Vcl.') or unit.startswith('Winapi.'):
                    continue
                
                # Primeiro, verificar no mesmo diretório
                pas_path = os.path.join(project_dir, f"{unit}.pas")
                if os.path.isfile(pas_path):
                    pas_files.append(pas_path)
                    continue
                
                # Depois, procurar em subdiretórios
                for root, _, files in os.walk(project_dir):
                    for file in files:
                        if file.lower() == f"{unit.lower()}.pas":
                            pas_files.append(os.path.join(root, file))
                            break
    
    except Exception as e:
        print(f"Aviso: Erro ao processar o arquivo .dpr {dpr_path}: {str(e)}")
    
    return pas_files 