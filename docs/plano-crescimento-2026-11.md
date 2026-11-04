# Plano de crescimento do @ursulino.ia (2026-11-03)

Base: dados reais de `pautas/desempenho.json` (35 Reels até 02/11), o estudo de 108 Reels de referência
(`referencias/estudos/2026-11-03/RELATORIO.md`) e o método da skill `instagram-growth` (diagnosticar a etapa
travada antes de dar dica genérica). Número de seguidores é vaidade: o que move o perfil é alcance em quem
ainda não segue, tempo assistido e envios por Direct.

## 1. Diagnóstico: onde o crescimento trava

| Etapa | Sinal hoje | Leitura |
|---|---|---|
| **Alcance** (não-seguidores) | mediana de **313 views**; média puxada por 1 hit de 54,7 mil | **Travado.** O algoritmo testa e não empurra. |
| **Retenção** (tempo assistido) | **6,9 s** em média, para vídeos de 20 a 50 s | **Causa principal.** Os primeiros 3 s não seguram, e o meio do vídeo descreve a ferramenta. |
| **Envios** (DM) | **1,18 por 100 alcançados** | No limite do aceitável (meta: passar de 1 a 2%). Sobe junto com conteúdo "mande pra um amigo". |
| **Salvos** | **4,17 por 100** | Bom: o conteúdo é útil. O problema não é valor, é embalagem. |
| **Conversão em seguidor** | não medido aqui (precisa de "visitas ao perfil" e "seguidores" do Insights nativo) | Conferir no app; se views sobem e seguidor não, o problema passa a ser o perfil. |

**Conclusão:** a etapa quebrada é **alcance por retenção**. Valor existe (salvos altos); falta gancho e
história. Por isso o estúdio com direção (ADR 0006) ataca exatamente isso: gancho por acontecimento, 3 ganchos
por pauta, cena nova a cada frase.

## 2. O que fazer (em ordem)

1. **Trocar o motor de conteúdo, não a frequência.** Ligar o estúdio com direção (`ESTUDIO_DIRETOR=1`) no
   vídeo de uma ferramenta depois que o Davi aprovar os vídeos de teste em `videos_teste/`.
2. **Gancho primeiro.** Todo roteiro sai com 3 ganchos (o mesmo vídeo com 3 ganchos fez 32 mil, 122 mil e
   941 mil no @gab.gouvea). Postar o gancho A; se ficar abaixo da mediana em 48 h, repostar com o gancho B
   em outro dia. Se o Instagram liberar **Testes de Reels** (Trial Reels) para a conta, usar lá primeiro: é
   o teste com não-seguidores sem risco para o perfil.
3. **Formatos que mais viajam no nicho** (estudo): experimento de IAs (58 mil), acontecimento com pessoa
   (941 mil), benefício de vida real (46,9 mil), esquete em diálogo (23 a 28 mil), ranking com prova (12 a
   17 mil). Rodízio semanal sugerido: 2 experimentos, 2 acontecimentos, 1 ranking, 1 esquete, 1 lista.
4. **Tema por desejo do público, não por nicho técnico.** O único hit do perfil foi "a IA cria vídeo". Temas
   de segurança/infra fizeram 122 views de mediana. Priorizar: vídeo, dinheiro, tempo, Instagram, celular,
   jogos, "faz sozinho".
5. **Envios.** Fechar com um motivo para mandar a alguém ("manda pro amigo que edita vídeo na mão") em 1 de
   cada 3 vídeos, alternando com o "comenta PALAVRA e me segue". Experimentos e esquetes são os mais
   enviáveis (são histórias).

## 3. Horário

| Faixa | Reels | Mediana de views |
|---|---|---|
| manhã (6–10h) | 4 | 920 |
| meio-dia (10–14h) | 8 | 169 |
| tarde (14–18h) | 5 | 163 |
| noite (18–22h) | 8 | 275 |
| tarde da noite (22–24h) | 8 | 1.176 |

Amostra pequena, então é indício. Teste proposto por 2 semanas, sem mudar o resto: mover o vídeo das 12:00
para **8:00** e manter a lista às 22:30. Comparar a mediana das duas semanas com a das duas anteriores.
(Mudança de grade só com o OK do Davi.)

## 4. Legenda e perfil

- **Legenda:** 1ª linha repete a promessa do gancho (é o que aparece antes do "mais"); 2ª linha diz o que a
  pessoa recebe e a palavra para comentar; 3 a 4 passos curtos para salvar; sem emoji (regra do Davi);
  palavras-chave que alguém buscaria ("editar vídeo com IA", "Claude Code") no texto, para a busca do
  Instagram categorizar o perfil.
- **Perfil:** bio com 1 promessa clara (o que a pessoa ganha seguindo) + prova + chamada; destaque fixado
  com o melhor experimento e o Reel de 54,7 mil. Revisar com a skill `all-profile` quando o Davi quiser.
- **Stories** continuam manuais e do Davi (regra dele); servem para retenção dos que já seguem.

## 5. Como medir (sem inventar número)

Toda semana, no Insights nativo: views de não-seguidores, tempo médio assistido, envios por alcance,
visitas ao perfil e seguidores ganhos por Reel. O `analista.py` já registra views, salvos, envios e tempo;
falta registrar **qual gancho** (A, B ou C) e **qual formato** foi usado, para o roteirista aprender com o
próprio perfil.
