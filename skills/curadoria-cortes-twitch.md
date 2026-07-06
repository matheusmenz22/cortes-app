# Skill: curadoria de cortes da TWITCH (gate visual antes de subir)

ESCOPO: clips vindos da **Twitch** (clip curto já recortado pela audiência).
Cortes de vídeo do YouTube (podcast/VOD longo) terão skill PRÓPRIA — a seleção
de momento lá é outro problema (ninguém pré-clipou).

Objetivo: nenhum clip sobe sem um agente ASSISTIR e (a) validar que existe
momento, (b) reescrever título/descrição com o que é visível. Validado
06/07/2026: clip de streamer grande com 27k views na Twitch era o cara parado
no LOBBY do client — teria ido ao ar num pipeline só-views.

## Princípio

**View da Twitch valida INTERESSE, não MOMENTO.** Em streamer grande qualquer
espirro clipa; ordenar por views seleciona o streamer, não o conteúdo. O gate
visual é obrigatório e roda ANTES da aprovação humana (humano só aprova, não
caça lixo).

## Fluxo (por leva de clips renderizados)

1. Listar a fila de clips renderizados aguardando revisão (id, streamer,
   título original da Twitch, duração, caminho do render).
2. Extrair **3 frames do RENDER final** (15%, 50%, 85% da duração) por clip —
   `ffmpeg -ss <t> -frames:v 1 -vf scale=360:-2`. Render final, não o source:
   é o que o espectador vai ver (crop/layout inclusos no julgamento).
3. O agente ASSISTE os frames + título original + streamer e decide:
   - **NEGAR** (com motivo gravado, prefixo "curadoria:"): lobby/menu/champ
     select/tela de carregamento; nada acontece; conversa sem ação visível;
     react de conteúdo alheio; defeito de render (crop torto, webcam duplicada,
     legenda sobre a ação).
   - **APROVAR COPY**: reescrever título + descrição no banco/fila.
4. Reportar ao dono: negados (com motivo) e títulos novos. Dono só aprova.

## Regras de título (evidência: título-lixo = ~4x menos views, n=72, jun/2026)

- Descreve o que REALMENTE aparece. Citação de fala visível/queimada no clip é
  o melhor hook que existe.
- 30-80 caracteres, gancho nos primeiros ~40 (feed trunca), máx 1 emoji.
- Nome próprio do jogo INTACTO (champion/spell/item/criatura na língua do
  jogo — comunidade não usa tradução).
- Palavras não-anunciáveis derrubam alcance: nada de morte/matar/sangue →
  "caiu", "eliminado", "quase foi".
- Canal EN → título e descrição em inglês; canal PT → português.
- Descrição: 1 linha do momento + crédito com link da Twitch do streamer +
  hashtags do nicho.

## Cuidados

- Se houver EXPERIMENTO de título rodando no canal (A/B), NÃO sobrescrever
  clips que pertencem a um braço do teste — contamina a medição. Revisar só o
  que está fora do experimento.
- 3 frames podem perder o payoff: na dúvida sobre NEGAR, extrair 6 frames
  antes de decidir. Negar injustamente custa mais que 3 frames extras.
- Sem transcrição de áudio, clip de FALA é julgado só pelo visual — em nicho
  talking-heavy, adicionar transcrição local (Whisper) antes de confiar no
  gate.
- Piso de views ajuda a cortar cauda, mas NUNCA substitui o gate visual (ver
  Princípio).

## Relacionado

- CLAUDE.md raiz → "Curadoria: view ≠ momento" e "O que MOVE views".
- Futuro: `skills/curadoria-cortes-youtube.md` (seleção de momento em VOD
  longo — transcrição + ranking de trechos; ainda não escrito).
