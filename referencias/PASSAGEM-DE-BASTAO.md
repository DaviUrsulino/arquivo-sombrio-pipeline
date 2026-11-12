# Passagem de bastão — pesquisa de referências do @ursulino.ia

Escrito em 2026-11-11 para outra sessão que vá trabalhar neste repositório. Responde três perguntas: onde estão
os dados, como foram coletados (para repetir), e o que foi descoberto — incluindo o que **não** foi pesquisado.

---

## 1. Onde estão as contas de referência e os Reels

| O quê | Caminho | Conteúdo |
|---|---|---|
| Contas de referência | `referencias/referencias.json` | **45 perfis** e **44 shortcodes** de Reels. Cada perfil tem `motivo` descritivo; **24 deles** trazem views medidas |
| Transcrições de virais | `referencias/transcricoes/<nome>/fala.txt` | **6 Reels** transcritos frase a frase com tempo. Só o texto — o vídeo de terceiro é apagado depois |
| Folhas de quadros | `referencias/transcricoes/<nome>/folha.png` | 15 quadros por vídeo numa imagem, para ver a estrutura de relance |
| Estudos completos | `segredos/estudos/2026-11-10/` | `RESUMO.md` (19 contas medidas, conclusões) e `views.json` (views cruas) |
| Estudo anterior | `segredos/estudos/2026-11-03/` | 108 Reels: folhas, transcrições e RELATORIO.md |
| **Catálogo de formatos** | `segredos/FORMATOS.md` | **Comece por aqui.** Os 7 formatos que funcionam com número, os 2 que já morreram, horários, e o que falta testar |

**Atenção ao número:** são 45 contas, não ~200. O que passa de 200 é o total de *Reels* olhados somando os dois
estudos (108 no de 03/11 + os grids de 19 contas no de 10/11).

Os estudos e o catálogo moram no repositório **privado** `DaviUrsulino/arquivo-sombrio-segredos`, clonado em
`./segredos` (o repositório público não pode conter a fórmula, ver `src/estudio_instagram/segredos.py`).

---

## 2. Como os links do Instagram foram abertos (e como repetir)

**Não foi usado Apify** (sem créditos, HTTP 402) **nem Playwright.** Dois caminhos, ambos de custo zero:

### a) Navegador embutido do Claude Code, sem login

O Instagram mostra as views no grid de `/reels/` mesmo deslogado. Abrir `instagram.com/<perfil>/reels/`, fechar
o modal de cadastro, rolar e extrair do DOM:

```js
[...document.querySelectorAll('a[href*="/reel/"]')].map(a => ({
  h: a.getAttribute('href').split('/')[3],   // shortcode
  v: a.innerText.trim(),                      // views ("558 mil", "1,9 mi")
}))
```

Para um Reels específico, `og:description` traz curtidas, comentários e a legenda inteira sem login:

```js
document.querySelector('meta[property="og:description"]').content
```

Duração e resolução saem de `document.querySelector('video').duration`. Alguns Reels não deixam avançar por
`currentTime` (streaming); nesses, só dá para capturar quadros esperando a reprodução.

### b) Transcrição do que é falado (o mais valioso)

Já virou módulo no repositório:

```bash
python -m src.estudio_instagram.transcrever_referencia https://www.instagram.com/p/XXXX/
```

Faz: `yt-dlp` baixa → `ffmpeg` extrai o áudio → **faster-whisper** local transcreve → salva `fala.txt` e
`folha.png` em `referencias/transcricoes/` e **apaga o vídeo** (é obra de terceiro; fica só o estudo).

Pré-requisitos, uma vez:

```bash
python3 -m venv /tmp/wenv && /tmp/wenv/bin/pip install faster-whisper "av<14"
export WHISPER_PY=/tmp/wenv/bin/python WHISPER_MODELO=small
```

O `av<14` importa: com a versão nova o faster-whisper quebra em
`TypeError: open() got an unexpected keyword argument 'metadata_errors'`.

---

## 3. O que foi descoberto sobre animação que viraliza

### Aviso honesto sobre o escopo

**Tudo que está medido aqui é Instagram Reels.** Não foi feita pesquisa no YouTube Shorts: nenhum vídeo de
Shorts foi aberto, medido ou transcrito. O único dado com origem no YouTube é indireto e chegou por um Reels:

> O @luiz_dunka (10/11) resume o método do **Zack D. Films** — canal de 29 milhões de inscritos, cujo vídeo de
> 30 segundos fez 255 milhões de views — em 4 passos: **uma pergunta absurda; começa direto no problema; a
> câmera entra onde nenhuma câmera entra; o boneco é sempre igual.**

Isso é relato de segunda mão, não medição nossa. Se o próximo chat precisar de dado de Shorts, tem que coletar.

### O que foi medido de verdade (Instagram, 19 contas)

1. **O tema decide, não a produção.** Prova dentro da mesma conta, duas vezes: no @guics.dev (mesmo motor
   Claude + 3D que o nosso, 2.927 seguidores) o truque de vaga remota fez **307 mil** e "transformei o Claude no
   meu estúdio 3D" fez **2.974**. No @eupauloleme, utilidade doméstica fez **4,9 milhões** e dica do nicho dele,
   **538**. Mesma produção, até 1000x de diferença.

2. **Capricho de animação não é o fator.** @aprendisemquere faz 3,5 milhões com 3D nível Roblox; @escolhas.app
   faz 1,2 milhão de mediana com 2D de olho esbugalhado. Ambos mais simples que o que já renderizamos.

3. **Seguidor não é requisito.** @nessemundo_br: **2.181 seguidores**, 1,7 milhão de views.

4. **Duração não é o problema.** Campeões têm 66 s, 107 s, 131 s, 145 s — iguais ou maiores que os nossos.

5. **O nicho dev não tem teto; o formato "ferramenta explicada" é que tem.** @canwebuildthis é dev puro
   ("an animated series about coding with AI") e fez **2,2 milhões**, com série de personagem fixo.

6. **Não existe fórmula de fechamento.** Das 6 transcrições: o de 3 milhões não pede nada; o de 3,5 milhões
   segmenta ("já sabia? comenta GELADO / aprendeu agora? comenta APRENDI SEM QUERER"); o de 1,9 milhão pede no
   meio e no fim.

7. **Diálogo rende mais que narração**, e **fato real no meio da ficção segura vídeo longo** (@gabriel.cta
   explica adenosina no meio de uma aventura de RPG).

8. **Placar fixo no topo** do primeiro ao último quadro (@escolhas.app: "DIAS RESTANTES: 4", "GLOW-UP: 75%").

9. **Deixar o vídeo respirar**: o Reels de 39 mil curtidas do @productivevick passa **70 dos 107 segundos sem
   narração nenhuma** e só então vira a chave com "você assistiu o vídeo inteiro, não é?".

A tabela completa, com os números de cada conta e os formatos ordenados, está em `segredos/FORMATOS.md`.
