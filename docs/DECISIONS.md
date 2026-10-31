# Decisões de arquitetura (ADR)

## ADR-001 — Dados originais preservados

- **Contexto:** o pacote inclui CSV, JSON e Markdown sintéticos que devem ser usados como fonte de verdade.
- **Decisão:** manter as pastas originais sem transformação in-place; arquivos derivados ficam em `data/processed/` e podem ser recriados.
- **Alternativas:** importar/substituir os CSVs por SQL no próprio pacote.
- **Consequências:** facilita auditoria e comparação com fixtures; exige loader local e uma etapa explícita de indexação.

## ADR-002 — Agregações tabulares determinísticas

- **Contexto:** perguntas financeiras pedem somas, filtros, períodos e orçamento, e as instruções da base destacam precisão decimal.
- **Decisão:** consultas financeiras ficam em Python controlado com `Decimal`, datas ISO e filtros enumerados. Ouvidoria usa protocolo exato e filtros fechados.
- **Alternativas:** SQL gerado por LLM ou carregar um banco Postgres.
- **Consequências:** respostas numéricas são reproduzíveis e não dependem de modelo; cobertura de consultas deve ser explicitamente limitada e testada.

## ADR-003 — Recuperação local BM25 para políticas

- **Contexto:** há 10 Markdown curtos e FAQ de 7 itens, sem embeddings ou endpoint de modelo fornecido.
- **Decisão:** fazer chunking por títulos/seções e retrieval lexical BM25 local, com filtro de domínio, seção e origem; permitir evolução para embeddings após avaliação.
- **Alternativas:** palavras-chave simples, TF-IDF com dependência adicional, embeddings locais/externos e banco vetorial.
- **Consequências:** execução sem rede e reconstrução simples; BM25 não entende todos os sinônimos e exige score mínimo/evidências antes de responder.

## ADR-004 — Provider opcional, fallback obrigatório

- **Contexto:** o desafio pede modo com e sem provedor, mas nenhuma credencial foi fornecida.
- **Decisão:** contrato de provider separado do domínio, integração externa ativada somente por configuração explícita, saída estruturada validada e fallback local em indisponibilidade.
- **Alternativas:** exigir uma chave de API ou não oferecer provider.
- **Consequências:** demo permanece executável sem chave; modo externo precisa documentar envio de conteúdo, timeout, limites e configuração. Não enviar dados sem ativação explícita.

## ADR-005 — Logs sem texto integral da pergunta

- **Contexto:** rastreabilidade é necessária, mas perguntas podem conter dados pessoais ou segredos.
- **Decisão:** registrar UUID, horário, hash do conteúdo, tamanho, categoria, confiança, agente, IDs/fontes, duração, status e erro sanitizado; omitir a pergunta literal.
- **Alternativas:** armazenar o texto integral ou desabilitar logs.
- **Consequências:** mantém rastreio com menos dados; inspeção qualitativa exigirá revisão manual separada e consentida.

## ADR-006 — API versionada e frontend mesma origem

- **Contexto:** contrato deve apresentar classificação, fontes, execução e latência; CORS aberto não é necessário para UI servida pelo FastAPI.
- **Decisão:** usar `/api/v1`, schemas Pydantic explícitos e servir UI na mesma origem; lista de origens externas fica configurável e vazia por padrão.
- **Alternativas:** manter `/api/chat` sem versão ou liberar CORS global.
- **Consequências:** contrato claro e navegável pelo Swagger; clientes antigos precisam migrar ou receber alias temporário documentado.
