# Skill: legenda PT queimada (transcreve + traduz + burn no render)

ESCOPO: corte com FALA — narração, react, caster, streamer gringo. Opt-in POR
CLIP (toggle no editor da esteira). Validado em produção jul/2026 (Tibia);
hipótese central pro nicho falado (LoL).

## Quando ajuda / quando é inútil

- AJUDA em clip falado: muita gente assiste Short no mudo → legenda segura a
  retenção; streamer gringo → a tradução vira o próprio valor do corte.
- INÚTIL em combate mudo (medido em Tibia): sem narração não há o que
  legendar — gasta 1 call de LLM e não muda nada. Por isso é opt-in por clip,
  não default do pipeline.

## Pipeline (1 call de LLM multimodal por clip)

1. Extrair SÓ o áudio do TRECHO que vai ao ar:
   `ffmpeg -ss START -t DUR -i clip -vn -ac 1 -ar 16000 -b:a 48k a.mp3`.
   Mono 16 kHz 48k: fala não precisa de mais e o payload fica pequeno.
2. Mandar o áudio pro LLM multimodal com saída JSON forçada (schema
   `[{start,end,text}]`) e temperatura baixa (~0.2 — transcrição não é tarefa
   criativa). O prompt exige:
   - `text` SEMPRE em pt-BR: TRADUZIR, nunca copiar o idioma original (sem
     essa regra explícita o modelo devolve o inglês/polonês como veio);
   - segmentos curtos (1 frase/cláusula — cabe em 1-2 linhas na vertical);
   - timestamps em segundos RELATIVOS ao início do áudio enviado (0-based);
   - nomes próprios e termos do jogo mantidos no original;
   - palavrão suavizado ("que merda" → "que saco"): legenda QUEIMADA corta
     alcance no YouTube e não dá pra editar depois;
   - sem fala clara (só ruído/música) → retornar `[]`.
3. Gerar o .srt a partir dos segmentos e queimar no render.

## O pulo do gato: SRT 0-based RELATIVO ao trecho trimado

O trim do render usa `-ss`/`-t` como opções de INPUT (antes do `-i`) → a
timeline do output RESETA pra 0. Timestamp absoluto do clip original quebra o
sync (legenda adiantada exatamente START segundos). Solução: transcrever só o
trecho que vai ao ar E pedir timestamps relativos ao início dele — os dois
zeros coincidem e o .srt casa com o vídeo final sem conversão nenhuma.

No .srt: quebrar cada segmento em no máx 2 linhas de ~28 chars (9:16 é
estreito) e forçar duração mínima ~1.2s quando `end <= start` — legenda de 0s
não dá tempo de ler.

## "Sem fala" ≠ "sem cota" (não gravar veredito errado)

Dois caminhos que dão o mesmo `[]` se não forem separados:

- LLM respondeu `[]` → clip SEM FALA. Ok: segue SEM legenda, veredito vale.
- LLM FALHOU (429 de cota / erro) → problema de infra, não de conteúdo.
  Lançar erro tipado (ex.: `TranscribeError("quota")`) e registrar status
  próprio (`sem_cota`/`erro`). NUNCA gravar como "sem fala": senão o operador
  não descobre que a cota estourou e o clip fica sem legenda pra sempre.

## Burn no ffmpeg (libass + force_style)

```
[v]subtitles='legenda.srt':force_style='FontName=Arial,Fontsize=12,Bold=1,
PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,
Shadow=0,Alignment={align},MarginV={mv}'[outv]
```

- Branco bold + contorno preto grosso (`Outline=3`): gameplay é fundo caótico
  — sem contorno a legenda some em cena clara.
- `Alignment` (padrão ASS): 8 = topo, 5 = meio, 2 = base.
- `MarginV`: ~110 na base (a UI do player de Short cobre a faixa inferior),
  ~80 no topo (sai de baixo da webcam/atribuição), 0 no meio.

## Regra de posição: legenda NUNCA sobre a ação

Posição (top/middle/bottom) é escolhida POR CLIP no editor da esteira, junto
do toggle de legendar — quem aprova vê ONDE a ação acontece e põe a legenda
no terço vazio. Default: bottom. Posição fixa global sempre atropela algum
clip (a ação muda de lugar a cada jogo/layout).
