# Analisador de Memória para Delphi

Este programa analisa arquivos Delphi (.pas) para identificar objetos que não são liberados da memória adequadamente, causando vazamentos de memória. Uma ferramenta essencial para desenvolvedores Delphi que desejam manter a qualidade e performance de suas aplicações.

## Funcionalidades

- Analisa projetos Delphi (.dproj) e arquivos individuais (.pas)
- Identifica objetos criados e não liberados em funções e procedimentos
- Gera relatório detalhado em HTML com os problemas encontrados
- Interface gráfica intuitiva e fácil de usar
- Suporte a análise de múltiplos arquivos em um projeto
- Barra de progresso para acompanhamento em tempo real
- Log detalhado do processo de análise

## Requisitos

- Python 3.6 ou superior
- Bibliotecas Python:
  - tkinter (incluído na instalação padrão do Python)
  - threading (incluído na instalação padrão do Python)
  - os (incluído na instalação padrão do Python)
  - re (incluído na instalação padrão do Python)
  - xml.etree.ElementTree (incluído na instalação padrão do Python)
  - collections (incluído na instalação padrão do Python)
  - datetime (incluído na instalação padrão do Python)
  - webbrowser (incluído na instalação padrão do Python)
- Bibliotecas de terceiros:
  - pyparsing (instalar via pip: `pip install pyparsing`)
- Sistema operacional Windows (recomendado para melhor compatibilidade com projetos Delphi)

## Como usar

1. Execute o arquivo `main.py`
2. Na interface, clique em "Selecionar Arquivo" e escolha:
   - Um arquivo de projeto Delphi (.dproj) para analisar todo o projeto
   - Um arquivo individual (.pas) para análise específica
3. Clique em "Iniciar Análise" para começar o processo
4. Acompanhe o progresso no log da aplicação
5. Ao final, um relatório HTML será gerado no mesmo diretório do arquivo analisado
6. O relatório será aberto automaticamente no seu navegador padrão

## O que o programa procura

O programa analisa o código em busca de padrões comuns de vazamento de memória, como:

```pascal
procedure ReturnJustify(Req: THorseRequest; Res: THorseResponse; const poConexao: TdmConexao);
var
  loDm: TQueryModule;
  loQry: TFDQuery;
begin
  loDm := nil;
  loQry := nil;
  try
    loDm := TQueryModule.Create(nil);

    if (not poConexao.VerificaPermiteJustificar(Req)) then begin
      Erro('You do not have permission to see all justifications in the system');
    end;

    loQry := poConexao.CriaQRY(loDm.qryReturnAllJustifies.SQL.Text);
    loQry.Open;

    Res.Send<TJSONArray>(FormataJSONArray(loQry));
  finally
    FreeAndNil(loDm);
    // Aqui deveria ter um FreeAndNil(loQry);
  end;
end;
```

No exemplo acima, `loQry` é criado mas não é liberado, o que causa um vazamento de memória.

## Estrutura do Projeto

O projeto é organizado em módulos principais que trabalham em conjunto:

- `main.py`: 
  - Interface gráfica do usuário (GUI)
  - Gerenciamento de threads para análise não-bloqueante
  - Controle do fluxo de análise
  - Geração e exibição de relatórios

- `dproj_parser.py`:
  - Leitura e interpretação de arquivos .dproj
  - Extração de arquivos .pas do projeto
  - Mapeamento de dependências entre arquivos

- `pas_analyzer.py`:
  - Análise sintática de código Delphi
  - Detecção de padrões de vazamento de memória
  - Rastreamento de criação e liberação de objetos
  - Geração de métricas de análise

- `report_generator.py`:
  - Geração de relatórios HTML
  - Formatação e estilização dos resultados
  - Categorização dos problemas encontrados
  - Estatísticas de análise

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes. 