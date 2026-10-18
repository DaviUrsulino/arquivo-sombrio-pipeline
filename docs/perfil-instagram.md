# Revisão do perfil @robo.estagiario (skill all-profile, escopo: auditoria)

Capturado em 2026-10-18, no navegador do Davi, **logado como dono** (não é a visão de um visitante).
Nada foi alterado na conta.

## Estado atual (antes)

| Campo | Valor observado | Estado |
|---|---|---|
| Usuário | `robo.estagiario` | ok |
| Nome de exibição | não aparece na tela de edição da web | **desconhecido** (fica na Central de Contas) |
| Bio | vazia (`0 / 150`) | **vazio** |
| Link (site) | vazio. A web diz: "somente é possível editar os links no celular" | **vazio, passo só no app** |
| Rótulo "Perfil gerado por IA" | ligado | mantido |
| Foto | robô laranja em pixel art com notebook | boa, manter |
| Destaques (Highlights) | nenhum (só o botão "Novo") | vazio |
| Posts fixados | nenhum visto | vazio |
| Números | 27 posts, 9 seguidores, 2 seguindo | só informativo |
| Grade de posts | estilo único (pixel art, biblioteca), capas legíveis | forte |

## Nota editorial (pesos da skill, avaliação local, não é ranking da plataforma)

| Dimensão | Peso | Nota 0 a 4 | Pontos |
|---|---|---|---|
| Associação (quem é, sobre o quê) | 25 | 1 | 6,25 |
| Público | 15 | 1 | 3,75 |
| Prova | 20 | 1 | 5,00 |
| Consistência | 10 | 3 | 7,50 |
| Encaixe nos campos | 10 | 0 | 0,00 |
| Visual | 10 | 3 | 7,50 |
| Próximo passo | 10 | 0 | 0,00 |
| **Total** | 100 | | **30 / 100** |

A grade e a foto carregam a identidade. O que falta é texto: bio, link e um próximo passo claro.

## Achados

1. **Bio vazia.** Quem chega por um Reels não vê o que o perfil é nem o que fazer a seguir.
2. **Sem link.** O CTA dos posts é "comenta LINK" (depende do bot). Quem não comenta não tem caminho.
3. **Sem destaques.** São a vitrine de confiança: nenhum.
4. **Sem post fixado.** Os 3 melhores posts poderiam explicar o perfil.
5. **Seguidores baixos (9)**: não usar número como prova na bio. Prova possível e verdadeira: cada post cita o
   repositório, a licença e o link (isso o pipeline faz de fato).

## Propostas de bio (rascunho, não aprovadas, nenhuma aplicada)

O rótulo "Perfil gerado por IA" aparece acima da bio, então a bio não precisa repeti-lo.
Contagem feita com `count_text.py` da skill (pontos de código Unicode / unidades UTF-16): o editor real pode contar diferente.

**A** (106 / 109), recomendada, foco em autoridade e kit:
```
🤖 Garimpo repositórios de IA no GitHub
🛠 Claude Code, agentes e prompts
👇 Kit grátis: CLAUDE.md + comandos
```

**B** (118 / 120), foco na promessa de entrega:
```
🤖 Uma ferramenta de IA por dia, com fonte e link
Comenta LINK no post e eu mando no direct
👇 Kit grátis p/ Claude Code
```

**C** (90 / 92), mais curta:
```
Robô que garimpa ferramentas de IA pra quem programa 🤖
Comenta LINK nos posts
👇 Kit grátis
```

Cuidado com a promessa: "uma ferramenta por dia" só vale enquanto o cron rodar 3 posts/dia sem falhar.
"Kit grátis" só vale enquanto o link do zip funcionar (hoje `https://tinyurl.com/2bgkh263`).

## Link (passo só no celular)

Sugestão: o zip do kit. Ressalva: link que baixa arquivo direto passa menos confiança do que uma página.
Melhor depois: uma página simples (kit + últimos repositórios). Passo manual no app: Editar perfil, Links, Adicionar link.

## Próximas ações (ordem sugerida)

1. Escolher a bio (A, B ou C). **Aplicar só com aprovação do Davi.**
2. Criar 3 destaques: "Kit grátis", "Ferramentas", "Como funciona".
3. Fixar 3 posts: o melhor Reels, o do kit (`CLAUDE.md`) e um carrossel.
4. Definir o nome de exibição na Central de Contas (sugestão: `Robô Estagiário | IA pra devs`), respeitando o limite de trocas.
5. Depois de aplicar, conferir pela visão de um visitante (conta deslogada ou outra conta).
