---
name: fusion360-api
description: Use when writing code for the Fusion 360 API via the fusion_eval MCP tool - covers units, the object model, components vs occurrences, proxies, sketches, features and the Python-specific traps. Trigger on Fusion 360, fusion_eval, adsk.fusion, adsk.core, sketch/extrude/timeline/parameter work in Fusion.
---

# Fusion 360 API

Writing code for `fusion_eval`. Everything here was verified against
Autodesk's official docs (Fusion API User's Manual), not recalled from
memory.

## This file grows with use — contribute

If you are an agent working in this codebase: **when you lose time to a trap
that isn't documented here, write it down before you finish the task.** Every
section below came from a real mistake that cost calls. A method with a
different name than expected, a signature that varies, an operation that
fails silently, a name that changes with the UI language — all of it earns
an entry.

The test is simple: *would this make me get it wrong again a month from now?*
If yes, write it. If it was your own reasoning error rather than an API trap,
it probably doesn't deserve a section — at most a warning line where the
topic is already covered.

Rules for contributing:

- **Verify before you write.** Run the case through `fusion_eval` and paste
  the real behaviour, not what you assume. A wrong line here costs more than
  a missing one, because it will be followed without checking.
- **Document the error message next to the fix.** Whoever hits the same trap
  will search for the error text, not the name of the concept.
- **Prefer the minimal example** that runs over the explanatory paragraph.
- **Fix what went stale.** If a section contradicts current behaviour,
  updating it is worth more than adding a new one — a skill that describes
  the tool wrongly is worse than an incomplete one.
- **The source is `src/fusion360_mcp/skill/SKILL.md` in the repo.** That's
  what goes in the PR and what the installer copies from. The file at
  `~/.claude/skills/fusion360-api/` is the installed copy that loads in your
  sessions — editing only there loses the work on the next install. Edit in
  the repo and run `fusion360-mcp install` to refresh yours.

### How to submit

Contributions come in as **pull requests** — nobody commits straight to
master. The maintainer (@artapo) reviews and decides what lands.

- One PR per finding. Two unrelated findings on separate branches review
  faster and don't block each other.
- In the PR body, say **what you were doing when you hit the trap**. Context
  is half the value: it separates the general case from the one-off
  accident.
- Paste the actual `fusion_eval` output that proves the behaviour — the call
  that failed and the one that worked. That's what lets a reviewer judge it
  without reproducing everything.
- If you fixed something that was written wrong here, say so in the title.
  Corrections get review priority over additions.

Don't wait for approval to open the PR: open it, with the verification
included. Do wait for approval before treating the matter as documented —
while the PR is open, the finding isn't shared knowledge yet.

## The fusion_eval environment

Pre-bound globals: `adsk`, `app`, `ui`, `design`, `root`.
Assign to `result` to return a value — it must be JSON-serializable or it
comes back as `repr()`. Runs on Fusion's main thread, so the API is fully
usable. 60s timeout.

```python
result = [b.name for b in root.bRepBodies]
```

`design` is already `adsk.fusion.Design.cast(app.activeProduct)` and `root`
is already `design.rootComponent` — don't redo it. If the user is in the
Manufacture workspace, `design` comes back `None`; check before touching
geometry.

Also pre-bound: `snapshot()`, `screenshot()`, `api()`, `undo()`.

**A call that changes the model says so.** The reply carries a delta line, so
you don't need a `snapshot()` just to confirm a build worked:

```
null
[timeline 3->5, +1 body]
```

No line means nothing changed — which is itself the answer when you expected
a build to happen.

## Units — bug source number one

The API **always** uses internal database units, regardless of what the user
configured in the UI:

| Design | CAM |
|---|---|
| Length: **cm** | Length: cm |
| Angle: **radians** | Angle: **degrees** |
| Mass: kg | Time: s, Power: W |

Design uses radians, CAM uses degrees. Don't mix them up.

`5` in an API call is **5 cm**, not 5 mm. For 10 mm write `1.0`, or better,
make it explicit:

```python
mm = 0.1  # mm -> cm factor
dist = adsk.core.ValueInput.createByReal(10 * mm)
```

When input comes from the user as a string ("3 in", "1/2", "hole_depth / 2"),
don't parse it by hand — use the UnitsManager:

```python
um = design.unitsManager
if um.isValidExpression(txt, um.defaultLengthUnits):
    cm = um.evaluateExpression(txt, um.defaultLengthUnits)
```

To display back to the user, format with `um.formatInternalValue(...)`.

`ValueInput.createByString('10 mm')` respects the explicit unit and accepts
expressions/parameters; `createByReal(1.0)` is always cm. Prefer
`createByString` when you want the value to become a parametric expression
in the model. Examples below abbreviate it as `VI = adsk.core.ValueInput`.

## Object model

`Application` → `Documents` / `Document` → `Product` (→ `Design`) →
`rootComponent` → sketches, features, bodies, construction geometry,
occurrences.

To find something, ask who owns it: a SketchLine belongs to a Sketch, which
belongs to a Component.

Every object has: `objectType`, `classType()`, `isValid` (checks whether it
still exists — a stored reference can be invalidated by a later operation).

Transient objects use static functions:
`adsk.core.ObjectCollection.create()`, `adsk.core.Point3D.create(x, y, z)`,
`adsk.core.Matrix3D.create()`.

## Components vs Occurrences

- **Component** holds the geometry. Always in model space, not
  repositionable.
- **Occurrence** is an instance of the component. It's what shows in the
  browser and on screen. Repositionable and constrainable.
- Only the root component exists without an occurrence.

**Trap:** when creating geometry through the API, the UI's active component
is **ignored**. Geometry goes into the component you called from. Editing
`Component1` means grabbing that component, not activating it in the UI.

Creating a new component = creating an occurrence:

```python
occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
newComp = occ.component
```

Editing a component affects **all** of its occurrences.

**`addExistingComponent(comp, m)` does not place the occurrence at `m`.** It
applies `m` on top of the transform of the component's first existing
occurrence. When that occurrence sits at the identity the result looks
right, which hides the trap. Asking for a pure translation of (1, 2, 3) cm:

    component whose first occurrence is at identity   -> (1, 2, 3)
    component whose first occurrence is elsewhere     -> (5.37, -15.16, -1.70)
                                                         = first + (1, 2, 3),
                                                           with first's rotation

The full matrix matches "first occurrence's transform, then `m`"
(`first.copy().transformBy(m)`), not the reverse. Set the transform again
once the occurrence exists, then capture the position:

```python
o = root.occurrences.addExistingComponent(comp, m)
o.transform2 = m                        # now it really is m
if design.snapshots.hasPendingSnapshot:
    design.snapshots.add()              # otherwise the move can be undone
```

An uncaptured move does not last in a parametric design. An occurrence set
to (1, 2, 3) and left uncaptured was back at (5.37, -15.16, -1.70) after the
next recompute, which here was triggered by `undo()`. The same goes for
moving any existing occurrence through `transform2`.

## Proxies

A face inside `Component9` that appears in two occurrences is ambiguous —
Fusion doesn't know which instance you mean. The proxy carries the full path
(`Component9:1/RedFace`).

- `assemblyContext` → top occurrence of the path
- `nativeObject` → the real entity inside the component
- `createForAssemblyContext(occ)` → creates the proxy in that context

If a call fails complaining about assembly context, a proxy is missing. In
single-component (root) designs this never comes up.

**The error doesn't always mention context.** Rotating the bodies of a
sub-component about that component's own axis, with a feature created in
that component:

```python
mi = C.features.moveFeatures.createInput2(bodies)   # C = occ.component
mi.defineAsRotate(C.xConstructionAxis, VI.createByString('90 deg'))
# RuntimeError: 3 : Invalid entity
```

Verified side by side, with the bodies both native (`C.bRepBodies`) and as
proxies (`occ.bRepBodies`) — same result either way:

    C.xConstructionAxis                                Invalid entity
    C.xConstructionAxis.createForAssemblyContext(occ)  ok
    root.xConstructionAxis                             ok (*)
    defineAsFreeMove(Matrix3D.setToRotation(...))      ok

(*) It runs, but it is the root's X axis: once the occurrence is moved, that
is a different line from the component's own X, and the rotation lands
elsewhere.

`Invalid entity` on construction geometry of a component that isn't the
root means: pass the proxy. A free move with a matrix sidesteps entities
altogether.

## The Input Object pattern

Complex features always follow: `createInput` → configure → `add`. The input
object is the equivalent of the command's dialog.

```python
sk = root.sketches.add(root.xYConstructionPlane)
sk.sketchCurves.sketchCircles.addByCenterRadius(
    adsk.core.Point3D.create(0, 0, 0), 2.0)   # radius 2 cm

prof = sk.profiles.item(0)
ext = root.features.extrudeFeatures
inp = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(1.0))  # 1 cm
result = ext.add(inp).name
```

**A Join that doesn't join is a `participantBodies` problem.** When the new
geometry starts inside an existing body (an offset `startExtent`), the Join
can still come back as a *separate* body — the delta line says `+1 body`
where you expected none. The feature needs to be told which bodies take
part, and that has to happen on the **input**, before `add()`:

```python
inp.participantBodies = [target_body]     # works
f = ext.add(inp)
f.participantBodies = [target_body]       # RuntimeError: 3 : Didn't roll
                                          # editing feature back.
```

Setting it after the fact is not recoverable — you delete the feature and
rebuild it. If the feature is already there, `combineFeatures` with
`JoinFeatureOperation` merges the two bodies instead.

`FeatureOperations`: `NewBodyFeatureOperation`, `JoinFeatureOperation`,
`CutFeatureOperation`, `IntersectFeatureOperation`,
`NewComponentFeatureOperation`.

**The signature of `createInput` varies per feature.** Don't assume it's
always `(profile, operation)`. `RevolveFeatures` wants the axis in the
middle:

```python
inp = rev.createInput(profile, axis, operation)   # 3 args, verified
```

If you get `TypeError: createInput() missing 1 required positional
argument`, that's this — check the signature in the local stubs at
`API/Python/defs/adsk/` before trying variations.

Collections have assorted `add*` methods — `sketchArcs` has
`addByThreePoints`, `addByCenterStartSweep`, `addFillet`. Look for the right
one before improvising.

## Sketch plane orientation — local axes are not the global ones

A sketch's local (x, y) maps onto global axes differently per plane, and two
of the three flip a sign. Verified by placing a point at local (10, 0) and
(0, 10) and reading `worldGeometry`:

| Plane | local +x | local +y | positive extrude |
|---|---|---|---|
| `xYConstructionPlane` | +X | +Y | +Z |
| `xZConstructionPlane` | +X | **−Z** | **+Y** |
| `yZConstructionPlane` | **−Z** | +Y | +X |

The `yZ` case is the trap: neither local axis is Y-then-Z as the name
suggests — local +x runs along **−Z**. On `xZ`, to place geometry at global
Z = +150..+240 you sketch at local y = −240..−150.

**`PositiveExtentDirection` follows the plane normal, not the name.** `xZ`
has local y = −Z, yet it extrudes toward **+Y**. An offset plane keeps the
normal of the plane it was offset from, so cutting *into* a body from the
far side needs `NegativeExtentDirection`. Verified with magnet pockets cut
into the four sides of a box sitting at X, Y ≥ 0:

| Face | Sketch plane | Direction that cuts into the body |
|---|---|---|
| bottom (Y = 0) | `xZConstructionPlane` | positive |
| top (Y = H) | `xZ` offset by H | **negative** |
| left (X = 0) | `yZConstructionPlane` | positive |
| right (X = W) | `yZ` offset by W | **negative** |

```python
inp.setOneSideExtent(
    adsk.fusion.DistanceExtentDefinition.create(VI.createByString('2 mm')),
    adsk.fusion.ExtentDirections.NegativeExtentDirection)
```

When unsure, cut one way and check that `body.physicalProperties.volume`
went down before moving on.

Don't reason it out — measure it. One point tells you the mapping:

```python
sk = root.sketches.add(root.yZConstructionPlane)
p  = sk.sketchCurves.sketchLines.addByTwoPoints(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(1.0, 0, 0)).endSketchPoint.worldGeometry
result = [p.x, p.y, p.z]      # -> [0, 0, -1]: local +x is global -Z
```

**`sketch.boundingBox` is in sketch space, not world space** — so it cannot
confirm where geometry landed. The same rectangle reports `min.y = 28.5,
min.z = 0` from the bounding box while its points are actually at
`y = 0, z = -28.5`. To check a sketch's real position, read
`worldGeometry` on a point; the bounding box will happily agree with a wrong
mental model.

## Sketch dimensions from the origin

**Two points that share a coordinate exactly can't both be dimensioned
from the origin.** Dimensioning the second one raises:

    RuntimeError: 3 : VCS_SKETCH_OVER_CONSTRAINTS - La géométrie d'esquisse est surcontrainte

(the message follows the UI language — search for the code, not the text).
Four circles at (±3.4, ±1.9) cm, each given a diameter plus a horizontal
and a vertical distance from `sk.originPoint`:

    1,1   dia ok  dx ok    dy ok
    1,-1  dia ok  dx FAIL  dy ok      <- same x as (1,1)
    -1,1  dia ok  dx ok    dy FAIL    <- same y as (1,1)
    -1,-1 dia ok  dx ok    dy ok

The exact alignment acts as a hidden constraint. Either fix works:

- create the geometry slightly off and let the dimension drive it to the
  exact value — `addByCenterRadius(P(x + 0.011 * i, y + 0.011 * i, 0), r)`,
  with `i` different per circle; both dimensions then go through;
- state the relation instead of repeating it: dimension the first point,
  then `geometricConstraints.addVerticalPoints(p1, p2)` (or
  `addHorizontalPoints`) and a single dimension for the other coordinate.
  Hanging the circles on the corners of a construction rectangle (centred
  on the origin with a construction diagonal and `addMidPoint`) also works,
  and gives you a width and height to drive.

**Deleting a line that starts on `sk.originPoint` deletes the origin
too** — and every dimension that hangs on it. `addByTwoPoints(sk.originPoint,
...)` doesn't copy the point, it uses it (`ln.startSketchPoint ==
sk.originPoint` is `True`):

    before ln.deleteMe():  1 dimension, originPoint valid
    after:                 0 dimensions, sk.originPoint is None

Nothing moves, so nothing looks wrong — the sketch just stops being driven,
and the next parameter change leaves that geometry behind.
`sk.isFullyConstrained` turning `False` is the only sign. Leave helper
lines that touch the origin in place (`isConstruction = True`) rather than
deleting them, and check `isFullyConstrained` after any cleanup.

## Python: the gotchas

**Out-args become tuples.** `Point3D.getData(out x, out y, out z)` in Python:

```python
(retVal, x, y, z) = point.getData()
```

**Equality:** use `==`, **never** `is`. Fusion objects are wrappers; `is`
compares the wrapper, not the entity.

```python
if face1 == face2:  # correct
```

**Types:** `type()` only gives the exact type. For hierarchy use
`isinstance`:

```python
isinstance(sel, adsk.fusion.SketchEntity)  # catches SketchLine, SketchArc, etc.
```

`cast()` returns `None` when the type doesn't match — it's the idiomatic way
to validate a selection:

```python
edge = adsk.fusion.BRepEdge.cast(sels[0].entity)
if not edge:
    result = 'not an edge'
```

**Collections** iterate like Python containers: `for x in col`, `len(col)`,
`col[0]`, `col[-1]`, `col[1:4]`. No need for `range(col.count)`.

**Returned arrays are "vector", not list.** They iterate, but have no
`append`. Convert: `list(sk.explode())`.

## Timeline and parameters

```python
design.timeline.markerPosition          # current position
design.userParameters.itemByName('d1')  # parameter by name
param.expression = '25 mm'              # respects the string's unit
param.value                             # always in cm
```

In parametric designs every feature enters the timeline. `DirectDesignType`
has no timeline — check `design.designType` before touching it.

## Making a feature count follow a parameter

Goal: one pocket per grid cell, with the cell count `Nx` a user parameter.
Two obvious routes fail, one silently.

**An extrude keeps the profiles it was created with.** Circles added to
the sketch later — by hand or by a sketch pattern — are not added to the
cut. Pockets patterned in the sketch with quantity `Nx`, cut by one
extrude:

    Nx x Ny = 1x1 -> 8 pockets      3x2 -> 8 pockets (expected 20)

No error, no warning, timeline healthy. Count the result; the health state
won't tell you. (The sketch pattern itself is fine and accepts quantity 1:
`gc.createRectangularPatternInput(entities, PatternDistanceType.SpacingPatternDistanceType)`,
then `setDirectionOne(sketch_line, VI.createByString('Nx'), VI.createByString('Pas_L'))`
— the direction must be a `SketchLine`.)

**A feature pattern fails as soon as no copy touches the body** — which is
exactly `Nx = 1`, where the next cell is outside the part:

    RuntimeError: 3 : ... PATTERN_FEATURES_NO_PASTE_INT_EDGES -
    Aucune intersection possible entre une occurrence de réseau et le corps

Quantity 1 fails the same way, with every `patternComputeOption`. Two
coincident instances (spacing 0) fail too: the copy cuts nothing. Created
at `Nx = 2` and then set to 1, the feature turns red (`healthState` 2).
What stays healthy is two instances **0.02 mm apart** when `Nx = 1`:

```python
q   = 'max(Nx; 2)'
gap = 'Pas_L * min(Nx - 1; 1) + 0.02 mm * (1 - min(Nx - 1; 1))'
inp = rp.createInput(features, axis, VI.createByString(q),
                     VI.createByString(gap),
                     adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
```

    Nx = 1 -> 8 pockets   Nx = 2 -> 12   Nx = 3 -> 16   no errors

At `Nx = 1` the pocket comes out 0.02 mm wider — irrelevant at 3D-printing
tolerances. Create the pattern while `Nx >= 2` (that's how it was
verified), then let the parameter go back to 1.

**Expression functions separate arguments with `;` here**, not `,` —
checked with `unitsManager.isValidExpression` on a French-language install:

    max(Nx; 2)   True
    max(Nx, 2)   False

Likely locale-dependent, like material names: validate an expression before
writing it into a feature.

## Materials

A library material **cannot** be assigned straight to a body — it raises
`RuntimeError: 3 : invalid parameter value`. Copy it into the design first:

```python
lib   = next(l for l in app.materialLibraries if 'materiais' in l.name.lower())
src   = next(m for m in lib.materials if 'inox' in m.name.lower())
steel = design.materials.addByCopy(src, src.name)   # required
body.material = steel
```

**Library and material names follow the UI language.** On this install they
are Portuguese: `'Biblioteca de materiais do Fusion'`, `'Aço inoxidável'`,
`'Alumínio'` — `itemByName('Fusion Material Library')` returns `None`. Don't
hardcode English names; filter by lowercase substring
(`'inox' in m.name.lower()`).

Watch out for accents: `m.name.startswith('Aço')` failed due to Unicode
normalization even though the name matched in the listing. Compare by
accent-free substring (`'inox'`, `'alum'`) rather than the accented prefix.

**`itemByName` is subject to the same normalization** — it is a string
compare like any other. `app.materialLibraries.itemByName('Biblioteca de
aparência do Fusion')` returns `None` even though a library by exactly that
name is in the listing, and the failure surfaces one line later as
`AttributeError: 'NoneType' object has no attribute 'appearances'`. Iterate
and match on an unaccented substring instead:

```python
lib = next(l for l in app.materialLibraries if 'apar' in l.name.lower())
```

Same trap, second form: `next(m for m in lib.materials if m.name ==
'Alumínio')` raises `StopIteration` — and since `next()` without a default
raises before the assignment to `result`, the traceback points at the
generator, not at the name. Give `next()` a default when you are probing,
or match by substring.

**Appearance is not material.** `body.material` drives physical properties;
what you see is `body.appearance`, from a separate library (`'apar'` above)
via `design.appearances.addByCopy(...)`. Setting only the material leaves
the body rendered in the material's default look:

```python
lib = next(l for l in app.materialLibraries if 'apar' in l.name.lower())
src = next(a for a in lib.appearances if a.name == 'Pintura - Metalizada (Preto)')
body.appearance = design.appearances.addByCopy(src, 'Preto')
```

Appearance can also be set per face (`face.appearance`), which overrides the
body's. Editing an upstream sketch reassigns face indices, so per-face
appearance lands on the wrong faces after a rebuild — reapply it, or keep it
at body level.

## Returning data

Fusion objects are not JSON-serializable. Extract primitives:

```python
result = [{'name': b.name, 'volume_cm3': b.physicalProperties.volume}
          for b in root.bRepBodies]
```

**`print()` returns nothing.** Fusion has no console wired to the bridge:
the output vanishes and the call comes back `null`. To inspect several
values, accumulate into a list and assign it to `result`:

```python
tab = []
for D in (19, 20, 21):
    tab.append({'D': D, 'area': ...})
result = tab          # not print(...) inside the loop
```

## Before modifying

The bridge has `undo()`: it reverts the last call that touched the model,
deleting the timeline entries it created. One level only. A call that raises
is rolled back automatically, so `undo()` is for taking back work that
succeeded but came out wrong.

```python
result = undo()   # 'undone: 4 timeline entries removed, back to position 7'
```

What `undo()` does **not** cover: it only works in parametric designs
(direct modelling has no timeline), and it only sees what goes through the
timeline — renaming a body, changing material or toggling visibility have no
way back. Deleting bodies and components still needs the user's
confirmation.

To go back more than one step, the rollback is manual and destructive — it
wipes everything after the mark:

```python
import sys
mod = sys.modules[next(n for n, m in sys.modules.items()
                       if getattr(m, '__file__', None) and 'Claude MCP' in str(m.__file__))]
mod._rollback_to(4)      # keeps the first 4 timeline entries
mod._checkpoint = None
```

Moving `markerPosition` alone **does not** undo anything: it suppresses the
features, which come back if something rolls forward. Real undo is deleting
each entry, back to front.

**How you delete one depends on the version.** `TimelineObject.deleteObject()`
(guarded by `isDeletable`) is the documented way, but neither exists before
~2705 — on 2704.1.36 both are absent and every call raised `AttributeError:
'TimelineObject' object has no attribute 'isDeletable'`. `entity.deleteMe()`
works on both, since deleting the feature removes its timeline row. The
bridge's `_delete_entry` tries the first and falls back to the second; write
new code the same way rather than assuming either.

## Threads

Thread queries are `all*`, not `getAll*` (`getAllSizes` does not exist). The
order is type → size → designation → class, and each step feeds the next:

```python
th = root.features.threadFeatures
q  = th.threadDataQuery
q.allThreadTypes                                  # 'ANSI Unified Screw Threads',
                                                  # 'ANSI Metric M Profile', ...
q.allSizes(type)                                  # '0.375'  (inch, string)
q.allDesignations(type, '0.375')                  # '3/8-24 UNF', '3/8-16 UNC', ...
cls = list(q.allClasses(False, type, desig))[0]   # '1A'; False = external thread
```

`createThreadInfo` only accepts a class that came from `allClasses` — an
invented name is rejected. And `isModeled = True` is what produces real
thread geometry; without it the thread is cosmetic (it shows, but the volume
doesn't change).

```python
info = th.createThreadInfo(False, type, desig, cls)
faces = adsk.core.ObjectCollection.create()
faces.add(cylindrical_face)          # the face the thread goes on
inp = th.createInput(faces, info)
inp.isModeled = True
th.add(inp)
```

To find the right face, filter by radius rather than index — face order
changes with every feature:

```python
target = next(f for f in body.faces
              if f.geometry.objectType == adsk.core.Cylinder.classType()
              and abs(f.geometry.radius*10 - 4.765) < 0.05)   # Ø9.53 in mm
```

## Checking geometry without a screenshot

`f.geometry.objectType` gives the surface type, and each type exposes the
dimension that matters: `Cylinder.radius`, `Sphere.radius`, `Cone.halfAngle`
(in radians). Listing that confirms design diameters and angles more cheaply
and more precisely than looking at an image:

```python
result = [{'type': f.geometry.objectType.split('::')[-1],
           'radius_mm': round(f.geometry.radius*10, 3)}
          for f in body.faces
          if f.geometry.objectType == adsk.core.Cylinder.classType()]
```

A large bounding box does not mean mirrored geometry: a profile revolved
around an axis that doesn't pass through the centre produces the whole body
at once. Check `minPoint`/`maxPoint` separately before concluding something
got duplicated.

## api() — ask the object before guessing

`api(obj)` lists what an object actually offers, with real signatures. One
cheap call instead of a write-fail-read-traceback round trip:

```python
result = api(root.features.revolveFeatures)
# createInput(profile: 'core.Base', axis: 'core.Base', operation: 'FeatureOperations')
# props: count, isValid, objectType
```

Second argument filters by substring — use it on big classes:

```python
result = api(inp, 'extent')   # setOneSideExtent(extent, direction, taperAngle=None), ...
```

Takes an instance or a class. It reads the API **as installed**, which is the
point: the online docs describe the newest version, and a method documented
there may not exist in the running Fusion. `TimelineObject.deleteObject`
is exactly that case — present in the docs, absent before ~2705. When docs
and `api()` disagree, `api()` wins.

Reach for it whenever you are about to guess a method name, and after any
`AttributeError`.

## Finding a class you don't have an object for

`api()` needs an object or a class. To find out whether something exists at
all, grep the installed stubs — they are the API as this Fusion actually has
it, which the online docs are not:

    # Windows
    grep -n "^class Revolve" ~/AppData/Roaming/Autodesk/Autodesk\ Fusion\ 360/API/Python/defs/adsk/fusion.py
    # macOS
    grep -n "^class Revolve" ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/Python/defs/adsk/fusion.py

`core.py` and `fusion.py` hold almost everything; `cam.py`, `drawing.py`,
`sim.py` cover the other workspaces. Once you have the class,
`api(adsk.fusion.RevolveFeatures)` gives the signatures.

Don't invent method names. If a grep over the stubs doesn't find it, it
doesn't exist under that name — look for the related concept.

## References

- **`references/guides.md`** — 9 guides from the User's Manual: BRep, Design
  Intent, Events, Attributes, Selection Filters, Custom Graphics, Commands,
  Command Inputs, Threading. Concepts the stubs don't explain.

      sed -n '/^## Attributes/,/^---/p' references/guides.md

- **`references/api-index.md`** — 1106 classes with their doc URLs. Superseded
  by `api()` and the stubs for everyday use, and it describes the *newest*
  Fusion, which may not be yours — the versioned `deleteObject` trap above
  came from trusting it. Kept for when you want the prose documentation of a
  class and its examples: grep the name, open the URL with WebFetch.

External sources: [User's Manual](https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-C1545D80-D804-4CF3-886D-9B5C54B2D7A2),
[object model PDF](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/ExtraFiles/Fusion.pdf),
and the local stubs at `API/Python/defs/adsk/` (exact signatures for the
installed version — the most accurate source when the online docs disagree).

## Drawings: reading a property can execute an action

`adsk.drawing` is documented, but every class carries *"preview feature — may
change in future releases. Do not use it in distributed programs."* Treat it
as unsafe on a real document until proven otherwise.

**`Sheet.tidyUp` is a property, not a method — reading it runs the rearrange.**
The local stub declares `def tidyUp(self) -> bool`, which is wrong; the
official docs list it under *properties*. Calling it the obvious way fails,
and the "fix" is what does the damage:

```python
sh.tidyUp()   # TypeError: 'bool' object is not callable
sh.tidyUp     # -> True, and the sheet has already been rearranged
```

There is no undo: the bridge's `undo()` only walks a Design timeline, and
drawings have none. Recovery is Ctrl+Z in the UI, or closing without saving.

On 2704.1.36 this corrupted a 9-view sheet. Before `tidyUp`, `View.type` and
`View.viewCurves` both worked (635 curves on view 0); after, every view
reported `isValid: True` while both members raised
`RuntimeError: 2 : InternalValidationError : pAsset`, and `viewCurves`
enumerated 0. The views become hollow. Do not run it on work you cannot
afford to reopen.

**`View` cannot be repositioned.** Its entire surface is `classType()`,
`isValid`, `objectType`, `type` — verified against both the stub and
`drawing_View.htm`. No position, scale, width or height. Laying out a sheet
by API is not possible; `tidyUp` is the only rearrange, and it is the one
above.

Other traps in the same namespace:

- `app.activeViewport` is `None` in the Drawing workspace, so the bridge's
  `screenshot()` raises `AttributeError: 'NoneType' object has no attribute
  'refresh'`. You cannot see a sheet from here.
- `design` is `None` (the active product is `adsk::drawing::Drawing`), so
  check before touching anything geometry-related.
- `viewCurves` raises `IndexError` on `[0]` but iterates fine — and a
  `next(iter(...))` that worked once can raise `StopIteration` later, because
  the collection is only populated in the right context.
- `Images` has no `count`.
