# Skill: música de fundo com DUCKING (abaixa quando a pessoa fala)

ESCOPO: qualquer corte com trilha de fundo — Shorts e vídeo LONGO (compilação).
Validado em produção 06-07/2026; feedback do dono no primeiro longform: "gostei
que vc baixava o som da musica quando o pessoal falava, nota 10".

## O que faz

Mixa uma faixa de música SOB o áudio original do clip. Quando há voz/SFX no
clip, a música abaixa sozinha (sidechain compression); no silêncio, ela volta.
Clip MUDO na origem (Twitch muta por copyright) é SALVO usando a música em
volume cheio como trilha única — vira aproveitável em vez de descartado.

## Receita ffmpeg (filter_complex, testada)

Entradas: `[0]` = clip, `[1]` = música (loop até a duração do clip:
`-stream_loop -1 -t {dur} -i musica.ogg`).

```
[1:a]volume=0.32,aresample=48000,aformat=channel_layouts=stereo[mus];
[0:a]aresample=48000,aformat=channel_layouts=stereo[clipa];
[mus][clipa]sidechaincompress=threshold=0.015:ratio=8:attack=5:release=300[musd];
[clipa][musd]amix=inputs=2:duration=first:dropout_transition=0,
alimiter=limit=0.95,loudnorm=I=-14:TP=-1:LRA=11[aout]
```

- `volume=0.32` — piso da música (sob a voz). Sobe/desce a gosto do nicho.
- `sidechaincompress` — a VOZ do clip comprime a MÚSICA:
  `threshold=0.015` (sensibilidade: menor = qualquer fala já abaixa),
  `ratio=8` (quão fundo abaixa), `attack=5` ms (abaixa rápido ao falar),
  `release=300` ms (volta suave no silêncio — release curto demais "bombeia").
- `amix duration=first` — resultado dura o clip, não o loop da música.
- `alimiter + loudnorm I=-14` — teto anti-clip + volume uniforme entre clips
  de streamers diferentes (essencial em compilação: cada live tem ganho
  próprio; sem loudnorm POR SEGMENTO o vídeo longo fica aos berros/sussurros).

Clip mudo (trilha única, sem sidechain):

```
[1:a]volume=1.0,aresample=48000,aformat=channel_layouts=stereo,
loudnorm=I=-14:TP=-1:LRA=11[aout]
```

Detecção de mudo antes de escolher o ramo: `mean_volume` do trecho usado
< -50dB (medir só o TRECHO — o mute da Twitch pode ser parcial). Evidência dos
thresholds: mudos medem -91/-80/-52 dB; com som -26/-28 dB.

## Regras de música (Content ID)

- **NUNCA OST real de jogo/artista** — "música de jogo antigo" É copyright e
  gera claim. Usar chiptune/lo-fi **CC0 de verdade** (ex: OpenGameArt) e
  guardar a licença junto das faixas.
- Rotacionar faixa por clip (hash do clip_id → faixa) — variedade sem estado.
- Pasta de música vazia = pipeline segue SEM trilha (no-op gracioso, clips
  mudos voltam a ser descartados).

## Onde aplica / não aplica

- Compilação longform: ducking POR SEGMENTO (cada clip mixa sua faixa, depois
  concat) — não uma trilha única por cima do vídeo inteiro.
- Short falado / react: mesma receita.
- NÃO usar em conteúdo onde a música original do clip é o momento (show,
  música ao vivo) — o sidechain briga com o conteúdo.
