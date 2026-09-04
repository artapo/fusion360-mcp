# fusion360-mcp

Deixa o Claude Code controlar o Fusion 360: executa Python dentro da sessão
aberta, com a API completa disponível — criar geometria, ler dimensões,
percorrer o timeline.

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
"Claude MCP" e clique **Run**. Marque *Run on Startup* para não repetir.
O add-in precisa estar rodando para o bridge responder.

```bash
uvx fusion360-mcp status      # o que está instalado onde
uvx fusion360-mcp uninstall   # remove tudo
```

Feche o Fusion antes de instalar: ele mantém os arquivos do add-in abertos.
O instalador detecta e avisa.

## Requisitos

- Fusion 360 (Windows ou macOS)
- Claude Code
- Python 3.9+

Sem dependências de runtime — o servidor MCP fala JSON-RPC só com a stdlib.

## Como funciona

O Fusion só aceita chamadas de API na thread principal. O add-in sobe um
servidor HTTP numa thread de fundo e despacha cada requisição por
`CustomEvent`; a thread HTTP bloqueia até a principal devolver o resultado.

```
Claude Code  --stdio-->  server.py  --HTTP:8766-->  add-in  -->  Fusion
```

Autenticação por token em `~/.claude-fusion-secret`, criado no primeiro
uso. Sem ele qualquer processo local executaria Python na sua sessão.

## A ferramenta

`fusion_eval` recebe código Python e devolve o que estiver em `result`.
Já vêm ligados `adsk`, `app`, `ui`, `design`, `root` e mais três ajudas:

| | |
|---|---|
| `snapshot()` | Estado do modelo em texto compacto. Corpos idênticos colapsam numa linha — um padrão de 50 furos custa o mesmo que um. |
| `screenshot(w, h, view)` | Renderiza o viewport e devolve a imagem. Caro (~10k tokens); prefira `snapshot()` quando o que importa são números. |
| `undo()` | Desfaz a última chamada que mexeu no modelo. Um nível. Chamada que falha é revertida sozinha. |

## A skill

O pacote instala junto a skill `fusion360-api`, que documenta as armadilhas
da API — unidades internas em cm e radianos, assinaturas que variam por
feature, nomes de material que seguem o idioma da UI. Cada seção nasceu de
um erro real.

Ela pede contribuição: se você bater numa armadilha que não está lá,
documente. O arquivo é `src/fusion360_mcp/skill/SKILL.md` e as regras estão
no topo dele.

## Contribuindo

Pull requests são bem-vindos. Abra um PR por achado, com a saída do
`fusion_eval` que comprova o comportamento — a chamada que falhou e a que
funcionou.

```bash
git clone https://github.com/artapo/fusion360-mcp
cd fusion360-mcp
python test_mcp_server.py    # passa com o Fusion aberto ou fechado
```

## Licença

[Apache 2.0](LICENSE) — permissiva como a MIT, e com concessão explícita de
patentes, que protege quem usa e quem contribui.

Fusion 360 é marca da Autodesk, Inc. Este projeto não é afiliado à Autodesk
nem endossado por ela.
