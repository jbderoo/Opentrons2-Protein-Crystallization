# -*- coding: utf-8 -*-
"""
Created on Sun Oct 22 22:42:18 2023

@author: jderoo
"""

from opentrons import protocol_api, types
from math import ceil, pi, cos, sin



MATRIX_COLUMN_STEP  = 50   # uL change volume increase 
MATRIX_ROW_STEP     = 30   # uL change volume increase
WELL_VOLUME         = 400  # uL ttl volume in reserviour 


vialPipetteOffsets = {
    "GREINER_50mL": {
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
    vial   = vialPipetteOffsets[vialName]
    
    if volume < vial["volume_offset"]:
        return plate[vialLocation].bottom(2)
   
    else:
        slope     = ((vial["offset"] + vial["step"]) - vial["offset"]) / (vial["volume_step"] - vial["volume_offset"])
        intercept = vial["offset"] - slope * vial["volume_offset"]
        
        if volume > vialPipetteOffsets[vialName]["maxVolume"]:
            vialOffset = (slope * vialPipetteOffsets[vialName]["maxVolume"]) + intercept
        else:
            vialOffset = (slope * volume) + intercept
        
        roundingDigits = 2

        return plate[vialLocation].top(round(vialOffset, roundingDigits))



metadata = {
    'apiLevel':     '2.11',
    'protocolName': 'Crystals: Colors practice run',
    'description':  'A protocol for growing CJ crystals with custom labware as provided by the OpenTrons team. This file name is hamptonresearch_24_wellplate_24x500ul.json',
    'author':       'Jacob DeRoo'
}



def convert_L2N(L):
    
    # a less clear but more optimal solution for this function:
    # return (ord(letter) - 65) * MATRIX_ROW_STEP
    
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
    
    return out * MATRIX_ROW_STEP 



def run(protocol: protocol_api.ProtocolContext):

    # some constants that we use somewhat frequently
    height               = 8     # come comically far above the well for safety
    depth                = -10   # how far into resivour to go to dipsense liquid
    offset               = 5.5   # mm, distance away from center  to resivour
    delay                = 0.25  # sec, slow robot down for liquid's benefit
    magenta_vol          = 49    # starting volume (mL) of magenta
    blue_vol             = 49    # starting volume (mL) of teal/blue
    water_vol            = 49    # starting volume (mL) of water
    yellow_vol           = 49    # starting volume (mL) of yellow
    const_vol_in_p300    = 20    # constant volume in the p300 for reverse pipette mimic
    p300_tip_size        = 200   # pipette tip size
    num_laps             = 8     # number of stops/checks for mixing in resivour
    const_vol_in_p10     = 2     # constant volume in the p10 for reverse pipette mimic
    growth_well_half_vol = 5     # volume of the resivour or pure protein in growth well
    xtal_well_depth      = -2    # the depth (mm) to go down to get into the growth well
    magenta_loc          = 'A1'  # where is the magenta falcon tube in the colors slot
    blue_loc             = 'A2'  # where is the blue    falcon tube in the colors slot
    water_loc            = 'B1'  # where is the water   falcon tube in the colors slot
    yellow_loc           = 'B2'  # where is the yellow  falcon tube in the colors slot
    

    letters = list('ABCDEF')
    numbers = [1, 2, 3, 4]
    wells   = []
    
    # convert to uL from mL
    m_vol = magenta_vol * 1000
    b_vol = blue_vol    * 1000
    w_vol = water_vol   * 1000
    y_vol = yellow_vol  * 1000
    
    all_volumes = [m_vol, b_vol, w_vol, y_vol]

    
    
    for letter in letters:
        for number in numbers:
            wells.append(letter + str(number))
   
            
    well_information = {}
    for well in wells:
        
        tmp    = {}
        letter = well[0]
        number = int(well[1])
        
        tmp['column'] = convert_L2N(letter)
        tmp['row']    = (number - 1) * MATRIX_COLUMN_STEP
        tmp['fill']   = WELL_VOLUME - (tmp['column'] + tmp['row'])
    
        well_information[well] = tmp
    
    
    # load our deck with locations and liquids
    tips_300ul    = protocol.load_labware('opentrons_96_filtertiprack_200ul', 4)
    tips_10ul     = protocol.load_labware('geb_96_tiprack_10ul', 1)
    colors        = protocol.load_labware('opentrons_6_tuberack_nest_50ml_conical', 2)
    crystal_plate = protocol.load_labware('hamptonresearch_24_wellplate_24x500ul', 3)
    
    # load arms with the pipettes
    p300 = protocol.load_instrument('p300_single_gen2', 'right', tip_racks = [tips_300ul]) 
    p10  = protocol.load_instrument('p10_single', 'left', tip_racks = [tips_10ul])
    


    # do magenta first, then blue, then clear water    
    fill_directions = ['column', 'row', 'fill']
    color_locs      = [magenta_loc, blue_loc, water_loc]

    
        
       
    
    
    
    
       
    ### BLOCK 1 ###
    for direction, cl, vol in zip(fill_directions, color_locs, all_volumes):
        # snag a new tip for each color
        p300.pick_up_tip()
        protocol.delay(seconds=delay)
        
        # to mimic reverse pipetting, keep a constant ~20 uL in the tip
        # update and track the volume in the falcon tube for depth calcs
        withdraw            = const_vol_in_p300 
        post_withdraw_vol   = vol - withdraw
        depth_and_vol       = getTopOffset(colors, cl, "GREINER_50mL", post_withdraw_vol)
        vol                 = post_withdraw_vol
        p300.aspirate(withdraw, depth_and_vol)
        protocol.delay(seconds=delay)
    
        # correponds to 12 o'clock if the reserviour was a clock
        x_offset = 0
        y_offset = offset

        for well in wells:
            
            well_info = well_information[well]
            w_volume  = well_info[direction] 
            
            # if we have no working volume (i.e. add 0 of a color), do nothing
            if w_volume == 0:
                continue
            
            new_center_location = crystal_plate[well].center() # home point
    
            # if we need to pull out more than 300 uL (such as 400 uL run), split
            # it up into N number of equal volumes. So 400 uL water is 2x200uL waters
            # use adder trick bc current if 400, it would actually do 3x 200. Bad!
            max_real_vol = p300_tip_size - const_vol_in_p300        
            runs         = ceil(w_volume / max_real_vol) # this is 200 and NOT 300 bc our tips are 200!
            volume       = w_volume / runs
    
                
        
            for run in range(runs):
                
                
                # pick up some amount of magenta, teal, or water
                withdraw           = volume
                post_withdraw_vol  = vol - withdraw
                vol                = post_withdraw_vol
                depth_and_vol      = getTopOffset(colors, cl, "GREINER_50mL", post_withdraw_vol)
                p300.aspirate(volume, depth_and_vol)
                protocol.delay(seconds=delay)
                
                # move to above resivour
                p300.move_to(crystal_plate[well].top(z=height).move(types.Point(x=x_offset, y=y_offset)))
                protocol.delay(seconds=delay)
                
                # dispense some resivour
                p300.dispense(volume, new_center_location.move(types.Point(x=x_offset, y=y_offset, z=depth)), rate=0.5)
                protocol.delay(seconds=delay)
                
                # move to above resivour
                p300.move_to(crystal_plate[well].top(z=height).move(types.Point(x=x_offset, y=y_offset)))
                protocol.delay(seconds=delay)

                
        p300.drop_tip() # yeet tip
            

    
    for well in wells:
        # new tip 
        p300.pick_up_tip()
        protocol.delay(seconds=delay)
        
        new_center_location = crystal_plate[well].center()
        
        # move to above resivour
        p300.move_to(crystal_plate[well].top(z=height).move(types.Point(x=x_offset, y=y_offset)))
        protocol.delay(seconds=delay)
        
        # pick up some resivour
        p300.aspirate(p300_tip_size, new_center_location.move(types.Point(x=x_offset, y=offset, z=depth-2.5)))
        protocol.delay(seconds=delay) 
        
        # move to above resivour
        p300.move_to(crystal_plate[well].top(z=height).move(types.Point(x=x_offset, y=y_offset)))
        protocol.delay(seconds=delay)
        
        # calc our dispense volume and number of dispenses
        circ_vol = p300_tip_size/num_laps
        slices   = pi/num_laps
        
        for lap in range(num_laps):
            pt   = slices * lap
            xpt  = cos(-pt) * offset
            ypt  = sin(-pt) * offset
            
            # if this is our first entry, move above the well into a good position to prevent collision
            if lap == 0:
                p300.move_to(crystal_plate[well].top(z=height).move(types.Point(x=xpt, y=ypt)))
                protocol.delay(seconds=0.1)
                
            # dispense some resivour
            p300.dispense(circ_vol, new_center_location.move(types.Point(x=xpt, y=ypt, z=depth-2.5)), rate=0.5)
            protocol.delay(seconds=delay)
            
        p300.drop_tip()
        
        
        

    ### BLOCK 2 ###  
    p10.pick_up_tip()
    protocol.delay(seconds=delay)     
    
    # initialize with 2 uL yellow to mimic reverse pipette
    withdraw           = const_vol_in_p10
    post_withdraw_vol  = y_vol - withdraw
    y_vol              = post_withdraw_vol
    depth_and_vol      = getTopOffset(colors, yellow_loc, "GREINER_50mL", post_withdraw_vol)
    p10.aspirate(withdraw, depth_and_vol)
    protocol.delay(seconds=delay)
    
    
    for well in wells:
 
        new_center_location = crystal_plate[well].center() # home point
        

        # pick up 5 uL yellow
        withdraw           = growth_well_half_vol
        post_withdraw_vol  = y_vol - withdraw
        depth_and_vol      = getTopOffset(colors, yellow_loc, "GREINER_50mL", post_withdraw_vol)
        y_vol              = post_withdraw_vol
        p10.aspirate(withdraw, depth_and_vol)
        protocol.delay(seconds=delay)

        
        # put yellow in crystal growth well
        p10.dispense(growth_well_half_vol, new_center_location.move(types.Point(x=0, y=0, z=xtal_well_depth)), rate=0.5)
        protocol.delay(seconds=delay) 
        
    p10.drop_tip()
        


    ### BLOCK 3 ###
    # pick up new tip. Let's keep 1 tip the whole time to encourage seeding between wells
    p10.pick_up_tip()
    protocol.delay(seconds=delay)
    

    
    for well in wells:
        new_center_location = crystal_plate[well].center() # home point

        
        # move to above resivour
        p10.move_to(crystal_plate[well].top(z=height).move(types.Point(y=offset)))
        protocol.delay(seconds=delay)
        
        # move to in resivour
        p10.move_to(crystal_plate[well].top(z=depth).move(types.Point(y=offset)))
        protocol.delay(seconds=delay)

        # pick up some resivour
        
        p10.aspirate(growth_well_half_vol, new_center_location.move(types.Point(x=0, y=offset, z=depth)))
        protocol.delay(seconds=delay)
        
        # move to above resivour
        p10.move_to(crystal_plate[well].top(z=height).move(types.Point(y=offset)))
        protocol.delay(seconds=delay)
        
        # dispense resivour into growth well
        p10.dispense(growth_well_half_vol, new_center_location.move(types.Point(x=0, y=0, z=xtal_well_depth)), rate=0.5)
        protocol.delay(seconds=delay)   

    # finish protocol
    p10.drop_tip()
   