bl_info = {
    "name" : "CoreBnimation",
    "author" : "Blaking707",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 3),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}
import bpy
import string
import re

from bpy_extras.io_utils import ExportHelper
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

class ImportCore(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "core.importdata" 
    bl_label = "Core_Import"

    filename_ext = ".pbt"

    filter_glob: StringProperty(
        default="*.pbt",
        options={'HIDDEN'},
        maxlen=255,
    )

    use_setting: BoolProperty(
        name="UseChildData",
        description="Set names to children type",
        default=True,
    )

    def execute(self, context):
        Data = ImportptbAsDic(context, self.filepath)
        print("____")
        return ExecuteImport(context, Data, self.use_setting)

#ADDS TO EXPORT BAR
def menu_func_import(self, context):
    self.layout.operator(ImportCore.bl_idname, text="CoreTemplate")

def ImportptbAsDic(context, filepath):
    
    f = open(filepath, 'r', encoding='utf-8')
    AllObj = []
    Lines = f.readlines()
    Passtext = Lines.copy()
    for line in Lines:
        line = line.replace(" ","")
        if ("Objects" in line):
            obj = SetObjectData(GetBracketGroup(Passtext, "Objects"))
            AllObj.append(obj)
        Passtext.pop(0)
    f.close()   

    print("____")
    """
    for o in AllObj:
        print(o.Name)
        print(o.Id)
        print(o.Rotation)
        print(o.Scale)
        print(o.Location)
    """
    return AllObj

def GetBracketGroup(Lines, text):
    PassText = Lines.copy()
    count = 0
    Objectstring = []
    for line in Lines:
        line = line.replace("Pitch","X")
        line = line.replace("Yaw","Y")
        line = line.replace("Roll","Z")
        if (text in line):
            count = 1
            continue
        if(count > 0):
            Objectstring.append(line)
            if("{" in line):
                count +=1
            elif("}" in line):
                count -= 1
                if(count == 0):
                    return Objectstring
    PassText.pop(0)
    raise Exception('Not Enough }')
    return None

def SetVector(text, name ):
    Data = GetBracketGroup(text, name)
    BlankReturnData =  {"X":0,"Y":0,"Z":0}
    for Entry in Data:
        Entry = Entry.replace(" ","")
        Entry = Entry.replace("\n","")
        if Entry[0] in BlankReturnData:
            BlankReturnData[Entry[0]] = float(Entry.replace(Entry[0]+Entry[1], "" ))
    return BlankReturnData

def SetValue(Text, Lable):
    tmp = Text.replace(Lable,"")
    tmp = tmp.replace('"',"")
    tmp = tmp.replace('\n',"")
    tmp = tmp.replace(" ","")
    return tmp

def SetObjectData(text):
    obj = Object()
    ChildData = []
    
    for line in text:
        if (" Id:" in line):
            if (obj.Id == None) :
                obj.Id = SetValue(line,"Id:")
                obj.Name = SetValue(line,"Id:")
            else :
                obj.MeshId = SetValue(line,"Id:")
        if ("Name" in line):
            pass
            #obj.Name = SetValue(line,"Name:")
        if ("ParentId" in line):
            obj.ParentId = SetValue(line,"ParentId:")
        if ("Scale" in line):
            obj.Scale = SetVector(text, "Scale")
        if ("Rotation" in line):            
            obj.Rotation = SetVector(text, "Rotation")
        if ("Location" in line):
            obj.Location = SetVector(text, "Location")
        if ("ChildIds" in line):
            ChildData.append(SetValue(line,"ChildIds:"))
    obj.Children = ChildData
    return obj   
            
class Object:
    def __init__(self,Id = None, Name = "None", Location = {"X":0,"Y":0,"Z":0}, Rotation =  {"X":0,"Y":0,"Z":0}, Scale =  {"X":1,"Y":1,"Z":1}, ParentId = "None" , MeshId = "None"):
        self.Id = Id
        self.Name = Name
        self.Location = Location
        self.Rotation = Rotation
        self.Scale = Scale
        self.Parent = ParentId
        self.MeshId = MeshId
  
def ExecuteImportObject(context, Data):
    bops = bpy.data.objects
    SpawnedObjs = []

    for Entry in Data:
        EntryObject = bops.new(name="data", object_data=None)  
        EntryObject.name = Entry.Name
        EntryObject.location = (Entry.Location["X"]/100,Entry.Location["Y"]/100,Entry.Location["Z"]/100)
        EntryObject.scale = (Entry.Scale["X"],Entry.Scale["Y"],Entry.Scale["Z"])
        EntryObject.rotation_euler =  (Entry.Rotation["X"],Entry.Rotation["Y"],Entry.Rotation["Z"])
        EntryObject["Id"] =  Entry.Id
        EntryObject["ParentId"] =  Entry.Parent
        EntryObject["MeshId"] =  Entry.MeshId
        bpy.context.view_layer.active_layer_collection.collection.objects.link(EntryObject) 
        SpawnedObjs.append(EntryObject)
    
    for Entry in SpawnedObjs:
        Parent = findParent(SpawnedObjs, Entry["ParentId"])
        if(Parent != None):
            Entry.parent = Parent


    return {'FINISHED'}

def ExecuteImport(context, Data, Setting):
    SpawnedObjsDat = {}
    SpawnedObjs = []
    Armdata = bpy.data.armatures.new(name="Amature")
    Armdata.display_type = 'BBONE'
    Armob = bpy.data.objects.new(Data[0].Name, object_data=Armdata)
    bpy.context.view_layer.active_layer_collection.collection.objects.link(Armob)
    bpy.context.view_layer.objects.active =  Armob
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    edit_bones = Armob.data.edit_bones
    Bbones = Armob.pose.bones
    
    if(Setting):
        Data = SetChildAsName(Data)

    #SPAWN BONES
    for Entry in Data:  
        b = edit_bones.new(Entry.Name)
        b.envelope_distance = 0
        b.head = (0, 0, 0.0)
        b.tail = (0, 0.01, 0)
        b["Id"] =  Entry.Id
        b["ParentId"] =  Entry.ParentId
        b["MeshId"] =  Entry.MeshId
        b["Children"] =  Entry.Children
        SpawnedObjsDat[b.name] = ((Entry.Location["X"]/100,Entry.Location["Y"]/100,Entry.Location["Z"]/100),(Entry.Rotation["X"],Entry.Rotation["Y"],Entry.Rotation["Z"]),(Entry.Scale["X"],Entry.Scale["Y"],Entry.Scale["Z"]))
        SpawnedObjs.append(b)
        
    #SET PARENT RELATION

    for Entry in SpawnedObjs:
        Parent = findParent(SpawnedObjs, Entry["ParentId"])
        if(Parent != None):
            Entry.parent = Parent


    #CHANGE TO POSE AND SET POSITIONS
    bpy.ops.object.mode_set(mode='POSE', toggle=False)
    for Entry in Bbones:
        Entry.location = SpawnedObjsDat[Entry.name][0]
        Entry.rotation_mode = "XYZ"
        Entry.rotation_euler = SpawnedObjsDat[Entry.name][1]
        Entry.rotation_mode = "QUATERNION"
        Entry.scale = SpawnedObjsDat[Entry.name][2] 

    #SAVE POSITIONS TO A POSE LIBARY AND MAKE SURE ITS A FAKE USER
    #could use position reset save, no scale (doing this but its dumb)
    #could set default action so they can reset themselves
    """
    bpy.ops.pose.armature_apply(selected=False)
    for Entry in Bbones:
        Entry.scale = SpawnedObjsDat[Entry.name][2]
        Entry.location = SpawnedObjsDat[Entry.name][0]
    """
    ##This is dumb the location is off when reset

    return {'FINISHED'}

def SetChildAsName(Data):
    Outerindex = 1
    for Entry in Data:
        index = 1
        for Child in Entry.Children:
            for O in Data:
                if(O.Id == Child):
                    O.Name = str(index)
                    index += 1
        if (HasParent(Data,Entry.ParentId) == False):
            Entry.Name = str(Outerindex)
            Outerindex += 1
    for Entry in Data:
        for Child in Entry.Children:
            for O in Data:
                if(O.Id == Child):
                    O.Name = Entry.Name + "-" +O.Name
    return Data

def findParent(List, id):
    for O in List:
        if(O['Id'] == id):
            return O
    return None

def HasParent(Data, id):
    for O in Data:
        if(O.Id == id):
            return True
    return False

class ExportSomeData(Operator, ExportHelper):
    """Export Animations to Core"""
    bl_idname = "core.exportdata" 
    bl_label = "Core_Export"

    # ExportHelper mixin class uses this
    filename_ext = ".lua"

    filter_glob: StringProperty(
        default="*.lua",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return write_some_data(context, self.filepath)

def write_some_data(context, filepath):
    Document = "Animations = {\n"
    actions = bpy.data.actions
    for action in actions:
        Document += ("\t"* 1 +  action.name +" = { \n")
        Document += ("\t"*2 +"Start = "+ str(action.frame_range.x) + ",\n")
        Document += ("\t"*2 +"End = "+ str(action.frame_range.y) + ",\n" )
        Document += ("\t"*2 +"Keyframes = {\n")
        index = 0
        for group in action.groups:
            Document += ("\t" * 3  + "Object{} {}\n".format(index, "= {") )
            Document += ("\t" * 4  + "Name =  '{}',\n".format(group.name) )
            Document += ("\t" * 4  + "FrameData = {\n")
            for Channel in group.channels:
                Channeltype = re.sub(".*\.", "" ,Channel.data_path)[0]
                Document += ( "\t" * 5 + "{} {}\n" .format(Channeltype + return_xyzw(Channel.array_index, Channeltype) , "= {"))
                for keyframe in Channel.keyframe_points:

                    Document +=( "\t" *6 + "{" + "{},{}".format(keyframe.co.x,round(keyframe.co.y if ( Channeltype != "l" ) else keyframe.co.y * 100,7)) + "},\n" )
                Document += ("\t"*5 +"},\n")
            Document += ("\t"*4 +"},\n")
            Document += ("\t"*3 +"},\n")
            index += 1
        Document += ("\t"*2 +"}\n \t },\n")
    Document += ("}\nreturn Animations")

    f = open(filepath, 'w', encoding='utf-8')
    f.write(Document)
    f.close()
    """
    datadict = {}
    actions = bpy.data.actions
    for action in actions:
        for group in action.groups:
            for channel in group.channels:
                for keyframe in channel.keyframe_points:
                   nested_set(datadict,[action.name,group.name, re.sub(".*\.", "" ,channel.data_path),str(keyframe.co.x), str(channel.array_index)], keyframe.co.y )
                   
                   
                    #print(re.sub(".*\.", "" ,Channel.data_path))    
    print(datadict)    
    """             
    return {'FINISHED'}

# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportSomeData.bl_idname, text="CoreExport")

def nested_set(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value

def return_xyzw(value, datapath):
    case = {
        0:"x",
        1:'y',
        2:'z',
        3:'w',
    }

    caserot = {
        0:"w",
        1:'x',
        2:'y',
        3:'z',  
    }
    if (datapath == "r"):
        return str(caserot.get(value))     
    else:
        return str(case.get(value))

def register():
    bpy.utils.register_class(ExportSomeData)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.utils.register_class(ImportCore)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ExportSomeData)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(ImportCore)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
