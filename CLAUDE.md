# cortes-app — CLAUDE.md

Este arquivo é lido automaticamente pelo Claude Code de QUALQUER máquina que
abra este repo (Gustavo e Matheus). Duas partes: (1) REGRAS DE OPERAÇÃO — como
o Claude deve se comportar ao mexer aqui; (2) CONHECIMENTO GERAL — o que vale
pra todos os nichos.

---

# PARTE 1 — REGRAS DE OPERAÇÃO (Claude: siga SEMPRE)

## Donos

| Área | Dono | GitHub |
|---|---|---|
| `nichos/tibia/` | Gustavo | guborges |
| `nichos/league-of-legends/` | Matheus | matheusmenz22 |
| `src/`, `tests/` (código do app) | Matheus (lead) | matheusmenz22 |
| `CLAUDE.md` (este arquivo) | os dois | — |

**Nicho novo = quem cria é o dono.** Registrar na tabela acima no mesmo PR.

## Roteamento: onde cada coisa entra (decidir ANTES de escrever)

Pergunte: "isso é código, conhecimento geral, ou peculiaridade de UM nicho?"

1. **Código do app** → `src/` + teste em `tests/` (TDD, ver CONTRIBUTING.md).
   Nunca subir código sem `pytest` e `ruff check .` passando local.
2. **Regra que vale pra 2+ nichos** → PARTE 2 deste arquivo, na seção certa.
3. **Peculiaridade de 1 nicho** → `nichos/<nicho>/AGENT.md`.
4. **Bug resolvido** → `nichos/<nicho>/bugs.md` (sintoma → causa → solução),
   NO MESMO DIA. Se o bug é do motor/genérico, vai na seção "Armadilhas
   técnicas" da PARTE 2.
5. **Hipótese sem dado** → entra marcada `[a validar]` no nicho. NUNCA entra
   como regra.
6. **Nicho novo** → copiar `nichos/_TEMPLATE.md` pra `nichos/<slug>/AGENT.md`
   (slug kebab-case, ex: `grand-theft-auto-v`), criar `bugs.md` vazio, se
   declarar dono.
7. **Na dúvida de onde vai** → abre o PR do jeito que achar e marca o parceiro
   no texto explicando a dúvida. NÃO adivinha em silêncio.

## Proibições absolutas

- **NUNCA commitar segredo**: `.env`, token, API key, client_secret, cookie,
  URL com credencial. O repo é visível pro parceiro e (hoje) PÚBLICO. Se
  escapar segredo: revogar a credencial NA HORA (rebase não salva — o GitHub
  guarda histórico de PR).
- **NUNCA push direto na `main`** — sempre branch + PR (main é protegida).
- **NUNCA editar o nicho do OUTRO dono direto** — mudança em nicho alheio só
  via PR com evidência no corpo, e o dono aprova. Corrigir typo pode; mudar
  regra não.
- **NUNCA apagar/enfraquecer regra com evidência** sem PR explicando por que a
  evidência não vale mais (dado novo > dado velho, mas mostra o dado).
- **NUNCA subir regra sem data + evidência** (medição com n, ou
  sintoma→causa→solução vivido). Opinião não entra nem com boa intenção.

## Fluxo git (resumo operacional pro Claude)

```
git switch -c <tipo>/<descricao-curta>   # tipo: feat|fix|docs|refactor
# ... mudanças ...
pytest && ruff check .                    # só se tocou src/ ou tests/
git commit                                # conventional commit (ver .gitmessage)
git push -u origin <branch>
gh pr create                              # corpo: o quê + evidência + onde encaixa
```

- 1 PR = 1 assunto. Conhecimento de nicho + refactor de código = 2 PRs.
- Commit de conhecimento: prefixo `docs:`. Código: `feat:`/`fix:`.

## Formato de regra de conhecimento

```
- **Título curto da regra.** O que fazer/não fazer. Evidência: o que foi
  medido/vivido, com n se houver. (dd/mm/aaaa)
```

Bug em `bugs.md`:

```
## título curto
**Sintoma:** o que se vê.
**Causa:** raiz real (não o chute inicial).
**Solução:** o que resolveu + como validar. (dd/mm/aaaa)
```

---

# PARTE 2 — Conhecimento GERAL (todos os nichos)

Peculiaridade de nicho vai em `nichos/<nicho>/`. Aqui só o que vale pra 2+.

Fonte inicial: 1 mês de produção real do canal Exiva Clips (Tibia, jun-jul/2026),
pipeline full-auto com esteira de aprovação. n indicado por regra.

---

## O que MOVE views (dados reais, jun-jul/2026)

1. **Cadência é a alavanca nº 1.** Canal de corte vive de HIT (spike de views
   que morre em ~3 dias), não de catálogo. Cortar postagem de 23→9/dia zerou os
   hits e derrubou o canal de 75k→40k views/dia (medido 26/06→05/07). Mais
   vídeo/dia = mais bilhete de loteria. MAS: burst de 25-31/dia sem gate de
   qualidade gerou revolta (ver seção Qualidade). Faixa sã: 9-17/dia COM gate.
2. **Título é sinal pro ALGORITMO, não pro humano.** Ninguém "lê" título de
   Short — mas o algoritmo classifica o vídeo por título/desc/tags e escolhe o
   público do seeding inicial. Título-lixo ("a", "f", "kkkk") = seeding
   aleatório = mediana ~4x menor (n=72, controlando confound). Título descreve
   o que ACONTECE no clip.
3. **Retenção NÃO move views** (correlação 0,19 medida em 28d de canal). Não
   otimizar retenção esperando distribuição — otimizar seleção de momento e
   título. Retenção importa pra marca, não pro alcance.
4. **Curto ganha**: clips ≤14s renderam mediana 1165 views / 55% retenção vs
   ≥20s = 970 / 46% (n=72, Tibia — VALIDAR por nicho antes de copiar o teto).
   Trim por ação: cortar intro morta, preservar o payoff no fim.
5. **Seleção de streamer importa** tanto quanto o clip: audiência segue rosto.

## Qualidade (aprendido na dor — revolta de 22/06)

- **Título mentiroso = morte.** Clickbait que o vídeo não entrega gera revolta
  nos comentários e PERDA de inscrito. 57 vídeos despublicados num dia por isso.
- **Frase editorial queimada no vídeo** ("Escapou por um triz!") = afirmação que
  o público contesta → briga no comentário, não retenção. Não queimar opinião.
- **Gate humano obrigatório.** Full-auto sem aprovação não segura padrão de
  qualidade (provado 2x). Esteira de aprovação antes de publicar; cada decisão
  humana (aprovar/negar/crop manual) vira dado pra calibrar o auto depois.
- **QA multimodal antes de subir**: crop torto, webcam não dividida, corte no
  meio da fala, "nada acontece", título-mentira — os 5 defeitos que geram
  comentário negativo.

## Áudio e música

- **~1/3 dos clips Twitch vêm MUDOS** (Audible Magic muta trecho com música
  protegida NA ORIGEM). Detectar com `mean_volume < -50dB` no TRECHO usado
  (mute pode ser parcial) e: descartar OU salvar com música de fundo em volume
  cheio (vira a trilha).
- **Música de fundo duckada** (sidechain compress: música por baixo, voz/SFX
  por cima) melhora o produto. Feedback real: "nota 10".
- **NUNCA OST de jogo/artista real** — "música de jogo antigo" É copyright
  (Content ID claim). Usar chiptune/lo-fi CC0 de verdade (OpenGameArt etc.),
  licença documentada na pasta de música.
- Loudnorm por clip (I=-14) = volume uniforme entre streamers.

## Armadilhas técnicas (cada uma custou horas)

- **Twitch serve clip novo em HEVC 1440p** (jul/2026): `<video>` do browser não
  decodifica HEVC → tela preta com áudio ok. ffmpeg decodifica normal. Preview
  web precisa de proxy h264; render usa o source original.
- **yt-dlp apodrece a cada ~3 meses** (Twitch muda schema): sintoma = TODOS os
  downloads falham com `KeyError('data')`. Fix: `pip install -U yt-dlp`. Se o
  render do dia cair pra 0, esse é o 1º suspeito.
- **Discovery sem credencial**: GQL público da Twitch (Client-Id do próprio
  site, tá no JS) — `game(name).clips(criteria:{period:LAST_DAY,
  sort:VIEWS_DESC, languages:[PT]})`. O filtro `languages` destrava categoria
  grande (LoL, GTA) só com clips PT. Cap de 100 por query.
- **VOD de afiliado expira em ~7 dias** — clip sobrevive, o VOD (contexto
  estendido) não. Baixar cedo o que for usar.
- **Clip guarda `videoOffsetSeconds` + `video.id`** no GQL = "Watch Full Video"
  programático: `yt-dlp --download-sections` baixa só a janela do VOD (estender
  clip com contexto antes/depois).

## YouTube ops

- **Upload via API custa 1.600 units; quota default = 10.000/dia = 6 uploads.**
  Acima disso: formulário de audit do Google (funciona, mas leva tempo). Quota
  é POR PROJETO Google Cloud, compartilhada entre canais do mesmo projeto.
- **Drip**: subir como `private` com `publishAt` escalonado (YouTube publica
  sozinho) = constância sem despejar tudo de uma vez.
- **Trava de canal**: verificar channel_id do token antes de subir (token
  trocado publica no canal errado — aconteceu).
- **Monetização de corte por AdSense NÃO fecha**: YPP reprova reused content e
  RPM de Short BR ≈ R$0,25/1k. Grana real: clipping pago (campanhas/programas
  oficiais), afiliado do nicho, patrocínio direto. Corte COM licença/cadastro
  oficial (podcasts) conta como conteúdo licenciado.
- Palavras não anunciáveis derrubam alcance: evitar "morte/matar/sangue" em
  título/desc — usar "caiu", "eliminado", "quase foi".

## Processo entre nós dois

- Toda melhoria de agente/conhecimento entra por PR (main protegida).
- Aprendizado novo no seu canal → PR no nicho (ou aqui se geral) na mesma
  semana, senão evapora.
- Erro novo resolvido → `bugs.md` do nicho ANTES de fechar o dia
  (anti-regressão: ninguém redescobre bug pago).
