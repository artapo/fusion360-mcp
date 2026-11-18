# Guias conceituais - Fusion API User's Manual

Texto extraido da documentacao oficial da Autodesk. Cobre o "como fazer"
que o api-index.md (lista de classes) nao explica.

## Fusion Solids and Surfaces (BRep)

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/BRepGeometry_UM.htm

Fusion Solids and Surfaces
Solid models in Fusion are represented by a group of surfaces that form a tightly closed volume.  This is commonly known as Boundary-Representation, or B-Rep modeling.  A B-Rep model provides a complete geometric description of a solid or surface model.  For a solid, the defining surfaces are tightly connected along all edges, forming a closed ('water tight') volume.  With this volume, Fusion is able to compute things like mass properties and perform operations on the surfaces as though they were actual 'real world' solid objects.  When a new feature is defined, Fusion creates the surfaces necessary to represent the feature, intersects them with the existing body, and then trims the affected surfaces back such that all of the seams are tight.

A B-Rep model is defined by two things; topology and geometry. The sections below describe the concepts of topology and geometry, as well as the API functionality that provides access to the topological and geometrical definition of a solid. Editing a Fusion model is done through features in a parametric model, or through direct modification in a direct edit (non-parametric) model.

Topology Defined

The Topology of a model is defined by a hierarchical structure of objects.  The full API object hierarchy for B-Rep topology is shown in the following illustration. The discussion that follows describes each of the objects in the hierarchy. You may have noticed in the chart that several of the objects can be obtained in different ways.  For example, you can get BRepFaces from a BRepBody, BRepLump, or BrepShell object.  You decide which object to get the faces from depending on which set of faces you want.  Getting the faces from the body will return all of the faces in the body.  Getting the faces from a shell will return only the faces that belong to that shell, which will be a subset of the faces in the body.  It would be similar to getting a list of all of the people in an entire building, versus a list of the people within a single room in that building.  The room list is a subset of the building list.

BRepBody

The B-Rep model is accessed through the Component object. A component can contain zero to any number of bodies. The top-level object is the BRepBody object (or “Body”).  The image below is an illustration of the API hierarchy to get to a body.  BRepBody objects are accessed from the BRepBodies collection object.  The BRepBodies collection object is obtained from the Component.

BRepLump

A BRepLump (or “Lump”) object represents a single set of connected faces and any hollowed out volumes within that set of faces.  In theory it is possible for a body to have multiple lumps however Fusion enforces that a body will always only contain a single lump.  In the example below, a hole in a part has been enlarged enough to cut the part into two pieces.  If multiple lumps were supported the result will be a single body, that has two lumps.  However, Fusion will create a new body in this case so the result will be two bodies, each containing a single lump.  If either of the pieces were to be hollowed out using a Shell feature with no open faces there is still a single body and lump and the new surfaces defining the internal void will also be part of the lump.

The BRepLump objects in a body are accessed through the BRepLumps collection, which is obtained from the parent BRepBody object.

BRepShell

A BRepShell (or “Shell”) object represents a single set of connected faces.  For most bodies there is a single BRepLump that consists of a single BRepShell.  However, it is possible for a body to have multiple shells.  This is illustrated in the example below where a sphere has been hollowed out using a Shell feature.  The result is a single body containing a single lump, that has two shells; the outer and inner set of faces.  Creating a hole in this model would reduce it to a single shell because the face representing the hole would join the inner and outer faces resulting in a single set of connected faces.

To determine whether a shell represents the outside of a part or a void within a part, use the isVoid property on the BRepShell object.

BRepShell objects in a body are accessed through the BRepShells collection, which can be obtained from the parent BRepBody, or from the BRepLump object.  The collection from the BRepBody contains all of the shells that exist within the body and collection from a BRepLump, contains only the shells within that Lump.

BRepFace

A BRepFace object represents a specific surface within a body.  The illustration below shows an exploded version of a body where the individual faces that make up the model can be seen more clearly.  Faces are accessed through the BRepFaces collection, which can be obtained from a BRepBody, BRepLump, or BRepShell object.

BRepLoop

A BRepLoop (or “Loop”) object defines a boundary of a specific face.  All faces have one outer loop and can have zero or more inner loops.  In the illustration below, the two loops of the face are highlighted in red.  There is one outer loop consisting of four edges, and one inner loop that consists of a single circular edge.  Loops are accessed through the BRepLoops collection which is obtained from teh parent BRepFace object.

BRepEdge

A BRepEdge object represents an individual curve within an edge loop.  An important purpose of an Edge is that it defines the connection between two faces.  The illustration below shows a single edge highlighted in red.  This single edge is shared by two adjacent faces.

There are several ways to access edges through the API.  You can query a BRepFace for all of its edges, either all at once or loop by loop by using the BRepLoops property of the BRepFace object.  You can also query for all edges within a BRepBody, BRepLump, or BRepShell.  From an edge, it is possible to get the two faces that it connects.  An edge along the open boundary of a surface is connected to only a single face.

BRepVertex

BRepVertex objects represent the end points of an edge.  The image below shows a single vertex highlighted in red.  This vertex is shared by three edges.  Vertices can be accessed from the BRepVertices collection available on the BRepBody, BRepLump, BRepShell and BRepFace objects. The vertices at the start and end of an edge can be accessed using the StartVertex and EndVertex properties of the BRepEdge object.  The vertex itself provides access to the edges and faces that it connects.

BRepCoEdge

A BRepCoEdge object is similar to a BRepEdge object in that they both define the boundaries of a face.  There are two differences between a BRepEdge and a BRepCoEdge object:  The first being that BRepCoEdge objects are unique for a particular face, whereas edges are shared between faces.  BRepCoEdge objects are in an ordered head-to-tail orientation around the boundary of the face.  BRepCoEdge objects flow in a counter-clockwise direction around the outer boundary, and they flow in a clockwise direction (the material is always to the left) around the inner boundary, as shown in the illustration below.  This is not possible with BRepEdge objects because there can be conflicts in direction since edges are shared.

The second difference between BRepCoEdge objects and BRepEdge objects is that the BRepCoEdge object is not a 3D object (all other B-Rep objects are 3D objects).  A BRepCoEdge object is defined in the 2D parametric space of its parent face.  The concept of parametric space is discussed in more detail below in the section on evaluators.

Accessing Topology Objects
There are other methods to access B-Rep objects, besides traversing the object hierarchy, that are more convenient to use in some cases.  These methods are as follows.

From Features

The Faces property of the Feature object can be used to get the faces that were created by that feature. Some features also provide categorized access to the faces they create.  For example, the extrude feature provides the EndFaces, StartFaces, and SideFaces properties that return the end caps and the sides of an extrusion.

By Selection

In cases where it is not possible to determine the entities needed automatically, the user can be prompted to select them.  User selections from solid models return BRepBody, BRepFace, BRepEdge, or BRepVertex objects.

By Association

A specific B-Rep entity can also be accessed through its association with some other object.  For example, in an assembly you can obtain the two entities that a joint is defining a relationship between.

By Geometry

Aquiring B-Rep geometry that meets certain criteria is also possible through the use of 'evaluator objects'.  For example, one could query for all planar faces, parallel to the X-Y plane and are facing “up”.  This can be done using the B-Rep hierarchy, explained above, to access all of the faces, and then the geometry evaluators, explained below, to search for the faces that meet the criteria.

Evaluating Topology Objects
Topology defines only the structure of a model; it is the geometry that defines its shape.  Topology can describe a model as having 6 faces and 12 edges, but this description is insufficient to convey the actual shape of such a model.  The simple block shown below is only one of an infinite number of shapes a model with 6 faces and 12 edges could have.

Shown below are three more models that are also made up of 6 faces and 12 edges.

A face represents a surface, but does not imply or convey anything about the shape of that surface.  The same is true of an edge; it represents a curve, but does not imply or convey anything about the shape of the curve.  Faces and edges define how the various geometries are connected but to understand the shape of the model the associated geometry is required.

There are some general queries that can be performed on B-Rep objects that provide generic shape related information.  These queries are performed using the API evaluator objects, as shown below.

Evaluators perform many of their 'evaluations' relative to the parametric space of the surface or curve.  Coordinates define a location in model space by specifying x, y, and z values within three dimensional design space.  In Parameter space, coordinates define a location by specifying u and v values within the parametric space of a specific surface.  Every surface has its own unique 2-dimensional parameter space.  The image below shows a planar face with a grid drawn on it that represents its parametric space.  Any location on the surface can be precisely specified using two values.  For parametric space, instead of x and y, the letters u and v are used to designate the values of the coordinate.  The range or size of the parametric space can vary depending on the geometry of the surface and how the face has been trimmed by its boundaries.  An untrimmed NURBS surfaces has minimum values of (0, 0) and the maximum is (1, 1) as indicated in the image below.  However, a cylinder goes from -π to π in the direction around the cylinder and is infinite along the axis of the cylinder. A plane is unbounded and is infinite in both directions, although when a surface is associated with a face, the boundaries of the face are used to limit the surface.  You also can't assume that the parameterization is uniform across the surface.  This means that for a NURBS surfaces (0.5,0.5) is not necessarily at the geometric center of the surface.

The image below shows some examples of other surface shapes with their parameter space grid. The left-most surface looks as though it could be a variation of the planar surface; imagine the planar above above is made of rubber and is stretched and flexed into the shape below.  Any point on the surface can still be specified by a u-v coordinate.  The surface in the middle could be formed by rolling the planar face into a cylinder, where two values can still define any point on the surface.  To create the surface on the right, two of the edges of the planar face have been reduced to zero length but a u-v value still defines any point on this surface as well.

As stated earlier, the BRepCoEdge object is a 2D object.  It defines the boundary of a face in the parametric space of the surface associated with the face.  A BRepEdge can return up to two BRepCoEdge objects; one for each face connected to the edge.  The geometry associated with a BRepCoEdge object is two dimensional and the coordinates for the geometry are in the parametric space of the surface.

Curves also have a parametric space, which a one dimensional. This means that any point on a curve can be identified with a single parameter value.  The start and end parameter values are the extents of the curve, and any value in between represents a specific point along the edge, as shown in the illustration below.

The following are some of the most commonly used evaluator functions:

SurfaceEvaluator

    getNormalAtParameter – Calculates the normal vector of the face at a specified parameter point.  The normal always points out of the solid.

    getNormalAtPoint – Calculates the normal vector of the face at a specified model space point.  The normal always points out of the solid.

    getParameterAtPoint  – Given a 3D model point this returns the equivalent 2D parametric point.

    getPointAtParameter  – Given a 2D parametric point, this returns the equivalent 3D point.

    isParamOnFace  – Given a 2D parametric point, this indicates if the point lies on the face or not.  This takes into account the boundaries of the face and is useful for determining if a given point lies on the visible portion of a face or in a void.

    parametricRange   – Returns the maximum and minimum parameter space coordinates of the face.

CurveEvaluator3D and CurveEvaluator2D

    getEndPoints – Gets the start and end points of the edge.

    getLengthAtParameter – Returns the actual length of the edge between two input parameters.

    getParameterAtLength – Returns the parameter value at a specified distance along the curve from a specified parameter point.

    getParameterAtPoint – Given a 3D model point, this returns the equivalent parametric value along the edge.

    getPointAtParameter – Given a parametric value, this returns the equivalent 3D point.

    getParameterExtents – Returns the minimum and maximum parameter values of the edge.

The SurfaceEvaluator object provides useful functions for getting the normals from a surface; such as the getNormalAtPoint and getNormalAtParameter functions.  A normal is a vector that is perpendicular to a face at a specific point.  The normals on a given planar face are all identical, regardless of their location on that face.  The normals on a spherical face are different at every location on that face.  The direction of the normal for a solid is always outward (i.e. points away from the volume of the solid).  The illustration below shows a series of normals displayed on a spline face.  The normals are all perpendicular to the face and point in an outward direction from the solid.

The Python sample code below demonstrates how to find the parametric center of a face and then return the surface normal at that location.  For tasks that involve getting multiple normals, there is also a getNormalsAtParameters function that takes in an array of Point2D objects and returns and array of Vector3D objects.

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Have a face selected.
        fc = ui.selectEntity('Select a face', 'Faces').entity

		# Get the normal.
        (normal, position) = getNormalAtParametricCenter(fc)

        # Draw the normal using a sketch line.
        des = adsk.fusion.Design.cast(app.activeProduct)
        sk = des.rootComponent.sketches.add(des.rootComponent.xYConstructionPlane)
        normPoint = position.copy()
        normPoint.translateBy(normal)
        sk.sketchCurves.sketchLines.addByTwoPoints(position, n

---

## Programming for Design Intent

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/DesignIntent_UM.htm

Programming for Design Intent

Introduction
Three Design Types
Behavior Changes
Best Practices to Update Your Add-In
Making Your Command Available
Supporting Different Design Types

Introduction
Since the beginning, Fusion has supported a document type that combined parts and assemblies into a single document. In fact, it didn’t even differentiate between a part and an assembly. A single document can contain all the data for any number of components and also define how those components are assembled. This approach has its pros and cons. The primary pros are its high flexibility and simple data management, since it’s a single file.
There are several cons to having everything in a single file.

It was easy to create a complicated structure and relationships between components that were difficult to diagnose and fix if problems did occur.
The single timeline contains all of the features, sketches, construction geometry, joints, and constraints for the entire assembly. This makes managing the timeline difficult and results in more expensive computations.
Having everything in a single file makes it difficult to reuse data and integrate with data management systems.
Those coming from other CAD systems found this confusing.

Three Design Types

Previously, there was a single design type, which represented an assembly, one or more parts, or a combination of the two. Whether a component was a part or an assembly wasn’t explicitly specified, but was inferred from the contents of the component. For example, if a component only contains bodies, you can assume it is a part. If a component contains occurrences of other components, you can assume it is an assembly. It is also possible for a component to include both bodies and occurrences, which is strange and is another con resulting from the flexibility provided by hybrid designs.

Now there are three distinct design types: hybrid, part, and assembly.

Hybrid – Fusion has always supported a hybrid design: a single design that can contain both parts and assemblies with both internal and external references.

Part - A part design is a new type of design that only supports modeling. A part design typically contains one or more bodies, along with all the construction geometry, sketches, and features used to create them. It does not contain other components or occurrences.

Assembly - An assembly design is a new design type that supports only assembly modeling, and all parts and subassemblies used in the assembly must be external.

When creating a new design document, you choose one of these three types using the dialog shown below.

Two things change depending on the design type you choose: the user interface and the functionality that’s available. Let’s look first at the user interface. Remember that the main toolbar is organized into tabs, each containing panels that contain the commands buttons.

First, here’s the main toolbar for the previous release. It provides access to all Fusion functionality for part and assembly modeling, since hybrid design was the only type supported.

Shown below is the new main toolbar when a hybrid design is active. It is the same as the previous main toolbar, including the ASSEMBLE panel. Any existing add-ins should continue to function normally when a hybrid design is active.

Below is the main toolbar when an assembly design is active. It doesn’t include the ASSEMBLE panel; instead, it has an ASSEMBLY tab that organizes assembly-related commands into panels. If you have an assembly-related command you want to be available when an assembly design is active, you’ll need to update your add-in to add it to this new user interface layout. This is discussed in more detail in the section on updating your commands.

Below is the main toolbar when a part design is active. It’s essentially the same as the hybrid toolbar, but it lacks the ASSEMBLE panel you’re familiar with. It does contain a panel named ASSEMBLE, but it is a new panel and differs from the previous ASSEMBLE panel. The new ASSEMBLE panel contains a single command to insert this part into an assembly. Even though it is named ASSEMBLE, the ID of this panel differs from the previous ASSEMBLE panel, so any add-ins that add commands to the ASSEMBLE panel will not accidentally add them to this new panel. Those commands will not be available for part designs.

Behavior Changes

Depending on the active design type, Fusion now exhibits different behaviors. These behavior changes are most likely to cause problems when updating an add-in to work with these new workflows and will require the most work to update your add-in.

Hybrid – Because hybrid designs are what we had before, there is no change in behavior when a hybrid design is active, so the logic of your program shouldn’t require any changes.

Part – If you have a command that is modeling-specific, it shouldn’t require any changes when a part design is active. It’s also likely that it won’t require any UI changes, since the UI layout uses the same toolbar panels as the hybrid design. However, many commands that appear to be modeling-specific also include assembly functionality. A typical example of this is a command that creates new geometry and creates a new component for that geometry. Creating a new component is not supported in a part design because it is an assembly-specific action and will fail.

Assembly – When an assembly design is active, creating features and other modeling operations are not supported and will fail if attempted.

Best Practices to Update Your Add-In

To examine potential problems and solutions, let’s look at one of the samples delivered with Fusion. The previous Spur Gear sample adds a new command to the CREATE panel on the SOLID tab, as shown below. When run, it creates a new local component and adds gear geometry to it. Because only hybrid designs existed in the past, this would always work. Now, there are three design types to consider when writing an add-in that impact both the user interface and the functional capabilities.

Making Your Command Available

You first need to decide which design types your command will support and where in the user interface the command best fits. For the Spur Gear sample, the command was in the CREATE panel, and this will continue to work for both hybrid and part designs. However, if we want the command to be available in an assembly design, it needs to be added to a second location that’s visible when an assembly design is active.

The general rule when adding any command is to determine the most logical location where the user will look for it. For the Spur Gear sample, the INSERT panel seems to make the most sense, since it lets you insert a new component that represents a gear.

There haven’t been any changes to the API related to the user interface, but in some cases Fusion has changed how the UI is laid out, and you need to update your program to conform to the new layout. The Write user interface to a file API Sample program can be used to write out the UI structure to help you understand how to add your command to a specific location. This is also described in the User Manual in the User Interface Customization with Fusion’s API topic.

Supporting Different Design Types

The next step is to determine whether the command is valid across all design types. It will be common for a command to be available only in part or hybrid designs, or only in assembly designs. You control where it’s available by deciding where to put the command button in the user interface.

However, there are some commands that you want available across all three design types. The spur gear command is a good example of this. However, the command needs to behave differently for each design type. For the spur gear sample, this new logic begins in the handler for the commandCreated event. Depending on the design type, the dialog varies slightly.

When executed in a part design, the dialog remains unchanged and includes only the inputs required to define a gear.

For a hybrid design, it adds three new command inputs: a StringValueCommandInput, a ButtonRowCommandInput, and a BoolValueCommandInput. The StringValueCommandInput allows the user to specify the new component's name. Because a hybrid design supports both internal and external components, the command uses the ButtonRowCommandInput to let the user choose which type to create. If they choose to create an external component, the BoolValueCommandInput is displayed. When clicked, it opens a dialog that lets the user select the cloud folder where the new component will be saved.

When executed in an assembly design, the dialog is similar to the hybrid dialog except the new component will always be external, so it doesn't display the ButtonRowCommandInput to let them choose internal or external.

To support working with these new design types, a new property has been added to the API. It is the Design.designIntent property. This property indicates whether the design is a part, assembly, or hybrid design, so you can use this information to apply different logic for each design type.

In addition to this property, two new methods have been added to the API to support these new workflows more fully. The first is the  Occurrences.addNewExternalComponent method. This method is equivalent to interactively using the Create Component command and selecting the option to create an external component, as shown below. When doing this, you need to provide the cloud folder and the file name. This method creates a new occurrence that is an external reference, and the referenced file is in-memory only and not saved to the cloud until the assembly is saved. Using the API, you can access this new component through the created occurrence and add geometry to it. When using the “Create Component” command, the new component is activated in Edit in Place. That does not happen with the API, and “Edit in Place” is not required when using the API to add geometry or edit the new component.

The second new capability is the ability to display a dialog that prompts the user to select a cloud folder. The API already supported selecting a local file or folder and a cloud file, but it lacked support for selecting a cloud folder. Now there is the UserInterface.createCloudFolderDialog method. In the new spur gear dialog, this method is used when the user clicks the “Location” button.

Although the dialog is unchanged, when a part design is active, the command's logic changes. For hybrid and assembly designs, a new local or external component is created for the gear. Because parts don’t support components, this can’t be done in a part design. In this case, the spur gear command now creates the gear geometry directly in the root component of the active part design. The assumption is that the user has a design open that will be a gear, so the command creates the geometry directly within it.

Let’s look at the code needed to handle the creation of the command and the final action when the command is executed. We’ll use a simple command that creates a square block with a single size. For a part design, it creates a new body in the root component. In an assembly design, it creates a new external component and adds the new body to it. For a hybrid design, it gives the user a choice between an external and an internal component and adds the new body to either.

Below is the code that adds the command to the CREATE panel of the SOLID tab for part and hybrid designs.

workspace = ui.workspaces.itemById('FusionSolidEnvironment')

# Add the command to the CREATE panel in the SOLID tab, below the existing Box command.
# This is used for part and hybrid designs.
panel = workspace.toolbarPanels.itemById('SolidCreatePanel')
control = panel.controls.addCommand(cmd_def, 'PrimitiveBox', False)

And here is the result.

Here’s the code to add the button to the INSERT panel in the ASSEMBLY tab so the command is available in an assembly design.

# Add the command to the INSERT panel in the ASSEMBLY tab, below the existing Insert Fastener command.
# This is used for assembly designs.
panel = workspace.toolbarPanels.itemById('InsertAssemblePanel')
control = panel.controls.addCommand(cmd_def, 'FusionFastenersCommand', False)

And here is the result.

The code below creates the command dialog, which differs for hybrid, assembly, and part designs. It uses the Design.designIntent property to determine the currently active design type; the code below applies to a hybrid design. It adds a StringValueInput to get the name to use when creating the new component for the box. It then creates a ButtonRowCommandInput to let the user choose whether to create an external or internal component. It also creates a BoolValueCommandInput that serves as a button to let the user select a cloud folder where the external component will be created. Finally, it adds a separator to distinguish the component definition from the box size input visually.

if des.designIntent == adsk.fusion.DesignIntentTypes.HybridDesignIntentType:
    # Create the dialog for a hybrid design. This includes a string input to get the name
    # of the component, buttons to specifiy if an external or internal component should
    # be created, and if it is external, a button that will allow the user to specify
    # the folder where it will be saved.

    # Add a string input to get the name of the component.
    inputs.addStringValueInput('componentName', 'Part Name', 'Square Box')

    # Add a button row of two buttons to let the user specify a local or external component.
    # The external button is pressed to make it the default setting.
    externalInternalInput = inputs.addButtonRowCommandInput('externalInternal', 'External/Internal', False)
    iconPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'External')
    externalInternalInput.listItems.add('External', True, iconPath)
    iconPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'Internal')
    externalInternalInput.listItems.add('Internal', False, iconPath)

    # Add a Boolean button that will be used to display a dialog to choose a folder where the
    # external component will be saved. The active folder in the data panel is used as the default.
    iconPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'FolderIcon')
    folderButton = inputs.addBoolValueInput('cloudFolder', 'Location', False, iconPath)
    folderButton.text = app.data.activeFolder.name

    # Save the current folder to a global variable.
    folder = app.data.activeFolder

    # Add a separator to the dialog.
    inputs.addSeparatorCommandInput('separator')

To allow the dialog to behave correctly, the following code is used in the InputChanged event handler. When the user clicks a button in the ButtonRowCommandInput, the code checks which button was clicked and hides or displays the BoolValueCommandInput to select a cloud folder. The InputChanged event also handles the case when they click the BoolValueCommandInput and uses the new UserInterface.createCloudFolderDialog method to let the user choose a cloud folder.

# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    if changed_input.id == 'externalInternal':
        # Check the state of the button rows to see if it is internal or external
        # and change the visibility of the button to choose the folder.
        buttonRowInput: adsk.core.ButtonRowCommandInput = inputs.itemById('externalInternal')
        isExternal = buttonRowInput.listItems[0].isSelected

        folderButton = inputs.itemById('cloudFolder')
        if isExternal:
            folderButton.isVisible = True
        else:
            folderButton.isVisible = False
    elif changed_in

---

## Events

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Events_UM.htm

Events in the Fusion API
Events allow you to receive notifications when specific actions occur within Fusion. Events are a crucial component when creating custom Fusion commands. Through events, your program can know that the user clicked the button associated with your command and interact with the user while your command is running (preview, input validation, selection, execute, etc.).

To implement an event, you need to add a "handler" function to your code and connect that handler to the event. Fusion will call your handler function whenever the related action occurs in Fusion that causes the event to fire. Even though the concept of implementing an event is the same, the actual practice differs from one language to another. Therefore, specifics for setting up events are provided in the topics covering each supported language; Python, C++, and TypeScript. In fact, for Python, there is a Fusion library provided to simplify using events. You can read more about it in the topic about the Fusion Python Add-In Template.

One thing to be aware of that can significantly simplify adding support for events is the "Syntax" portion of the help for every event shows example code for the event handler and connecting the handler to the event. You can copy and paste this code from the help, make minor edits to a couple of variable names, and you'll have the event implemented. There are two tabs for Python and one for C++. The reason for the two tabs with Python is that the tab labeled "Python Using fusion360utils" uses a library provided when you create a Python add-in. This library simplifies the implementation of events. The "Python" tab illustrates implementing an event handler without help from an external library.

Some basic concepts apply to all events, regardless of your programming language.

The initial access to an event is through a property on the object that supports the event.  For example, the UserInterface object supports the activeSelectionChanged, commandCreated, commandStarting, and several other events.  These are accessed through properties of the same name on the UserInterface object.  Events are listed in an "Events" section within the help topic of the object, as shown below.

The object returned by the event property is an object that derives from the Event base class. Any object derived from Event supports the "add" method, which you call to connect the event to your handler. Event objects also support the "remove" method to disconnect a handle, they support the "name" property, which returns the name of the event, and they support the "sender" property, which returns the object that is firing the event. For example, the ApplicationCommandEvent object returned by the commandStarting event will return the UserInterface object as the event's sender.

When implementing the handler, the handler type must match the type of event. For example, in the case of the commandStarting event, the event type is ApplicationCommandEvent, and the handler is ApplicationCommandEventHandler. In addition, all handlers support a single method named "notify". The notify method is called by Fusion when the event occurs and by reacting to the notify method, you can handle the event.

The notify method has a single argument that provides an object derived from EventArgs. This object provides information about the event being fired. All objects derived from EventArgs support the firingEvent property, which returns the event object that is firing the event. In this example of the commandStarting event, it will return the ApplicationCommandEvent object. Most objects derived from EventArgs also support other properties that provide additional information specific to that type of event. For example, in the case of the notify method for the commandStarting event, an ApplicationCommandEventArgs object is returned and supports the commandDefinition, commandId, and isCanceled properties specific to application command events. These provide information about which command is starting and allow you to cancel it.

		© Copyright 2026 Autodesk, Inc.

		Comment on this page.

---

## Attributes

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Attributes_UM.htm

Fusion Attributes
Attributes are something that are technically very simple, but they enable the ability to create very sophisticated scripts and add-ins. An attribute is simply the ability to associated named values with a Fusion entity. The named value is saved by Fusion and can be retrieved later, either from the entity it is on or by querying the design.  This doesn't seem like much, but it provides that ability to do some interesting things.

There are two basic low-level capabilities this provides. The first is the ability to name an entity and find it later. The second is adding information to an entity. Here is a simple example that demonstrates both uses.  It's an add-in that provides fly-through capabilities. When first executed, the user is prompted to select a curve that the camera will follow along. They can also specify a couple of other settings. When they click the "Animate" button, the view is animated with the camera following along the selected curve.  Without attributes, the add-in requires the user to re-select the path curve and change the other settings every time they run the command. With attributes, the selected curve can be "named" so when the command is run again it first looks to see if there is a previously selected path and uses it as the default path. Attributes are also used to save the value of the settings so they will become the default settings the next time the command is run.

Let us look in a little more detail at exactly what an attribute is and how you create, query, edit, and delete them.

Creating Attributes
All objects that support attributes have an "attributes" property that returns the Attributes collection associated with that entity. Initially this collection is empty, because by default entities do not have any attributes. To create a new attribute on that entity you use the add method of the Attributes object. Below is an example of adding an attribute where the user selects a face in the model and an attribute is added to the face and assigns the current area of the face as the value.

			Copy Code

# Have a face selected.
selectedFace = ui.selectEntity('Select a face', 'Faces').entity

# Add an attribute to the face.
selectedFace.attributes.add('ADSK-AttribSample', 'FaceArea', str(selectedFace.area))

There are three arguments needed when creating an attribute:

	groupName - The first argument is the group name. This is a string that serves to group all of the attributes you'll create. The group name serves two purposes.  First, it avoids duplicate name problems. All attributes on a specific entity must have a unique name.  For example, the name of the attribute above is 'FaceArea'. If attribute groups did not exist, when another add-in tries to create an attribute called 'FaceArea' on the same face, it will fail because there already is one with that name. Groups eliminate this problem because attribute names are only required to be unique within a group on that entity. Each add-in should use a different group name to allow different add-ins to create attributes with the same name on an entity. The most common use if for you to use the same group name for all attributes that your add-in creates. To ensure uniqueness, it's recommended you use some combination of your company and add-in name as your group name, i.e. "ADSK-FlyThrough".

	The second purpose that an attribute group serves is it provides an easy way to query and find the attributes associated with your add-in, regardless of what entity they're associated with. Querying for attributes is discussed in more detail below, but you can query based on group name which allows you to quickly access all the attributes your add-in has created.

	name - The second argument is the name of the attribute. This can be any string and is typically a name that makes sense to you and describes the data the attribute represents.  It is a similar thought process as to how you name variables in a program.

	value - The third argument is the value of the attribute.  An important thing to notice in the example above is that the value is being converted to a string.  Attribute values are always a string.  There are various libraries available in the different programming languages that let you convert from binary data to text and back again so it's possible to store any kind of data in an attribute.  By using JSON or XML formatting you can also store more complex data into a single attribute.

Getting Existing Attributes
There are two ways to access existing attributes; from an entity and querying.

Attributes from an Entity

You can get any of the attributes that are associated with a specific entity. Getting attributes from an entity is demonstrated in the example below, where a face is selected and then the attribute that was added in the previous example is read and the value is displayed.  If the selected face does not have the specified attribute, a message is displayed to notify the user.

			Copy Code

# Have a face selected.
selectedFace = ui.selectEntity('Select a face', 'Faces').entity

# Get the area attribute from the selected face.
areaAttrib = selectedFace.attributes.itemByName('ADSK-AttribSample', 'FaceArea')

# Check to see if an attribute was returned and display the value.
if areaAttrib:
    ui.messageBox('Original area: ' + areaAttrib.value + ' cm^2')
else:
    ui.messageBox('The selected face does not have the attribute.')

Besides the itemByName property, the Attributes collection also supports the item method that lets you iterate through all the attributes regardless of their group or name.  The Attributes collection also supports the itemsByGroup method that returns an array of all of the attributes on the entity that belongs to a specific group.  And finally, it supports the groupNames property that returns an array of the names of the groups that exist on that entity.

Querying for Attributes
The above technique of getting an attribute from an entity works well when you know which entity contains the attributes you are interested in.  However, that is often not the case.  Even with this simple example, the model could have hundreds or even thousands of faces and the attribute could have been applied to any number of them.  You do not want to have to look to through every face in the design to see if any of them have a particular attribute.  A much more efficient way is to use the findAttributes method of the Design object.  This lets you query the entire design to quickly find any existing attributes.  This is demonstrated in the example below.

			Copy Code

# Find all attributes with a certain name in the design.
attribs = des.findAttributes('attributeSample', 'FaceArea')

# Check the length of the returned array to see if any attributes were found.
if len(attribs) > 0:
    ui.messageBox(str(len(attribs)) + ' FaceArea attributes were found.')
else:
    ui.messageBox('No attributes were found.')

The findAttributes method has two arguments, just like the itemByName method discussed earlier.  However, their use is more flexible with the findAttributes method. They can be used like above to specify the exact name of the group and attribute to find anything that exactly matches, but you can also just specify one or the other and use an empty string to get all.  For example, if you call findAttributes using the code below, it will return all attributes that have the group name "attributeSample".

			Copy Code

attribs = des.findAttributes('attributeSample', '')

And the following will return all attributes named "FaceArea" regardless of their group name.

			Copy Code

attribs = des.findAttributes('', 'FaceArea')

In addition to exact matches, you can also use regular expressions to perform a search. To use a regular expression, you prefix the expression string with "re:".  If you're unfamiliar with regular expressions they can be a bit intimidating at first, but you can think of them as somewhat equivalent to a wild card search, but it's different in how you define the search string.  Regular expressions are more complicated than simple wild card searches but are also much more powerful. There are several good introductions to regular expressions on the web.  Here is one site entirely devoted to regular expressions, http://regexone.com. When using a regular expression, the regular expression much match the full group or attribute name.

Here are a few examples of some common types of searches:
   "re:abc" - Matches if "abc" is the name being searched.
   "re:abc.*" - Matches if "abc" is found at the beginning of the named being searched.  For example, it will match "abc123".
   "re:.*abc" - Matches if "abc" is found at the end of the name being searched.  For example, it will match "Some test abc" but not "abcTest".
   "re:.*abc.* - Match if "abc" is found anywhere in the name being searched.  For example, it will match "abc", "123abc456", and "123 456 abc".

Below is a simple example of how a regular expression search is done. The assumption is that I have written several add-ins that create attributes and they all follow the recommended group naming described above. I have groups "ADSK-FlyThrough", "ADSK-MeshCut", "ADSK-AttribSample", "ADSK-SpurGear", etc. and now I want to find all of the attributes that any of my add-ins have created and delete all of them.  The obvious similarity between all of the attributes is the company portion of the group name. The code below uses a regular expression to find all of my attributes and deletes them.  It uses an empty string as the attribute name to match all names.

			Copy Code

# Find all attributes whose group name begins with "ADSK".
attribs = des.findAttributes('re:ADSK.*', '')

# Delete all of the found attributes.
for attrib in attribs:
    attrib.deleteMe()

Getting the Associated Entity
The findAttributes method returns an array of Attribute objects.  Frequently what you really want is the entity that the attribute is attached to.  This is where attributes serve as a mechanism of naming an entity so you can find it later.  If you have an Attribute object, you can get the entity it is attached to by using its "parent" property.

Something that might seem a little odd at first is that it is possible to get an attribute whose parent entity no longer exists.  In that case, calling the parent property will return null. One example of where you can get an unattached attribute is in the case of B-Rep entities (faces, edges, and vertices of a model). When an attribute is created on a B-Rep entity it is never automatically deleted because the lifetime of that entity is unknown.  For example, if you add an attribute to an edge and then the edge is filleted, that edge is consumed and no longer exists in the model and the parent property of the attribute will return null. However, it's possible that the edge can come back in the future; the fillet can be deleted or suppressed and then the parent property of the attribute will return the edge. Because attributes can exist without an owner, it's important to always check the return value of the parent property to verify that you did get back an entity.

Attribute Usage Examples
How you apply the use of attributes is almost as varied as there are programs that use them. To better understand their potential, let us look closer at the previous fly through example add-in.

This add-in uses attributes for two purposes, attaching an ID to an entity to find it later (naming), and saving custom data.  The entity it wants to remember is the path curve that the user selected.  It does this by adding using the code below to add an attribute to the selected curve. The group name is "ADSK-FlyThrough", the attribute name is "pathCurve", and the value is an empty string because it's not needed in this case.  When the command is invoked, it used the findAttributes method to get the attribute, if it exists. If it exists it pre-populates the selection in the command dialog when the command is executed.

pathCurve.attributes.add('ADSK-FlyThrough', 'pathCurve', '')

Because the user can choose a different curve as the path, the old attribute also needs to be removed from the old curve.  The following is a small function that uses the functionality discussed previously to see if the attribute name already exists on the entity and if it does it does nothing but if it doesn't it deletes attributes of the same name of from any other entities and then adds the attribute to the new curve.

			Copy Code

# Function that adds an attribute to an entity if it doesn't already exist,
# and it removes any attributes with the same name from any other entities
# so that only one entity can have an attribute with this name at a time.
def addSingleName(design, entity, groupName, attributeName):
    attrib = entity.attributes.itemByName(groupName, attributeName)
    if not attrib:
        # Get any existing attributes with this name and delete them.
        oldAttribs = design.findAttributes(groupName, attributeName)
        for oldAttrib in oldAttribs:
            oldAttrib.deleteMe()

        # Add the attribute to the specified entity.
        entity.attributes.add(groupName, attributeName, '')

In addition to using attributes to name the path curve, the add-in also saves the other settings as attributes on the Design object. It saves them there instead of an entity because it is general information that's not associated with a particular entity. This is demonstrated in the code below where the up direction and smoothness values are saved.  Remember that attributes values are always strings so other values need to be converted to a string first.  If you call the add method and an attribute with the same name already exists, it results in updating the value of the existing attribute.

			Copy Code

des.attributes.add('sampleCameraAnimate', 'upDir', upDir)
des.attributes.add('sampleCameraAnimate', 'smoothness', str(smoothness))

An alternative that can be more efficient in some cases is to combine all of your data into a string and save it in a single attribute. You can use JSON or XML or any other string-based format to save the data.  The example below demonstrates concatenating the values together with a known delimiter.  The string can be parsed when it is read later to extract the individual values. Creating multiple attributes or using a single attribute are both viable options and choosing one over the other is primarily based on what's the most convenient for your specific case.  Keeping the data in separate attributes can make updating individual values easier, while combining it into a single attribute lets you easily store complex data and is more efficient.

			Copy Code

attribValue = upDir + '|' + str(smoothness)
des.attributes.add('sampleCameraAnimate', 'settings', attribValue)

		© Copyright 2026 Autodesk, Inc.

		Comment on this page.

---

## Selection Filters

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SelectionFilters_UM.htm

Selection Filters

When using the API to have the user select an entity you can specify which type(s) of entities are valid to be selected.  For example, when using the selectEntity method of the UserInterface object the second argument is the selection filter.  Also when performing selections using in a custom command using the SelectionCommandInput object you can define a filter to specify which type(s) of entities are selectable.  The selection filter is a string.  The complete list of all valid selection filter strings are listed below.

              Filter String

              Description

        Bodies
        Select BRepBody entities (both solid and surface).

        SolidBodies
        Select solid BRepBody entities.

        SurfaceBodies
        Select open (surface) BRepBody entities.

        MeshBodies
        Select mesh bodies.

        Faces
        Select BRepFace entities of any shape on solid and surface BRepBody objects.

        SolidFaces
        Select BRepFace entities of any shape on solid BRepBody objects.

        SurfaceFaces
        Select BRepFace entities of any shape on surface BRepBody objects.

        PlanarFaces
        Select planar BRepFace entities.

        CylindricalFaces
        Select cylindrical BRepFace entities.

        ConicalFaces
        Select conical BRepFace entities.

        SphericalFaces
        Select spherical BRepFace entities.

        ToroidalFaces
        Select toroidal BRepFace entities.

        SplineFaces
        Select spline (NURBS) BRepFace entities.

        Edges
        Select BRepEdge entities of any shape.

        LinearEdges
        Select linear BRepEdge entities.

        CircularEdges
        Select circular BRepEdge (circles and arcs) entities.

        EllipticalEdges
        Select elliptical BRepEdge (full ellipses and elliptical arcs) entities.

        TangentEdges
        Select a BRepEdge that connects faces that are tangent along that edge.

        NonTangentEdges
        Select a BRepEdge that connects faces that are not tangent along that edge.

        Vertices
        Select BRepVertex entities.

        RootComponents
        Select root Component objects.

        Occurrences
        Select Occurrence objects.

        Sketches
        Select Sketch objects.

        SketchConstraints
        Selects sketch geometric and dimensions constraints.

        Profiles
        Select profiles.

        Texts
        Select sketch text.

        SketchCurves
        Select any shape of sketch entity.

        SketchLines
        Select SketchLine entities.

        SketchCircles
        Select SketchCircle entities.

        SketchPoints
        Select SketchPoint entities.

        ConstructionPoints
        Select ConstructionPoint entities.

        ConstructionLines
        Select ConstructionLine entities.

        ConstructionPlanes
        Select ConstructionPlane entities.

        Features
        Select any type of feature.

        Canvases
        Select canvases.

        Decals
        Select decals.

        JointOrigins
        Select joint origins.

        Joints
        Select joints.

		© Copyright 2026 Autodesk, Inc.

		Comment on this page.

---

## Custom Graphics

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CustomGraphics_UM.htm

Using Custom Graphics

Custom Graphics Overview
Object Model
Triangle Meshes
Line Graphics
Point Graphics
Text Graphics
B-Rep Body Graphics
CurveGraphics
Graphics Colors
   Solid Color Effect
   Basic Material Color Effect
   Appearance Color Effect
   Vertex Color Effect
   Show Through Color Effect
Additional Graphics Behaviors
   Orientation
   Size
   Combining Orientation and Size
   Position

Custom Graphics Overview
A key part of the Fusion user interface is the graphics window where you see and interact with the model and other graphical information. When using Fusion interactively or through the API, you create things like features and sketch entities and a side effect of their creation is that they’re displayed in the graphics window. The creation and display of the graphics that represent the geometry are automatically handled by Fusion. However, there are cases when you want to show something in the graphics window that is not a standard Fusion entity.  This is typically used in more advanced applications but can also be useful in smaller, simple applications too.

For example, if you are integrating an electromagnetic field simulator application into Fusion, there are symbols and analysis results you’ll want to display to the user that are different from any of the standard Fusion geometry. Or maybe you have an interesting manufacturing process that requires that you label each face. The Fusion API supports the ability to draw custom graphics in the graphics window.  These custom graphics display along with the other Fusion graphics but to Fusion they’re just “graphics” without any meaning. It’s your add-in that understands what those graphics represent and provides the expected behavior.  Below is a detailed description of the custom graphics functionality supported by the Fusion API.

When working with most of the Fusion API you can draw parallels between using the API and how you would use the user interface to do the same thing interactively.  For example, creating an extrusion has very many similarities between the UI and the API.  The custom graphics portion of the Fusion API is a completely new concept that doesn’t have any parallels in the user interface.  With custom graphics, you’re defining graphics primitives in the same way that the Fusion core does to draw the high-level objects.  For example, when you draw a solid box using Fusion you see a solid cube in the graphics window and can interact with the faces and edges.  Internally, Fusion draws the graphics that represent the box using 12 triangles (2 for each face) and 12 lines (1 for each edge).  Fusion then maps these low-level graphics to the higher-level object that the user understands. When using custom graphics, you’ll also be drawing low-level graphics to represent objects in your application that you want the user to see and interact with.

If you’ve not worked with any low-level graphics before there is a somewhat steep learning curve.  If you’ve programmed graphics before using something like DirectX, OpenGL, or WebGL many of these concepts will already be familiar.

There are several types of custom graphics objects that can be drawn.  These are points, lines, triangles, B-Rep bodies, and curves.  Triangles, lines, and points are the low-level graphics and the other types are a higher level, more intelligent graphics that make some workflows much easier.  We’ll begin with a discussion of the primitive types first.

Custom Graphics Object Model

Before getting into the details of creating and using custom graphics, here’s an overview of the object model that supports them.  The first thing to notice is that you access the custom graphics related objects through the Component object.  In most cases, this will be the root component but it can be any component.

From the Component object, you access the CustomGraphicsGroups object. This collection is initially empty because by default a component doesn’t contain any custom graphics.  You can create a new CustomGraphicsGroup object using the add method of the CustomGraphicsGroups collection object. From the CustomGraphicsGroup object, you can now create custom graphics of various types and they will all be contained within this group.  A CustomGraphicsGroup object can also contain other CustomGroupsGroup objects so it’s possible to build up a hierarchical structure of graphics.

All of the graphics types are derived from CustomGraphicsEntity which supports all of the general capabilities that all custom graphics support like color, visibility, depth priority, selectability, etc.  In fact, a CustomGraphicsGroup is also derived from the CustomGraphicsEntity object and supports the same capabilities.

The various types of graphics and the capabilities they support are described in more detail below.

Triangle Meshes
Most of the graphics you typically see when looking at a Fusion design are made up of triangles. Internally, when doing solid, surface, and T-Spline modeling, the model is mathematically exactly represented using smooth surfaces.  For example, a solid cylinder is defined using a cylinder and two planes but this can’t directly be displayed by the graphics card so Fusion automatically calculates a triangle mesh representation of the model and uses that for the display. The underlying mathematically exact model is unchanged and that’s what you continue to use for modeling but you’re looking at the triangle mesh version of the model.  It doesn’t look like a triangle mesh because there are enough triangles that it looks smooth and the graphics system applies lighting in a way so you don’t see flat triangles but instead it appears smooth. Fusion will also create more or fewer triangles depending on how closely you’re zoomed into the model.  This is referred to as “Level of Detail” or “LOD”.  When zoomed out, cylinders that represent holes might be displayed using a few triangles so the opening of the hole could actually be an octagon but because it’s so small you can’t tell and it looks circular.  If you zoom in, Fusion will create a new triangle mesh from the model with more triangles so the edge of the hole continues to look circular.

Let’s look at some of the basic concepts of custom graphics using triangles as an example.  You access the custom graphics functionality using the CustomGraphicsGroups collection object which you can get from a Component object. The code below creates a new CustomGraphicsGroup object on the root component.  You won’t see any changes in the graphics window because the new group is empty until graphics entities are defined.

# Create a graphics group on the root component.
graphics = root.customGraphicsGroups.add()

Triangle Mesh Coordinates

To fully define a triangle mesh you need to provide several pieces of data.  The first and most obvious is the set of points that define the corners of the triangle.  In this example, we’ll create a mesh made up of two triangles that will end up looking like a 10cm x 6cm rectangular plane.

A triangle is defined by three points and because there are two triangles the above mesh requires the definition of 6 points.  Below is a slightly more complex mesh that contains 5 triangles and as a result needs 15 points.  But as you can see in both cases, this seems somewhat wasteful because some of the points are used by more than one triangle.  In the first example, there are just four unique points to define the two triangles.  In the second there are just seven unique points to define the 5 triangles.

Graphics systems allow for the re-use of the points by using an index into the list of coordinate points.  It might appear complex at first but let’s look at the rectangle example to see how it’s used.  Below on the left, is a picture showing the points and the resulting triangles.  The table on the left is a list of the coordinates. The points are defined as a list of X,Y,Z coordinates and each coordinate has an index number based on its position within the list. The table on the right is a list of index values which is a list of integers where each set of three sequential numbers indicates which points in the point list to use to draw the triangle.  The first three numbers are 0, 1, and 2 which indicates that coordinates 0, 1, and 2 are used to draw triangle A.  The next three numbers are 0, 2, and 3 which draws triangle B.

Now let’s look at this with the more complex mesh. The list of points contains 6 coordinates and the list of indices contains 15 values, three for each triangle. You can see how in this case the point as index 0 is used by all the triangles and points 2, 3, 4, and 5 are each used by two triangles.

Even though creating a mesh by specifying an index list is the most efficient way to define a mesh, it's not required.  If you pass in an empty array for the index list, the API will assume that you want to use each of the coordinates in the order they exist in the coordinate list.

Triangle Mesh Normals

There’s also another piece of information that’s needed to correctly render a triangle mesh; the mesh normal vectors.  The normals define how light is reflected off the mesh.  Without any lighting, a model would be all the same color without any shading, as shown below.  As you can see, without lighting and shading it’s not possible to understand the internal shape of the model because all you can see is the filled silhouette of the part.

When creating a triangle mesh you specify a normal vector for every triangle point.  Typically, the normal vectors represent the true surface normal at that point on the smooth surface the mesh is representing.  Below on the left is a partial cylinder.  The next picture is a coarse mesh of the surface with the normals defined so each triangle facet is shaded as a plane.  And the third picture uses the same mesh as the middle mesh but with the normals oriented using the cylinder normals.  All three have the same appearance assigned to them.  Notice that even though the last one is a very coarse mesh, that the lighting and the chrome appearance is still very close to the original smooth cylinder because the angle that the light reflects off the triangle changes across the face of the triangle.  However, in the middle picture the triangle has a solid color because the lighting is the same across the entire triangle.

Below is a picture that illustrates the top view of the middle and right pictures above.  The black lines are the triangles, the green lines are the vectors used, and the red is the original cylinder.  On the picture on the left, you can see that the normal vectors are perpendicular to the face of each triangle.  However, on the picture on the right, the normals are not perpendicular to the triangles but are instead perpendicular to the cylinder at the point where the triangle vertex touches the cylinder.  The normals for a specific triangle are not all the same like they are on the left.  This results in the lighting changing how it reflects off the triangle as it moves across the triangle because it varies from one normal to the other across the triangle.

Defining normals is similar to how the triangle coordinates are defined, as described above, except instead of a list of points you have a list of vectors.  You still use an index list to index into the list of normals.  You define a normal for each triangle vertex.  The normals are assigned in the same order as you assigned the vertex coordinates.

The example below puts this all together to draw a pyramid shape made up of four triangles.  In this case, we want it to look like a pyramid with flat sides so the normals are drawn so they are perpendicular to each of the triangles.  Below is a top view of the pyramid with each of the vertices and triangles labeled. You can also see that the model origin is at the lower-left corner and positive X is to the right, Y is up and Z is towards you.

import adsk.core, adsk.fusion, traceback
import math

def run(context):
    try:
        des = adsk.fusion.Design.cast(_app.activeProduct)
        root = des.rootComponent

        # Check to see if a custom graphics groups already exists and delete it.
        if root.customGraphicsGroups.count > 0:
            root.customGraphicsGroups.item(0).deleteMe()
            _ui.messageBox('Deleted existing graphics.')
            _app.activeViewport.refresh()
            return

        # Define the size of the pyramid.
        pyramidSize = 10
        pyramidWidth = math.sqrt(pyramidSize**2 - (pyramidSize/2)**2)
        pyramidHeight = 6

        # Create a graphics group on the root component.
        graphics = root.customGraphicsGroups.add()

        # Create graphics coordinates for the four points used to define the triangles.
        # An array of the x,y,z components of the coordinates is first defined and then
        # that is passed into the CustomGraphicsCoordinates.create method to create
        # the graphics coordinates.
        coordArray = [0, 0, 0,
                      pyramidSize, 0, 0,
                      pyramidSize/2, pyramidWidth, 0,
                      pyramidSize/2, pyramidWidth*(1/3), pyramidHeight]
        coords = adsk.fusion.CustomGraphicsCoordinates.create(coordArray)

        # Create the index list to define how the coordinates are connected
        # into the four triangles.
        vertexIndices = [0,1,2, 0,1,3, 1,2,3, 2,0,3]

        # Create the triangle normal vectors. This creates vectors along two of the
        # edges of each triangle and then uses the vector crossproduct function to
        # calculate the normal vector.
        vec1 = coords.getCoordinate(0).vectorTo(coords.getCoordinate(1))
        vec2 = coords.getCoordinate(0).vectorTo(coords.getCoordinate(3))
        normal1 = vec1.crossProduct(vec2)

        vec1 = coords.getCoordinate(1).vectorTo(coords.getCoordinate(2))
        vec2 = coords.getCoordinate(1).vectorTo(coords.getCoordinate(3))
        normal2 = vec1.crossProduct(vec2)

        vec1 = coords.getCoordinate(2).vectorTo(coords.getCoordinate(0))
        vec2 = coords.getCoordinate(2).vectorTo(coords.getCoordinate(3))
        normal3 = vec1.crossProduct(vec2)

        normals = [0,0,-1,
                   normal1.x, normal1.y, normal1.z,
                   normal2.x, normal2.y, normal2.z,
                   normal3.x, normal3.y, normal3.z]

        # Create the index list to define how the normals are assigned to the vertices.
        normalIndices = [0,0,0, 1,1,1, 2,2,2, 3,3,3]

        # Create the mesh.
        mesh = graphics.addMesh(coords, vertexIndices, normals, normalIndices)

        # Refresh the graphics.
        _app.activeViewport.refresh()
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

Even though it's best for you to define the normals for a mesh it's not required.  If you pass in  empty arrays for the normals and the normal index list, the API will automatically create normals that are perpendicular to each triangle to create a result similar to that shown in the middle picture of the three partial cylinder meshes above.

Line Graphics

Line graphics provide the ability to draw lines.  At the low level, all wireframe graphics displayed on the screen is displayed as lines.  Smooth curves, including circles, are also drawn using lines but the curves are approximated with enough lines that it looks like a smooth curve.  Fusion also uses levels of detail with curves just as it does with surfaces. It might create multiple representations so that as you zoom in and out it can show the level of detail to make the curve look smooth.

Line graphics are defined in a very similar way to how triangles are defined, as described above.  You have a list of points and a separate index list that indexes into the list of points.  Each pair of index values defines a line. To draw a rectangle will require 8 indices, two for each of the four lines.

The code below can be added to the tr

---

## Commands

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Commands_UM.htm

Creating Custom Fusion Commands

Command Overview
Command Features
   Transactions
   Scripts and Commands
   Command Dialogs
   Command Inputs
   Execute Event
   InputChanged Event
   ValidateInputs Event
   ExecutePreview Event
   Activate, Deactivate, and Destroy Events
   SelectionEvent Event
   Mouse and Keyboard Events

Command Overview
Fusion has a well-defined concept of what a command is. At a high level, a command is exactly what you would expect; a user clicks a command button to execute it, a dialog guides them through the process of collecting the required input, it often provides a preview of the expected result, and then it creates the final result, which can be undone.

Both scripts and add-ins can create commands but most commonly they are created by add-ins. There are cases where you might want to take advantage of some of the command functionality within a script too, which is discussed later. The reason that commands are used more with add-ins is because an add-in can be automatically loaded when Fusion is started and as part of the loading process they can add buttons for their commands into the Fusion user-interface, making the commands much easier for the user to access. The user can now execute the custom command by clicking the button, just as they do for any other Fusion command. A user executes a script through the Scripts and Add-Ins command, so it's not as convenient to execute a command implemented by a script.

An add-in is typically run automatically by Fusion at start-up where in the run function of the add-in you create a command definition. This is exactly what the name implies; it's the definition of a command. A command definition primarily defines how the command will look in the user-interface. For example, the most common type of command definition is a button and it defines all of the information needed to display a button in the user-interface; the icon, tool tip, enabled state, visibility, etc.). In addition to a button, there are also other types of command definitions that are used to create other types of controls you see in the user interface; a single check box, list of radio buttons, check boxes, and text. These are all described in more detail in the User Interface Customization topic.

Once the command definition has been created, you then use it to create a button in the user interface by defining a location in the user interface and providing the command definition.  The new button references the command definition to get the information it needs to displays itself, (icon, tool tip, etc.). This is also discussed in the User Interface Customization topic.  The add-in now runs passively in the background waiting for the button to be clicked and then responds appropriately.

Any command (standard Fusion or API created commands) can be run by the user clicking a button or by a program calling the command definitions execute method.  In either case, Fusion creates a new Command object and fires the commandCreated event where it passes the Command object to your add-in.  Your add-in reacts to this event by connecting to other command related events and defining the contents of the command dialog, if it has one.

Below is the full Python code for a basic add-in that does the bare minimum for a command that doesn't have a dialog. The result of this command is very simple in that it just displays a message box but it could do anything in the execute event.  There are a few important things to notice in the program:

In the run function it creates a command definition.  (See the topic on User Interface Customization for more information on defining the icon, which is specified in the fourth argument to the addButtonDefinition method.)
In the run function it adds a button into the main toolbar to allow the user to run the command.

It implements a handler for the CommandCreated event, (the SampleCommandCreatedEventHandler class in this example).
In the run function it connects the handler to the CommandCreated event.
It implements a handler for the execute event, (the SampleCommandExecuteHandler class).
In the handler for the CommandCreated event it connects the execute event handler to the execute event.
The add-in performs whatever the final action of the command is within the execute event handler.
In the stop function it cleans up the user interface by deleting the control from the user-interface and deleting the command definition.

Basic Add-In Command (Python)
import adsk.core, adsk.fusion, adsk.cam, traceback

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Get the CommandDefinitions collection.
        cmdDefs = ui.commandDefinitions

        # Create a button command definition.
        buttonSample = cmdDefs.addButtonDefinition('MyButtonDefIdPython',
                                                   'Python Sample Button',
                                                   'Sample button tooltip',
                                                   './Resources/Sample')

        # Connect to the command created event.
        sampleCommandCreated = SampleCommandCreatedEventHandler()
        buttonSample.commandCreated.add(sampleCommandCreated)
        handlers.append(sampleCommandCreated)

        # Get the ADD-INS panel in the model workspace.
        addInsPanel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')

        # Add the button to the bottom of the panel.
        buttonControl = addInsPanel.controls.addCommand(buttonSample)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler for the commandCreated event.
class SampleCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        cmd = eventArgs.command

        # Connect to the execute event.
        onExecute = SampleCommandExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)

# Event handler for the execute event.
class SampleCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # Code to react to the event.
        app = adsk.core.Application.get()
        ui  = app.userInterface
        ui.messageBox('In command execute event handler.')

def stop(context):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Clean up the UI.
        cmdDef = ui.commandDefinitions.itemById('MyButtonDefIdPython')
        if cmdDef:
            cmdDef.deleteMe()

        addinsPanel = ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')
        cntrl = addinsPanel.controls.itemById('MyButtonDefIdPython')
        if cntrl:
            cntrl.deleteMe()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

Command Features
There are several features of a command that your add-in or script can take advantage of. The simple example above takes advantage of the ability to add a button to the user-interface and have the user execute the associated command. This capability is typically used by add-ins. A capability that is very useful for both add-ins and scripts, and that's not shown in the code above, is that any creation or edits that are done within the execute event handler are automatically grouped into a single transaction. This means that you can perform multiple creation and edit operations within the execute handler but the user will be able to undo all of it with a single undo operation. Also, the undo list will show the name of the command as the operation to be undone, as shown below.

Transactions
As described above, everything you do in the execute event handler is bundled within a single transaction and can be undone with one undo. This capability is a big reason to use a command within a script. Without this, every API call that causes a change within Fusion will show up as a separate operation in the undo list. For example, if you write a simple script that draws three lines to create a triangle in a sketch, there will be three operations listed in the undo list and the user will need to run the Undo command three times to revert the process. However, if you call that same code that draws the three lines from the execute event handler, there will be a single operation in the undo list and a single undo will revert all of the changes.

Scripts and Commands
As mentioned before, it's possible for a script to create a command but because a script is run from the Scripts and Add-Ins command, it doesn't create a button in the user-interface so the command definition can't be executed by the user clicking a button.  For a script to use a command, it still creates a command definition like an add-in but it executes the command itself by calling the command definition's execute method, which starts the command process.

Below is a simple script example that demonstrates how this is done. Most of the code is similar to the add-in code above except it's missing the user interface code and it does two additional things, which are highlighted in yellow in the code below. First, it calls the execute method of the command definition it just created.  Second, it sets a property to stop the script from automatically terminating. By default, a Python script will automatically terminate after the run function is finished. This is unique to Python scripts. When running a command from a script, the script needs to continue running so that it can handle the command related events. In the handler for the execute event it calls the terminate method to finally terminate the script.

Basic Script Command (Python)
import adsk.core, adsk.fusion, adsk.cam, traceback

# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Get the CommandDefinitions collection.
        cmdDefs = ui.commandDefinitions

        # Create a button command definition.
        buttonSample = cmdDefs.addButtonDefinition('SampleScriptButtonId',
                                                   'Python Sample Button',
                                                   'Sample button tooltip')

        # Connect to the command created event.
        sampleCommandCreated = SampleCommandCreatedEventHandler()
        buttonSample.commandCreated.add(sampleCommandCreated)
        handlers.append(sampleCommandCreated)

        # Execute the command.
        buttonSample.execute()

        # Keep the script running.
        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler for the commandCreated event.
class SampleCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        cmd = eventArgs.command

        # Connect to the execute event.
        onExecute = SampleCommandExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)

# Event handler for the execute event.
class SampleCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # Code to react to the event.
        app = adsk.core.Application.get()
        des = adsk.fusion.Design.cast(app.activeProduct)

        if des:
            root = des.rootComponent
            sk = root.sketches.add(root.xYConstructionPlane)
            lines = sk.sketchCurves.sketchLines
            l1 = lines.addByTwoPoints(adsk.core.Point3D.create(0,0,0),
                                      adsk.core.Point3D.create(5,0,0))
            l2 = lines.addByTwoPoints(l1.endSketchPoint,
                                      adsk.core.Point3D.create(2.5,4,0))
            l3 = lines.addByTwoPoints(l2.endSketchPoint, l1.startSketchPoint)

        # Force the termination of the command.
        adsk.terminate()

def stop(context):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Delete the command definition.
        cmdDef = ui.commandDefinitions.itemById('SampleScriptButtonId')
        if cmdDef:
            cmdDef.deleteMe()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

In the execute event handler of the script above, it creates a new sketch and draws three lines.  Because this creation is done in the execute event handler they're grouped into a single transaction and the undo command shows a single operation with the title of the command name, as shown below.  Because we didn't assign an icon to the command definition, it's using a default icon in the undo list.

Command Dialogs
A command dialog is displayed whenever you create any command inputs within the commandCreated event.  This is discussed in more detail below.  A standard command dialog displays a vertical stack of command inputs, along with OK and CANCEL buttons.  Below is the command dialog for the Fillet command.  It contains several types of inputs to get the necessary information from the user.

By default, the position and width of the dialog is the shared by all commands and the height is automatically set based on the number of command inputs.  This means if the user runs a command and moves or resizes the command dialog the next command will display in the same location and have the same width.  In general it's best for your command to have this same behavior to have consistency between commands.  However there are cases when you need specific behavior.  Using the setDialogInitialSize, you can override the default and specify the size for your dialog.  However, if the user changes the size, Fusion will remember the change and that will become the new default initial size for your dialog.  There is also the setDialogMinimumSize that lets you specify the minimum size your dialog can be resized to.  These settings only apply to your dialog and do not affect any other commands.

There is also some other customization you can do to on the dialog.  You can use the isOKButtonVisible property of the Command object to specify if the OK button should be shown or not.  You can also specify your own text for the OK and CANCEL buttons using the cancelButtonText and okButtonText property of the Command object.  Overriding the OK button text is demonstrated below.

Command Inputs
In the previous samples, nothing was done in the commandCreated event except for connecting to the execute event. This is ok for a command that doesn't need to interact with the user but most commands need to get additional information from the user through the use of a dialog. The primary use of the commandCreated event is to define the contents of the dialog associated with the command. This is done by creating command inputs using the Command object that Fusion created and passes to you through the commandCreated event handler. If you create any command inputs, a command dialog is displayed with the created command inputs. The execute event is fired when the user clicks the OK button on the dialog. The OK button isn't enabled until the user has provided valid input to the command inputs. You can use the information collected by the command inputs to do whatever the command is supposed to do. A complete list of the different types of command inpu

---

## Command Inputs

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CommandInputs_UM.htm

Command Inputs

AngleValueCommandInput
BoolValueCommandInput
BrowserCommandInput
ButtonRowCommandInput
DirectionCommandInput
DistanceValueCommandInput
DropDownCommandInput
FloatSliderCommandInput and FloatSliderListCommandInput
FloatSpinnerCommandInput
GroupCommandInput
ImageCommandInput
IntegerSliderCommandInput and IntegerSliderListCommandInput
IntegerSpinnerCommandInput
RadioButtonGroupCommandInput
SelectionCommandInput
StringValueCommandInput
TabCommandInput
TableCommandInput
TextBoxCommandInput
TriadCommandInput
ValueCommandInput

Command inputs are used in command dialogs to get input from the user.  Simple commands don't always need a command dialog, and if they do require some input, you can gather the input in other ways. For example, a message box can get a yes/no answer to a question, but most commands need to get several user inputs before performing whatever actions they do. An important part of Fusion's command machinery is support for getting various types of input from the user. Examples of this can be seen in almost all of Fusion's commands. For example, when the Loft command is run, the dialog below is displayed to gather the required input.

A command dialog consists of a list of command inputs. In the loft command, there is a selection input to select the profiles, two Boolean inputs, one for chain selection and one to specify if the result will be closed, and a drop-down input to get the operation type. Fusion supports many different types of command inputs, and the API currently supports a subset that you can use in your commands. Support for additional input types will continue to be added in future releases.

Below are descriptions of the different command inputs the API currently supports.

AngleValueCommandInput

A AngleValueCommandInput displays as a value input on the command dialog and displays as a widget in the graphics window that the user can drag to set the value. Fusion's commands commonly use this specific command input.  For example, it is used to specify the taper angle of an extrusion or the sweep angle of a revolve feature.

Command inputs that also have associated graphical widgets are usually first set to be invisible or disabled. Then once enough information has been gathered to define their position and orientation in space, their isVisible or isEnabled properties are toggled to make them visible. Making them invisible or disabled also hides the associated graphical widget.

BoolValueCommandInput

A BoolValueCommandInput is used to get a True or False response from the user.  You can create four different visual styles depending on the arguments specified when the command input is created.  The four styles are shown below; a check box, a button with an icon that changes states between pressed and unpressed, a button with an icon that doesn't change states but can be clicked, and a button with text that doesn't change states but can be clicked. The fifth example below is the same as the fourth except the isFullWidth property has been set to True, which turns off the text to the left and only leaves the button, centered on the dialog.

Here are the values of the arguments in the addBoolValueInput method to achieve the different results shown above.

    Type
    isCheckBox
    resourceFolder

  Checkbox
    True
    Empty String

  Button with icon and states
    True
    folder containing the icon images

  Click button with icon
    False
    folder containing the icon images

  Click button with text
    False
    Empty String

BrowserCommandInput

A BrowsersCommandInput is used to render HTML as one of the inputs in a dialog. You can think of this like any other command input, but instead of a pre-defined widget, it is a placeholder for a browser that displays the contents of a specified HTML file. Because the content is defined using HTML, you're open to displaying anything you want.

The picture below is a simple example where two BrowserCommandInputs have been added to the command dialog. BrowserCommandInputs behave like other command inputs in that they are displayed in the same sequence they were created, and they have a name displayed on the left with the browser on the right. The first BrowserCommandInput looks very similar to a textbox command input but adds a button beside the text field.

The second BrowserCommandInput demonstrates creating a table that is difficult with standard command inputs. It is possible to use a TableCommandInput to display tabular data, but the TabCommandInput is used to arrange other command inputs, not to display data. With a BrowserCommandInput, a table is easily defined in HTML. Notice that in this case, it doesn't have a name to the left. All command input types can expand to the entire width of the dialog by setting their isFullWidth property to True.

Displaying HTML is useful, but it's more helpful if your add-in and the HTML can interact. For example, it is possible for your add-in to send data to the HTML and for the HTML to send data to your add-in. For more details about the BrowserCommandInput see the user manual topic on Palletes and Browser Inputs.

ButtonRowCommandInput

A ButtonRowCommandInput displays a row of buttons, where the user can choose one or more.  In the first example below, the isMultiSelectEnabled property is true, allowing the user to select more than one button.  In the second example it is false so only one button can be selected.  In the second case, selecting another button deselects the currently selected button.

DirectionCommandInput

A DirectionCommandInput displays as a button on the command dialog and also displays an arrow in the graphics window that the user can change the direction of.  This is used to let the user choose a positive or negative direction.

Command inputs that also have associated graphical widgets are usually initially set to be invisible and then their isVisible property is toggled once the user has specified other required input and you have enough information to define the location and direction of the graphical widget.

DistanceValueCommandInput

A DistanceValueCommandInput displays as a value input on the command dialog and also displays an arrow in the graphics window that the user can drag to set the value. This specific command input is very commonly used by Fusion's commands.  For example, to specify the depth of an extrusion or the offset distance of a construction plane.

Command inputs that also have associated graphical widgets are usually initially set to be invisible or disabled and then their isVisible or isEnabled property is toggled once the user has specified other required input and you have enough information to define the location and direction of the graphical widget.  Making the input invisible or disabled will also hide the associated graphical widget.

DropDownCommandInput

A DrowDownCommandInput is used to get a choice of zero or more selections from a user.  Depending on settings and the style of drop-down, the user can select multiple items or may be restricted to selecting a single item from the list.  There are four styles of drop down inputs, which are each shown below.

The first drop down style displays a list with check boxes where the user can check and uncheck any combination of items in the list.  This is defined by setting the drop down style to DropDownStyles.CheckBoxDropDownStyle. No icons are used for this style.

The second drop down style displays a list of items with an icon where the user can select one item from the list and the selected item is shown.  This is defined by setting the drop down style to DropDownStyles.LabeledIconDropDownStyle and specifying an icon for each item in the list.

Fusion uses this type of control in many of its commands as can be seen here in the Extrude command dialog where the Direction, Operation, and Extents are all inputs of this type.

There is also a variation of this type of drop down where radio button is displayed instead of an icon.  This happens if you don't define an icon for an item in the list.

The third drop down style displays a list of items as text only.  This is defined by setting the drop down style to DropDownStyles.TextListDropDownStyle.  No icons are used for this style. This style of drop down is useful when displaying a dynamic list where the contents can change.  For example, Fusion uses this to get the font selection in the Text command when placing text in a sketch.

FloatSliderCommandInput and FloatSliderListCommandInput

The FloatSliderCommandInput and the FloatSliderListCommandInput are used to get one or two floating point numbers within a defined range from the user.  There are several options that change how it is displayed and how it behaves.  The various options are illustrated in the picture below; a single slider with a value spin control, text instead of the spin control, and two sliders to define a value range.  The FloatSliderListCommandInput defines a list of valid values so that the slider can only select one of the pre-defined values.

FloatSpinnerCommandInput

The FloatSpinnerCommandInput is similar to a value input except it has a "spinner" to the right of the edit field where the user can enter a value using the keyboard or they can click the up or down arrows to increment or decrement the value by a predefined amount.

GroupCommandInput

The GroupCommandInput allows you to group a set of command inputs.  The group can be expanded and collapsed by clicking the triangle to the left of the group label. The picture below contains two groups.  The first group, "Expanded Group", is expanded and contains two command inputs.  The second group, "Collapsed Group", is collapsed so it's command inputs are not visible.  This input can be useful in more complex dialogs to allow better organization where you have a lot of inputs. It is also particularly useful when you have inputs that are not commonly changed so you can put them into a collapsed group so that they're still available but don't complicate typical usage of your command.

ImageCommandInput

The ImageCommandInput allows you to display an image in the command dialog.  Images are in the png format and support transparent backgrouns.  They are displayed full size.  In the example below, no name has been defined so the label is not displayed. The isFullWidth property can also be used so that the image will be centered within the width of the dialog.

IntegerSliderCommandInput and IntegerSliderListCommandInput

The IntegerSliderCommandInput and the IntegerSliderListCommandInput are used to get one or two whole numbers within a defined range from the user.  There are several options that change how it is displayed and how it behaves.  The various options are illustrated in the picture below; a single slider with a value spin control, text instead of the spin control, and two sliders to define a value range.  The IntegerSliderListCommandInput defines a list of valid values so that the slider can only select one of the pre-defined values.

IntegerSpinnerCommandInput

The IntegerSpinnerCommandInput is similar to a value input except it has a "spinner" to the right of the edit field where the user can enter a value using the keyboard or they can click the up or down arrows to increment or decrement the value by a predefined amount.

RadioButtonGroupCommandInput

The RadioButtonGroupCommandInput allows you to display a list of radio buttons that are all visible and grouped together.

SelectionCommandInput

A SelectionCommandInput is used to get geometric selections from the user.  You can use filtering to define which types of entities are selectable and set limits on the number of entities that can be selected.

StringValueCommandInput

A StringValueCommandInput is used to get any string input from the user.  Any text can be entered and no validation is performed.

TabCommandInput

A TabCommandInput is used to provide additional grouping beyone what a group command input can provide.  With tabs the entire dialog is available on different tabs.  This allows you to provide many inputs without the dialog exceeding the height of the window and provides the opportunity to logically group your command inputs.  Each tab can contain all of the command inputs, including groups, as shown below.

TableCommandInput

A TableCommandInput is used to organize other command inputs within a row-column structure. A table command input is not a generic table like you might be used to where it typically contains text and occasionally other types of data.  A table command input is a table, but only contains other command inputs. It's best to think of it as just a way to structure command inputs on the dialog. Most of the other command inputs can be used in a table. However, selection and button row command inputs are not supported in a table. Below are some examples of where Fusion commands use a table command input.

Looking in more detail at the Loft command dialog you can see there are two tables used. Looking more closely at the top table where profiles are specified we can see that there are currently two rows and three columns.  the cells in the first column ("Profile 1" and "Profile 2") each contain a StringValueInput object that is set to be read-only.  Using a read-only StringValueInput is the way to display simple text in a table.  The second and third colums of each row contain DropDownCommandInput objects so the user can re-order the profiles and define direction conditions. You can't assign a command input to more than one location in the table, so each command input much be unique.

Besides the cells within the table, the TableCommandInput also has it's own toolbar which is displayed at the bottom of the table.  The toolbar is also a host for command inputs.  The Loft command has two BoolValueCommandInput objects in the toolbar to allow for adding and removing profiles from the list.

The workflow when working with a table command input is to create the table using the CommandInputs object you get from the command, just like you would any other command input.  The table will be positioned in the order it was created relative to the other inputs on the dialog.  At any time, during the create or in reaction to the event when inputs are changed you can create the command input you want to place in the table.  You also create this using the CommandInputs object you get from the command.  Then you use the addCommandInput method of the TableCommandInput object to add the command input to the table.  As a result of adding it to the table it won't be shown outside of the table in the dialog.  You can also use the addToolbarCommandInput to add the input to the table's toolbar.

Below is some example Python code that illustrates creating a table, adding a button to the table's toolbar and adding a StringValueInput and a DropDownCommandInput to the table.  Similar code would exist in the inputChanged event of the command where additional rows could be added to the table.

# Create the table, defining the number of columns and their relative widths.
table = inputs.addTableCommandInput('sampleTable', 'Table', 2, '1:1')

# Define some of the table properties.
table.minimumVisibleRows = 3
table.maximumVisibleRows = 6
table.columnSpacing = 1
table.rowSpacing = 1
table.tablePresentationStyle = adsk.core.TablePresentationStyles.itemBorderTablePresentationStyle
table.hasGrid = False

# Create a button and add it to the toolbar of the table.
button = inputs.addBoolValueInput('tbButton', 'Add Row', False, 'Resources/Add', False)
table.addToolbarCommandInput(button)

# Create a string value input and add it to the first row and column.
stringInput = inputs.addStringValueInput('string1', '', 'Sample Text')
stringInput.isReadOnly = True
table.addCommandInput(stringInput, 0, 0, 0, 0)

# Create a drop-down input and add it to the first row and second column.
dropDown = inputs.addDropDownCommandInput('dropList1', '', adsk.co

---

## Working in a Separate Thread

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Threading_UM.htm

Working in a Seperate Thread
Introduction

The desire to have multi-threaded applications became very popular when computer processors started to have multiple cores. Multi-threading is one way to take better advantage of the full processing capabilities of a computer. In concept it's a great idea but in practice it doesn't always fit real-world workflows and is very difficult to implement.  Most of Fusion is single threaded, as are most applications with a user-interface. Each step of constructing a model depends on the result of the previous step.  For example, if you create a very complex feature that will take several seconds to compute it doesn't make sense for Fusion to return control back to you to continue modeling while it's still calculating the feature because the model needs to be complete before you can begin to define the next feature. Ideally, multi-threading would be used in the calcuation of the feature to speed up that part of the process but that can be difficult to implement too.

If you think of a thread as a sequence of instructions that are processed by the computer, multi-threading allows many threads to be processed simultaneously.  Besides being used to speed up the processing of complex tasks, multiple threads are also very useful in interactive applications when you need to have background processing occurring but still want to allow the user to interact with the application. That's the big benefit of what's provided by the Fusion API, as you'll see in the example below.

It's important to remember that most of Fusion is running in the single main thread and this includes the user-interface and your program. You can think of it as a single queue where everyone has to wait their turn and only one person is being waited on at a time. When your program is executing a function, nothing else is happening inside Fusion. Let's look at how this works with an add-in and a command.  When an add-in is loaded, Fusion calls its run function.  At that point, your add-in is actively running in the main thread and nothing else is happening in Fusion.  Once the run function has completed Fusion begins processing the other queued up actions, while your add-in sits in the background.  When the user executes a command the add-in defined, the commandCreated event is fired to the add-in.  This moves the add-in to the front of the queue and while its event handler for the command created event is running it has the main thread.  In the command created event handler it defines the command dialog and connects to other events.  Once the command created event has completed it gives up control of the main thread and Fusion takes over to allow the user to interact with the command dialog.  As the user does interact with the dialog, Fusion then fires events to the add-in notifying of what's happening but this also allows the add-in to run in the main thread as it responds to the events.  By using events, Fusion and other add-ins are able to share the main thread.

It becomes a problem when an add-in wants to continue to run and not give up the main thread.  This blocks Fusion from doing any other work. For example, if an add-in wants to monitor a known file to see if it's modified date changes.  One way to do this is to have a loop that continuously checks the date of the file.  However, if you have a function in an add-in that does this, it will block the use of Fusion because it is monopolizing the main thread.  Fusion does support a doEvents function which temporarily returns control back to Fusion to allow any queued up actions to be processed and then it goes back to the running function.  It's not appropriate to use this in a long term loop and will likely result in Fusion crashing at some point.  The better solution is to have the add-in start a new worker thread that will do whatever work needs to be done and set up a custom event so the worker thread can notify the add-in of it's progress or when it's complete.  When the worker thread causes the event to be fired, the add-in then gains control of the main thread where it can do whatever is appropriate.

Custom Event

The Fusion API doesn't support the creation or management of threads, you do that through whatever threading capabilities the language you've chosen to use supports. Both Python and C++ support the creation of threads. What the Fusion API does support is a way for the code running in a worker thread to communicate back to your add-in running in the main thread. This is done through a custom event that allows the program in the worker thread to fire an event that your add-in will handle. Your worker thread should never do any work inside Fusion because that should always be done in the main thread.

Here are a couple of examples that illustrate two common ways this functionality might be used. The first  is a command that accesses the web to get information to populate the command dialog. Web calls are dependent on a lot of factors and can sometimes take some time. The interaction with the web service can be done in a seperate thread allowing the main thread to continue processing the command so the command dialog can quickly be displayed and then when the web data is retrieved is can be passed from the worker thread to the add-in running in the main thread to update the command dialog.

Another example of how this functionality can be used is to start a worker thread that continuously watches for something and then does something in reaction to a specific action.  For example, an add-in can be written that starts a worker theread that checks the modified time of a specific csv file periodically to see if it has been changed. If it has, it reads the updated csv file and updates the values of corresponding parameters in the design. This type of background polling was not possible before because it would have consumed the main thread.

A third, more obscure use of this functionality is to allow two add-ins to communicate with each other. It's possible for another add-in to fire the custom event of another add-in. A custom event is identified by name so by knowing the name and the format of the data the add-in expects, one add-in can send another add-in information. It will be interesting to see if any interseting applications are developed that take advantage of this capability.

Using a Custom Event

Conceptually, implementing and using a custom event is relatively simple. In practice it is a little more difficult because it involves understanding how to create and use a seperate thread and basic principles of threading. The steps to set up and use a custom event are listed below.

		Register your custom event and connect your handler to the event.

		Create the worker thread and start it.

		The worker thread does whatever work it does and when it has information to share with the add-in it calls the fireCustomEvent method. This results in Fusion calling the event handler for the custom event and passing the information provided. This gives the add-in control of the main thread so it can do whatever is supposed to happen.

		If in response to the event, the add-in will be creating or modifying something in Fusion (some action that will cause an undo operation to be added), the add-in should first terminate the active command before doing it's work.  This can easily be done using the code below which checks to see if the default Select command is running and if not, it executes the select command which has the side-effect of terminating the currently running command.

# Make sure a command isn't running before changes are made.
if ui.activeCommand != 'SelectCommand':
    ui.commandDefinitions.itemById('SelectCommand').execute()

		Clean up by unregistering the custom event.

Sample Programs

There are two samples that demonstrate two of the uses described above.  The first sample starts a worker thread with a timer that will send a random number between 1 and 15 back to the main thread which then updates the parameter named "d1" in the active design using the value passed in.

The second sample demonstrates using this capability within a command to get information to display in the command dialog. It creates a command with a dialog containing a table. The worker thread periodically sends new data back to the main thread which is used to populate the table.

Using a Custom Event

One important thing to know when using custom events is that you should not call any Fusion API functions within the worker thread. Even calling the messageBox method can sometimes result in Fusion crashing. To help in debugging your program you can use other techniques to display messages. For example, in Python on Windows you can use ctypes library and its MessageBoxW function as shown below. This is a Python friendly wrapper over the Windows MessageBoxW function that you can call directly from C++.

import ctypes

ctypes.windll.user32.MessageBoxW(None, "The message.", "Title", 1)

The main thing is that all Fusion specific work needs to be done by your add-in in the main thread.

		© Copyright 2026 Autodesk, Inc.

		Comment on this page.

---

## Sheet Metal API - Introduction

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SheetMetalIntroduction_UM.htm

Introduction to the Sheet Metal API

The Sheet Metal API exposes the same sheet metal rules, features, and flat patterns you create in the Design workspace. Use it from a script or add-in to define and apply sheet metal rules, create and edit features (flanges, hems, corner closures, and more), and work with the resulting flat pattern for manufacturing.

This introduction explains the sheet metal object model and how to create rules, features, and flat patterns from a script or add-in. The content is split into four topics. Examples use Python; the same types and methods are available in TypeScript and C++. For every class, method, and property, see the API Reference Manual (for example SheetMetalRule and HemFeatures).

Before You Begin

- Use a parametric design (history captured). Sheet metal is not supported in a direct, history-free design.

- At the start of your script, define the application, design, root component, and document. Later samples assume these variables exist:

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent
doc = app.activeDocument
```

- For runnable examples, see the Sheet Metal Rules Sample and other samples under Sheet Metal on the API Samples page.

How the Sheet Metal API Is Structured

The Sheet Metal API uses two entry points: the Design and its components. Knowing which to use helps you find rules, features, and flat patterns in code:

- Rules live on the Design. SheetMetalRule objects come from design.designSheetMetalRules or design.librarySheetMetalRules.

- Features and flat patterns live on each component. Sheet metal feature collections (flangeFeatures, hemFeatures, ripFeatures, and others) come from Component.features, alongside extrudes, fillets, and other feature types. A component's flat pattern comes from Component.flatPattern.

Sketching on a flat pattern is the one exception. It goes through that flat pattern's own FlatPatternProduct in the document's products collection. See Flat Patterns.

Area | Root | How you reach it

Sheet metal rules | Design | design.designSheetMetalRules, design.librarySheetMetalRules

Sheet metal features | Component | component.features.flangeFeatures, .hemFeatures, .ripFeatures, …

Flat pattern | Component | component.flatPattern

Topics in This Introduction

- Sheet Metal API Overview – Feature collections, sheet metal bodies and rules, flat patterns, and the common feature pattern.

- Sheet Metal Rules and Conversion – Rules, units, assigning rules to components, and converting solids to sheet metal.

- Sheet Metal Features – Flanges, lofted flanges, hems, rips, corner closures, join by bend, rule overrides, folding and unfolding, fillets, and chamfers.

- Flat Patterns – Creating flat patterns, bend info, and sketching on the flat pattern.

Related API Reference

- SheetMetalRule Object

- FlangeFeatures Object

- FlatPatternProduct Object

---

## Sheet Metal API - Overview

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SheetMetalOverview_UM.htm

Sheet Metal API Overview

Sheet metal rules and features use the same Design and Component objects as sketches and solid features. You reach sheet metal features the same way you reach any other feature: through Component.features.

Feature Collections on Component.features

Each sheet metal feature type has its own collection on Component.features. The table lists the collections covered in this introduction and links to reference topics.

Collection property | Feature types

flangeFeatures | Base, contour, and edge flanges

loftedFlangeFeatures | Lofted flanges

hemFeatures | Hems

ripFeatures | Rips

cornerClosureFeatures | Corner closures

joinByBendFeatures | Join by bend

unfoldFeatures | Unfold (temporary flat)

refoldFeatures | Refold

foldFeatures | Fold (explicit bend lines)

sheetMetalFilletFeatures | Sheet metal fillets

sheetMetalChamferFeatures | Sheet metal chamfers

The following example gets collections from the root component:

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent

# Feature collections for sheet metal live on Component.features, alongside
# extrudes, fillets, and every other feature type.
hemFeatures = rootComp.features.hemFeatures
ripFeatures = rootComp.features.ripFeatures
# Same pattern for other collections, for example flanges:
flangeFeatures = rootComp.features.flangeFeatures
```

Sheet Metal Bodies and Rules

A sheet metal body has a sheet metal rule applied. Use BRepBody.isSheetMetal to test a body.

Rules are SheetMetalRule objects in either:

- design.designSheetMetalRules – rules stored in the document.

- design.librarySheetMetalRules – rules from libraries.

Details are in Sheet Metal Rules and Conversion.

Flat Pattern

Each sheet metal component can have one flat pattern. Read it from Component.flatPattern, which returns None if the component does not have a flat pattern yet:

```python
flatPattern = rootComp.flatPattern
if flatPattern is None:
    # No flat pattern yet. See Flat Patterns for Component.createFlatPattern.
    raise RuntimeError('No flat pattern in this component')
```

Each flat pattern also has its own FlatPatternProduct in the document. You only need it to sketch on the flat pattern.

Tip: Create the flat pattern with Component.createFlatPattern first, then read geometry from the FlatPattern and sketch on it through FlatPatternComponent. See Flat Patterns.

Common API Pattern for Features

Sheet metal features follow the usual Fusion pattern:

- Get the collection from Component.features.

- Create an input object (createInput or a type-specific create…Input method).

- Set properties on the input (the same options as in the command dialog).

- Call add(input).

Edge, face, profile, sketch, and body variables in the examples (edge1, hemEdge, profile, sketch, body, and so on) are assumed to come from your own selection or query code, such as UserInterface.selectEntity or traversing a body's edges and faces. When an input accepts multiple edges or profiles, pass a plain Python list, not an ObjectCollection.

---

## Sheet Metal API - Rules and Conversion

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SheetMetalRules_UM.htm

Sheet Metal Rules and Conversion

A SheetMetalRule bundles the manufacturing parameters for a material: thickness, bend radius, k-factor, and relief behavior. You assign a rule to a component rather than defining thickness per body, similar to assigning a material.

There is no way to create a rule from scratch. Copy an existing rule from the design or library with the addByCopy method of SheetMetalRules, then edit the copy.

Note: The designSheetMetalRules collection is only available once the design contains sheet metal. In a new design, assign a library rule to the component's activeSheetMetalRule (see Assign a Rule to a Component, below), create the first sheet metal feature, and then copy rules into the design.

Create and Edit a Rule

The following example copies the default library rule into a design that already contains sheet metal:

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)

# Copy the default library rule into the design.
steelRule = design.librarySheetMetalRules.itemByName('Steel (mm)')
newRule = design.designSheetMetalRules.addByCopy(steelRule, 'Steel (2 mm)')

# The thickness and bendRadius properties are SheetMetalRuleValue objects.
# Set either a numeric value (in centimeters) or an expression string.
newRule.thickness.value = 0.2
newRule.bendRadius.expression = 'Thickness'

# kFactor is a plain unitless ratio on the rule, not a SheetMetalRuleValue.
newRule.kFactor = 0.44
```

Note: For SheetMetalRuleValue, the value property is in centimeters (Fusion internal length units). Setting newRule.thickness.value = 0.2 means 2 mm. To stay consistent with unit strings in the rest of your script, you can set expression instead (for example '2 mm') or use ValueInput.createByString('2 mm') where the API accepts ValueInput. See SheetMetalRuleValue Object.

Tip: Call addByCopy on designSheetMetalRules to store the copy in the document, or on librarySheetMetalRules to store it in the library. The Sheet Metal Rules Sample shows a complete example that copies within the library.

The most frequently used properties are thickness, bendRadius, and kFactor. The SheetMetalRule reference topic lists relief shape and size, the gap for miter, rip, and seam conditions, and other rule settings.

Code samples in this introduction are self-contained. Later examples re-fetch rules or edges instead of assuming a variable such as newRule still exists.

Assign a Rule to a Component

Assign the rule to the component where you will create sheet metal geometry, the same as in the UI. Set component.activeSheetMetalRule before creating base flanges or other features on that component. This works the same way for nested components. To create a flange that starts a new body in a nested component, also activate that component first (see Sheet Metal Features).

In a new design, assign a library rule:

```python
rootComp.activeSheetMetalRule = design.librarySheetMetalRules.itemByName('Steel (mm)')
```

Once the design contains sheet metal, you can assign a design rule instead, such as the copy created above:

```python
rootComp.activeSheetMetalRule = design.designSheetMetalRules.itemByName('Steel (2 mm)')
```

Convert a Body to Sheet Metal

An imported solid, or a body built from ordinary extrudes and other non-sheet-metal features, is not sheet metal. Sheet metal features cannot operate on it until you convert it.

Call BRepBody.convertToSheetMetal, passing a face used to measure thickness and the rule to assign:

```python
body = rootComp.bRepBodies.item(0)

# Pass one of the large flat faces of the sheet; thickness is measured from it.
# item(0) stands in for your own face selection.
thicknessFace = body.faces.item(0)
body.convertToSheetMetal(thicknessFace, rootComp.activeSheetMetalRule)
```

After conversion, body.isSheetMetal is True and the body works with flangeFeatures, hemFeatures, and the other sheet metal collections.

For the interactive workflow, see product help for Convert to Sheet Metal.

---

## Sheet Metal API - Features

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SheetMetalFeatures_UM.htm

Sheet Metal Features

Each sheet metal feature collection uses the pattern described in Sheet Metal API Overview: create an input, set the same options you would set in the command dialog, then call add.

The input object is analogous to the command dialog. For example, the Edge Flange dialog below shows the settings that EdgeFlangeInput exposes:

- Edges/Profiles – the edges passed to createEdgeFlangeInput. The edge list above Edges/Profiles, with Full edge for each edge, corresponds to edgeDefinitions.

- Extent type and Height – the distance passed to createEdgeFlangeInput, or setToObjectExtent to extend to an object.

- Angle – angle.

- Height datum – heightDatumType.

- Bend position – bendPositionType.

- Bend override – bendRadiusOverride and bendReliefOverride.

- 2-Bend corner override – twoBendCornerOverride.

- 3-Bend corner override – threeBendCornerOverride.

Flanges

flangeFeatures covers three flange types, each with its own input: EdgeFlangeInput, BaseFlangeInput, and ContourFlangeInput.

- Edge flange – adds material along one or more edges with distance and bend angle.

- Base flange – starts a new sheet metal body from one or more profiles.

- Contour flange – extrudes one or more open profiles a specified distance.

Edge Flange

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent
flangeFeatures = rootComp.features.flangeFeatures

flangeEdges = [edge1, edge2]

edgeFlangeInput = flangeFeatures.createEdgeFlangeInput(
    flangeEdges,
    adsk.core.ValueInput.createByString('10 mm'))
edgeFlangeInput.bendPositionType = adsk.fusion.BendPositionTypes.InsideBendPositionType
edgeFlangeInput.angle = adsk.core.ValueInput.createByString('90 deg')
flangeFeature = flangeFeatures.add(edgeFlangeInput)
```

The distance argument is the flange height (the Height field), shared by every edge in the input. It is not a per-edge value.

Per-edge width (how much of each edge's length the flange covers) is controlled separately:

- Edges passed directly to createEdgeFlangeInput are full-length and cannot be changed afterward.

- For custom widths, pass an empty edge list and add edges through edgeFlangeInput.edgeDefinitions:

```python
edgeFlangeInput = flangeFeatures.createEdgeFlangeInput(
    [], adsk.core.ValueInput.createByString('10 mm'))
edgeFlangeInput.edgeDefinitions.addFullLengthEdge(edge2)
edgeFlangeInput.edgeDefinitions.addSymmetricEdge(
    edge1, adsk.core.ValueInput.createByString('5 mm'))
```

The edgeDefinitions methods are:

- addFullLengthEdge – full edge length.

- addSymmetricEdge – width centered on the edge midpoint (total width is twice the value given).

- addTwoSidedEdge – independent widths from the midpoint.

- addTwoOffsetsEdge – insets from each end of the edge.

Other edge flange input properties:

- heightDatumType (FlangeHeightDatumTypes) – where the distance is measured from: the outer faces (OuterFacesFlangeHeightDatumType, the default), the inner faces (InnerFacesFlangeHeightDatumType), or tangent to the bend (TangentToBendFlangeHeightDatumType).

- isMiteredCorners – miter where adjacent edge flanges meet.

- setToObjectExtent(toEntity, offset) – extend to another face or plane instead of a fixed distance.

Base and Contour Flanges

Set activeSheetMetalRule on the component before creating a base, contour, or lofted flange; the rule sets the new body's thickness:

```python
rootComp.activeSheetMetalRule = design.librarySheetMetalRules.itemByName('Steel (mm)')
profile = sketch.profiles.item(0)
baseFlangeInput = flangeFeatures.createBaseFlangeInput([profile])
flangeFeature = flangeFeatures.add(baseFlangeInput)
```

Note: When you create a base, contour, or lofted flange in a nested component, activate that component first (Occurrence.activate()). Otherwise the new body is created in the root component.

Base and contour inputs expose operation (FeatureOperations). Because they create the initial sheet metal body from a profile, only NewBodyFeatureOperation (the default) and NewComponentFeatureOperation are valid.

The orientation property (FlangeOrientations) controls which side of the profile plane receives material: SideOneFlangeOrientation, SideTwoFlangeOrientation, or CenteredFlangeOrientation.

A contour flange takes open profiles, which you create from sketch curves with Component.createOpenProfile. The following example creates a symmetric contour flange. The setSymmetricDirection method replaces the distance passed to createContourFlangeInput and applies its own distance to each side of the profile plane, so '10 mm' gives a 20 mm flange:

```python
# line1 is the first sketch line of an open sketch shape, such as an L.
openProfile = rootComp.createOpenProfile(line1, True)
contourFlangeInput = flangeFeatures.createContourFlangeInput(
    [openProfile], adsk.core.ValueInput.createByString('10 mm'))
contourFlangeInput.setSymmetricDirection(adsk.core.ValueInput.createByString('10 mm'))
flangeFeature = flangeFeatures.add(contourFlangeInput)
```

Lofted Flanges

Lofted flanges use loftedFlangeFeatures, not flangeFeatures. They loft between exactly two profiles, which must both be open or both be closed and must lie on separate planes.

The formingType property (LoftedFlangeFormingTypes) controls how the flange is formed. The default, BrakeFormLoftedFlangeFormingType, approximates the loft with flat facets joined by straight bends, as a press brake would. DieFormLoftedFlangeFormingType produces a smooth surface instead. Lofted flange inputs also have an orientation property, as base and contour flanges do.

With brake forming, you must set the facet control before calling add, using one of:

- setFacetControlByChordTolerance – the maximum distance between the true surface and the facets.

- setFacetControlByFacetAngle – the maximum angle between adjacent facets.

- setFacetControlByFacetDistance – the maximum length of a facet edge.

- setFacetControlByFacetNumber – a fixed number of facets, from 1 to 1000.

For open profiles, create each one with Component.createOpenProfile, as for a contour flange.

```python
loftedFlangeFeatures = rootComp.features.loftedFlangeFeatures
# startCurve and endCurve are sketch curves on two separate planes.
startProfile = rootComp.createOpenProfile(startCurve, True)
endProfile = rootComp.createOpenProfile(endCurve, True)
profiles = [startProfile, endProfile]
loftedFlangeInput = loftedFlangeFeatures.createInput(profiles)
loftedFlangeInput.setFacetControlByFacetNumber(adsk.core.ValueInput.createByReal(10))
loftedFlangeFeature = loftedFlangeFeatures.add(loftedFlangeInput)
```

Hems

hemFeatures fold material back at an edge. Configure HemFeatureInput with the setter for the hem style (flat, open, rolled, rope, teardrop, or double), such as setFlatHem or setRolledHem. Every hem setter takes a bend position, which must be StartEdgeBendPositionType or TangentToSideBendPositionType. The other BendPositionTypes values, such as InsideBendPositionType, apply to edge flanges and are not valid for hems.

```python
hemFeatures = rootComp.features.hemFeatures
hemInput = hemFeatures.createHemFeatureInput()

# The third argument, isFlipped, reverses the fold direction when True. False keeps the default direction.
hemInput.setFlatHem(
    hemEdge,
    adsk.core.ValueInput.createByString('5 mm'),
    False,
    adsk.fusion.BendPositionTypes.StartEdgeBendPositionType)
hemFeature = hemFeatures.add(hemInput)
```

Rips

ripFeatures cut a gap so a closed shape can unfold. Configure RipFeatureInput with:

- setByFace – removes an entire face.

- setAlongEdge – creates a gap along an edge. The edge must lie between two smoothly connected faces on the same side of the sheet, such as the line where a flat face runs into a bend. A sharp corner edge or an outer boundary edge is rejected.

- setBetweenPoints(pointOne, pointTwo, gapDistance, offsetOne, offsetTwo) – creates a gap between two points.

```python
ripFeatures = rootComp.features.ripFeatures
ripInput = ripFeatures.createRipFeatureInput()
ripInput.setAlongEdge(ripEdge, adsk.core.ValueInput.createByString('1 mm'))
ripFeature = ripFeatures.add(ripInput)
```

Corner Closures

cornerClosureFeatures connect and miter two planar flanges at a corner. CornerClosureFeatureInput is created from the dominant edge and the submissive edge of the corner closure: one linear edge from each of two flanges that meet at the corner. When you select edges in the Corner Closure command, the first edge is the dominant edge and the second is the submissive edge.

When the input is created, the alignment type is a symmetric gap; set the gap distance with gap. To set the alignment type to an overlap, call setToOverlapAlignmentType(overlap, isFlipped). The overlap argument is the overlap percentage, a unitless value from 0 (no overlap) to 1 (100% overlap). The isFlipped argument defines whether the dominant edge goes over the submissive edge or vice versa.

The isWidthExtentAligned property controls whether the corner closure extends along the flange edges, aligned with the edge direction (True, the default), or perpendicular to the flange edges (False). The bendTransition property (BendTransitionTypes) can be smooth (SmoothCornerBendTransitionType, the default), straight line (StraightLineCornerBendTransitionType), or trim to bend (TrimToBendCornerBendTransitionType).

Note: Overlap alignment is not available in Fusion for Personal Use. In Fusion for Personal Use, calling setToOverlapAlignmentType or editing an existing corner closure that uses an overlap throws an exception.

```python
cornerClosureFeatures = rootComp.features.cornerClosureFeatures
cornerInput = cornerClosureFeatures.createInput(dominantEdge, submissiveEdge)
cornerInput.gap = adsk.core.ValueInput.createByString('1 mm')
cornerClosureFeature = cornerClosureFeatures.add(cornerInput)
```

The read-only closureType property (CornerClosureTypes) reports whether the corner is a two-bend or three-bend corner, which determines which corner override type applies (see the table in Sheet Metal Rule Overrides).

Join by Bend

Use joinByBendFeatures to join two sheet metal bodies with a bend, using one edge from each of the two bodies.

```python
joinByBendFeatures = rootComp.features.joinByBendFeatures
joinInput = joinByBendFeatures.createInput(edge1, edge2)
joinByBendFeature = joinByBendFeatures.add(joinInput)
```

Join by bend features support bendRadiusOverride and bendReliefOverride, but not corner overrides.

Note: Join by bend is not available in Fusion for Personal Use. Creating or editing a join by bend feature in Fusion for Personal Use throws an exception.

Sheet Metal Rule Overrides

A feature can override part of the active rule locally. The override objects are BendRadiusOverride, BendReliefOverride, TwoBendCornerOverride, and ThreeBendCornerOverride. Each feature exposes only the overrides that apply to it:

Feature | bendRadiusOverride | bendReliefOverride | twoBendCornerOverride / threeBendCornerOverride

Base flange | no | no | no

Contour flange | yes | no | no

Edge flange | yes | yes | yes (whichever matches the corner)

Hem | yes, except rolled, rope, and teardrop hems | open and double hems only | no

Corner closure | no | no | yes (matches closureType)

Join by bend | yes | yes | no

On the input object while creating the feature:

```python
edgeFlangeInput = flangeFeatures.createEdgeFlangeInput(
    [edge1, edge2], adsk.core.ValueInput.createByString('10 mm'))
edgeFlangeInput.bendRadiusOverride.setOverride(adsk.core.ValueInput.createByString('3 mm'))
flangeFeature = flangeFeatures.add(edgeFlangeInput)
```

On an existing feature, roll the timeline marker before that feature, edit it, then move the marker back to the end:

```python
# flangeFeature is an existing edge flange, such as the one created above.
flangeFeature.timelineObject.rollTo(True)
flangeFeature.bendRadiusOverride.setOverride(adsk.core.ValueInput.createByString('4 mm'))
design.timeline.moveToEnd()
```

Other override types use the same pattern with different setOverride arguments. Every override object supports isOverridden and clearOverride().

Folding and Unfolding

Unfold and Refold work as a pair:

- UnfoldFeature temporarily unfolds bends around a stationary face so you can add sketches, holes, or other features on the flat shape.

- A refold feature refolds the bends that an unfold feature flattened. Create its RefoldFeatureInput from that unfold feature.

Besides the stationary face, the unfold input needs to know which bends to unfold. Either set isUnfoldAllBends to True, or set bendFaces to the inner or outer cylindrical face of each bend to unfold. If you do neither, add fails.

```python
unfoldFeatures = rootComp.features.unfoldFeatures
refoldFeatures = rootComp.features.refoldFeatures

stationaryFace = body.faces.item(0)
unfoldInput = unfoldFeatures.createInput(stationaryFace)
unfoldInput.isUnfoldAllBends = True
unfoldFeature = unfoldFeatures.add(unfoldInput)

# Add sketch, hole, or other features on the flat body here.

refoldInput = refoldFeatures.createInput(unfoldFeature)
refoldFeature = refoldFeatures.add(refoldInput)
```

FoldFeatures is separate: you add explicit bend lines on the input instead of unfolding existing flange bends.

Sheet Metal Fillets and Chamfers

sheetMetalFilletFeatures and sheetMetalChamferFeatures are separate from the general filletFeatures and chamferFeatures collections. They operate only on thickness-direction edges (perpendicular to the sheet metal front and back faces).

Edges are grouped into edge sets, and each set has one radius or distance.

```python
sheetMetalFilletFeatures = rootComp.features.sheetMetalFilletFeatures
filletInput = sheetMetalFilletFeatures.createInput()
filletInput.edgeSetInputs.add(filletEdges, adsk.core.ValueInput.createByString('1 mm'))
filletFeature = sheetMetalFilletFeatures.add(filletInput)
```

Chamfers use the same pattern, with a distance instead of a radius:

```python
sheetMetalChamferFeatures = rootComp.features.sheetMetalChamferFeatures
chamferInput = sheetMetalChamferFeatures.createInput()
chamferInput.edgeSetInputs.add(chamferEdges, adsk.core.ValueInput.createByString('1 mm'))
chamferFeature = sheetMetalChamferFeatures.add(chamferInput)
```

Note: Sheet metal fillets and chamfers are not available in Fusion for Personal Use. Creating or editing them in Fusion for Personal Use throws an exception.

---

## Sheet Metal API - Flat Patterns

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/SheetMetalFlatPatterns_UM.htm

Flat Patterns

A flat pattern is the persistent unfolded counterpart to a sheet metal component. It is separate from the temporary Unfold feature in Sheet Metal Features.

The FlatPattern object exposes flattened geometry: bend lines, extent lines, and the top, bottom, and side faces of the flat body.

Create a Flat Pattern

Call Component.createFlatPattern on the component that owns the sheet metal body. Pass a face to hold stationary while the rest unfolds.

```python
import adsk.core, adsk.fusion

app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
rootComp = design.rootComponent
doc = app.activeDocument
body = rootComp.bRepBodies.item(0)

stationaryFace = body.faces.item(0)
flatPattern = rootComp.createFlatPattern(stationaryFace)
```

The createFlatPattern method returns the FlatPattern object directly. It fails if the component already has a flat pattern. To get an existing flat pattern, use Component.flatPattern, which returns None if the component does not have one.

FlatPattern is a timeline feature. Useful properties and methods include:

Member | Purpose

flatBody | Flattened BRepBody

bendLinesBody | Bend line geometry

extentLinesBody | Extent lines

topFace, bottomFace, sideFaces | Faces on the flat body

foldedBody | Original folded body

getBendInfo(bendEdge) | Fold direction and angle for a bend edge

Sketch on the Flat Pattern

Each flat pattern has its own FlatPatternProduct in the document. Sketches on the flat pattern use that product's FlatPatternComponent, from FlatPatternProduct.rootComponent. No property leads from a FlatPattern to its product, so find the product in the document's products collection by matching the flat pattern's entityToken:

```python
flatPattern = rootComp.flatPattern

# Find the FlatPatternProduct that belongs to this flat pattern.
fpComponent = None
for product in doc.products:
    fpProduct = adsk.fusion.FlatPatternProduct.cast(product)
    if fpProduct and fpProduct.flatPattern.entityToken == flatPattern.entityToken:
        fpComponent = adsk.fusion.FlatPatternComponent.cast(fpProduct.rootComponent)
        break

sketchOnFlat = fpComponent.sketches.add(flatPattern.topFace)

# Draw a 5 mm radius circle on the flat pattern. Sketch coordinates are in centimeters.
sketchOnFlat.sketchCurves.sketchCircles.addByCenterRadius(
    adsk.core.Point3D.create(0, 0, 0), 0.5)
```

Read Bend Information

To read the fold direction and angle of each bend, call getBendInfo on each edge of the flat pattern's bendLinesBody:

```python
import math

flatPattern = rootComp.flatPattern
bendLinesBody = flatPattern.bendLinesBody
for bendEdge in bendLinesBody.edges:
    ok, isBendUp, bendAngleRad = flatPattern.getBendInfo(bendEdge)
    if ok:
        print(f'Bend angle: {math.degrees(bendAngleRad):.1f} deg, up={isBendUp}')
```

Tip: Workflow order is (1) build the sheet metal body in the design, (2) createFlatPattern, (3) read bends and sketch on FlatPatternComponent.

Samples

The Sheet Metal category on API Samples includes complete sample scripts for sheet metal workflows.

Related API Reference

- FlatPattern Object

- FlatPatternProduct Object

- FlatPatternComponent Object

---

## Configuration Rules

Fonte: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/ConfigurationRules_UM.htm

Configuration Rules NIDL API Reference

The Configuration Rules API lets you read and author the rules that drive and limit the configured aspects of a Configured Design in Fusion — the same rules you can build on the Rules Canvas, expressed as typed objects in code.

Preview: The Configuration Rules API is provided in preview. Its objects, methods, and properties may change in a future release.

In this Document

Overview — what a configuration rule is and the object model.

Getting Started — prerequisites, reaching the manager, and the script scaffold the examples use.

Reading Rules — getRules, itemById, itemByIds.

Modifying Rules — add, update, delete, reorder, and round-trip as JSON.

Building Rule Bodies — the typed statement and condition blocks.

Columns and Values — the columns a rule can target, the value to use for each, and expressions.

Issues and Errors — handling problems reported by a call you made.

Rule Statuses — getStatuses, getStatusesByRuleId, getStatusesByConfigurationId.

Best Practices — writing predictable rules.

See also

Overview

What a Configuration Rule Is

A configuration rule is a logical rule that limits or drives the values of the configured aspects of a Configured Design. Each rule is evaluated against every configuration in the design — the configurations in order from left to right — and the rules themselves are evaluated from top to bottom. A rule produces one of two kinds of result for a configured aspect:

- A driven value is a single valid value the rule determines. Because there is only one valid value, it cannot be changed.

- A limited value is a subset of valid values the rule determines. It can be changed, but only within that subset.

In the user interface, you author rules on the Rules Canvas by connecting blocks from the Toolbox into conditional statements. The API works with the same rules and the same building blocks, but you construct them as typed objects in code. A rule you create with the API appears on the Rules Canvas, and a rule authored in the user interface can be read and modified with the API.

The Object Model

Access begins with the configurationRulesManager property of the Design object. It returns a ConfigurationRulesManager, or null if the design is not a Configured Design. Because rules are stored with the design rather than held in memory, each read is a discrete request, so read what you need into your own variables rather than calling the manager repeatedly. Through the manager you can:

- Read rules — getRules returns every rule in one request; itemById and itemByIds return specific rules.

- Modify rules — modifyRules applies a batch of additions, updates, deletions, and reordering in a single call; addRule and deleteRule are conveniences for the single-rule cases.

- Check rule health — getStatuses reports what the rules engine found the last time the rules ran; getStatusesByRuleId and getStatusesByConfigurationId narrow that to one rule or one configuration. See Rule statuses.

Each rule is a ConfigurationRule with a name, an optional comment, an isActive flag, and a body. The body is an ordered list of typed blocks in two families — statement blocks (the actions a rule performs) and condition blocks (the tests an If block evaluates) — plus the typed values those blocks carry. See Building rule bodies for the full block reference.

In the user interface, these blocks sit inside a Rule block on the Rules Canvas that carries the rule's name and on/off state. In the API that container is the ConfigurationRule object itself — its name, isActive, and body — not a block within the body.

Reads and modifications both return a result that carries an issues array alongside the affected rules. An empty issues array means the operation was applied or read cleanly; entries describe non-fatal problems. Fatal problems are reported as an error instead (see Issues and errors).

Issues and statuses are different things. An issues entry describes what went wrong with the call you just made — a malformed block, an id that matched nothing. A status describes what the rules engine found when the rules last ran, for one rule on one configuration. A call can return no issues at all while a rule is switched off on half the design's configurations, so check both (see Rule statuses).

Configuration rules act on the columns of the configuration table's top table — not on theme tables directly, though a top-table theme column's value is a theme-table row key (see Columns and values).

Getting Started

Before using the API, create and edit some configuration rules through Fusion's user interface so you are familiar with how they behave; this document explains the equivalent functionality in the API. All examples are Python, intended to be run from the Fusion Script Editor (Utilities > Scripts and Add-Ins) with a Configured Design open and active.

Prerequisites

- The active document must be a Configured Design. For a design that is not configured, Design.configurationRulesManager returns null. See the Configurations topic for how to create a Configured Design.

- Reading rules works in any Fusion. Creating, editing, and deleting rules requires the Fusion Design Extension; those operations report an error when the extension is not enabled (in Python, a raised exception).

- Reading statuses also works in any Fusion, and is cheaper than reading rules: the three status queries read data already held in memory, so unlike getRules they make no round trip and never trigger a rules run.

- All operations act on the active design.

- Rules are applied as soon as the call returns — there is no separate step to run or apply them.

The Script Scaffold

Every example in this document runs inside the following scaffold, which connects to the manager and handles fatal errors. Later snippets show only the lines that matter and assume rulesManager, app, ui, and design are in scope from here.

```python
import adsk.core, adsk.fusion, traceback

def
run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design: adsk.fusion.Design = app.activeProduct

        # The manager is null for a design that is not a Configured Design.
        rulesManager = design.configurationRulesManager

        if rulesManager is None:
            ui.messageBox('The active design is not a Configured Design.')
            return

        # ---- example code goes here, using `rulesManager` ----
except:
        # Fatal problems, such as a missing extension entitlement, arrive here.
        if ui:
            ui.messageBox('Failed:{}'.format(traceback.format_exc()))
```

Reading Rules

All three read methods return the affected rules together with an issues array. Inspect issues even on a read — a non-empty array describes a non-fatal problem, such as a CONVERSION_WARNING encountered while reading a rule back.

- getRules() returns a ConfigurationRulesResult with every rule on the design in evaluation order. Iterate its rules collection rather than indexing the manager.

- itemById(id) returns a ConfigurationRuleResult for a single rule. It reports an error if the id is empty or does not match an existing rule (in Python, a raised exception), so use it when you expect the rule to exist.

- itemByIds(ids) returns a ConfigurationRulesResult for a list of ids. A miss is reported as a RULE_NOT_FOUND entry in issues and is simply absent from rules, rather than being reported as an error — unless none of the requested ids match, in which case the call fails with an error (NO_MATCHING_RULES) instead of returning a result. An empty array returns every rule, like getRules.

```python
result = rulesManager.getRules()
app.log(f'The design has {len(result.rules)} configuration rule(s).')

for rule in result.rules:
    state = 'active' if rule.isActive else 'inactive'
    app.log(f'  {rule.name} (id={rule.id}, {state})')
for issue in result.issues:
    app.log(f'  issue: {issue.code} - {issue.message}')
```

Each ConfigurationRule exposes its id, name, comment, isActive flag, and body. To work with the blocks in a body, see Building rule bodies.

Modifying Rules

All changes go through modifyRules, which takes a ConfigurationRulesModifyInput built with ConfigurationRulesModifyInput.create(). The input has three optional collections:

- rules — the rules to add or update.

- deleteRuleIds — the ids of rules to delete.

- orderedRuleIds — the desired final order of the rules.

The request is applied in a fixed order — deletes first, then reorder, then adds and updates — but it is not all-or-nothing: a per-rule or per-block problem does not roll back the rest of the batch. If an individual block fails validation, it is replaced with an empty placeholder and a VALIDATION_FAILED issue is recorded, while the rest of the rule and the batch still apply. Always inspect issues after a call. modifyRules returns a ConfigurationRulesResult whose rules collection holds the post-mutation state of the added or updated rules (in input order), which is how you recover the ids assigned to new rules.

Adding

A rule with an empty id is treated as new. Create it with ConfigurationRule.create(), populate it, and add it to the input's rules collection. (See Building rule bodies for populating body.)

```python
newRule = adsk.fusion.ConfigurationRule.create()
newRule.name = 'Power requires table'
newRule.comment = 'Created from the API'

# newRule.body = [ ... ]  # see Building rule bodies

modifyInput = adsk.fusion.ConfigurationRulesModifyInput.create()
modifyInput.rules = [newRule]

result = rulesManager.modifyRules(modifyInput)

for rule in result.rules:
    app.log(f'Added "{rule.name}" with id {rule.id}.')

for issue in result.issues:
    app.log(f'  issue: {issue.code} - {issue.message}')
```

Updating

Submit a ConfigurationRule with a non-empty id. The name, comment, and isActive fields are merged individually — you can change one without affecting the others. The body, however, is replaced as a whole: setting body replaces the existing body completely. To change a single block, read the rule, modify its body, and submit the whole rule (see Building rule bodies).

```python
# Deactivate a rule without touching anything else about it.
existing = rulesManager.itemById(ruleId).rule
existing.isActive = False

modifyInput = adsk.fusion.ConfigurationRulesModifyInput.create()
modifyInput.rules = [existing]
rulesManager.modifyRules(modifyInput)
```

Deleting

List the ids to remove in deleteRuleIds. Deletes run before reorder and add/update. An id that does not match an existing rule is reported as a RULE_NOT_FOUND issue; the remaining ids are still deleted.

```python
modifyInput = adsk.fusion.ConfigurationRulesModifyInput.create()
modifyInput.deleteRuleIds = [ruleId]
rulesManager.modifyRules(modifyInput)
```

Reordering

Because rules are evaluated top to bottom, order matters when more than one rule affects the same column. Set orderedRuleIds to the desired final order. When non-empty, it must list exactly one entry for every rule that remains after the delete phase. An empty orderedRuleIds leaves the order unchanged.

```python
currentIds = [rule.id for rule in rulesManager.getRules().rules]
modifyInput = adsk.fusion.ConfigurationRulesModifyInput.create()
modifyInput.orderedRuleIds = list(reversed(currentIds))  # reverse the current order
rulesManager.modifyRules(modifyInput)
```

Convenience Methods

For single-rule cases you can skip building a ConfigurationRulesModifyInput:

- addRule(name) creates one rule with the given name and an empty body, and returns a ConfigurationRuleResult with the new rule and any issues.

- deleteRule(id) deletes one rule and returns True if a rule was deleted, or False if no rule with that id exists.

```python
added = rulesManager.addRule('Width minimum').rule
app.log(f'Added rule with id {added.id}.')
wasDeleted = rulesManager.deleteRule(added.id)
app.log(f'Deleted: {wasDeleted}')
```

Use a ConfigurationRulesModifyInput when you need to populate a body before submitting, or to batch several changes together.

Duplicating a Rule and Round-Tripping as JSON

A rule's id identifies an existing rule, so to copy a rule you detach the copy from that id. ConfigurationRule.toJson() returns a JSON string capturing the rule's full state; the static ConfigurationRule.fromJson(ruleJson) parses it back into a detached rule. Call clearId() on the copy so the next submit treats it as new.

clearId() clears the rule id only. Each block in the copied body still carries the blockId of the original rule's block, so submitting the copy as-is records a BLOCK_ID_CONFLICT issue per block while Fusion mints fresh ids. The copy is still created correctly, but clear blockId on the copied blocks to duplicate without those issues (see Block IDs).

```python
original = rulesManager.itemById(ruleId).rule
copy = adsk.fusion.ConfigurationRule.fromJson(original.toJson())
copy.clearId()
copy.name = original.name + ' (copy)'

# Detach the copied blocks from the original's block ids as well.
for block in copy.body:
    block.blockId = ''

modifyInput = adsk.fusion.ConfigurationRulesModifyInput.create()
modifyInput.rules = [copy]
rulesManager.modifyRules(modifyInput)
```

This example clears the ids on the body's top-level blocks. A body with If blocks nests further blocks inside condition, thenBlocks, elseIfBranches, and elseBlocks; clear those too, or accept the BLOCK_ID_CONFLICT issues and let Fusion mint the ids.

Rule names are disambiguated automatically on submit — a second "Width minimum" becomes "Width minimum 2". JSON is also useful for storing a rule outside the design or exchanging rules with external tooling. Round-tripping preserves blocks this version of the API does not recognize: an unknown block kind is kept as a read-only ConfigurationRuleRawStatement or ConfigurationRuleRawCondition and re-emitted unchanged.

Building Rule Bodies

A rule body is an ordered list of blocks that fall into two families: statement blocks and condition blocks. Each slot in a rule accepts only one family — a rule's body and an If block's branches take statement blocks, while a condition slot takes condition blocks.

Statement blocks are the actions a rule performs. They derive from ConfigurationRuleStatement and are legal in a rule's body and in an If block's thenBlocks and elseBlocks:

- ConfigurationRuleSetBlock — assigns a value to a column (drives or limits it).

- ConfigurationRuleIfBlock — evaluates a condition and runs statements conditionally.

- ConfigurationRuleCommentBlock — documents a section of the body; it does nothing when the rule runs.

Condition blocks are the tests an If block evaluates. They derive from ConfigurationRuleCondition and are legal only as a condition or as the operand of another condition (an If block's condition, an If branch's condition, the left/right of an And/Or block, or the operand of a Not block):

- ConfigurationRuleGetBlock — reads a column and compares it against a value.

- ConfigurationRuleAndBlock / ConfigurationRuleOrBlock — combine two conditions.

- ConfigurationRuleNotBlock — negates a condition.

Both Get and Set blocks carry a value — a subclass of ConfigurationRuleBlockValue — whose class depends on the column's type and the operator; see Columns and values.

Building a Body

Construct every block with the static create factory on its class, set its fields, and assemble the blocks. This example builds if the width is less than 400 mm, set the shelf count to 1. Column ids come from the configuration table — see Columns and values. Both values are expressions, which carry their own units.

```python
# The condition: width < 400 mm.
condition = adsk.fusion.ConfigurationRuleGetBlock.create()
condition.columnId = widthColumnId
condition.operatorType = adsk.fusion.ConfigurationRuleGetOperators.LessThanConfigurationRuleGetOperator
condition.value = adsk.fusion.ConfigurationRuleExpressionValue.create('400 mm')

# The action: set the shelf count to 1.
action = adsk.fusion.ConfigurationRuleSetBlock.create()
action.columnId = shelfCountColumnId
action.operatorType = adsk.fusion.ConfigurationRuleSetOperators.EqualsConfigurationRuleSetOperator
action.value = adsk.fusion.ConfigurationRuleExpressionValue.create('1')

# The If block ties them together.
ifBlock = adsk.fusion.ConfigurationRuleIfBlock.create()
ifBlock.condition = condition
ifBlock.thenBlocks = [action]

rule = adsk.fusion.ConfigurationRule.create()
rule.name = 'Narrow shelves have one shelf'
rule.body = [ifBlock]

modifyInput = adsk.fusion.ConfigurationRulesModifyInput.create()
modifyInput.rules = [rule]
rulesManager.modifyRules(modifyInput)
```

The If Block: Branches and Fallbacks

A ConfigurationRuleIfBlock evaluates its condition and runs thenBlocks when it is true. It also carries:

- elseIfBranches — an ordered list of ConfigurationRuleIfBranch objects, each with its own condition and thenBlocks.

- elseBlocks — statements that run when no condition is true.

Evaluation follows a fixed order: the primary condition, then each branch in elseIfBranches in order; the first true branch runs its thenBlocks and no others; if none is true, elseBlocks runs.

```python
getOps = adsk.fusion.ConfigurationRuleGetOperators
setOps = adsk.fusion.ConfigurationRuleSetOperators

def widthLessThan(width):
    block = adsk.fusion.ConfigurationRuleGetBlock.create()
    block.columnId = widthColumnId
    block.operatorType = getOps.LessThanConfigurationRuleGetOperator
    block.value = adsk.fusion.ConfigurationRuleExpressionValue.create(width)
    return block

def setShelves(count):
    block = adsk.fusion.ConfigurationRuleSetBlock.create()
    block.columnId = shelfCountColumnId
    block.operatorType = setOps.EqualsConfigurationRuleSetOperator
    block.value = adsk.fusion.ConfigurationRuleExpressionValue.create(count)
    return block

ifBlock = adsk.fusion.ConfigurationRuleIfBlock.create()
ifBlock.condition = widthLessThan('400 mm')
ifBlock.thenBlocks = [setShelves('1')]

branch = adsk.fusion.ConfigurationRuleIfBranch.create()
branch.condition = widthLessThan('800 mm')
branch.thenBlocks = [setShelves('2')]
ifBlock.elseIfBranches = [branch]

ifBlock.elseBlocks = [setShelves('3')]           # otherwise
```

Combining conditions with And, Or, and Not

ConfigurationRuleAndBlock is true when both its left and right operands are true; ConfigurationRuleOrBlock is true when either is; ConfigurationRuleNotBlock is true when its operand is false. Operands are themselves condition blocks, so you can nest them to any depth.

```python
# width >= 400 mm AND height >= 600 mm
widthOk = adsk.fusion.ConfigurationRuleGetBlock.create()
widthOk.columnId = widthColumnId
widthOk.operatorType = getOps.GreaterThanOrEqualConfigurationRuleGetOperator
widthOk.value = adsk.fusion.ConfigurationRuleExpressionValue.create('400 mm')

heightOk = adsk.fusion.ConfigurationRuleGetBlock.create()
heightOk.columnId = heightColumnId
heightOk.operatorType = getOps.GreaterThanOrEqualConfigurationRuleGetOperator
heightOk.value = adsk.fusion.ConfigurationRuleExpressionValue.create('600 mm')

bothOk = adsk.fusion.ConfigurationRuleAndBlock.create()
bothOk.left = widthOk
bothOk.right = heightOk
```

Reading a Body, Placeholders, and Unrecognized Blocks

When you read a rule, its body contains the same block objects typed as their abstract base classes. Use the cast method on a concrete class to work with a block as its specific type; cast returns None if the block is not of that type, which is how you branch on block kind.

```python
for block in rulesManager.itemById(ruleId).rule.body:
    ifBlock = adsk.fusion.ConfigurationRuleIfBlock.cast(block)

if ifBlock is
not
None:
        getBlock = adsk.fusion.ConfigurationRuleGetBlock.cast(ifBlock.condition)

if getBlock is
not
None:
            app.log(f'If block reads column {getBlock.columnId}.')

continue
    setBlock = adsk.fusion.ConfigurationRuleSetBlock.cast(block)

if setBlock is
not
None:
        app.log(f'Set block writes column {setBlock.columnId}.')
```

A Get or Set block with no operator, no value, or no columnId is an unconfigured placeholder: it is valid to store but does nothing until completed. A block whose columnId cannot be resolved, or whose operator or value is not valid for the column, is also reduced to a placeholder on submit and records a VALIDATION_FAILED issue. The read-only ConfigurationRuleRawStatement and ConfigurationRuleRawCondition wrappers hold block kinds a newer Fusion produced that this version does not recognize; they round-trip unchanged and are never constructed directly.

Block IDs

Every block carries a blockId — a stable id that identifies it within its rule. It is defined on both family base classes, ConfigurationRuleStatement and ConfigurationRuleCondition, so every statement and every condition has one.

A block you have just created with create() has an empty blockId. Fusion mints one when the rule is submitted and reports it back on the next read, so a body read with getRules or itemById has ids on all of its blocks.

You can also set blockId yourself, and Fusion honours it wherever it does not collide with a block that already exists. On a collision Fusion mints a fresh id instead; the rule still applies, and a BLOCK_ID_CONFLICT issue records that the id you asked for was not the id used. Always read the id back rather than assuming the one you supplied was kept.

Block ids matter because of the round trip. Setting body replaces the body as a whole, so a read-edit-submit cycle rebuilds every block. Carrying each block's existing blockId back through that cycle is what keeps the ids on the blocks you did not change — which in turn is what lets a rule status name the block that raised it (see Rule statuses). Blocks read back from Fusion already carry their ids, so a cycle that edits a body in place preserves them for free.

```python
# Read, edit one block, and submit. The other blocks keep their ids because the
# objects read back from Fusion still carry them.
rule = rulesManager.itemById(ruleId).rule

for block in rule.body:
    setBlock = adsk.fusion.ConfigurationRuleSetBlock.cast(block)
    if (setBlock is not None and setBlock.columnId == shelfCountColumnId
            and setBlock.operatorType == setOps.EqualsConfigurationRuleSetOperator):
        setBlock.value = adsk.fusion.ConfigurationRuleExpressionValue.create('2')

modifyInput = adsk.fusion.ConfigurationRulesModifyInput.create()
modifyInput.rules = [rule]
result = rulesManager.modifyRules(modifyInput)

# Read the ids back; a BLOCK_ID_CONFLICT means an id you supplied was replaced.
for block in result.rules[0].body:
    app.log(f'block {block.blockId}')
```

Columns and Values

A Get or Set block targets a column of the configuration table by its columnId, which is the id of a ConfigurationColumn. Never invent a columnId — obtain it from the top table (below). A columnId Fusion does not recognize at all, or an operator or value not valid for the column, is reduced to a placeholder with a VALIDATION_FAILED issue. A columnId Fusion recognizes but does not support for rules (see Known limitations) is reduced the same way but reported as COLUMN_NOT_SUPPORTED instead, so you can tell a typo apart from a column that will never work. Neither case raises an error, so always inspect issues after submitting.

Each column has a leaf type that determines the value class a block must carry:

Leaf type | Value class

number | ConfigurationRuleExpressionValue wherever the operator accepts an expression; otherwise ConfigurationRuleNumberValue (or ConfigurationRuleGetRangeValue / ConfigurationRuleSetRangeValue for ranges, or ConfigurationRuleNumberSelectionValue for AnyOf/NoneOf)

text | ConfigurationRuleExpressionValue wherever the operator accepts an expression; otherwise ConfigurationRuleStringValue

boolean | ConfigurationRuleBooleanValue

dropdown / list | ConfigurationRuleStringListValue (a ConfigurationRuleStringValue is accepted on write and reads back as a list)

Finding Column IDs and Their Values

Column ids and the valid values for list columns come from Design.configurationTopTable, not from the rules API. Iterate its columns; every ConfigurationColumn has an id, a title, and a type you can test with isinstance.

```python
top = design.configurationTopTable

for column in top.columns:
    columnId = column.id                       # use this as the block's columnId

if isinstance(column, adsk.fusion.ConfigurationParameterColumn):
        app.log(f'{columnId}: parameter "{column.parameter.name}"')

elif isinstance(column, adsk.fusion.ConfigurationSuppressColumn):
        app.log(f'{columnId}: suppression of "{column.feature.name}"')

elif isinstance(column, adsk.fusion.ConfigurationVisibilityColumn):
        app.log(f'{columnId}: visibility of "{column.entity.name}"')

elif isinstance(column, adsk.fusion.ConfigurationInsertColumn):
        app.log(f'{columnId}: insert of "{column.occurrence.name}"')

elif isinstance(column, adsk.fusion.ConfigurationThemeColumn):
        app.log(f'{columnId}: theme column')
```

For a dropdown column (a theme column or an insert column) the value you supply is an option key — the id of a ConfigurationRow in the referenced table, not its display name. Enumerate the referenced table's rows to get the keys:

```python
for theme in top.customThemeTables:

for i in range(theme.rows.count):
        row = theme.rows.item(i)
        app.log(f'  option key {row.id} = "{row.name}"')
```

The Configuration Name aspect has no physical column; address it with the fixed id "CONFIGURATION_NAME", and its valid values are the top table's row names.

Supported Columns

Column type | Controls | Read | Write | Value class

ConfigurationParameterColumn (numeric) | A numeric parameter | ✅ | ✅ | ConfigurationRuleExpressionValue where the operator accepts one; otherwise ConfigurationRuleNumberValue, or range values for ranges

ConfigurationParameterColumn (text) | A text parameter | ✅ | ✅ (Equals only) | ConfigurationRuleExpressionValue; ConfigurationRuleStringValue for Contains and NotContains

ConfigurationSuppressColumn | Feature/occurrence suppression | ✅ | ✅ | ConfigurationRuleBooleanValue

ConfigurationVisibilityColumn | Entity visibility | ✅ | ✅ | ConfigurationRuleBooleanValue

ConfigurationThemeColumn | Active theme-table row | ✅ | ✅ | ConfigurationRuleStringListValue (option keys)

ConfigurationInsertColumn | Inserted configuration row | ✅ | ✅ | ConfigurationRuleStringListValue (option keys)

Configuration Name ("CONFIGURATION_NAME") | The configuration's name | ✅ | ❌ | ConfigurationRuleStringValue

Joint feature aspects | A joint's configurable aspects | ✅ | ✅ | ConfigurationRuleBooleanValue / ConfigurationRuleStringListValue

Operators by Leaf Type

The operator must be valid for the column's leaf type. Set the Unknown operator to leave a block as an unconfigured placeholder. Each name is a value of ConfigurationRuleGetOperators or ConfigurationRuleSetOperators, suffixed with the operator kind — for example LessThanConfigurationRuleGetOperator and EqualsConfigurationRuleSetOperator.

Leaf type | Get operators | Set operators

number | Equals, NotEquals, GreaterThan, GreaterThanOrEqual, LessThan, LessThanOrEqual, Range, AnyOf, NoneOf | Equals, Minimum, Maximum, Range, AnyOf

text | Equals, NotEquals, Contains, NotContains | Equals

boolean | Equals, NotEquals | Equals, NotEquals

dropdown / list | Equals, NotEquals | Equals, NotEquals

Value Semantics

- Number values are in Fusion internal units — centimetres for length, radians for angle — not the design's display units. A width of 400 mm is 40.0; an angle of 90° is 1.5708.

- Prefer expressions. Wherever an operator accepts one, write the value as an expression, fixed values included. An expression is written the way you would type it in the Parameters dialog and carries its own units, so a width of 400 mm is 400 mm with no conversion (see Expressions).

- Dropdown values are option keys, not display labels. A dropdown always reads back as a ConfigurationRuleStringListValue, even when a single value was written with a ConfigurationRuleStringValue, so prefer the list form.

- Boolean values follow the aspect's state. For a suppression column, True means the feature is present (not suppressed); for a visibility column, True means visible.

```python
# Dropdown/theme values take a LIST of option keys, even for a single choice:
themeValue = adsk.fusion.ConfigurationRuleStringListValue.create([optionKey])

# Boolean values follow the aspect's state:
suppressValue = adsk.fusion.ConfigurationRuleBooleanValue.create(True)
```

Expressions

Instead of a fixed number or piece of text, a Get or Set block on a number or text column can carry an expression — a formula such as Length / 2 that Fusion evaluates when the rules run. This lets a rule compare or drive one parameter relative to another, the same way you would build a parameter's value from other parameters in the Parameters dialog. Expressions are carried by a ConfigurationRuleExpressionValue, created with ConfigurationRuleExpressionValue.create(expression); its value property gets and sets the formula string.

Prefer expressions wherever they are accepted, for fixed values as well as formulas: write 400 mm rather than the number 40.0, and 'Oak' rather than the string Oak. An expression states its units, so it needs no conversion to internal units. Use ConfigurationRuleNumberValue and ConfigurationRuleStringValue only with the operators that do not accept an expression.

An expression uses the same syntax as Parameter.expression:

- A literal with units — 400 mm or 6.25 in. A number with no units takes the units of the column's parameter.

- A reference to another parameter, or an equation — Height, Length / 2, Width + 2 * Thickness.

- For text columns, literal text in single quotes, joined with + and combined with functions such as if — 'Hello Fusion' or if (Length < 20 mm; 'Short'; 'Long'). Numeric expressions are written without quotes; only literal text inside an expression is single-quoted. In Python, wrap an expression that contains single quotes in a double-quoted string, as in the examples below.

The result must suit the column: a number column needs an expression that evaluates to a compatible number and unit, while a text column accepts either text or a number. Expressions are accepted only by these operators:

Block | Operators that accept an expression

Get | Equals, NotEquals, GreaterThan, GreaterThanOrEqual, LessThan, LessThanOrEqual

Set | Equals

Every other operator takes its literal value class. The one exception is a Get-side Range, whose bounds can be expressions through minExpression and maxExpression on the range value itself (see Ranges).

On the Rules Canvas, an expression appears in a block's value field in place of a number. The rule below drives a minimum shelf count from the cabinet's proportions: when the width is greater than five times the depth plus 100 mm, it sets the minimum number of shelves to 2.

This builds the same rule in code. The Get block compares Width3 against an expression, so the threshold follows Depth in every configuration. The Set block uses Minimum, which takes a literal number rather than an expression.

```python
# The condition: Width3 > (Depth * 5) + 100 mm, evaluated per configuration.
isWide = adsk.fusion.ConfigurationRuleGetBlock.create()
isWide.columnId = width3ColumnId
isWide.operatorType = getOps.GreaterThanConfigurationRuleGetOperator
isWide.value = adsk.fusion.ConfigurationRuleExpressionValue.create('(Depth * 5) + 100 mm')

# The action: at least 2 shelves. Minimum takes a number, not an expression.
minShelves = adsk.fusion.ConfigurationRuleSetBlock.create()
minShelves.columnId = shelfCountColumnId
minShelves.operatorType = setOps.MinimumConfigurationRuleSetOperator
minShelves.value = adsk.fusion.ConfigurationRuleNumberValue.create(2.0)

ifBlock = adsk.fusion.ConfigurationRuleIfBlock.create()
ifBlock.condition = isWide
ifBlock.thenBlocks = [minShelves]

rule = adsk.fusion.ConfigurationRule.create()
rule.name = 'Minimum shelves'
rule.comment = 'Set minimum shelves based on width'
rule.body = [ifBlock]

modifyInput = adsk.fusion.ConfigurationRulesModifyInput.create()
modifyInput.rules = [rule]
result = rulesManager.modifyRules(modifyInput)

for issue in result.issues:
    app.log(f'  issue: {issue.code} - {issue.message}')
```

A Set block with Equals can drive a column from an expression too. On a text column, that lets the value be built from other parameters:

```python
# Drive a text parameter from the length.
setLabel = adsk.fusion.ConfigurationRuleSetBlock.create()
setLabel.columnId = labelColumnId
setLabel.operatorType = setOps.EqualsConfigurationRuleSetOperator
setLabel.value = adsk.fusion.ConfigurationRuleExpressionValue.create(
    "if (Length < 500 mm; 'Short'; 'Long')")
```

Expressions are checked when you submit. Fusion validates each expression against the design's current parameters when modifyRules runs. The Configuration Rules API has no call to check a rule expression in advance. UnitsManager.isValidExpression can catch syntax and unit errors beforehand, but only submitting the rule gives the definitive result, so always inspect issues. A block whose expression fails is reduced to a placeholder with a VALIDATION_FAILED issue, and the rest of the rule still applies. The issue's message names the reason, for example:

Reason in the message | Cause

emptyExpression | The expression string is empty or contains only spaces. create('') is accepted, but the block is rejected on submit.

parseError | The expression is not valid syntax.

variableNotFound | The expression names a parameter the design does not have.

unitMismatch | The result does not suit the column — for example, a length expression on an angle column, or text on a number column.

sameVariableUsed | The expression refers to the column's own parameter, such as Width * 2 on the Width column.

An expression on an operator that does not accept one, or on a boolean or dropdown column, is reported as VALIDATION_FAILED in the same way. Treat these reasons as diagnostic text rather than a fixed list to branch on.

Expressions are evaluated when the rules run. A valid expression is evaluated separately for each configuration, using that configuration's parameter values. If it cannot be evaluated for a configuration — for example, it divides by a parameter that is zero there — the rule reports an ERR_EXPRESSION_INVALID status for that configuration rather than an issue on your call (see Rule statuses).

Read the expression back rather than assuming it is the text you wrote. Fusion stores each expression in a standard form, so the value you read back can differ from what you submitted in spacing, number formatting, or units while meaning the same thing. Compare expressions by what they mean — for example, by checking for the parameter names they reference — rather than by exact string.

A literal value can read back as an expression. On a number or text column with an operator that accepts expressions, Fusion stores a plain ConfigurationRuleNumberValue or ConfigurationRuleStringValue as an expression too, so the block reads back with a ConfigurationRuleExpressionValue — a number comes back as an equivalent expression with units, and the text Oak as the text expression 'Oak'. Code that reads values should check for an expression as well as for the literal class:

```python
getBlock = adsk.fusion.ConfigurationRuleGetBlock.cast(ifBlock.condition)

if getBlock is not None:
    expression = adsk.fusion.ConfigurationRuleExpressionValue.cast(getBlock.value)
    if expression is not None:
        app.log(f'Compares against the expression {expression.value}')
    else:
        number = adsk.fusion.ConfigurationRuleNumberValue.cast(getBlock.value)
        if number is not None:
            app.log(f'Compares against {number.value} (internal units)')
```

Ranges

On a Get block, the Range operator tests whether the column's current value falls within [min, max]. Use a ConfigurationRuleGetRangeValue, and prefer expressions for its bounds: create the range with both bounds unset, then set minExpression and maxExpression. A bound that is not set is open on that side.

```python
# True when the width is between 400 mm and 900 mm, inclusive.
inRange = adsk.fusion.ConfigurationRuleGetBlock.create()
inRange.columnId = widthColumnId
inRange.operatorType = getOps.RangeConfigurationRuleGetOperator
bounds = adsk.fusion.ConfigurationRuleGetRangeValue.create(False, 0.0, False, 0.0)
bounds.minExpression = '400 mm'
bounds.maxExpression = '900 mm'
inRange.value = bounds
```

create(hasMin, min, hasMax, max) takes only numbers, which is why the expressions are assigned afterwards through the range value's minExpression and maxExpression properties. Each bound is either a number or an expression, never both; setting one replaces the other:

- Setting minExpression to a non-empty string also sets hasMin to True and resets min to 0.0. While an expression is the bound, min always reads 0.0 — it does not hold the evaluated result.

- Setting min clears minExpression, sets hasMin to True, and keeps the number you set.

- Setting hasMin to False clears both, leaving the range open below.

- An empty minExpression means "no expression", not an empty expression, so it is never rejected. Setting it to empty leaves min and hasMin as they are, so clearing an expression you set leaves a numeric lower bound of 0.0; set hasMin to False to open the range instead.

maxExpression, max, and hasMax behave the same way.

```python
# True when the width is between half the length and 900 mm, inclusive.
bounds = adsk.fusion.ConfigurationRuleGetRangeValue.create(False, 0.0, False, 0.0)
bounds.minExpression = 'Length / 2'    # hasMin becomes True; min stays 0.0
bounds.maxExpression = '900 mm'

inRange = adsk.fusion.ConfigurationRuleGetBlock.create()
inRange.columnId = widthColumnId
inRange.operatorType = getOps.RangeConfigurationRuleGetOperator
inRange.value = bounds
```

When you read a range back, a bound you submitted as a number may be reported as an equivalent expression, with minExpression populated and min reading 0.0. Test which form a bound is in rather than assuming the form you wrote:

```python
bounds = adsk.fusion.ConfigurationRuleGetRangeValue.cast(getBlock.value)

if bounds is not None and bounds.hasMin:
    if bounds.minExpression:
        app.log(f'Lower bound is the expression {bounds.minExpression}')
    else:
        app.log(f'Lower bound is {bounds.min} (internal units)')
```

On a Set block, the Range operator constrains the column with a lower bound, an upper bound, an increment, or any combination. Use ConfigurationRuleSetRangeValue.create(hasMin, min, hasMax, max, hasIncrement, increment). Each of the three parts — min, max, and increment — is independently optional, and at least one must be set. Only the parts you set take effect: min is the lowest value the user can choose, max the highest, and increment the step between the allowed values in between. When both min and max are set, min must not be greater than max.

```python
# Constrain the width to 400-900 mm in 5 mm steps.
fullRange = adsk.fusion.ConfigurationRuleSetBlock.create()
fullRange.columnId = widthColumnId
fullRange.operatorType = setOps.RangeConfigurationRuleSetOperator
fullRange.value = adsk.fusion.ConfigurationRuleSetRangeValue.create(True, 40.0, True, 90.0, True, 0.5)
```

A Set block can also use Minimum and Maximum with a plain ConfigurationRuleNumberValue, but a Range expresses the same intent in one block and can carry an increment, so prefer Range. Do not use a get-range value on a Set block or a set-range value on a Get block — the two classes differ (only the set range has an increment), and each belongs with its own operator.

AnyOf and NoneOf

Where Range tests or constrains a span of numbers, AnyOf and NoneOf test or constrain a number column against a discrete set of candidate values. On a Get block, AnyOf is true when the column's current value equals one of the selected entries; NoneOf is true when it equals none of them. On a Set block, AnyOf limits the column to the selected entries — there is no set-side NoneOf; use AnyOf whenever a Set block needs to offer a discrete list of numbers.

Both operators carry a ConfigurationRuleNumberSelectionValue, built from an array of ConfigurationRuleNumberSelectionEntry objects assigned to its entries property. Each entry pairs a numeric value (Fusion internal units) with its own isSelected flag, so an entry can be carried in the block without being part of the current selection. At least one entry must be selected; an all-false selection is rejected.

```python
# True when the width is 400 mm, 600 mm, or 900 mm.
anyOf = adsk.fusion.ConfigurationRuleGetBlock.create()
anyOf.columnId = widthColumnId
anyOf.operatorType = getOps.AnyOfConfigurationRuleGetOperator
anyOf.value = adsk.fusion.ConfigurationRuleNumberSelectionValue.create()
anyOf.value.entries = [
    adsk.fusion.ConfigurationRuleNumberSelectionEntry.create(40.0, True),
    adsk.fusion.ConfigurationRuleNumberSelectionEntry.create(60.0, True),
    adsk.fusion.ConfigurationRuleNumberSelectionEntry.create(90.0, True),
]
```

NoneOf reads the same way with NoneOfConfigurationRuleGetOperator; to limit a Set block to the same kind of candidate list, use AnyOfConfigurationRuleSetOperator with a ConfigurationRuleNumberSelectionValue built the same way.

Known Limitations

The supported-columns table above lists what a rule can read and write today. A few limitations are worth calling out:

- Unsupported columns are flagged distinctly. Targeting one of the columns below — a column Fusion recognizes but does not support for rules — is reported as a COLUMN_NOT_SUPPORTED issue rather than the generic VALIDATION_FAILED, so you can tell "this will never work" apart from a typo'd or otherwise unrecognized id (see Issues and errors).

- Property columns (ConfigurationPropertyColumn) cannot be read or written.

- Boolean parameter columns are not yet supported.

- Of the feature-aspect columns, only joint aspects are exposed (for both read and write); thread and hole feature-aspect columns cannot be targeted by a rule.

- Configuration Name is read-only — it can be a Get target but not a Set target.

- Text columns can only be set with  Equals; Contains and NotContains exist only on Get blocks. Set NotEquals is valid only on boolean and dropdown columns.

- NoneOf has no Set-side counterpart — it exists only as a Get operator on number columns; use AnyOf to constrain a Set block to a candidate list.

- Expressions are limited to number and text parameter columns and to the operators listed in Expressions; of the range values, only ConfigurationRuleGetRangeValue has expression bounds. Only submitting a rule fully validates its expressions — inspect issues afterwards.

Issues and Errors

This section covers problems with the call you just made. For what the rules engine found when the rules last ran, see Rule statuses.

The API distinguishes two kinds of problem: non-fatal problems, reported as issues on the returned result, and fatal problems, reported as errors. An operation can succeed overall while a part of it silently degrades, so understanding the difference matters.

Non-fatal problems become issues. When a single block or rule in a request has a problem, the API records an issue and continues: the offending block is reduced to an empty placeholder and the rest of the rule and the batch still apply. The batch is not rolled back. Inspect the issues collection after every call, including reads and apparently successful writes.

Fatal problems are reported as an error. An invalid request shape, an uninitialised rules pipeline, or a missing extension entitlement on a write is reported as an error rather than returning a result. In Python the error is raised as an exception (a RuntimeError), so wrap calls in try/except; in C++ the call does not throw — retrieve the error with Application::getLastError.

The issue Object and Codes

Every issue is a ConfigurationRulesIssue with a code, a message (developer-facing, not localized), a ruleId, a columnId, a path (such as rules[0].body[2]), and a ruleIndex guarded by hasRuleIndex. To correlate an issue back to a rule in your request, use ruleIndex (when hasRuleIndex is True) rather than parsing path.

Code | Meaning

VALIDATION_FAILED | A Get or Set block did not pass validation and was replaced with a placeholder — e.g. a columnId Fusion does not recognize at all, an operator/value not valid for the column, or an expression that is empty or invalid (see Expressions).

COLUMN_NOT_SUPPORTED | A Get or Set block targeted a columnId that Fusion recognizes but does not support for rules (see Known limitations) — distinct from VALIDATION_FAILED, which covers columns Fusion does not recognize at all. The block is replaced with a placeholder the same way.

RULE_NOT_FOUND | An id in deleteRuleIds, or requested through itemByIds, did not match an existing rule.

DELETE_FAILED | A rule could not be deleted.

CREATE_FAILED | A new rule could not be created.

CONVERSION_WARNING | A non-fatal problem occurred while reading a rule back.

EXTENSION_REQUIRED | A write was attempted without the Fusion Design Extension.

BLOCK_ID_CONFLICT | A blockId you supplied was already in use by a block outside the rule being written, so Fusion minted a fresh id instead. The rule still applies; read the ids back (see Block IDs).

BLOCK_ID_NOT_PRESERVED | A blockId you supplied did not end up on the rebuilt block. The rule still applies; read the ids back.

Treat any code you do not recognize as an opaque string — future versions may add more.

```python
result = rulesManager.modifyRules(modifyInput)

if
not result.issues:
    app.log('Applied cleanly.')

for issue in result.issues:
    location = f'rule {issue.ruleIndex}'
if issue.hasRuleIndex else
'request'
    app.log(f'{issue.code} at {location} (column "{issue.columnId}"): {issue.message}')
```

Rule Statuses

A status is what the configuration rules engine found the last time the rules ran, for one rule on one configuration. A rule that fails on four configurations produces four statuses. These are the same errors, warnings, and information the Configuration Rules panel shows against the blocks on the Rules Canvas.

Only problems are reported. A rule that applied cleanly to a configuration reports nothing for it, so the absence of statuses is the signal that all is well.

Statuses answer a different question from issues, and you generally need both:

| Issues | Statuses

Answers | What went wrong with the call I just made? | What did the engine find when the rules last ran?

Where | The issues array on the result of the call | The three getStatuses methods

Scope | The request, or a rule or block in it | One rule on one configuration

Message | Developer-facing, not localized | Localized, ready to display to a user

A modifyRules call can return no issues at all while a rule is switched off on half the design's configurations. Statuses exist only once the rules have run, so a design whose rules have never run returns an empty result — that is not an error.

The Three Queries

All three are read-only, need no Fusion Design Extension, and never trigger a rules run. Each returns a ConfigurationRuleStatusesResult.

Method | Answers | Returns null when

getStatuses() | Everything the engine holds, design-wide | Never — it always returns a result

getStatusesByRuleId(ruleId) | Is this rule healthy? | ruleId names no rule the engine is running

getStatusesByConfigurationId(configurationId) | Is this configuration healthy? | configurationId does not match a row on the design's top configuration table

On the two filtered queries, null and an empty result mean opposite things. An empty statuses array means the subject was found and nothing is wrong — that is the success case. null means there is no such subject. Check for null first: a script that goes straight to result.errorCount == 0 reads a typo'd id as a clean bill of health. Both filtered methods report an error if the id is empty (in Python, a raised exception).

getStatusesByRuleId returns null for an inactive rule as well as an unknown or deleted one, because an inactive rule is excluded from the engine's rule set. Use itemById to tell them apart: it returns the rule when it exists, and ConfigurationRule.isActive then says whether the rule is merely switched off.

The Result Object

A ConfigurationRuleStatusesResult holds the matching statuses, in no guaranteed order, plus errorCount, warningCount, and infoCount. The counts are scoped to the query, so getStatusesByRuleId(ruleId).errorCount is the error count for that one rule. They always sum to the length of statuses, so a health check needs no iteration at all.

A result is a point-in-time snapshot. It does not update when the rules run again or when the design changes — call the query again for current statuses.

The Status Object

Property | Description

severity | A ConfigurationRuleStatusSeverities value. Use this for triage rather than inspecting code.

code | The kind of status, such as ERR_CONSTRAIN. Use this to branch on a specific condition.

message | The localized, human-readable description, ready to display. This is the same text the Configuration Rules panel shows.

ruleId | The rule this status belongs to. Matches ConfigurationRule.id, so the rule can be fetched with itemById.

configurationId | The configuration this status applies to. Matches ConfigurationRow.id on Design.configurationTopTable. Empty when the status is not scoped to a single configuration.

blockId | The block within the rule that raised the status. Matches blockId on a block in the rule's body (see Block IDs). Empty when the status describes the rule as a whole, which is normal, or when the rule's blocks have no ids yet.

Severity

Severity tells you what happened to the rule on the affected configuration. The Error row is the one that matters most: an error does not mean the rule applied and something looked odd, it means the rule is not running there at all.

Value of ConfigurationRuleStatusSeverities | Was the rule applied? | What it means

InformationConfigurationRuleStatusSeverity | Yes | The configuration is correct as generated. The message is best-practice advice about how the rule is authored or how it applied.

WarningConfigurationRuleStatusSeverity | Yes, but it may produce unpredictable results | Review the message and confirm the configuration is what you intended.

ErrorConfigurationRuleStatusSeverity | No | The rule has been turned off for that configuration until the error is resolved. The configuration does not reflect the rule at all, and will not until the reported problem is fixed.

A configuration with no error statuses for a rule had that rule applied to it.

Status Codes

Branch on severity for general triage and on code only when you need a specific condition. Treat any code you do not recognize as an opaque string — future versions may add more.

Code | Severity | Meaning

ERR_CONSTRAIN | Error | The aspect is already constrained by another rule or block with a conflicting value, so this rule could not constrain it.

ERR_EXPRESSION_INVALID | Error | An expression — in a parameter, or in one of the rule's blocks — could not be evaluated for the affected configuration (see Expressions).

ERR_INVALID_INPUT | Error | The block is missing data it requires. Rebuild the block, and contact Autodesk Support if it recurs.

ERR_UNHANDLED | Error | The block hit an error Fusion could not classify. Contact Autodesk Support.

WARN_CUSTOM_CONSTRAIN | Warning | A non-custom aspect is driven by a custom aspect, so only parent-row values change.

WARN_SNAP_CONSTRAIN | Warning | Both joint snaps point to the same component, which a joint does not allow.

WARN_INCOMPLETE | Warning | The block is an unconfigured placeholder, so it is ignored when the rule runs.

INFO_CONSTRAIN | Information | Another block also constrains the aspect, so only the values common to both are valid.

INFO_SNAP_CONSTRAIN | Information | A joint snap list contains an invalid option; the last valid snap is selected.

INFO_CYCLE | Information | The same aspect is referenced in a Get block and a Set block, which may create a cycle and produce unstable results (see Avoiding cycles).

Reading Every Status

```python
severities = adsk.fusion.ConfigurationRuleStatusSeverities
labels = {
    severities.ErrorConfigurationRuleStatusSeverity: 'ERROR',
    severities.WarningConfigurationRuleStatusSeverity: 'WARNING',
    severities.InformationConfigurationRuleStatusSeverity: 'INFO',
}

result = rulesManager.getStatuses()
app.log(f'{result.errorCount} error(s), {result.warningCount} warning(s), '
        f'{result.infoCount} information.')

for status in result.statuses:
    # blockId is empty when the status describes the rule as a whole.
    block = status.blockId or '-'
    app.log(f'[{labels[status.severity]}] {status.code} rule={status.ruleId} '
            f'configuration={status.configurationId} block={block}: {status.message}')
```

Checking One Rule

A non-null result with a zero errorCount means the rule is active and was applied to every configuration.

```python
health = rulesManager.getStatusesByRuleId(ruleId)

if health is None:
    # Not a rule the engine is running. itemById separates a deleted rule, where it
    # reports an error, from an inactive one, where it returns the rule.
    try:
        rule = rulesManager.itemById(ruleId).rule
        app.log(f'"{rule.name}" is inactive, so it is not evaluated.')
    except RuntimeError:
        app.log('No rule with that id exists.')
elif health.errorCount == 0:
    app.log('Applied to every configuration.')
else:
    app.log(f'Turned off on {health.errorCount} configuration(s).')
```

Checking One Configuration

Configuration ids are ConfigurationRow.id values from Design.configurationTopTable. The result also carries every status that names no configuration at all — a rule with an unfilled socket is a problem for this configuration too — so it may contain entries whose configurationId is empty rather than the id you asked for.

```python
rows = design.configurationTopTable.rows

for i in range(rows.count):
    row = rows.item(i)
    health = rulesManager.getStatusesByConfigurationId(row.id)

    if health is None:
        app.log(f'{row.name}: not a row on the top configuration table.')
    elif health.errorCount == 0:
        app.log(f'{row.name}: reflects every rule.')
    else:
        app.log(f'{row.name}: {health.errorCount} rule(s) turned off.')
        for status in health.statuses:
            app.log(f'    {status.code}: {status.message}')
```

Finding the Block That Raised a Status

When blockId is not empty, it names a block in the rule's body. Read the rule with itemById and walk the body to find it — remembering that an If block nests further blocks in its condition, thenBlocks, elseIfBranches, and elseBlocks. The example below descends through If blocks; extend it through the left, right, and operand of And, Or, and Not blocks if your rules nest conditions.

```python
def findBlock(blocks, blockId):
    """Depth-first search of a statement list for the block with the given id."""
    for block in blocks:
        if block.blockId == blockId:
            return block

        ifBlock = adsk.fusion.ConfigurationRuleIfBlock.cast(block)
        if ifBlock is None:
            continue

        # Everything an If block can nest: its own condition and then-branch, each
        # else-if branch's condition and then-branch, and the else branch.
        nested = list(ifBlock.thenBlocks) + list(ifBlock.elseBlocks)
        if ifBlock.condition is not None:
            nested.append(ifBlock.condition)
        for branch in ifBlock.elseIfBranches:
            nested += list(branch.thenBlocks)
            if branch.condition is not None:
                nested.append(branch.condition)

        found = findBlock(nested, blockId)
        if found is not None:
            return found

    return None

for status in rulesManager.getStatuses().statuses:
    if not status.blockId:
        continue    # Describes the rule as a whole rather than one block.

    rule = rulesManager.itemById(status.ruleId).rule
    block = findBlock(rule.body, status.blockId)
    if block is not None:
        app.log(f'{status.code} raised by {block.objectType} in "{rule.name}".')
```

Best Practices

Writing clear rules

- One concern per rule. Keep each rule focused on a single constraint, such as "power option requires a table." Single-purpose rules are easier to read, reorder, and toggle while troubleshooting.

- Name rules clearly. Prefer short constraint phrasing ("Width minimum 400 mm") over generic names. Duplicate names are disambiguated automatically on submit.

- Use comments for intent. Set the rule's comment, and use ConfigurationRuleCommentBlock entries to document sections of a body.

- Prefer expressions. Wherever an operator accepts an expression, use one — fixed values included — rather than a number or string value (see Expressions).

- Complete every block. A Get or Set block with no operator, value, or columnId is ignored when the rule runs; inspect issues to find placeholders.

- Keep logic flat. Prefer one If with elseIfBranches over nested If blocks, and prefer a Range or a multi-value ConfigurationRuleStringListValue over nested And/Or blocks — a range for a span of numbers, a multi-entry list to accept several dropdown options.

Ordering and Evaluation

Rules are evaluated top to bottom, and the statements within a rule run in order. When more than one rule or block affects the same column, order determines the outcome, so use orderedRuleIds to control it deliberately. When multiple Set blocks limit the same column under the same condition, the result is the intersection of their value lists — you can narrow a list this way but not widen it. If two rules leave no value in common, the configuration has no valid value for that aspect, which is an error; lead with the least restrictive condition and review rules that constrain the same aspect.

Avoiding Cycles

A rule can both read and write the configuration, but avoid cycles that never settle. A cycle arises when rules read and write each other's columns in a loop — for example, Rule 1 sets Width from Length while Rule 2 sets Length from Width — so the values oscillate rather than settle. Avoid reading and writing the same column within one rule unless the write immediately satisfies the read, and structure rules so their conditions read from different columns than the ones they set.

Expressions can create the same kind of loop less visibly, because the parameters an expression references are reads too. Setting Width to Length / 2 in one rule while another rule sets Length from Width is a cycle, even though neither Get block mentions the other column. Fusion accepts such rules when you submit them — only an expression that refers to its own column is rejected — and the INFO_CYCLE status does not flag them either, because it only compares the columns of Get and Set blocks. Review the parameters your expressions reference as carefully as the columns your conditions read.

See also

- Configurations — creating a Configured Design and working with the configuration table using the API.

- Configuration Rules (product help) — Authoring rules on the Rules Canvas, block reference, and best practices in the user interface.

---
