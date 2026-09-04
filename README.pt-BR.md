# fusion360-mcp

Deixa o Claude Code controlar o Fusion 360: executa Python dentro da sessão
em andamento, com a API completa disponível para criar geometria, ler
dimensões e percorrer a timeline.

*[Read in English](README.md)*
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-FFDD00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/artapo)

```python
result = snapshot()
# doc: rolamento.f3d  [mm]  sketches:7  timeline:16
# bodies: 11
#   anel_externo_flangeado   173.978 mm3  17x17x4.6  faces:10
#   esfera x7                  2.572 mm3  1.7x1.7x1.7  faces:1
```

## Instalação

```bash
uvx fusion360-mcp install
```

Instala as três partes: o add-in dentro do Fusion, a skill `fusion360-api`
em `~/.claude/skills/` e a entrada MCP no Claude Code.

Depois, no Fusion: **Utilities → ADD-INS → Add-Ins**, selecione
"Claude MCP" e clique **Run**. Marque *Run on Startup* para não ter de
repetir isso na próxima vez. O add-in precisa estar em execução para a ponte
responder.

```bash
uvx fusion360-mcp status      # o que está instalado onde
uvx fusion360-mcp uninstall   # remove tudo
```

Feche o Fusion antes de instalar, porque ele mantém os arquivos do add-in
abertos. O instalador detecta essa situação e avisa você, em vez de corromper
a cópia.

## Requisitos

- Fusion 360 (Windows ou macOS)
- Claude Code
- Python 3.9+

Não há dependências de execução: o servidor MCP fala JSON-RPC usando apenas a
biblioteca padrão.

## Como funciona

O Fusion só aceita chamadas de API na thread principal. O add-in sobe um
servidor HTTP numa thread de fundo e entrega cada requisição à thread
principal por um `CustomEvent`; a thread HTTP fica bloqueada até o resultado
voltar.

```
Claude Code  --stdio-->  server.py  --HTTP:8766-->  add-in  -->  Fusion
```

As requisições levam um token de portador guardado em
`~/.claude-fusion-secret`, criado no primeiro uso. Sem ele, qualquer processo
local poderia executar Python na sua sessão do Fusion.

## A ferramenta

`fusion_eval` recebe código Python e devolve o que estiver em `result`.
`adsk`, `app`, `ui`, `design` e `root` já vêm ligados, além de três
auxiliares:

| | |
|---|---|
| `snapshot()` | Estado do modelo em texto compacto. Corpos idênticos são reduzidos a uma linha só, de modo que um padrão de 50 instâncias custa o mesmo que um corpo. |
| `screenshot(w, h, view)` | Renderiza o viewport e devolve a imagem na própria resposta. Custa caro (~10k tokens); prefira `snapshot()` quando o que importa são os números. |
| `undo()` | Desfaz a última chamada que alterou o modelo. Um nível só. Uma chamada que levanta exceção é revertida automaticamente. |

## A skill

O pacote também instala a skill `fusion360-api`, que documenta as armadilhas
da API: unidades internas em centímetros e radianos, assinaturas que mudam
conforme a feature, nomes de material que seguem o idioma da interface. Cada
seção nasceu de um erro real.

A skill é a parte que se acumula com o tempo. O código se escreve uma vez; as armadilhas
continuam aparecendo, e cada uma que alguém anota é uma hora que ninguém
depois vai perder.

## Achou uma armadilha? Mande de volta

**Se a API surpreendeu você, isso vale um PR.** Um método cujo nome real é
diferente do óbvio, uma assinatura que muda conforme a feature, uma operação
que falha em silêncio, um valor que só funciona numa unidade — é exatamente
o que pertence à skill, e é o tipo de coisa que documentação nenhuma lista,
porque só aparece na prática.

A régua é baixa de propósito. Você não precisa consertar nada nem escrever
bem:

- **Duas chamadas bastam** — a que falhou e a que funcionou. Cole a saída
  real do `fusion_eval`, com a mensagem de erro; é por ela que alguém vai
  procurar ao bater na mesma parede.
- **Diga o que você estava construindo.** O contexto separa a armadilha
  geral do acidente isolado, e costuma ser a diferença entre uma nota que
  ajuda e uma que confunde.
- **Um PR por achado.** Achados sem relação entre si, em branches separadas,
  são revisados mais rápido e não travam um ao outro.
- **Correção vale mais que acréscimo.** Se algo na skill está errado ou
  ficou desatualizado, apontar isso vale mais que uma seção nova: uma skill
  que descreve a ferramenta errado é pior que uma incompleta. Avise no título
  do PR e ele é revisado primeiro.

O arquivo é `src/fusion360_mcp/skill/SKILL.md`; as regras completas estão no
topo dele. **A skill é escrita em inglês**, para que contribuidores de
qualquer lugar consigam mantê-la.

Está em dúvida se vale reportar? Abra o PR assim mesmo. Decidir é trabalho
do mantenedor, e uma armadilha não reportada custa à próxima pessoa a mesma
hora que custou a você.

## Contribuindo com código

```bash
git clone https://github.com/artapo/fusion360-mcp
cd fusion360-mcp
python test_mcp_server.py    # passa com o Fusion aberto ou fechado
```

O teste roda sem o Fusion instalado: aceita tanto a resposta real quanto
"Cannot reach Fusion". O CI o executa em Linux, macOS e Windows.

## Licença

[Apache 2.0](LICENSE) — tão permissiva quanto a MIT, com uma concessão
explícita de patentes que protege tanto quem usa quanto quem contribui.

Fusion 360 é marca da Autodesk, Inc. Este projeto não é afiliado à Autodesk
nem endossado por ela.
