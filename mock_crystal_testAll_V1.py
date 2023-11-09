# -*- coding: utf-8 -*-
"""
Created on Sun Oct 22 22:42:18 2023

@author: jderoo
"""

from opentrons import protocol_api, types # , execute

import os
import sys
import json
import math



vialPipetteOffsets = {
    "DeRoo_GREINER_50mL": {
        "volume_offset": 5,    # mL
        "volume_step":  50,    # mL
        "offset":      -93.25, # mm
        "step":         81.1,  # mm
        "maxVolume":    50     # mL
                          }
}

# this function was written by Thomas Lauer
# https://github.com/tjlauer/Opentrons_OT-2
def getTopOffset(plate, vialLocation, vialName, volume_uL):
    
    volume_uL = volume_uL - 1000
    
    if vialName == "Sample_2mL":
        return plate[vialLocation].bottom(5)
    
    volume = volume_uL / 1000
    vial = vialPipetteOffsets[vialName]
    
    if volume < vial["volume_offset"]:
        # return True
        return plate[vialLocation].bottom(2)
    else:
        slope = ((vial["offset"] + vial["step"]) - vial["offset"]) / (vial["volume_step"] - vial["volume_offset"])
        intercept = vial["offset"] - slope * vial["volume_offset"]
        
        if volume > vialPipetteOffsets[vialName]["maxVolume"]:
            vialOffset = (slope * vialPipetteOffsets[vialName]["maxVolume"]) + intercept
        else:
            vialOffset = (slope * volume) + intercept
        
        roundingDigits = 2

        return plate[vialLocation].top(round(vialOffset, roundingDigits))
    
    
metadata = {
    'apiLevel': '2.11',
    'protocolName': 'Crystals: Colors practice run',
    'description': '''A protocol for growing CJ crystals with custom 
     labware as provided by the OpenTrons team. This file name is 
     hamptonresearch_24_wellplate_24x500ul.json''',
    'author': 'Jacob DeRoo'
    }

def convert_L2N(L):
    if L == 'A':
        out = 0
    if L == 'B':
        out = 1
    if L == 'C':
        out = 2
    if L == 'D':
        out = 3
    if L == 'E':
        out = 4
    if L == 'F':
        out = 5
    
    return out*30 

def run(protocol: protocol_api.ProtocolContext):

    # some constants that we use somewhat frequently
    height  = 8     # come comically far above the well for safety
    depth   = -10   # how far into resivour to go to dipsense liquid
    offset  = 5.5   # mm, distance away from center  to resivour
    delay   = 0.25  # sec, slow robot down for liquid's benefit
    m_vol   = 49    # starting volume (mL) of magenta
    b_vol   = 49    # starting volume (mL) of teal/blue
    w_vol   = 49    # starting volume (mL) of water
    y_vol   = 49    # starting volume (mL) of yellow
    
    const_vol_in_p300    = 20   # constant volume in the p300 for reverse pipette mimic
    p300_tip_size        = 200  # pipette tip size
    num_laps             = 8    # number of stops/checks for mixing in resivour
    const_vol_in_p10     = 2    # constant volume in the p10 for reverse pipette mimic
    growth_well_half_vol = 5    # volume of the resivour or pure protein in growth well
    
    

    letters = 'ABCDEF'
    numbers = [1, 2, 3, 4]
    wells   = []
    
    # convert to uL from mL
    all_volumes = [m_vol*1000, b_vol*1000, w_vol*1000, y_vol*1000]

    
    
    for i in letters:
        for j in numbers:
            
            wells.append(i + str(j))
   
            
    my_dict = {}
    for well in wells:
        
        tmp = {}
        tmp['right'] = convert_L2N(well[0])
        tmp['down']  = (int(well[1]) - 1)*50
        tmp['water'] = 400 - (tmp['right'] + tmp['down'])
    
        my_dict[well] = tmp
    
    
    #reservoir     = protocol.load_labware('opentrons_15_tuberack_falcon_15ml_conical', 5) 
    #pure_CJ       = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 2)
    tips_300ul    = protocol.load_labware('opentrons_96_filtertiprack_200ul', 4)
    tips_10ul     = protocol.load_labware('geb_96_tiprack_10ul', 1)
    colors        = protocol.load_labware('opentrons_6_tuberack_nest_50ml_conical', 2)
    crystal_plate = protocol.load_labware('hamptonresearch_24_wellplate_24x500ul', 3)
    
    # load arms with the pipettes
    p300 = protocol.load_instrument('p300_single_gen2', 'right', tip_racks = [tips_300ul]) 
    p10  = protocol.load_instrument('p10_single', 'left', tip_racks = [tips_10ul])
    


    # do magenta first, then teal, then water    
    data_locs = ['down', 'right', 'water']
    cl_locs   = ['A1', 'B1', 'A2']
    
    
    # where do we dispense logic
    # UNUSED, instead dispense in one place and do a "dispensing lap"
    '''
    n_places = len(cl_locs)
    circ_xyz = []
    slices = 2*math.pi/n_places # can OT handle math/np imports? 3.14159265359

    for step in range(n_places):
        
        pt = slices*step 
        x  = math.cos(pt) * offset
        y  = math.sin(pt) * offset
        circ_xyz.append([x,y])
    '''
    
        
       
    
    
    
    
       
    ### BLOCK 1 ###
    for direction, cl, vol in zip(data_locs, cl_locs, all_volumes):
        print(f'-----------------my direction is: {direction}-----------------')
        
        # snag a new tip for each color
        p300.pick_up_tip()
        protocol.delay(seconds=delay)
        
        # to mimic reverse pipetting, keep a constant ~20 uL in the tip
        withdraw      = const_vol_in_p300 
        depth_and_vol = getTopOffset(colors, cl, "DeRoo_GREINER_50mL", vol-withdraw)
        p300.aspirate(withdraw, depth_and_vol)
        vol -= withdraw
        
        # UNUSED
        # x_offset = coords[0] # implement
        # y_offset = coords[1] # implement
        
        x_offset = 0
        y_offset = offset

        for well in wells:
            
            well_info = my_dict[well]
            w_volume  = well_info[direction] 
            
            # if we have no working volume (i.e. add 0 of a color), do nothing
            if w_volume == 0:
                continue
            
            new_center_location = crystal_plate[well].center() # home point
    
            # if we need to pull out more than 300 uL (such as 400 uL run), split
            # it up into N number of equal volumes. So 400 uL water is 2x200uL waters
            # use adder trick bc current if 400, it would actually do 3x 200. Bad!
            
            max_real_vol = p300_tip_size - const_vol_in_p300
            
            if w_volume % max_real_vol == 0:
                adder = 0
            else:
                adder = 1
                
                    
            runs = (w_volume // max_real_vol) + adder # this is 200 and NOT 300 bc our tips are 200!
            volume = w_volume/runs
            
            # Debugging
            # print(f'for well {well}, im picking up {volume}')
                
        
            for run in range(runs):
                
                
                # pick up some amount of magenta, teal, or water
                depth_and_vol = getTopOffset(colors, cl, "DeRoo_GREINER_50mL", vol-volume)
                p300.aspirate(volume, depth_and_vol)
                vol -= volume
                protocol.delay(seconds=delay)
                
                # move to above resivour
                p300.move_to(crystal_plate[well].top(z=height).move(types.Point(x=x_offset, y=y_offset)))
                protocol.delay(seconds = delay)
                
                # dispense some resivour
                p300.dispense(volume, new_center_location.move(types.Point(x=x_offset, y=y_offset, z=depth)), rate=0.5)
                protocol.delay(seconds = delay)
                
                # move to above resivour
                p300.move_to(crystal_plate[well].top(z=height).move(types.Point(x=x_offset, y=y_offset)))
                protocol.delay(seconds = delay)

                
        p300.drop_tip() # yeet tip
            

    p300.pick_up_tip()
    for well in wells:
        
        
        new_center_location = crystal_plate[well].center()
        
        # move to above resivour
        p300.move_to(crystal_plate[well].top(z=height).move(types.Point(x=x_offset, y=y_offset)))
        protocol.delay(seconds = delay)
        
        # pick up some resivour
        p300.aspirate(p300_tip_size, new_center_location.move(types.Point(x=x_offset, y=offset, z=depth-2.5)))
        protocol.delay(seconds = delay) 
        
        # move to above resivour
        p300.move_to(crystal_plate[well].top(z=height).move(types.Point(x=x_offset, y=y_offset)))
        protocol.delay(seconds = delay)
        
        
        circ_vol = p300_tip_size/num_laps
        slices = math.pi/num_laps
        for lap in range(num_laps):
            
            pt  = slices*lap
            xpt  = math.cos(-pt) * offset
            ypt  = math.sin(-pt) * offset
            
            if lap == 0:
                p300.move_to(crystal_plate[well].top(z=height).move(types.Point(x=xpt, y=ypt)))
                protocol.delay(seconds = 0.1)
                
            
            # dispense some resivour
            p300.dispense(circ_vol, new_center_location.move(types.Point(x=xpt, y=ypt, z=depth-2.5)), rate=0.5)
            protocol.delay(seconds = delay)
            
    p300.drop_tip()
        
        
        

    

    ### BLOCK 2 ###  
    y_vol = all_volumes[3]  
    p10.pick_up_tip()
    protocol.delay(seconds=delay)     
    
    # initialize with 2 uL yellow to mimic reverse pipette
    withdraw = const_vol_in_p10
    depth_and_vol = getTopOffset(colors, "B2", "DeRoo_GREINER_50mL", y_vol-withdraw)
    p10.aspirate(withdraw, depth_and_vol)
    protocol.delay(seconds=delay)
    y_vol -= withdraw
    
    
    for well in wells:
 
        new_center_location = crystal_plate[well].center() # home point
        

        # pick up 5 uL yellow, hence hard coded "B2"
        withdraw = growth_well_half_vol
        depth_and_vol = getTopOffset(colors, "B2", "DeRoo_GREINER_50mL", y_vol-withdraw)
        p10.aspirate(withdraw, depth_and_vol)
        protocol.delay(seconds=delay)
        y_vol -= withdraw
        
        # put yellow in crystal growth well
        p10.dispense(growth_well_half_vol, new_center_location.move(types.Point(x=0, y=0, z=-2)), rate=0.5)
        protocol.delay(seconds = delay) 
        
    p10.drop_tip()
        


    ### BLOCK 3 ###
    for well in wells:
        
        new_center_location = crystal_plate[well].center() # home point

        
        # pick up new tip
        p10.pick_up_tip()
        protocol.delay(seconds=delay)
        
        # move to above resivour
        p10.move_to(crystal_plate[well].top(z=height).move(types.Point(y=offset)))
        protocol.delay(seconds = delay)
        
        # move to in resivour
        p10.move_to(crystal_plate[well].top(z=depth).move(types.Point(y=offset)))
        protocol.delay(seconds = delay)

        # pick up some resivour
        initial_pickup = growth_well_half_vol + const_vol_in_p10
        p10.aspirate(initial_pickup, new_center_location.move(types.Point(x=0, y=offset, z=depth)))
        protocol.delay(seconds = delay)
        
        # move to above resivour
        p10.move_to(crystal_plate[well].top(z=height).move(types.Point(y=offset)))
        protocol.delay(seconds = delay)
        
        # dispense resivour into growth well
        p10.dispense(growth_well_half_vol, new_center_location.move(types.Point(x=0, y=0, z=-2)), rate=0.5)
        protocol.delay(seconds = delay)   

        # drop tip in for loop bc this is expensive/unique mixture, don't cross contaminate!
        p10.drop_tip()
        protocol.delay(seconds = delay)  
   
        
