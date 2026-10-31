# Limitações reais

| Área | Limitação e impacto | Evolução recomendada |
|---|---|---|
| Classificação | Regras lexicais; confidence score heurístico, não probabilístico. Paráfrases e perguntas com dois domínios podem pedir esclarecimento. | Avaliar classificador com exemplos rotulados; calibrar threshold; usar modelo estruturado opcional depois de medir precisão/recall. |
| Busca interna | BM25 local com reforço de título por IDF e heurística de plural; não entende sinônimos (ex.: "trabalhar de casa" não encontra home office). A resposta extrativa mostra os itens com mais termos em comum, podendo omitir um item relevante (ex.: T012 omite a orientação de não incluir segredos no chamado). | Avaliar recall por consulta; adicionar stemming/embeddings locais e reranking se houver ganho mensurável. |
| Resposta com LLM | Provider opcional não foi testado contra serviço real. O prompt restringe as fontes, mas geração pode extrapolar. | Adicionar avaliação de groundedness, limite de tokens, moderação e revisão de privacidade antes de habilitar em produção. |
| Financeiro | Suporta soma/média/contagem por competência, filtros (centro de custo, departamento, categoria, status, pagamento, contraparte), agrupamentos, orçamento, execução orçamentária e inadimplência. Qualificadores fora dessa lista (ex.: texto livre da descrição) não são filtrados; "Marketing" é ambíguo entre departamento e categoria e é tratado como categoria quando não há a palavra "departamento". Não é consulta livre nem contabilidade real. | Expandir intents/filtros, métricas e testes de borda. Se volume crescer, migrar a camada tabular para SQL parametrizado. |
| Ouvidoria | Consulta protocolo exato, enumerações e contagem simples por status; não abre manifestação nem envia resposta. | Integrar canal oficial apenas com autenticação, autorização, auditoria e confirmação explícita. |
| Segurança | Sem autenticação, autorização por perfil ou rate limiting. Adequado apenas a execução local/demonstração. | Adicionar SSO/RBAC, limitação de requisições, HTTPS, secrets manager, retenção e auditoria antes de exposição externa. |
| Logs | Pergunta integral omitida; hash e tamanho mantêm rastreio mas não permitem auditoria textual da conversa. Hash de pergunta simples não é anonimização forte para entradas de baixa entropia. | Definir retenção e acesso; manter dados de auditoria separados e consentidos, com mascaramento validado. |
| Docker | Dockerfile/Compose foram revisados estaticamente na Fase 8. Em 2026-10-31 o Docker Desktop executou `desafiotecnico-agente-1` com status healthy na porta 8000 (evidências em `docs/evidencias/`). Não houve validação em Linux CI neste ambiente. | Manter o healthcheck no CI e testar clone limpo em outra máquina quando possível. |
| Navegador | JavaScript passou `node --check`, e integração API passou TestClient; não houve inspeção visual end-to-end em navegadores reais. | Conferir layout/teclado/leitor de tela em Chrome/Edge e celular. |
| Compatibilidade | Desenvolvido no Python 3.12 do ambiente; o projeto pede 3.11+ e não foi executado em Python 3.11. | Rodar CI em Python 3.11 e 3.12. |
| Entrega | A exportação nativa integral das conversas da ferramenta não está disponível. O histórico estruturado está em `docs/AI_INTERACTIONS.md` e `DEVELOPMENT_LOG.md`. | Manter esses arquivos atualizados em qualquer evolução posterior. |

## Desvio de categoria no caso de segurança

O arquivo de avaliação descreve T010 como `fora_de_escopo_ou_segurança`, mas o contrato do projeto normaliza apenas quatro categorias. A aplicação classifica o pedido de senha como `informacoes_internas` para acionar o agente de segurança e recusa a divulgação. A ação é segura; a diferença está no rótulo esperado do fixture.
