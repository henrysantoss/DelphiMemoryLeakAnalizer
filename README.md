# Analisador de Memória para Delphi

Este programa analisa arquivos Delphi (.pas) para identificar objetos que não são liberados da memória adequadamente, causando vazamentos de memória.

## Funcionalidades

- Analisa projetos Delphi (.dproj)
- Identifica objetos criados e não liberados em funções e procedimentos
- Gera relatório detalhado dos problemas encontrados
- Interface gráfica para facilitar o uso

## Requisitos

- Python 3.6 ou superior
- Bibliotecas padrão do Python (não requer instalação de pacotes adicionais)

## Como usar

1. Execute o arquivo `main.py`
2. Na interface, clique em "Selecionar arquivo .dproj" e escolha o projeto Delphi que deseja analisar
3. Clique em "Iniciar Análise" para começar o processo
4. Acompanhe o progresso no log da aplicação
5. Ao final, um relatório será gerado no mesmo diretório do arquivo .dproj

## O que o programa procura

O programa procura por padrões como este:

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

## Limitações

- O analisador pode não detectar situações complexas de criação e liberação de objetos
- Não analisa objetos passados como parâmetros que devem ser liberados dentro da função
- Análise estática pode gerar falsos positivos em algumas situações 