---
name: fusion360-api
description: Use when writing code for the Fusion 360 API via the fusion_eval MCP tool - covers units, the object model, components vs occurrences, proxies, sketches, features and the Python-specific traps. Trigger on Fusion 360, fusion_eval, adsk.fusion, adsk.core, sketch/extrude/timeline/parameter work in Fusion.
---

# Fusion 360 API

Escrever código para `fusion_eval`. Tudo aqui foi verificado na documentação
oficial da Autodesk (Fusion API User's Manual), não de memória.

## Ambiente do fusion_eval

Globais já ligados: `adsk`, `app`, `ui`, `design`, `root`.
Atribua a `result` para devolver valor — precisa ser JSON-serializável ou volta
como `repr()`. Roda na main thread do Fusion, API 100% utilizável. Timeout 60s.

```python
result = [b.name for b in root.bRepBodies]
```

`design` já é `adsk.fusion.Design.cast(app.activeProduct)` e `root` já é
`design.rootComponent` — não refaça. Se o usuário estiver no workspace de
Manufacture, `design` vem `None`; cheque antes de mexer em geometria.

## Unidades — a fonte de bug nº 1

A API **sempre** usa unidades internas de banco de dados, independente do que o
usuário configurou na UI:

| Design | CAM |
|---|---|
| Comprimento: **cm** | Comprimento: cm |
| Ângulo: **radianos** | Ângulo: **graus** |
| Massa: kg | Tempo: s, Potência: W |

Design usa radianos, CAM usa graus. Não confunda.

`5` numa chamada de API é **5 cm**, não 5 mm. Para 10 mm escreva `1.0`, ou
melhor, deixe explícito:

```python
mm = 0.1  # fator mm -> cm
dist = adsk.core.ValueInput.createByReal(10 * mm)
```

Quando a entrada vem do usuário como string ("3 in", "1/2", "hole_depth / 2"),
não parseie na mão — use o UnitsManager:

```python
um = design.unitsManager
if um.isValidExpression(txt, um.defaultLengthUnits):
    cm = um.evaluateExpression(txt, um.defaultLengthUnits)
```

Para exibir ao usuário, formate de volta com `um.formatInternalValue(...)`.

`ValueInput.createByString('10 mm')` respeita unidade explícita e aceita
expressões/parâmetros; `createByReal(1.0)` é sempre cm. Prefira `createByString`
quando quiser que o valor vire uma expressão paramétrica no modelo.

## Object model

`Application` → `Documents` / `Document` → `Product` (→ `Design`) →
`rootComponent` → sketches, features, bodies, construction geometry, occurrences.

Para achar algo, pergunte quem é o dono: uma SketchLine pertence a um Sketch,
que pertence a um Component.

Todo objeto tem: `objectType`, `classType()`, `isValid` (checa se ainda existe —
uma referência guardada pode ser invalidada por uma operação posterior).

Objetos transientes usam funções estáticas: `adsk.core.ObjectCollection.create()`,
`adsk.core.Point3D.create(x, y, z)`, `adsk.core.Matrix3D.create()`.

## Components vs Occurrences

- **Component** contém a geometria. Sempre em model space, não reposicionável.
- **Occurrence** é uma instância do component. É o que aparece no browser e na
  tela. Reposicionável e constrangível.
- Só o root component existe sem occurrence.

**Armadilha:** ao criar geometria pela API, o componente ativo da UI é
**ignorado**. A geometria vai no componente de onde você chamou. Editar
`Component1` requer pegar aquele component, não ativá-lo na UI.

Criar componente novo = criar occurrence:

```python
occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
newComp = occ.component
```

Editar um component afeta **todas** as suas occurrences.

## Proxies

Uma face dentro de `Component9` que aparece em duas occurrences é ambígua — o
Fusion não sabe qual instância você quer. O proxy carrega o caminho completo
(`Component9:1/RedFace`).

- `assemblyContext` → occurrence de topo do caminho
- `nativeObject` → a entidade real dentro do component
- `createForAssemblyContext(occ)` → cria o proxy naquele contexto

Se uma chamada falhar reclamando de contexto num assembly, é proxy faltando.
Em designs de um componente só (root), isso não aparece.

## Padrão Input Object

Features complexas seguem sempre: `createInput` → configurar → `add`. O input
object é o equivalente ao diálogo do comando.

```python
sk = root.sketches.add(root.xYConstructionPlane)
sk.sketchCurves.sketchCircles.addByCenterRadius(
    adsk.core.Point3D.create(0, 0, 0), 2.0)   # raio 2 cm

prof = sk.profiles.item(0)
ext = root.features.extrudeFeatures
inp = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1.0))  # 1 cm
result = ext.add(inp).name
```

`FeatureOperations`: `NewBodyFeatureOperation`, `JoinFeatureOperation`,
`CutFeatureOperation`, `IntersectFeatureOperation`, `NewComponentFeatureOperation`.

**A assinatura de `createInput` varia por feature.** Não assuma que é sempre
`(profile, operation)`. `RevolveFeatures` pede o eixo no meio:

```python
inp = rev.createInput(profile, axis, operation)   # 3 args, verificado
```

Se vier `TypeError: createInput() missing 1 required positional argument`,
é isso — confira a assinatura nos stubs locais em `API/Python/defs/adsk/`
antes de tentar variações.

Collections têm `add*` variados — `sketchArcs` tem `addByThreePoints`,
`addByCenterStartSweep`, `addFillet`. Procure o add certo antes de improvisar.

## Python: as pegadinhas

**Out-args viram tupla.** `Point3D.getData(out x, out y, out z)` em Python:

```python
(retVal, x, y, z) = point.getData()
```

**Igualdade:** use `==`, **nunca** `is`. Objetos Fusion são wrappers; `is`
compara o wrapper, não a entidade.

```python
if face1 == face2:  # correto
```

**Tipos:** `type()` só dá o tipo exato. Para hierarquia use `isinstance`:

```python
isinstance(sel, adsk.fusion.SketchEntity)  # pega SketchLine, SketchArc, etc.
```

`cast()` retorna `None` quando o tipo não bate — é a forma idiomática de
validar seleção:

```python
edge = adsk.fusion.BRepEdge.cast(sels[0].entity)
if not edge:
    result = 'não é uma aresta'
```

**Collections** iteram como container Python: `for x in col`, `len(col)`,
`col[0]`, `col[-1]`, `col[1:4]`. Não precisa de `range(col.count)`.

**Arrays retornados são "vector", não list.** Iteram, mas não têm `append`.
Converta: `list(sk.explode())`.

## Timeline e parâmetros

```python
design.timeline.markerPosition          # posição atual
design.userParameters.itemByName('d1')  # parâmetro por nome
param.expression = '25 mm'              # respeita unidade da string
param.value                             # sempre em cm
```

Em designs paramétricos cada feature entra na timeline. `DirectDesignType` não
tem timeline — cheque `design.designType` se for mexer nela.

## Materiais

Material de biblioteca **não** pode ser atribuído direto a um body — dá
`RuntimeError: 3 : invalid parameter value`. Copie para o design primeiro:

```python
lib   = app.materialLibraries.itemByName('Biblioteca de materiais do Fusion')
src   = next(m for m in lib.materials if 'inox' in m.name.lower())
steel = design.materials.addByCopy(src, src.name)   # obrigatório
body.material = steel
```

**Os nomes das bibliotecas e materiais seguem o idioma da UI.** Nesta
instalação é português: `'Biblioteca de materiais do Fusion'`, `'Aço
inoxidável'`, `'Alumínio'` — `itemByName('Fusion Material Library')` volta
`None`. Não hardcode nome em inglês; filtre por substring minúscula
(`'inox' in m.name.lower()`).

Cuidado com acento: `m.name.startswith('Aço')` falhou por normalização
Unicode mesmo com o nome batendo na listagem. Compare por substring sem
acento (`'inox'`, `'alum'`) em vez do prefixo acentuado.

## Retornando dados

Objetos Fusion não são JSON-serializáveis. Extraia primitivos:

```python
result = [{'name': b.name, 'volume_cm3': b.physicalProperties.volume}
          for b in root.bRepBodies]
```

## Antes de modificar

Operações destrutivas (deletar bodies, features, componentes) não têm undo pelo
bridge. Confirme com o usuário antes. Para inspecionar primeiro, retorne a
estrutura e só depois aplique a mudança.

## Referências — consulte antes de chutar

Este arquivo cobre o essencial. Para o resto da API, use `references/`:

- **`references/api-index.md`** — 1832 classes/enums com a URL oficial de cada
  uma. Faça grep para descobrir se algo existe e como se chama, depois abra a
  URL com WebFetch para a assinatura e o exemplo.

      grep -i "revolvefeature" references/api-index.md

- **`references/guides.md`** — 9 guias do User's Manual: BRep, Design Intent,
  Events, Attributes, Selection Filters, Custom Graphics, Commands, Command
  Inputs, Threading.

      sed -n '/^## Attributes/,/^---/p' references/guides.md

- **`references/README.md`** — qual dos dois usar para quê.

Não invente nomes de método. Se não achou no índice, o método provavelmente não
existe com esse nome — procure o conceito relacionado.

Fontes externas: [User's Manual](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-C1545D80-D804-4CF3-886D-9B5C54B2D7A2),
[PDF do object model](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/ExtraFiles/Fusion.pdf),
e os stubs locais em `API/Python/defs/adsk/` (assinaturas exatas da versão
instalada — a fonte mais precisa se a docs online divergir).
