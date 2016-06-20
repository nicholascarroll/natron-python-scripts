# -*- coding: utf-8 -*-
#Reconstruct Cycles Toolset PyPlug
import NatronEngine

#To access selection in the NodeGraph
from NatronGui import *
import sys
from collections import namedtuple


#Specify that this is a toolset and not a regular PyPlug
def getIsToolset():
    return True

def getPluginID():
    return "com.casanico.ReconstructCycles"

def getLabel():
    return "Reconstruct Cycles"

def getVersion():
    return 1

def getGrouping():
    return "Other"

def getPluginDescription():
    return "Reconstructs the Cycles combined pass for a single reader selected in the Node Graph."

def make_room(app,node, pixels):
    """ Repositions all nodes under node so many pixels to the right.
    """
    needsashove = False
    from_x = node.getPosition()[0] - 10
    from_y = node.getPosition()[1]
    to_x = from_x + 10 + pixels
    all_nodes = app.getChildren() 
    for node in all_nodes:
        node_x, node_y = node.getPosition()
        if (node_x > from_x) and (node_x < to_x) and (node_y > from_y):
            needsashove = True
            break
    if needsashove:
        for node in all_nodes: 
            node_x, node_y = node.getPosition()
            if (node_x > from_x) and (node_y > from_y):
                node.setPosition(node_x+pixels, node_y)

def append_shuffle(app,parent,layer, label): 
    """Creates a shuffle node and connects it to parent.

    Defaults all outputs to one layer and gives it the label you specify.
    """
    s = app.createNode('net.sf.openfx.ShufflePlugin')
    s.connectInput(1, parent) 
    s.setScriptName(label)
    s.setLabel(label)
    s.getParam('outputChannelsChoice').setValue('Color.RGBA')
    params = ('outputRChoice','outputGChoice','outputBChoice','outputAChoice')
    # TODO maybe set alpha to CYCLES_COMBINED_LAYER for all
    for i in params:
        s.getParam(i).setValue('0')
    for i in range(layer.getNumComponents()):    
        s.getParam(params[i]).setValue('A.' + layer.getLayerName() + '.'
                                       + layer.getComponentsNames()[i])
    return s

def reconstruct_combined(app):
    """Reconstructs the combined pass for a single reader selected in the Node Graph. 

    Valid values for renderer are: 'CYCLES'.
    """
    # CONSTANTS
    ## Blender Cycles Passes
    ### TODO need to test with multiple layers
    ### TODO debug the TypeError: 'NoneType' object is not callable error
    Shader = namedtuple('BSDF', ['name', 'direct', 'indirect', 'colour'])
    CYCLES_DIFFUSE_BSDF = Shader(name = 'Diffuse',
                                 direct = 'RenderLayer.DiffDir',
                                 indirect = 'RenderLayer.DiffInd',
                                 colour = 'RenderLayer.DiffCol')
    CYCLES_GLOSSY_BSDF = Shader(name = 'Glossy',
                                direct = 'RenderLayer.GlossDir',
                                indirect = 'RenderLayer.GlossInd',
                                colour = 'RenderLayer.GlossCol')
    CYCLES_TRANSMISSION_BSDF = Shader(name = 'Transmission',
                                      direct = 'RenderLayer.TransDir',
                                      indirect = 'RenderLayer.TransInd',
                                      colour = 'RenderLayer.TransCol')
    CYCLES_SUBSURFACE_BSDF = Shader(name = 'Subsurface',
                                    direct = 'RenderLayer.SubsurfaceDir',
                                    indirect = 'RenderLayer.SubsurfaceInd',
                                    colour = 'RenderLayer.SubsurfaceCol')
    CYCLES_ENVIRONMENT_LAYER = 'RenderLayer.Env'
    CYCLES_EMISSION_LAYER = 'RenderLayer.Emit'
    CYCLES_COLOUR_LAYER = 'Color'
    CYCLES_COMBINED_LAYER = 'RenderLayer.Combined'
    CYCLES_OBJECT_INDEX_LAYER = 'RenderLayer.IndexOB'
    CYCLES_DEPTH_LAYER = 'RenderLayer.Depth'

    # VALIDATION
    selectedNodes = app.getSelectedNodes()
    if len(selectedNodes) != 1: 
        natron.informationDialog("Info","Select one reader.")
        return
    reader = selectedNodes[0]
    if reader.getPluginID() not in natron.getPluginIDs('.Read'):
        natron.informationDialog("Info","First select a reader.")
        return
    layers = reader.getAvailableLayers()
    if len(layers) < 2:
        natron.errorDialog("Error","This node has no layers.")
        return

    last_node = reader
    make_room(app,reader, 400)
    leaf_list = []

    for BSDF in [CYCLES_DIFFUSE_BSDF,
                 CYCLES_GLOSSY_BSDF,
                 CYCLES_TRANSMISSION_BSDF,
                 CYCLES_SUBSURFACE_BSDF]:
        Direct = None
        Indirect = None
        Colour = None
    
        for layer in layers.keys():
            if layer.getLayerName() == BSDF.direct:
                Direct = append_shuffle(app,last_node, layer, BSDF.name+' Direct')
                x,y = last_node.getPosition() 
                Direct.setPosition(x,y+150)
                last_node = Direct

        for layer in layers.keys():
            if layer.getLayerName() == BSDF.indirect:
                Indirect = append_shuffle(app,last_node, layer, BSDF.name+' Indirect')
                x,y = last_node.getPosition()
                Indirect.setPosition(x,y+50)
                last_node = Indirect

                if Direct is not None and Indirect is not None:
                    dot = app.createNode('fr.inria.built-in.Dot')
                    x,y = last_node.getPosition()
                    dot.setPosition(x+163,y-43)
                    dot.connectInput(0, Direct)

                    Dir_Ind = app.createNode('net.sf.openfx.MergePlugin')
                    Dir_Ind.setScriptName(BSDF.name+'_Dir_Ind')
                    Dir_Ind.setLabel(BSDF.name+' Dir Ind')
                    x,y = last_node.getPosition()
                    Dir_Ind.setPosition(x+130,y-10)
                    Dir_Ind.getParam('operation').set('plus')
                    Dir_Ind.getParam('AChannelsA').setValue(False)
                    Dir_Ind.connectInput(1, Indirect)
                    Dir_Ind.connectInput(0, dot)

        for layer in layers.keys():
            if layer.getLayerName() == BSDF.colour:
                Colour = append_shuffle(app,last_node, layer, BSDF.name+' Colour')
                x,y = last_node.getPosition()
                Colour.setPosition(x,y+50)
                last_node = Colour

                if Direct is not None and Indirect is not None and Colour is not None:
                    Complete_BSDF = app.createNode('net.sf.openfx.MergePlugin')
                    Complete_BSDF.setScriptName(BSDF.name)
                    Complete_BSDF.setLabel(BSDF.name)
                    x,y = last_node.getPosition()
                    Complete_BSDF.setPosition(x+130,y-10)
                    Complete_BSDF.getParam('operation').set('multiply')
                    Complete_BSDF.connectInput(0, Dir_Ind)
                    Complete_BSDF.connectInput(1, Colour)
                    leaf_list.append(Complete_BSDF)

                    Backdrop = app.createNode('fr.inria.built-in.BackDrop')
                    Backdrop.setScriptName(BSDF.name+'_Backdrop')
                    Backdrop.setLabel(BSDF.name.upper())
                    x,y = last_node.getPosition()
                    Backdrop.setPosition(x-20,y-150)
                    Backdrop.setSize(250, 200)

    for layer in layers.keys():
        if layer.getLayerName() == CYCLES_EMISSION_LAYER:
            Emission = append_shuffle(app,last_node, layer, 'Emission')
            x,y = last_node.getPosition()
            Emission.setPosition(x,y+100)
            last_node = Emission
            leaf_list.append(Emission)

    for layer in layers.keys():
        if layer.getLayerName() == CYCLES_ENVIRONMENT_LAYER:
            Environment = append_shuffle(app,last_node, layer, 'Environment')
            x,y = last_node.getPosition()
            Environment.setPosition(x,y+50)
            Environment.getParam('disableNode').setValue(True)
            last_node = Environment
            leaf_list.append(Environment)

    final_merge = app.createNode('net.sf.openfx.MergePlugin')
    final_merge.setLabel('Combined')
    final_merge.getParam('operation').set('plus')
    final_merge.getParam('AChannelsA').setValue(False)
    x,y = last_node.getPosition() 
    final_merge.setPosition(x+300,y+50)
    for z in zip([0,1,3,4,5,6,7,8,9],leaf_list):# TODO refactor
        dot = app.createNode('fr.inria.built-in.Dot')
        x,y = z[1].getPosition()
        dot.setPosition(final_merge.getPosition()[0]+30,y+10)
        dot.connectInput(0, z[1])
        final_merge.connectInput(z[0],dot)

    return


def createInstance(app,group):
    #Since this is a toolset, group will be set to None
    reconstruct_combined(app)
