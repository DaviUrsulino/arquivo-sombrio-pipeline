# Prompt de planejamento (plan mode)

Use quando a tarefa mexe em mais de um arquivo, ou quando você não tem certeza do caminho. A ideia:
o Claude lê o projeto e escreve um plano, **sem editar nada**. Você revisa e só depois manda executar.

## Como ativar o plan mode

- Digite `/plan` antes do pedido (vale só para aquele pedido), ou
- Aperte `Shift+Tab` para alternar entre os modos de permissão até aparecer "plan mode" na barra de
  status. Aperte de novo para sair sem aprovar o plano.

No plan mode o Claude lê arquivos, roda comandos para explorar e escreve o plano, mas não edita o seu
código. Quando o plano aparece, você escolhe aprovar, ou pedir ajustes e continuar planejando.

## O prompt

Cole e troque o que está entre `[colchetes]`:

```
/plan

Objetivo: [o que eu quero ter no final, em uma frase]

Contexto:
- [onde isso mora no projeto, se eu souber]
- [o que já existe e não pode quebrar]

Antes de propor o plano:
1. Leia os arquivos relevantes e liste os que você vai tocar.
2. Se algo estiver ambíguo, faça no máximo 3 perguntas e espere eu responder.

O plano deve ter:
- Passos numerados e pequenos, cada um verificável.
- Para cada passo: arquivo, o que muda e como eu confirmo que funcionou (qual teste ou comando).
- Riscos e o que pode quebrar.
- O que fica FORA do escopo, para você não sair mexendo no resto.

Não edite nenhum arquivo agora. Só o plano.
```

## Depois que o plano aparecer

Antes de aprovar, revise com estas 4 perguntas:

1. **Tem passo grande demais?** Peça para quebrar em passos que cabem em um commit.
2. **Cada passo diz como testar?** Se não disser, peça.
3. **Mexe em algo que eu não pedi?** Peça para tirar ou mover para "fora do escopo".
4. **Faltou algum arquivo que você sabe que importa?** Aponte.

Para ajustar sem aprovar, responda no próprio plano, por exemplo: "junte os passos 2 e 3, e acrescente
um teste para o caso de lista vazia".

## Quando NÃO vale a pena

Para corrigir uma linha ou renomear uma variável, o plano só atrasa. Vá direto.
