bl_info = {
  "name": "Random Walking Splines A",
  "author": "Desmarkie",
  "description": "Generate splines with a random walk",
  "location": "Add > Mesh",
  "category": "Object"
}

import bpy
import bmesh
import random
from mathutils import Vector
from mathutils import Euler
from bpy.props import IntProperty, FloatProperty


class RandomWalkingSplines(bpy.types.Operator):
  
  """Generate splines with a random walk"""
  bl_idname = "desmarkie_addons.generative"
  bl_label = "Random Walking Splines"
  bl_description = "Generate splines with a random walk"
  bl_options = {"REGISTER", "UNDO"}

  # generation properties for Tool panel
  randomSeed = IntProperty(
    name="Random Seed",
    default=0,
    min=0,
    max=999999,
    subtype="NONE",
    description="Seed used to for PRNG"
  )  

  numCurves = IntProperty(
    name="Number of Curves",
    default=30,
    min=1,
    max=1024,
    subtype="NONE",
    description="Number of curves to create"
  )

  pathLength = IntProperty(
    name="Number of Path Steps",
    default=128,
    min=1,
    max=1024,
    subtype="NONE",
    description="Number of random steps added to a path"
  )

  minMove = FloatProperty(
    name="Minimum wander amount",
    default=0.1,
    min=-9999,
    max=9999,
    subtype="NONE",
    description="Minimum wander rotation applied to walk algorithm"
  )

  maxMove = FloatProperty(
    name="Maximum wander amount",
    default=2,
    min=-9999,
    max=9999,
    subtype="NONE",
    description="Maximum wander rotation applied to walk algorithm"
  )


  # create a new Random() for seeding
  prng = random.Random()


  # return a random float between min & max
  def random_range( self, min, max ):
    return min + ( self.prng.random() * ( max - min ) )

  # generate a line of vertices with a random walk pattern
  def generate_walking_verts( self, pathLength ):
    
    # create array for verts
    verts = []

    # minimum path length of 1
    if pathLength < 1:
      pathLength = 1

    # add the first array at origin
    verts.append( ( 0, 0, 0 ) )

    # last position and movement vecs
    lastPos = Vector( ( 0, 0, 0 ) )
    moveVec = Vector( ( 0, 0, .1 ) )

    # add a new vert for each path step
    for i in range( 0, pathLength - 1 ):
      # rotate the move vector a little
      moveVec.rotate(Euler((
        self.random_range( self.minMove, self.maxMove),
        self.random_range( self.minMove, self.maxMove),
        self.random_range( self.minMove, self.maxMove)
      )))

      # new vert pos is lastPos + move vec
      lastPos = lastPos + moveVec

      # append to verts array
      verts.append( ( lastPos.x,lastPos.y,lastPos.z ) )

    # return it
    return verts


  # generate a curve made from walking verts
  def generate_curve( self, pathLength, curveCount ):

    # generate verts
    verts = self.generate_walking_verts( pathLength )

    # create a new curve object
    curveData = bpy.data.curves.new("random-walking-curve-"+str(curveCount), type="CURVE")
    curveData.dimensions = "3D"
    # mesh resolution
    curveData.resolution_u = 2
    # tube diameter, resolution and fill type
    curveData.bevel_depth = 0.01
    curveData.bevel_resolution = 8
    curveData.fill_mode = "FULL"

    # create new nurbs object on curveData and add points from verts
    polyline = curveData.splines.new("NURBS")
    polyline.points.add(len(verts))
    for i, coord in enumerate(verts):
      x,y,z = coord
      polyline.points[i].co = ( x, y, z, 1 )

    # grab the curve material...
    mat = bpy.data.materials.get("CurveMaterial")
    # ...create one if not already there
    if mat is None:
      mat = bpy.data.materials.new(name="GeneratedCurveMaterial")

    # create a new scene object with the curveData
    curveObj = bpy.data.objects.new("random-walking-curve-"+str(curveCount), curveData)
    if curveObj.data.materials:
      curveObj.data.materials[0] = mat
    else:
      curveObj.data.materials.append( mat )

    # add it to the scene
    scene = bpy.context.scene
    scene.objects.link(curveObj)
    
    # and select it
    curveObj.select = True

    # return new object
    return curveObj


  # called by blender to execute the addon
  def execute(self, context):

    # used for naming children
    curveCount = 0

    self.prng = random.Random()
    self.prng.seed( self.randomSeed )

    # scene ref
    scene = bpy.context.scene

    # look for empty in scene....
    empty = bpy.data.objects.get("RandomWalkingSplines")
    # ... create one if it doesn't exist....
    if empty is None:

      empty = bpy.data.objects.new("RandomWalkingSplines", None)
      scene.objects.link( empty )

    else: # ... delete all it's children if it does

      bpy.ops.object.select_all( action = "DESELECT" )

      for child in empty.children:
        child.select = True

      bpy.ops.object.delete()

    # select the empty and set as active object
    empty.select = True
    scene.objects.active = empty

    # generate required number of paths
    # increment curveCount
    # set new curve parent to empty
    for i in range( 0, self.numCurves ):

      curve = self.generate_curve( self.pathLength, curveCount )
      curveCount = curveCount + 1
      curve.parent = empty

    # all done!
    return {"FINISHED"}

# display in Add > Mesh menu
def menu_func(self, context):
    self.layout.operator(RandomWalkingSplines.bl_idname, icon = "CURVE_PATH")

# register Addon and add to menu
def register():
  bpy.utils.register_class(RandomWalkingSplines)
  bpy.types.INFO_MT_mesh_add.append(menu_func)

# unregister and remove
def unregister():
  bpy.utils.unregister_class(RandomWalkingSplines)
  bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
  register()