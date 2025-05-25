import os
from datetime import datetime
import collections
import webbrowser

def generate_report(results, output_path, title="Relatório de Vazamento de Memória", detailed=True):
    """
    Gera um relatório HTML de objetos não liberados
    
    Args:
        results (list): Lista de resultados da análise
        output_path (str): Caminho para salvar o relatório
        title (str): Título do relatório
        detailed (bool): Se deve incluir detalhes completos
    """
    if not results:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(generate_empty_report())
        return
    
    # Agrupar resultados por arquivo
    results_by_file = {}
    for item in results:
        file_path = item['file']
        if file_path not in results_by_file:
            results_by_file[file_path] = []
        results_by_file[file_path].append(item)
    
    # Estatísticas por tipo de objeto
    object_types = collections.Counter([item['object_type'] for item in results])
    most_common_types = object_types.most_common(10)
    
    # Criar conteúdo HTML
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2, h3, h4 {{
            color: #2c3e50;
            margin-top: 20px;
        }}
        h1 {{
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            text-align: center;
        }}
        .summary {{
            background-color: #fff;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .file-box {{
            background-color: #fff;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .method-box {{
            background-color: #f9f9f9;
            border-left: 3px solid #3498db;
            padding: 10px;
            margin: 10px 0;
        }}
        .object-item {{
            margin-left: 20px;
            padding: 8px;
            border-bottom: 1px dashed #ddd;
        }}
        .object-item:last-child {{
            border-bottom: none;
        }}
        .stats {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
        }}
        .stat-box {{
            flex: 1;
            min-width: 250px;
            background-color: #fff;
            border-radius: 5px;
            padding: 15px;
            margin: 0 10px 20px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .recommendations {{
            background-color: #e9f7fe;
            border-left: 3px solid #3498db;
            padding: 15px;
            margin-top: 20px;
        }}
        .code {{
            font-family: Consolas, monospace;
            background-color: #f8f8f8;
            padding: 10px;
            border-radius: 3px;
            overflow-x: auto;
            margin: 10px 0;
            border: 1px solid #ddd;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }}
        th, td {{
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .severity-high {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .severity-medium {{
            color: #f39c12;
            font-weight: bold;
        }}
        .datetime {{
            text-align: right;
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 20px;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 7px;
            font-size: 12px;
            font-weight: bold;
            line-height: 1;
            color: #fff;
            text-align: center;
            white-space: nowrap;
            vertical-align: baseline;
            border-radius: 10px;
            background-color: #3498db;
            margin-left: 5px;
        }}
        .objects-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
            font-size: 14px;
        }}
        .objects-table th {{
            background-color: #f0f7ff;
            padding: 8px;
            text-align: left;
            border-bottom: 2px solid #3498db;
        }}
        .objects-table td {{
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }}
        .objects-table tr:hover {{
            background-color: #f5f5f5;
        }}
        .objects-table code {{
            font-family: Consolas, monospace;
            font-size: 12px;
            background-color: #f8f8f8;
            padding: 2px 4px;
            border-radius: 3px;
            border: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="datetime">Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>
    
    <div class="summary">
        <h2>Resumo da Análise</h2>
        <p>Total de objetos não liberados: <strong>{len(results)}</strong></p>
        <p>Total de arquivos com problemas: <strong>{len(results_by_file)}</strong></p>
    </div>
    
    <div class="stats">
        <div class="stat-box">
            <h3>Top Tipos de Objeto</h3>
            <table>
                <tr>
                    <th>Tipo</th>
                    <th>Contagem</th>
                </tr>
                {"".join(f"<tr><td>{obj_type}</td><td>{count}</td></tr>" for obj_type, count in most_common_types)}
            </table>
        </div>
        
        <div class="stat-box">
            <h3>Arquivos com Mais Problemas</h3>
            <table>
                <tr>
                    <th>Arquivo</th>
                    <th>Objetos</th>
                </tr>
                {"".join(f"<tr><td>{os.path.basename(file)}</td><td>{len(items)}</td></tr>" 
                         for file, items in sorted(results_by_file.items(), key=lambda x: len(x[1]), reverse=True)[:10])}
            </table>
        </div>
    </div>
"""
    
    # Adicionar detalhes para cada arquivo
    if detailed:
        html_content += "<h2>Detalhes por Arquivo</h2>\n"
        
        for file_path, items in results_by_file.items():
            file_name = os.path.basename(file_path)
            
            html_content += f"""
    <div class="file-box">
        <h3>{file_name} <span class="badge">{len(items)}</span></h3>
        <p>Caminho: {file_path}</p>
"""
            
            # Agrupar por método
            methods = collections.defaultdict(list)
            for item in items:
                key = (item['method_name'], item['method_line'])
                methods[key].append(item)
            
            for (method_name, method_line), method_items in methods.items():
                method_info = method_items[0]
                html_content += f"""
        <div class="method-box">
            <h4>{method_name} ({method_info['method_type']}) - Linha {method_line}</h4>
            <table class="objects-table" width="100%">
                <tr>
                    <th>Nome do Objeto</th>
                    <th>Tipo</th>
                    <th>Linha no Arquivo</th>
                    <th>Declaração</th>
                </tr>
"""
                
                for item in method_items:
                    html_content += f"""
                <tr class="object-item">
                    <td><strong>{item['object_name']}</strong></td>
                    <td>{item['object_type']}</td>
                    <td>{item['line']}</td>
                    <td><code>{item['initialization']}</code></td>
                </tr>
"""
                
                html_content += """
            </table>
        </div>
"""
            
            html_content += "</div>\n"
    
    # Adicionar recomendações
    html_content += """
    <div class="recommendations">
        <h2>Recomendações para Correção</h2>
        
        <h3>1. Use blocos try-finally para garantir a liberação de objetos</h3>
        <div class="code">
try<br>
&nbsp;&nbsp;Obj := TStringList.Create;<br>
&nbsp;&nbsp;// Uso do objeto<br>
finally<br>
&nbsp;&nbsp;FreeAndNil(Obj);<br>
end;
        </div>
        
        <h3>2. Considere usar o padrão de escopo automático</h3>
        <p>Utilize construtores de escopo automático como <code>TAutoFree&lt;T&gt;</code> quando disponível</p>
        
        <h3>3. Verifique se o objeto é transferido de escopo</h3>
        <p>Se o objeto é passado para outro método que assume a propriedade dele, não é necessário liberar no método atual.</p>
        
        <h3>4. Para interfaces Delphi (IInterface)</h3>
        <p>Objetos que implementam <code>IInterface</code> usam contagem de referência e são liberados automaticamente quando a última referência é liberada.</p>
    </div>
</body>
</html>
"""
    
    # Salvar o relatório
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def generate_empty_report():
    """Gera um relatório HTML quando nenhum problema é encontrado"""
    return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Vazamento de Memória</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            text-align: center;
        }
        .success-box {
            background-color: #dff0d8;
            border-radius: 5px;
            padding: 20px;
            margin: 50px auto;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            max-width: 500px;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .icon {
            font-size: 72px;
            color: #4caf50;
        }
        .datetime {
            text-align: right;
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>Relatório de Vazamento de Memória</h1>
    <div class="datetime">Gerado em: """+datetime.now().strftime('%d/%m/%Y %H:%M:%S')+"""</div>
    
    <div class="success-box">
        <div class="icon">✓</div>
        <h2>Nenhum vazamento de memória encontrado!</h2>
        <p>Todos os objetos estão sendo liberados corretamente nos arquivos analisados.</p>
    </div>
</body>
</html>
"""

def generate_brief_report(results):
    """
    Gera um resumo dos resultados para exibição na interface
    
    Args:
        results (dict): Dicionário com resultados da análise
        
    Returns:
        str: Texto formatado com o resumo
    """
    if not results:
        return "Nenhum objeto não liberado encontrado."
    
    total_objects = sum(len(objs) for objs in results.values())
    total_files = len(results)
    
    report = []
    report.append(f"Encontrados {total_objects} objetos não liberados em {total_files} arquivos.")
    
    # Top 5 arquivos com mais problemas
    file_counts = [(file, len(objs)) for file, objs in results.items()]
    file_counts.sort(key=lambda x: x[1], reverse=True)
    
    report.append("Arquivos com mais problemas:")
    for file_path, count in file_counts[:5]:
        report.append(f"  • {os.path.basename(file_path)}: {count} objetos")
    
    return "\n".join(report) 