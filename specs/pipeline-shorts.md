# Spec: pipeline de Shorts a partir de clips da Twitch

**Escopo:** comportamento ponta-a-ponta do pipeline que transforma clips da
Twitch (top 24h de UMA categoria) em Shorts 9:16 com gate humano antes de
publicar. É spec de decisões, não de código — replicável em qualquer stack.
Fonte: pipeline Tibia em produção (jun-jul/2026). Regras de qualidade/curadoria
gerais estão no `CLAUDE.md` (PARTE 2); aqui só o fluxo e o porquê de cada gate.

## 1. Fluxo (a ORDEM dos gates é o ouro)

```
discover (24h, sort views desc, filtro de idioma)
  → elegibilidade (duração 8–60s → blocklist → dedup is_seen → priority fura fila)
  → corta em N*3 candidatos (folga p/ mudos e rejeições)
  → por clip, até N renderizados:
      download
      → detecção de ação (trim: janela de combate, teto 14s)
      → gate de áudio mudo (~1/3 dos clips)
      → caption/curador (título+desc+tags DEPOIS do trim; allow_fallback=False)
      → render 9:16 (split webcam/gameplay ou gameplay-only)
      → QA multimodal do arquivo FINAL (opcional, recomendado)
      → status 'rendered'
  → ESTEIRA HUMANA (painel web: aprovar / negar com motivo / re-crop)
  → aprovado → agendamento drip (private + publishAt escalonado)
  → YouTube publica sozinho no horário → 'published'
```

Decisões de ordem, com o porquê:

- **Caption DEPOIS do trim + gate de mudo.** O LLM recebe frames+áudio da
  JANELA que vai ao ar. Gerar copy só do título da Twitch produzia metadado sem
  relação com o vídeo (vivido, jun/2026). E não gastar quota com clip que o
  gate de áudio vai derrubar.
- **São DOIS gates de curadoria, em momentos diferentes (não é contradição
  com a skill):** (1) curador-LLM PRÉ-render — roda junto do caption, vendo
  frames+áudio do SOURCE trimado; se diz "filler, sem momento", pula sem pagar
  render nem QA; (2) curadoria visual PÓS-render na FILA
  (`skills/curadoria-cortes-twitch.md`) — agente assiste frames do RENDER
  final antes da aprovação humana (pega defeito de render e lixo que passou).
  Quem roda sem LLM usa só o gate (2).
- **QA no arquivo FINAL renderizado**, não no source: os defeitos que geraram
  revolta (22/06 — crop torto, webcam não dividida, corte no meio da fala,
  título-mentira) só aparecem no render.

## 2. Discover

- GQL público da Twitch (Client-Id do próprio site — está no JS, sem registrar
  app): `game(name).clips(criteria:{period:LAST_DAY, sort:VIEWS_DESC,
  languages:[PT]})`. Fallback: Helix oficial — entra SÓ quando o GQL falha E
  existem creds configuradas (sem creds, o erro do GQL é terminal e avisa).
  Helix NÃO filtra idioma de clip — o filtro só existe no GQL; operação normal
  é 100% GQL, Helix é seguro-reserva pra quando a Twitch mudar o schema.
- `first=100`: o GQL capa em 100 por query (200 retorna vazio). 100 em vez de
  50 dobra o pool — folga p/ dedup + ~1/3 de mudos não secarem a fila em
  cadência alta (17/dia).
- **Filtro `languages` é obrigatório em categoria global** (LoL, GTA,
  Valorant): sem ele o top-24h vem gringo/coreano. Tibia nunca precisou (PT
  domina a categoria) — em LoL é a primeira coisa a ligar.

## 3. Elegibilidade

- **Duração 8–60s**: <8s não segura hook+payoff; >60s estoura Short.
- **Blocklist** de streamer (arquivo texto, 1 por linha): ex. streamer que não
  joga o jogo da categoria. Editável sem deploy.
- **Priority** fura a fila (sort estável: prioritários primeiro, views desc
  dentro de cada grupo): ex. envolvidos numa guerra/rivalidade do momento.
- **Dedup `is_seen`**: qualquer registro definitivo no banco bloqueia
  reprocesso. EXCEÇÃO: `deferred` (ver §4).

## 4. Máquina de estados do clip

| Estado | Dispara | Terminal? |
|---|---|---|
| `discovered` | entrou no processamento | não |
| `skipped` | mudo na origem E sem música disponível p/ salvar | sim |
| `deferred` | LLM indisponível (quota) no caption, OU título gerado fraco, OU QA não conseguiu rodar | **não** |
| `curador_rejected` | LLM assistiu e reprovou: clip é filler, sem momento | sim |
| `qa_rejected` | QA achou defeito REAL no render (re-render daria o mesmo) | sim |
| `error` | exceção em qualquer etapa (motivo gravado) | reprocessável manualmente |
| `rendered` | passou todos os gates automáticos; entra na esteira | não |
| `denied` | humano negou na esteira, COM motivo gravado (vira dado p/ calibrar o auto) | sim |
| `approved` | humano aprovou mas o upload ficou pra depois (cap/quota do dia estourado no fluxo em lote, ou falha de upload a re-tentar) | não |
| `scheduled` | upload feito: private + publishAt gravado no YouTube | não |
| `published` | YouTube publicou no horário agendado | sim |

**Dois caminhos do aprovar (evita confusão):** o botão Aprovar da esteira
agenda NA HORA — upload imediato no próximo slot livre (a quota é consumida
nesse momento; se os slots de hoje acabaram, o publishAt cai no dia seguinte
automaticamente). O fluxo em LOTE (agendar todos os aprovados de uma vez)
aplica cap de `posts_per_day` por execução; o excedente fica `approved` e o
lote do dia seguinte pega. Mesmo destino, gatilhos diferentes.

**LLM é opcional — mas escolha explícita:** existe modo TÍTULO CRU sem LLM
nenhum (foi o "modo treino" do sistema original: título da Twitch sanitizado +
gate humano; zero quota). Nesse modo não existe `deferred` por caption. O
`allow_fallback=False` vale só no modo LLM: se você OPTOU por título gerado,
LLM caiu = adia, nunca degrada silenciosamente pro cru (título-lixo = ~4x
menos, §6). Não deixar o modo "meio a meio" acontecer por acidente.

**Por que `deferred` NÃO conta como visto:** o adiamento é sempre falha de
INFRA (quota do LLM), nunca veredito sobre o clip. Publicar com o fallback
(título cru da Twitch) renderia ~4x menos (ver §6) — adiar > postar morto. O
clip volta a ser elegível no próximo run ENQUANTO ainda estiver no top-24h; ao
sair do trending, some sozinho da fila. Bound natural: não posta lixo, não
represa fila.

## 5. Dedup em 2 níveis

1. **Tabela `clips`** (PK = clip_id): garante que um clip nunca é
   baixado/renderizado duas vezes (`is_seen`, com a exceção do `deferred`).
2. **Tabela `posts`** (PK = clip_id + plataforma): 1 linha por entrega.
   `is_posted(clip, plataforma)` = já `scheduled`/`published` LÁ. Permite o
   MESMO mp4 estar `published` no YouTube e `pending` no TikTok, sem tocar no
   status do clip. Nunca dedupar entrega pelo status do clip — trava
   multi-plataforma.

## 6. Decisões com evidência (não inventar valores — herdar estes ou medir)

- **Buffer: renderizar N=12/dia com cap de publicação 6/dia.** A folga absorve
  negações da esteira + ~1/3 de mudos; sempre há estoque pra revisar mesmo em
  dia fraco. Excedente aprovado fica pro dia seguinte.
- **Título-lixo derruba ~4x** ("a", "f", "kkkk" → mediana ~4x menor, n=72,
  confound controlado). Daí `allow_fallback=False` no caption: LLM caiu → 
  `deferred`, nunca gravar o título cru como fallback silencioso.
- **Trim: teto 14s** (era 25): clips ≤14s = mediana 1165 views / 55% retenção
  vs ≥20s = 970 / 46% (n=72, Tibia — VALIDAR no seu nicho antes de copiar).
  Front-chop: corta a frente morta, preserva o payoff no fim.
- **Gate de mudo**: `mean_volume < -50dB` no TRECHO usado (mute do Audible
  Magic pode ser parcial). Com música CC0 disponível → salva com música em
  volume cheio (vira a trilha); sem música → `skipped`, Short mudo não sobe.
  Mix e ducking: `skills/ducking-musica-voz.md`.
- **Cadência**: faixa sã 9–17/dia COM gate (cortar 23→9 derrubou 75k→40k
  views/dia; burst 25–31/dia sem gate gerou a revolta de 22/06).
- **Drip**: subir `private` + `publishAt` escalonado em slots (default de hora
  em hora, 06–22 local) = constância sem despejar tudo. Atenção: cada upload
  via API gasta quota NO DIA do upload, mesmo agendado — o cap diário de
  publicação é também o cap de uploads/dia.
- **Gate humano é obrigatório** (full-auto puro falhou 2x): nada publica sem
  aprovação na esteira. Cada aprovar/negar/re-crop vira dado de calibração.

## 7. Segurança de canal (trava dura)

Antes de QUALQUER upload, consultar o canal do token autenticado
(`channels.list(mine=true)`) e comparar com o channel_id ESPERADO (config):

- channel_id esperado vazio → **recusa** o upload (fail-closed, não fail-open);
- canal autenticado ≠ esperado → **recusa** com mensagem dizendo qual canal o
  token aponta.

Motivo: token OAuth trocado publica no canal errado — aconteceu (Tibia quase
caiu em canal de outro assunto). Com 2+ canais na mesma máquina, cada produto
tem seu próprio diretório de token + channel_id. Memoizar a verificação por
canal (1 chamada por processo). Custo: 1 unit de quota; barato demais pra pular.

## Relacionados

- `skills/curadoria-cortes-twitch.md` — critério de aprovar/negar na esteira
- `skills/ducking-musica-voz.md` — mix da BGM, loudnorm, clip mudo
- `skills/borda-neon-logo.md` — identidade visual do render 9:16
- `CLAUDE.md` PARTE 2 — o que move views, armadilhas técnicas, YouTube ops
