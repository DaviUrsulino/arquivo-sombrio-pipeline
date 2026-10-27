# Guia de comandos (conferido na documentação oficial, out/2026)

Só entra aqui o que está na documentação oficial: <https://code.claude.com/docs/en/commands>.
Digite `/` dentro do Claude Code para ver o que existe na **sua** versão.

## Dentro da sessão (comandos `/`)

| Comando | Para quê |
|---|---|
| `/init` | Gera um `CLAUDE.md` inicial analisando o projeto |
| `/memory` | Abre e edita os arquivos `CLAUDE.md`; mostra a memória automática |
| `/plan [descrição]` | Entra no plan mode. Com texto, já começa a planejar aquela tarefa |
| `/compact [instruções]` | Resume a conversa para liberar contexto, **continuando na mesma conversa** |
| `/clear` | Começa uma conversa nova, com contexto vazio |
| `/context` | Mostra quanto do contexto está usado e sugestões de economia |
| `/rewind` | Volta a conversa e/ou o código a um ponto anterior (aliases: `/checkpoint`, `/undo`) |
| `/resume` | Retoma uma conversa anterior pelo nome ou escolhendo numa lista |
| `/model` | Troca o modelo e salva como padrão |
| `/permissions` | Vê e edita as regras de permissão (permitir, perguntar, negar) |
| `/usage` | Mostra custo da sessão e limites do plano (`/cost` é um alias) |
| `/doctor` | Diagnóstico da instalação e do `CLAUDE.md`; `/doctor prompt-audit` procura regras velhas ou contraditórias |
| `/review` | Revisa o diff atual (alias de `/code-review`) |
| `/status` | Versão, modelo, conta e conexão |
| `/help` | Ajuda e lista de comandos |

## Quando usar `/compact` e quando usar `/clear`

- **`/compact`**: a tarefa continua, mas a conversa ficou longa. O Claude resume e segue.
- **`/clear`**: você vai começar outra tarefa. Tire o que não importa do caminho.
- Regra prática: terminou a tarefa e vai para outra, `/clear`. No meio da tarefa com a conversa
  pesada, `/compact`.

## Modos de permissão (`Shift+Tab`)

Aperte `Shift+Tab` para alternar o modo. O ciclo passa por: manual (`default`), aceitar edições
(`acceptEdits`) e plan mode (`plan`). A barra de status mostra o modo ativo.

- **Plan mode:** o Claude lê o projeto e escreve um plano, **sem editar seus arquivos**.
- **Aceitar edições:** edita arquivos sem perguntar cada vez. Use quando você já revisa o resultado
  depois.
- Para sair do plan mode sem aprovar o plano, aperte `Shift+Tab` de novo.

## Arquivos de instrução

| O quê | Onde | Observação |
|---|---|---|
| Regras do projeto | `CLAUDE.md` na raiz | Carregado em toda sessão. Alvo: menos de 200 linhas |
| Regras só suas, não versionadas | `CLAUDE.local.md` | Coloque no `.gitignore` |
| Regras por pasta ou tipo de arquivo | `.claude/rules/*.md` com `paths:` | Só carregam quando o Claude mexe nesses arquivos |
| Importar outro arquivo | `@caminho/do/arquivo` dentro do `CLAUDE.md` | Até 4 níveis de importação |

Exemplo de regra com escopo de caminho (`.claude/rules/api.md`):

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# Regras da API

- Todo endpoint valida a entrada.
- Erros seguem o formato padrão do projeto.
```

Importante: o Claude trata o `CLAUDE.md` como **contexto**, não como configuração obrigatória. Para
**bloquear** uma ação de verdade, a documentação recomenda um hook `PreToolUse`, não uma frase no
`CLAUDE.md`.

## O que mudou ou pode mudar

O Claude Code evolui rápido. Se um comando daqui não existir na sua versão, rode `claude --version`,
atualize, e confira a documentação oficial.
