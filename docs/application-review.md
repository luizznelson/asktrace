# Revisão da aplicação: entrada clara e falhas verificáveis

## O problema observado

A página de boas-vindas exibia uma espera de IA mesmo sem uma pergunta nesta aba.
O estado pertence à aplicação e preserva tentativas anteriores, inclusive avaliações;
não representa o consumo desta sessão. Apagar esse registro poderia provocar novas
chamadas durante uma quota já observada.

Agora a entrada permanece livre desse alerta. A indisponibilidade aparece junto à
tentativa que falhou, com explicação do que ocorreu e recuperação explícita por regras
locais. Abrir a página, restaurar o histórico ou atualizar a disponibilidade não envia
uma pergunta aos provedores. O modo local não exibe o alerta de IA.

## O que foi revisado e corrigido

| Área | Correção ou proteção conferida | Evidência |
| --- | --- | --- |
| Entrada e recuperação | Aviso condicionado à falha; nova exploração limpa o estado visual; falha de atualização tratada | Contrato DOM em Node |
| Organização da interface | Traduções consolidadas, funções nomeadas, remoção de renderização e eventos duplicados, código formatado | Código e contrato DOM |
| Histórico | Limites de tamanho/quantidade e validação da estrutura de respostas antes da restauração | Contrato DOM com registro corrompido |
| HTTP de entrada | Host, origem e token; token não ASCII rejeitado; corpo limitado; enquadramento ambíguo e JSON excessivamente aninhado rejeitados | Testes HTTP reais em loopback |
| HTTP de saída | Provedores não seguem redirecionamentos; respostas de erro são fechadas | Teste com servidor local que retorna 302 e confirma ausência de segunda requisição |
| Estado dos provedores | Catálogo validado; espera corrompida não é apagada nem autoriza nova chamada; sessão continua disponível para regras locais | Testes com estado inválido e transporte simulado |
| Falhas de arquivos e serviços | Respostas genéricas sem conteúdo interno; falha do diagnóstico não impede abrir a sessão | Testes de falha controlada |
| Banco e integridade | Consultas fixas parametrizadas, snapshot verificado e acesso somente leitura | Suíte com PostgreSQL e verificação das permissões efetivas |
| Arquivos para commit | Credenciais locais e estado de quota ignorados; busca pelos valores secretos configurados em arquivos versionados/não ignorados | Registro minimizado, sem valores secretos |

## Resultado reproduzível

Execute na raiz, com ambiente instalado, PostgreSQL ativo e login de leitura configurado:

```powershell
.venv/Scripts/python.exe -m scripts.verify_application_review
```

O comando roda 102 testes Python (incluindo integração), Ruff, sintaxe JavaScript,
contrato DOM, verificação de espaços do Git, busca pelas credenciais locais configuradas,
permissões do banco e duas consultas HTTP por regras locais. Publica somente o resumo
em uma nova pasta `runs/application-review-*`; não publica token da sessão nem chaves.
Não executa provedores externos ou atualiza versões de dados.

[Registro desta revisão](../runs/application-review-dbcf1edc-1550-4274-bfb9-fcc210fa104f/verification.json): resumo da base original com 1.081 compras
e consulta por municípios da ampliada com 2.537 compras, sem tentativas de LLM.
Hashes identificam os arquivos de aplicação/teste verificados. A busca de credenciais
cobre valores ativos conhecidos nos arquivos atuais; não cobre todo o histórico Git
nem credenciais antigas desconhecidas.

## Limites que permanecem

- O servidor HTTP é local, restrito a `127.0.0.1`. O token protege a sessão local;
  não é autenticação de usuários para uma hospedagem pública.
- O bloqueio de consultas é por processo. O estado de quota usa substituição atômica
  de arquivo, sem coordenação entre vários processos. Não operar várias instâncias
  compartilhando a mesma quota como se existisse um limite distribuído.
- Tempos de rede são limites de operações de socket; não há cancelamento completo
  do trabalho do servidor quando a aba fecha.
- Cotas e capacidade externas continuam sujeitas aos provedores. Esta revisão não
  comprova que a IA voltou a responder nem redefine esperas observadas.
- O histórico fica nesta aba e não constitui memória conversacional do modelo.
  Respostas restauradas são registros anteriores, não novas consultas.
- Não houve inspeção visual em navegador nesta revisão. O teste DOM verifica
  comportamentos, sem comprovar layout, contraste ou experiência em dispositivos reais.
- Esta revisão não substitui teste de intrusão ou auditoria independente.
