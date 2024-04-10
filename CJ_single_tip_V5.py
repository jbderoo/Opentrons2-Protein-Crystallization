# -*- coding: utf-8 -*-
"""
Created on Sun Oct 22 22:42:18 2023

@author: jderoo
"""

from opentrons import protocol_api, types
from math import ceil, pi, cos, sin




vialPipetteOffsets = {
    "GREINER_50mL": {
        "volume_offset": 5,    # mL
        "volume_step":  50,    # mL
        "offset":      -93.25, # mm
        "step":         81.1,  # mm
        "maxVolume":    50     # mL
                          },
    
    "USA_1.5mL": {
        "volume_offset": 0.1,  # mL
        "volume_step":  1.5,   # mL
        "offset":      -31.1,  # mm
        "step":         26.8,  # mm
        "maxVolume":    1.5    # mL
                          },
    "VMR_15mL": {
        "volume_offset": 2,    # mL
        "volume_step":  15,    # mL
        "offset":      -93.2,  # mm
        "step":         83.5,  # mm
        "maxVolume":    15     # mL
                          }
}



# this function was written by Thomas Lauer
# https://github.com/tjlauer/Opentrons_OT-2
def getTopOffset_OLD(plate, vialLocation, vialName, volume_uL):
    
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


def getTopOffset(plate, vialLocation, vialName, volume_uL):
    
    volume_uL = volume_uL - (0.03 * vialPipetteOffsets[vialName]["maxVolume"] * 1000)
   # print(f'I have {volume_uL} ')
    
    if vialName == "Sample_2mL":
        return plate[vialLocation].bottom(5)
    
    volume = volume_uL / 1000
    vial   = vialPipetteOffsets[vialName]
    
    
    if volume < vial["volume_offset"]:
        return plate[vialLocation].bottom(2)
    
    else:
        slope     =  -vial['step'] / (vial['volume_step'] - vial['volume_offset'])
        intercept =  vial['offset'] + vial['step']
        
        if volume > vialPipetteOffsets[vialName]["maxVolume"]:
            volume = vial['maxVolume'] 
        
           
        print(f'volume {volume}')
        print(f'slope {slope}')
        print(f'int {intercept}')  
                     
        height = intercept + (vial['maxVolume'] - volume) * slope
        roundingDigits = 2
       # print(f'my height is {intercept} and my change is {slope}')
        #return round(height, roundingDigits)
        return plate[vialLocation].top(round(height, roundingDigits))
            

def make_plate(wells):
    
    buffers           = ['BisTris60', 'BisTris65']
    buffer_vol        = 40
    max_water_vol     = 25
    water_step_change = 5
    max_well_vol      = 400
    
    well_information  = {}
    
    
            
    for well in wells:
        tmp    = {}
        letter = well[0]
        number = int(well[1])
        
        for buffer in buffers:
            # Row A/C block
            if (letter == 'A' or letter == 'C') and buffer == 'BisTris60':
                tmp[buffer] = buffer_vol    
            elif (letter == 'A' or letter == 'C') and buffer != 'BisTris60':
                tmp[buffer] = 0
                
            # Row B/D block
            if (letter == 'B' or letter == 'D') and buffer == 'BisTris65':
                tmp[buffer] = buffer_vol    
            elif (letter == 'B' or letter == 'D') and buffer != 'BisTris65':
                tmp[buffer] = 0         
                    
            
            

        tmp['water']    = max_water_vol - (water_step_change * (number - 1))
        tmp['AmmSulf']   = max_well_vol - (buffer_vol + tmp['water']) 
            
        well_information[well] = tmp
        
    return well_information
        
    
    


metadata = {
    'apiLevel':     '2.11',
    'protocolName': 'CJ Plate Protocol',
    'description':  'Practice CJ run with colors',
    'author':       'Jacob DeRoo'
}




def run(protocol: protocol_api.ProtocolContext):

    # define constants and initial values
    height               = 10    # come comically far above the well for safety
    depth                = -11   # how far into resivour to go to dipsense liquid
    offset               = 5.5   # mm, distance away from center  to resivour
    delay                = 0.25  # sec, slow robot down for liquid's benefit
    BisTris60_vol        = 25    # starting volume (mL) of magenta
    BisTris65_vol        = 25    # starting volume (mL) of teal/blue
    water_vol            = 40    # starting volume (mL) of water
    AmmSulf_vol          = 11    # starting volume (mL) of precipitant
    protein_vol          = 0.9   # starting volume (mL) of yellow
    const_vol_in_p300    = 20    # constant volume in the p300 for reverse pipette mimic
    p300_tip_size        = 200   # pipette tip size uL
    p10_tip_size         = 10    # pipette tip size uL
    num_laps             = 9     # number of stops/checks for mixing in resivour
    const_vol_in_p10     = 2     # constant volume in the p10 for reverse pipette mimic
    growth_well_half_vol = 2.5   # volume of the resivour or pure protein in growth well
    xtal_well_depth      = -1.5  # the depth (mm) to go down to get into the growth well
    bistris60_loc        = 'A3'  # where is the magenta falcon tube in the colors slot
    bistris65_loc        = 'A4'  # where is the magenta falcon tube in the colors slot
    ammsul_loc           = 'B2'  # where is the blue    falcon tube in the colors slot
    water_loc            = 'B3'  # where is the water   falcon tube in the colors slot
    protein_loc          = 'C6'  # where is the yellow  falcon tube in the colors slot
    


    letters = list('ABCD')
    numbers = [1, 2, 3, 4, 5, 6]
    wells   = []
    
    # convert to uL from mL
    b60_vol = BisTris60_vol * 1000
    b65_vol = BisTris65_vol * 1000
    w_vol   = water_vol     * 1000
    prt_vol = protein_vol   * 1000
    as_vol  = AmmSulf_vol   * 1000
    
    #buffer_vols = []
    all_volumes = [b60_vol, b65_vol, as_vol]

    
    
    for letter in letters:
        for number in numbers:
            wells.append(letter + str(number))
   
    wells = ['A1', 'B1', 'B2', 'B3']
    #wells = ['A1', 'B2', 'B3', 'C4', 'C5', 'D6']
    #wells = wells[2:]
    well_information = make_plate(wells)


    # load our deck with locations and liquids
    tips_300ul    = protocol.load_labware('opentrons_96_filtertiprack_200ul', 4)
    tips_10ul     = protocol.load_labware('geb_96_tiprack_10ul', 1)
    colors        = protocol.load_labware('opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', 2)
    crystal_plate = protocol.load_labware('hamptonresearch_24_wellplate_24x500ul_jd', 3)
    protein       = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_snapcap', 5)
    
    # load arms with the pipettes
    p300 = protocol.load_instrument('p300_single_gen2', 'right', tip_racks = [tips_300ul]) 
    p10  = protocol.load_instrument('p10_single', 'left', tip_racks = [tips_10ul])
    


    # do buffer then precip with the p300 
    fill_directions = ['BisTris60', 'BisTris65', 'AmmSulf']
    color_locs      = [bistris60_loc, bistris65_loc, ammsul_loc]

        
    
         
    ### BLOCK 1 ###
    previous_letter = 'initiate_trip_logic'
    
    
    for direction, cl, vol in zip(fill_directions, color_locs, all_volumes): 
        print(f'I am doing {direction} in place {cl} with volume {vol}')
        # correponds to 12 o'clock if the reserviour was a clock
        x_offset = 0
        y_offset = offset
        
        
        # precipitant buffer is more expensive and harder to get lots of;
        # only use in 15 mL tubes
        if direction == 'AmmSulf':
            vial = 'VMR_15mL'

        else:
            vial= 'GREINER_50mL'
            

        for well in wells:
            well_info = well_information[well]
            w_volume  = well_info[direction] 
            
            # if we have no working volume (i.e. add 0 of a color), do nothing
            if w_volume == 0:
                continue
            
            # initiate a new row with picking up a new tip and withdrawing a constant
            # volume to mimic reverse pipetting
            if (well[0] != previous_letter and 'BisTris' in direction) or well == wells[0]:
                if p300.has_tip:
                    p300.drop_tip()
                    protocol.delay(seconds=delay)
                
                p300.pick_up_tip()
                protocol.delay(seconds=delay)
                
                previous_letter = well[0]
                
                # to mimic reverse pipetting, keep a constant ~20 uL in the tip
                # update and track the volume in the falcon tube for depth calcs
                withdraw            = const_vol_in_p300 
                post_withdraw_vol   = vol - withdraw
                depth_and_vol       = getTopOffset(colors, cl, vial, post_withdraw_vol)
                vol                 = post_withdraw_vol
                p300.aspirate(withdraw, depth_and_vol)
                protocol.delay(seconds=delay)
            
            
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
                depth_and_vol      = getTopOffset(colors, cl, vial, post_withdraw_vol)
                p300.aspirate(volume, depth_and_vol)
                protocol.delay(seconds=delay)
                
                # precip is very viscous, give the tip a tap
                # if direction == 'precip':
                #    p300.touch_tip(v_offset=-3, radius=0.85)
                #    protocol.delay(seconds=delay)
                
                # move to above resivour
                p300.move_to(crystal_plate[well].top(z=height).move(types.Point(x=x_offset, y=y_offset)))
                protocol.delay(seconds=delay)
                
                # dispense some resivour
                p300.dispense(volume, new_center_location.move(types.Point(x=x_offset, y=y_offset, z=depth)), rate=0.8)
                protocol.delay(seconds=delay)
                
                # move to above resivour
                p300.move_to(crystal_plate[well].top(z=height).move(types.Point(x=x_offset, y=y_offset)))
                protocol.delay(seconds=delay)

            # update all volumes as we go along for row C because we use the same buffer in rows C and D
            # this will ensure we can height match at the end of C and beginning of D
            #if well[0] == 'C':
             #   all_volumes[2] = vol

        #if p300.has_tip:         
    p300.drop_tip() # yeet tip
    
    
    ### Block 2 ###

    # we need a special water loop because it's an awkward range (0-25)
    switched_arms = True # initialize the pipette swapping logic before run starts
    direction     = 'water'
    cl            = water_loc
    vol           = w_vol


    # purely a speed check - if we need 300, load it up. Otherwise, just use 10
    # useful for test runs
    if min([int(x[1]) for x in wells]) < 2:     
        p300.pick_up_tip()
        withdraw           = const_vol_in_p300
        post_withdraw_vol  = vol - withdraw
        vol                = post_withdraw_vol
        depth_and_vol      = getTopOffset(colors, cl, "GREINER_50mL", post_withdraw_vol)
        p300.aspirate(const_vol_in_p300, depth_and_vol)
        protocol.delay(seconds=delay)


    # purely a speed check - if we need 10, load it up. Otherwise, just use 200
    # useful for test runs
    if max([int(x[1]) for x in wells]) >= 2:
        p10.pick_up_tip()
        withdraw           = const_vol_in_p10
        post_withdraw_vol  = vol - withdraw
        vol                = post_withdraw_vol
        depth_and_vol      = getTopOffset(colors, cl, "GREINER_50mL", post_withdraw_vol)
        p10.aspirate(const_vol_in_p10, depth_and_vol)
        protocol.delay(seconds=delay)
    
    
    for well in wells: 
        if int(well[1]) == 1:
            pip       = p300
            const_vol = const_vol_in_p300
            tip_size  = p300_tip_size
         
        else:
            
            #if p300.has_tip:
            #    p300.drop_tip()
            pip             = p10
            const_vol       = const_vol_in_p10
            tip_size        = p10_tip_size
            switched_arms   = True
            
            
            
        well_info = well_information[well]
        w_volume  = well_info[direction] 
        
    
        # if we have no working volume (i.e. add 0 of a color), do nothing
        if w_volume == 0:
            continue
        
        new_center_location = crystal_plate[well].center() # home point  
 
       
        # if we need to pull out more than 300 uL (such as 400 uL run), split
        # it up into N number of equal volumes. So 400 uL water is 2x200uL waters
        # use adder trick bc current if 400, it would actually do 3x 200. Bad!
        max_real_vol = tip_size - const_vol       
        runs         = ceil(w_volume / max_real_vol) # this is 200 and NOT 300 bc our tips are 200!
        volume       = w_volume / runs


        for run in range(runs):
            # pick up some amount of magenta, teal, or water
            withdraw           = volume
            post_withdraw_vol  = vol - withdraw
            vol                = post_withdraw_vol
            depth_and_vol      = getTopOffset(colors, cl, "GREINER_50mL", post_withdraw_vol)
            pip.aspirate(volume, depth_and_vol)
            protocol.delay(seconds=delay)
            
            # move to above resivour
            pip.move_to(crystal_plate[well].top(z=height).move(types.Point(x=x_offset, y=y_offset)))
            protocol.delay(seconds=delay)
            
            # dispense some resivour
            pip.dispense(volume, new_center_location.move(types.Point(x=x_offset, y=y_offset, z=depth)), rate=0.8)
            protocol.delay(seconds=delay)
            
            # move to above resivour
            pip.move_to(crystal_plate[well].top(z=height).move(types.Point(x=x_offset, y=y_offset)))
            protocol.delay(seconds=delay)
    
    if p300.has_tip:
        p300.drop_tip()
    if p10.has_tip:
        p10.drop_tip()
        
   
        
    
    # mix and distribute the resivour
    # commented out for now, left in if needed. Should probably be used, or give
    # plate a jiggle at the end to distribute the liquid in the reservior
    
    '''
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
            p300.dispense(circ_vol, new_center_location.move(types.Point(x=xpt, y=ypt, z=depth-2.5)), rate=1)
            protocol.delay(seconds=delay)
            
        p300.drop_tip()
    '''
         
       
        

    ### BLOCK 3 ###
    for well in wells:
 
        new_center_location = crystal_plate[well].center() # home point
        p10.pick_up_tip()
        protocol.delay(seconds=delay)
        

        # pick up 5 uL yellow
        withdraw           = growth_well_half_vol
        post_withdraw_vol  = prt_vol - withdraw
        depth_and_vol      = getTopOffset(protein, protein_loc, "USA_1.5mL", post_withdraw_vol)
        prt_vol            = post_withdraw_vol
        p10.aspirate(withdraw, depth_and_vol)
        protocol.delay(seconds=delay)

        
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
        p10.dispense(2.5*growth_well_half_vol, new_center_location.move(types.Point(x=0, y=0, z=xtal_well_depth)), rate=0.5)
        protocol.delay(seconds=delay) 
        
        #p10.blow_out()
        
        p10.touch_tip(v_offset=xtal_well_depth-2.5, radius=0.125)
        protocol.delay(seconds=delay)

        # yeet tip
        p10.drop_tip()

