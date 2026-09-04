# Referências da API do Fusion 360

Consulte sob demanda. Não carregue tudo — abra só o que a tarefa pede.

**Antes de vir aqui:** para saber o que um objeto oferece, use `api(obj)` no
`fusion_eval`; para saber se uma classe existe, faça grep nos stubs locais
(`API/Python/defs/adsk/*.py`). Os dois leem a API **como instalada**, enquanto
os arquivos abaixo descrevem a versão mais nova publicada pela Autodesk. Essa
divergência é real: `TimelineObject.deleteObject` está na docs e não existe
antes da ~2705.

| Arquivo | O que tem | Quando abrir |
|---|---|---|
| `guides.md` | 9 guias conceituais completos do User's Manual | Quando precisa do **como fazer** de um assunto |
| `api-index.md` | 1106 classes com a URL da página oficial de cada uma | Quando quer a **documentação em prosa** e os exemplos de uma classe |

## api-index.md — a prosa oficial de uma classe

Substituído por `api()` e pelos stubs no uso diário. Vale quando o que falta
é a explicação e o exemplo, não a assinatura.

Não leia o arquivo inteiro (212 KB). Faça grep:

```bash
grep -i "extrudefeature" api-index.md
grep -i "revolve" api-index.md
grep -i "enum" api-index.md | grep -i "operation"
```

Cada linha traz a URL da página oficial. Abra com WebFetch para ver assinatura,
argumentos, valor de retorno e exemplo em Python.

Seções: Design (core & fusion) — a maior, Drawing, Electronics, Manufacturing
(cam), Volumetric.

Prefixos das URLs indicam o módulo: `core_X.htm` → `adsk.core.X`,
`fusion_X.htm` → `adsk.fusion.X`, `cam_X.htm` → `adsk.cam.X`.

## guides.md — entender o mecanismo

Seções disponíveis:

- **Fusion Solids and Surfaces (BRep)** — bodies, faces, edges, vertices; como
  percorrer a topologia e extrair geometria
- **Programming for Design Intent** — construir modelos que sobrevivem a
  mudanças de parâmetro; por que referências frágeis quebram
- **Events** — o mecanismo de handler/notify, EventArgs, add/remove
- **Attributes** — anexar dados próprios a entidades, sobrevive ao save
- **Selection Filters** — restringir o que o usuário pode selecionar
- **Custom Graphics** — desenhar na viewport sem criar geometria real
- **Commands** / **Command Inputs** — criar comandos com diálogo próprio
- **Working in a Separate Thread** — a regra que sustenta o bridge MCP:
  nenhuma chamada de API fora da main thread, comunicação por custom event

```bash
grep -n "^## " guides.md          # listar seções
sed -n '/^## Attributes/,/^---/p' guides.md
```

## Regenerar

Ambos vêm de `help.autodesk.com`. Se o Fusion atualizar e algo parecer
defasado, peça ao Claude para regerar — o `api-index.md` sai do
`toctree.json` oficial (`/view/fusion360/ENU/data/toctree.json`) e o
`guides.md` das páginas `/cloudhelp/ENU/Fusion-360-API/files/*_UM.htm`.

## O que NÃO está aqui

O texto detalhado de cada uma das 1106 classes — são páginas demais para
espelhar. O índice dá o nome e a URL; o detalhe vem por WebFetch na hora.

Assinaturas exatas não estão aqui de propósito: elas vêm de `api(obj)` e dos
stubs locais, que refletem a versão instalada.
