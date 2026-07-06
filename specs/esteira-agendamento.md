# Esteira de aprovação + Agendamento drip

> **ESCOPO**: comportamento da fila de aprovação humana e do agendamento de publicação
> para pipelines de cortes (Twitch → Shorts). Agnóstico de stack — descreve decisões de
> produto e regras validadas em produção; implemente na sua arquitetura (fila + UI de
> aprovação/reprovação do review/). Não é dump de código.

## 1. Filosofia: gate humano obrigatório

- **Full-auto reprovou 2x na prática**: título-mentira, crop torto e corte no meio da fala
  geraram revolta nos comentários e perda de inscrito. Nenhum vídeo vai ao ar sem um humano
  clicar "aprovar".
- O humano **aprova, não caça lixo**: antes da fila humana roda uma curadoria por agente
  (assiste frames, reescreve título honesto, nega clip sem momento) — ver
  `skills/curadoria-cortes-twitch.md`. A fila que chega ao humano já deve estar limpa.
- **Toda decisão humana é dado de calibração**: motivo de negação, caixa de crop, título
  editado. O objetivo é o automático aprender com o histórico até o humano só confirmar.

## 2. Fluxo da esteira

Estados do clip: `rendered` (na fila) → `approved` → `scheduled` → `published` | `denied` | `error`.
A fonte de verdade é o status no banco; a UI é só uma view disso.

**Card** (grid, um por clip em `rendered`): player do vídeo final vertical + título (editável
inline, sobrepõe o gerado — vale até subir) + streamer/views/duração + badge com nota do
pipeline. Ações: **Aprovar**, **Negar**, **Ajustar enquadramento**.

**Aprovar** — agenda **na hora**, no próximo slot livre (ver §4):
- UI **otimista**: o card some imediatamente; o upload roda em background.
- Toast confirma com o horário agendado ("agendado 08/07 14:00").
- Se o upload falhar, o clip continua `rendered` no servidor e o próximo refresh da fila
  o traz de volta — a UI nunca é fonte de verdade.

**Negar** — **exige motivo** (modal, não fecha sem texto):
- **Chips de motivos comuns** clicáveis que concatenam no campo: "webcam cortada",
  "sem webcam mas devia ter", "gameplay sem ação", "título fraco", "legenda errada",
  "áudio ruim", "clip chato", "atribuição errada".
- O motivo é **dado**: salvo com o registro (`status=denied` + `deny_reason`). O histórico
  de negações calibra os filtros automáticos do futuro.
- **Auto-blocklist**: se o motivo contém palavra-chave de exclusão ("remove", "não joga",
  "não é <jogo>", "fora"), o streamer do clip entra automaticamente na blocklist de
  descoberta — nunca mais é buscado. Uma negação vira regra permanente sem passo extra.

## 3. Editor de enquadramento manual

Corrige o crop automático errado sem sair da fila.

- Abre sobre um **frame do meio do trecho que vai ao ar** (não do source inteiro — o começo
  do clip pode ser outra tela).
- **Caixa VERDE = jogo**, com **aspect travado** no aspecto exato do painel de jogo no vídeo
  final (9:16 quando gameplay-only; quando há webcam, o aspecto resultante do split, que
  varia com o tamanho da cam). Arrastar move; o canto redimensiona mantendo o aspect.
- **Caixa AZUL = webcam**, **livre** (qualquer aspecto/tamanho).
- Controles: tem webcam (sim/não), posição da cam (cima/baixo), tamanho da cam (frações da
  altura final, ex.: 0.2/0.3/0.4), legenda opcional + posição.
- **Prévia em canvas ao lado = WYSIWYG exato**: reproduz a mesma matemática do render
  (center-crop para cobrir o destino, cam+jogo empilhados), atualiza ao vivo durante o
  arrasto. O que se vê na prévia é o corte final, sem surpresa pós-render.
- **Salvar não trava**: fecha o editor na hora, re-renderiza em background (ver §5) e o
  usuário segue para o próximo card.
- **Spec persistido** (`crop_json`): JSON com frações 0–1 do source (`cx, cy, w, h` de cada
  caixa) + flags (posição/tamanho da cam, legenda). Reabrir o editor recarrega o último
  spec — as caixas voltam onde estavam.
- **`crop_json` é dado de treino**: cada correção manual é um exemplo rotulado
  (frame de entrada → enquadramento correto) para calibrar o detector automático de
  webcam/ação. Meta: auto acertar >90% e o humano só confirmar.
- **Webcam real ≠ PiP de destaque**: além da webcam, o editor permite destacar um elemento
  da tela (zoom/PiP). O render é idêntico, mas o rótulo é separado
  (`split_kind: "webcam" | "focus"`) — senão o PiP suja o dataset do detector de webcam.

## 4. Agendamento drip (publicação escalonada)

Aprovar **não publica na hora**. O vídeo sobe como **`private` com `publishAt`**
(RFC3339 UTC) e o YouTube publica sozinho no horário. Resultado: constância de N posts/dia
em horários fixos, sem despejar um lote inteiro de uma vez — mesmo que a aprovação humana
aconteça em um único sentão de manhã.

**Slots**: grade de horários locais configurável (ex.: de hora em hora, 06–22) +
`posts_per_day` (cap diário).

**Espaçamento quando `posts_per_day` < nº de slots**: escolher os slots **espalhados** pela
grade por interpolação de índice — `idx_i = round(i * (S-1) / (n-1))` para `i` em `0..n-1`,
com S slots e cap n (ex.: 17 horários com cap 6 → 06, 09, 12, 16, 19, 22). Sem isso os
posts amontoam no começo do dia. Cap ≥ total → usa todos.

**Próximo slot livre** (usado pelo Aprovar): varre dia a dia a partir de agora, pulando
(a) horários no passado ou muito próximos (margem ~10 min) e (b) horários já reservados —
manter um set dos `publishAt` de tudo que está `scheduled` para nunca colidir. Guarda de
iteração (ex.: 60 dias) contra loop infinito.

**Quota — a pegadinha central**: cada `videos.insert` custa ~1600 units **no dia da
chamada**, mesmo com `publishAt` semanas no futuro. Agendar 30 vídeos hoje = estourar a
quota hoje. Logo:
- **Cap por execução** do agendador em lote = `posts_per_day`.
- O **excedente permanece `approved`** e é agendado na execução do dia seguinte — nada se
  perde, só espera.

**Trava de canal (obrigatória em multi-canal)**: token OAuth **por canal**, e antes de
qualquer upload comparar o channel id autenticado com o esperado na config daquele pipeline.
Id divergente **ou vazio** = upload recusado com erro explícito. É o que impede um corte de
um jogo cair no canal de outro.

## 5. Regras operacionais

- **Render manual serializado**: semáforo de 1 — encode de qualidade é pesado; N renders
  simultâneos derrubam a máquina. Pedidos extras entram em fila (`queued` → `running`);
  pedido repetido para o mesmo clip é recusado (já está na fila).
- **Estado de re-render é server-side**: o endpoint da fila devolve `rendering: true/false`
  por item; o front desenha o badge "re-renderizando" e desabilita Aprovar/Ajustar a partir
  disso. Sobrevive a refresh da página — nunca guardar esse estado só no navegador.
- **Polling adaptativo**: rápido (~4s) enquanto há busca/render ativo, lento (~15s) ocioso.
  Não re-renderizar cards existentes no refresh (não interromper o player); só adicionar
  novos e remover os que saíram.
- **Render atômico**: renderizar num arquivo temporário e mover por cima do final só quando
  terminar — a fila nunca serve um mp4 meio escrito.
- **Busca com trava anti-duplicata**: o botão "buscar clipes" dispara o pipeline de
  descoberta+render em background (não publica nada). Antes de disparar, verificar se já
  existe um processo de busca vivo — inclusive checando no SO, não só numa variável do
  servidor web (robusto a restart). Já tem um rodando = recusa. Clipes novos pingam na
  fila conforme renderizam.
- **Controle manual do ritmo**: enquanto a qualidade não estiver validada, busca é manual
  (botão), não timer. Timer automático só depois do gate de qualidade estar provado.
