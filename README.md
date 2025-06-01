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
- Bibliotecas padrão do Python (não requer instalação de pacotes adicionais)
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

- `main.py`: Interface gráfica e controle principal do programa
- `dproj_parser.py`: Parser para arquivos de projeto Delphi
- `pas_analyzer.py`: Analisador de código fonte Delphi
- `report_generator.py`: Gerador de relatórios HTML

## Contribuindo

Contribuições são bem-vindas! Se você encontrar algum bug ou tiver sugestões de melhorias, por favor abra uma issue no GitHub.

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes. 