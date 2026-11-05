# Hospedagem gratuita: avaliação para o AskTrace

Pesquisa em 04/11/2026. Planos e limites devem ser reconferidos antes da criação dos serviços.
Não houve criação de conta, publicação ou alteração dos serviços do ReceiptTrace.

## Recomendação

**Render Free para o app e Neon Free para o PostgreSQL**, com um artefato de dados
verificado entregue ao app na publicação. A combinação preserva Python/PostgreSQL,
mantém interface e API na mesma origem e aproveita a familiaridade do mantenedor com Render.
É uma recomendação para uma demonstração de baixo tráfego, sujeita às cotas dos serviços.

| Opção | Condições verificadas | Adequação ao projeto |
| --- | --- | --- |
| Render Free + Neon Free | Render suspende o app após 15 minutos sem tráfego; 750 horas/mês compartilhadas no workspace e disco efêmero. Neon informa 1 GB de PostgreSQL e 100 CU-h/mês por projeto no Free. | Recomendada para manter o stack e evitar a expiração do banco gratuito do Render. |
| Render Free + Supabase Free | Supabase informa 500 MB de banco e pausa após uma semana de inatividade. | Alternativa, com atenção à retomada de um projeto pouco visitado. |
| Render Free + Render Postgres Free | O banco gratuito do Render expira após 30 dias. | Serve para teste temporário, não como base durável da demonstração. |
| Hugging Face Docker Spaces | A documentação atual exige plano pago para criar novos Docker/Gradio Spaces, apesar de CPU Basic não ter custo por hora. | Não é a opção de custo zero para criar esta aplicação. A exceção ZeroGPU de Gradio não corresponde ao stack atual. |

Fontes oficiais: [Render Free](https://render.com/docs/free), [Neon](https://neon.com/pricing),
[Supabase](https://supabase.com/pricing), [Hugging Face Spaces](https://huggingface.co/docs/hub/spaces-overview).

Neon informa Free sem prazo fixo e sem cartão, com suspensão de compute ao consumir as
cotas. Não se deve tratar isso como disponibilidade ilimitada. Render pode suspender
serviços ao esgotar horas e tem limites separados de tráfego/build. Se ReceiptTrace e
AskTrace estiverem no mesmo workspace, compartilham a franquia de horas do Render.

## Medidas locais, não estimativas de preço

- Banco `asktrace`: **12.236.467 bytes**, exibido como 12 MB pelo PostgreSQL.
- Arquivos de `data/raw` e `data/processed`: **12.661.290 bytes** no momento da revisão.
  Incluem arquivos históricos e tentativas; isso ainda não é a seleção de um pacote de deploy.
- Cobertura atual: 2.537 compras, 2.536 compras aptas pesquisadas e 679 contratos.

O volume medido cabe com margem nas cotas de armazenamento de banco citadas. Isso não
comprova consumo mensal de compute, egress ou memória da aplicação. O uso precisa ser
monitorado na demonstração; limites de conta/serviço continuam válidos.

## O que falta adaptar antes de publicar

O código atual é explicitamente local. Não basta enviar o repositório ao Render:

1. **Servidor público:** trocar o servidor de desenvolvimento da biblioteca padrão por
   uma entrada apropriada para publicação, com porta do ambiente e escuta configurável.
   Host/origem devem continuar validados para o domínio HTTPS correto, sem liberar tudo.
2. **Banco remoto:** parametrizar a conexão, habilitar TLS com validação e separar o
   login somente leitura do procedimento de migração/carga. Hoje as conexões usam
   `127.0.0.1:15432` e o banco do Docker local.
3. **Dados reprodutíveis:** selecionar os arquivos referenciados pelos dois recortes,
   empacotar com hashes e defini-los como artefato de leitura. Hoje eles ficam fora do
   Git. A API precisa desses bytes para conferir as evidências, mesmo com PostgreSQL remoto.
   Não publicar os arquivos brutos sem revisão; definir uma entrega privada ao build/app.
4. **Reinícios:** o disco Free do Render é efêmero. A demonstração deve reconstruir os
   arquivos necessários de maneira verificável, sem refazer horas de coleta do PNCP a
   cada inicialização. Dados persistentes não devem depender do diretório do servidor.
5. **Quotas de IA:** definir orçamento compartilhado e persistência da espera. O arquivo
   `data/runtime/provider-health.json` atual pode desaparecer em reinícios. Começar a
   demonstração com regras locais disponível, mantendo a IA opcional e identificada.
6. **Operação:** endpoint de saúde, erros sem segredos, timeout, limites de uso e teste
   de reinício/cold start. Importar a base uma vez e conferir as mesmas contagens e hashes.
7. **Verificação final:** abrir o endereço público em computador e celular, executar
   os seis caminhos, testar exportação e só então gravar o vídeo.

Esse checklist é avaliação de prontidão; a adaptação e o deploy não foram executados
nesta pesquisa. Chaves e strings de conexão devem ser cadastradas como segredos do serviço,
sem serem enviadas por chat, colocadas no README ou versionadas.

## Revisão de interface disponível nesta etapa

O navegador local continua desativado nas configurações do Work, então esta não é uma
aprovação visual de desktop/celular. A inspeção do código identificou e corrigiu:

- Histórico inacessível abaixo de 800 px: agora há uma área expansível própria.
- Botão de nova exploração sem rótulo explícito quando o texto é ocultado: rótulo adicionado.
- Controles de toque pequenos: envio e botões do cabeçalho receberam área mínima de 44 px.
- Rótulos de 8–9 px e notas com contraste fraco: tamanhos e cores foram ajustados nos
  elementos revisados; isso não é uma certificação de acessibilidade da aplicação inteira.

Os testes DOM conferem que o histórico móvel abre o resultado salvo sem nova consulta
ou chamada de IA, fecha após a seleção e acompanha a limpeza da sessão. A disposição
real, corte de texto, foco, rolagem e contraste devem ser conferidos no navegador.
