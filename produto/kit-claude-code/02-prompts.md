# 20 prompts prontos

Troque o que está entre `[colchetes]`. Cada prompt tem **para que serve** e **o que esperar**. Os
prompts funcionam melhor com um `CLAUDE.md` bom (veja `01-modelos-claude-md/`).

Regra geral: peça **a prova** (comando rodado e resultado), não só "pronto".

---

## A. Planejar

### 1. Plano antes de editar
Para: tarefa que mexe em mais de um arquivo.
```
/plan
Objetivo: [o que quero ter no final, em uma frase]
Leia os arquivos relevantes e liste os que você vai tocar.
Se algo estiver ambíguo, faça no máximo 3 perguntas e espere.
O plano deve ter passos pequenos e numerados; para cada um: arquivo, o que muda e como eu confirmo
que funcionou. Liste riscos e o que fica FORA do escopo. Não edite nada.
```

### 2. Três caminhos antes de decidir
Para: decisão de arquitetura ou de ferramenta.
```
Preciso [resolver X]. Proponha 3 abordagens diferentes. Para cada uma: como funciona em 3 linhas,
o que ela facilita, o que ela complica, e quando eu me arrependeria de tê-la escolhido.
Termine com a sua recomendação e o motivo. Não escreva código ainda.
```

### 3. Quebrar tarefa grande
Para: tarefa que parece enorme.
```
Quebre "[tarefa grande]" em etapas que cabem em um commit cada. Ordene de modo que o projeto
continue funcionando depois de cada etapa. Para cada etapa, diga o teste que prova que ela terminou.
```

### 4. Entender projeto novo
Para: primeira vez num código que não é seu.
```
Explique este projeto para quem acabou de chegar: o que ele faz, como está organizado, por onde um
pedido entra e sai, e quais são os 5 arquivos mais importantes. Cite os caminhos reais. Se não tiver
certeza de algo, diga que não tem.
```

## B. Implementar

### 5. Funcionalidade com teste primeiro
```
Implemente: [funcionalidade]. Primeiro escreva o teste que falha e mostre que ele falha. Depois o
código mínimo para passar. Depois rode todos os testes e mostre o resultado.
```

### 6. Mudança pequena e segura
```
Faça só isto: [mudança]. Não mexa em mais nada, não renomeie, não "melhore" o que está ao lado. Se
achar algo que deveria ser mudado, liste no final sem mudar.
```

### 7. Seguir o padrão que já existe
```
Antes de escrever, ache 2 exemplos parecidos com [o que vou criar] neste projeto e mostre quais são.
Depois crie o novo seguindo exatamente o mesmo padrão (nomes, estrutura, tratamento de erro).
```

### 8. Tratar os casos de borda
```
Para a função [nome], liste os casos de borda (vazio, nulo, muito grande, caractere estranho,
concorrência, falha de rede). Para cada um, diga o comportamento atual e escreva um teste.
Corrija só os que quebram.
```

## C. Revisar

### 9. Revisão cética do diff
```
Revise este diff como um engenheiro sênior cético. Liste só: bugs reais, riscos de segurança e código
confuso. Ignore estilo. Para cada item: arquivo, linha, por que é um problema e a correção sugerida.
Se não achar nada importante, diga isso em vez de inventar.
```

### 10. O que pode quebrar em produção
```
Olhe as mudanças desta branch e responda: o que pode quebrar em produção? Pense em dados existentes,
migração, configuração, quem consome isto e o que acontece se der erro no meio.
```

### 11. Segurança em uma entrada de dados
```
Audite [função/endpoint] como se o usuário fosse mal-intencionado. Verifique: validação de entrada,
injeção (SQL, comando, HTML), autorização (quem pode chamar), vazamento de dado em erro e em log.
Mostre uma entrada de exemplo que tentaria abusar, e a correção.
```

### 12. Explicar para eu aprender
```
Explique o que este código faz linha a linha, em linguagem simples, e aponte o que eu precisaria
saber para mantê-lo sozinho. Termine com 3 perguntas que eu deveria saber responder.
```

## D. Depurar

### 13. Achar a causa antes de mexer
```
Erro: [cole a mensagem completa]. Quando acontece: [passos]. NÃO corrija ainda. Liste 3 hipóteses
em ordem de probabilidade, e para cada uma o comando ou log que a confirma ou descarta. Rode as
verificações e diga qual hipótese venceu.
```

### 14. Reproduzir com teste
```
Escreva um teste que reproduz este bug: [descrição]. Confirme que ele falha pelo motivo certo. Só
depois corrija, e mostre o teste passando junto com os demais.
```

### 15. Voltar ao último estado que funcionava
```
Isto funcionava na versão [commit/data] e agora não. Compare e liste as mudanças que podem ter
causado. Proponha como achar o commit exato (git bisect ou equivalente) antes de eu aplicar qualquer
correção.
```

## E. Testar e refatorar

### 16. Testes de código existente
```
Escreva testes para [módulo]. Cubra o comportamento atual, inclusive os bugs conhecidos (marque-os
como "comportamento atual, a corrigir"). Não altere o código de produção.
```

### 17. Refatorar sem mudar comportamento
```
Refatore [trecho] para ficar mais simples: [objetivo, ex. quebrar função grande]. Regra: nenhum
comportamento muda. Rode os testes antes e depois e mostre que o resultado é o mesmo. Se não houver
testes, escreva-os primeiro.
```

### 18. Achar o que sobrou
```
Procure neste projeto código morto: funções nunca chamadas, arquivos sem referência, dependências
não usadas, configuração sem efeito. Liste com evidência (onde você procurou). Não apague nada sem
eu confirmar.
```

## F. Documentar e entregar

### 19. README que funciona
```
Escreva o README deste projeto. Teste cada comando de instalação e de execução que você colocar e
diga se funcionou. Inclua: o que faz, como instalar, como rodar, como testar, estrutura de pastas.
Sem exagero e sem recurso que não existe.
```

### 20. Mensagem de commit e resumo do que mudou
```
Veja as mudanças em andamento e escreva: (1) uma mensagem de commit curta no formato do projeto,
(2) um resumo de até 5 linhas do que mudou e por quê, (3) o que ficou sem testar.
```

---

## Como adaptar qualquer prompt

Um bom pedido tem 4 partes: **objetivo** (o que), **contexto** (onde e o que já existe), **limite**
(o que não mexer) e **prova** (como saber que está certo). Se o resultado veio ruim, quase sempre
faltou uma dessas quatro.
