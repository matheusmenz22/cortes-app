# Agente de cortes — LEAGUE OF LEGENDS

STATUS: rascunho — hipóteses a validar com dado do canal (dono: Matheus).
Regra da casa: hipótese vira regra quando tiver evidência (data + n).

## Hipóteses iniciais (do README + transferidas de Tibia)

- Hook nos 2-3s: começar no clímax (pentakill, 1v5, roubo de Baron), não na
  construção da jogada. [a validar]
- Momento detectável por: killfeed/multikill, voz do narrador/streamer
  gritando, pico de chat, pico de volume. [a validar]
- Priorizar teamfight; nunca lane/farm parado. [a validar]
- Legenda queimada AJUDA em LoL (streamer narra a jogada) — diferente de
  Tibia, onde combate é mudo. [a validar]

## Transferível de Tibia (evidência lá, validar aqui)

- Título descreve o que ACONTECE (sinal pro algoritmo; lixo = -4x mediana).
- Nome próprio do jogo em inglês quando a comunidade usa assim (Baron, ult,
  flash — não traduzir termo consagrado).
- Cadência > perfeccionismo: mais posts/dia com gate humano.
- Teto de duração: em Tibia ≤14s ganhou; LoL teamfight pode pedir mais —
  MEDIR antes de copiar.

## Discovery "melhores das 24h" — técnica VALIDADA (06/07/2026)

Categoria GIGANTE global: sem filtro de idioma o top-100 vem coreano/gringo.
O GQL público da Twitch (Client-Id do site, sem credencial) aceita filtro de
idioma no criteria. Query que funciona:

```graphql
query($game: String!, $first: Int!) {
  game(name: $game) {          # "League of Legends"
    clips(criteria: {period: LAST_DAY, sort: VIEWS_DESC, languages: [PT]},
          first: $first) {     # cap 100 por query (200 retorna vazio)
      edges { node {
        slug title viewCount durationSeconds createdAt
        broadcaster { displayName }
        video { id lengthSeconds }   # + videoOffsetSeconds = pad de VOD
        videoOffsetSeconds
      } }
    }
  }
}
```

- Endpoint: `POST https://gql.twitch.tv/gql`, header
  `Client-Id: kimne78kx3ncx6brgo4mv6wki5h1ko` (o do web client, público).
- `languages` é ENUM (PT sem aspas). Helix (API oficial) NÃO tem esse filtro
  de idioma em clips — só o GQL.
- Evidência 06/07: 97 clips PT/24h, 66 streamers, CBLOL oficial no meio
  (FURIA vs T1). Sem o filtro: top-100 sem nenhum clip PT.

## Outras peculiaridades

- Concorrência de canais de corte de LoL BR é alta — diferencial precisa ser
  velocidade (clip do dia no dia) + seleção de streamer.
- Canal oficial CBLOL clipa jogo competitivo — clips de esports têm regra de
  uso própria da Riot (checar antes de repostar jogo oficial; live de
  streamer é outro caso).
