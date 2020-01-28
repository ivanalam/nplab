# -*- coding: utf-8 -*-
"""
Created on Thu Aug 01 16:38:56 2019

@author: ee306
"""
from __future__ import division
from __future__ import print_function
from past.utils import old_div
import os
import numpy as np
from scipy import interpolate 
import time
from qtpy import QtWidgets, uic
from nplab.ui.ui_tools import UiTools
from nplab.experiment.gui import run_function_modally
from nplab.instrument import Instrument
from AOM import AOM as Aom
from Rotation_Stage import Filter_Wheel


class PowerControl(Instrument):
    '''
    Controls the power. power_controller is something with a continuous input parameter like a filter wheel, or an AOM. 
    '''
    def __init__(self, power_controller, white_light_shutter, laser_shutter, power_meter, laser = '_633'):       
        self.pc = power_controller        
        if laser == '_633':
            self.laser = '_633'
            self._633 = True
            self._785 = False
            
        elif laser == '_785':
            self.laser = '_785'
            self._633 = False
            self._785 = True
                         
        else: raise ValueError('power_controller must be AOM or Filter Wheel')
        
        if isinstance(self.pc, Filter_Wheel): 
            self.min_param = 260
            self.max_param = 500
        if isinstance(self.pc, Aom):
            self.min_param = 0
            self.max_param = 1

        self._set_to_midpoint()
        self.maxpower = None 
        self.minpower = None
        self.measured_power = None
        self.update_power_calibration()
        self.wutter = white_light_shutter        
        self.lutter = laser_shutter         
        super(PowerControl, self).__init__()
        self._initiate_pc()
        self.pometer = power_meter
  
    def _initiate_pc(self):
        if isinstance(self.pc, Aom):            
            self.pc.Switch_Mode()
        self.param = self.mid_param
   
    def _set_to_midpoint(self):
        self.param = self.mid_param
    def _set_to_maxpoint(self):
       self.param = self.max_param
    def _initiate_pometer(self):
        if isinstance(self.pometer, 'Thorlabs_powermeter'):      
            self.pometer.system.beeper.immediate()
            if self._785: self.pometer.sense.correction.wavelength = 785   
            if self._633: self.pometer.sense.correction.wavelength = 633              
        else: print('wavelength not corrected for')
    @property
    def param(self):
        if isinstance(self.pc, Filter_Wheel):
            p = int(self.pc.Stage.Get_Position().split(' ')[-1])
            return 0. if p>500 else np.round(p, decimals = 2)
        if isinstance(self.pc, Aom):
            return self.pc.Get_Power()               
    @param.setter
    def param(self,value):
        if isinstance(self.pc, Filter_Wheel):        
            self.pc.Stage.Rotate_To(value)     
        if isinstance(self.pc, Aom):
            self.pc.Power(value) 
    @property
    def mid_param(self):
        return old_div((self.max_param - self.min_param),2)

    @property
    def points(self):
        if isinstance(self.pc, Filter_Wheel):        
            return np.logspace(0,np.log10(self.max_param-self.min_param),self.number_points)+self.min_param
        if isinstance(self.pc, Aom):
            return np.linspace(self.min_param,self.max_param,num = self.number_points, endpoint = True) 
            
    def Calibrate_Power(self, update_progress=lambda p:p):
        attrs = {}       
        if self.measured_power is not None: attrs['Measured power at maxpoint'] = self.measured_power
        if isinstance(self.pc, Filter_Wheel):
            attrs['Angles']  = self.points  
    
        if isinstance(self.pc, Aom):
            attrs['Voltages'] = self.points
        attrs['x_axis'] = self.points
        attrs['parameters'] = self.points

        powers = []
        
        self.wutter.close_shutter()    
        self.lutter.open_shutter() 
        
        for counter, point in enumerate(self.points):          
            self.param = point
            time.sleep(0.01)
            powers = np.append(powers,self.pometer.power)
            update_progress(counter)
        group = self.create_data_group('Power_Calibration{}_%d'.format(self.laser), attrs = attrs)
        group.create_dataset('measured_powers',data=powers)
        if self.measured_power is None:
            group.create_dataset('ref_powers',data=powers, attrs = attrs)
        else:
            group.create_dataset('ref_powers',data=( old_div(powers*self.measured_power,max(powers))), attrs = attrs)
        self.lutter.close_shutter()
        self._set_to_midpoint()
        self.wutter.open_shutter()
        self.update_power_calibration()    
    
    def update_power_calibration(self, specific_calibration = None, laser = None):
        '''
        specific_calibration should be the exact name of the power calibration group, otherwise
        the most recent calibration for the given laser is used.
        '''
        if laser is None:
           laser = self.laser 
        
        try:
            search_in = self.get_root_data_folder()
            if specific_calibration is not None:
                try:power_calibration_group = search_in[specific_calibration] 
                except: 
                    print('This calibration doesn\'t exist!')
                    return
                self.power_calibration = {'ref_powers' : power_calibration_group['ref_powers']}
                if isinstance(self.pc, Filter_Wheel):self.power_calibration.update({'Angles' : power_calibration_group.attrs['Angles']})
                if isinstance(self.pc, Aom): self.power_calibration.update({'Voltages' : power_calibration_group.attrs['Voltages']})
                self.power_calibration.update({'parameters' : power_calibration_group['parameters']})
                return
            
            
            power_calibration_group = max([(int(name.split('_')[-1]), group)\
            for name, group in list(search_in.items()) \
            if name.startswith('Power_Calibration') and (name.split('_')[-2] == laser[1:])])[1]
            self.power_calibration = {'ref_powers' : power_calibration_group['ref_powers']} 
            if isinstance(self.pc, Filter_Wheel):
                self.power_calibration.update({'Angles' : power_calibration_group.attrs['Angles']})
                self.update_config('Angles'+self.laser, power_calibration_group.attrs['Angles'])
            if isinstance(self.pc, Aom):
                self.power_calibration.update({'Voltages' : power_calibration_group.attrs['Voltages']})
                self.update_config('Voltages'+self.laser, power_calibration_group.attrs['Voltages'])
            self.power_calibration.update({'parameters' : power_calibration_group.attrs['parameters']})
            self.update_config('parameters'+self.laser, power_calibration_group.attrs['parameters'])
            self.update_config('ref_powers'+self.laser, self.power_calibration['ref_powers'])
            
        except ValueError:
            if len(self.config_file)>0:            
                self.power_calibration = {'_'.join(n.split('_')[:-1]) : f for n,f in list(self.config_file.items()) if n.endswith(self.laser)}
                print('No power calibration in current file, using inaccurate configuration')
            else:
                print('No power calibration found')

    @property
    def power(self):
        return self.pometer.power
    @power.setter
    def power(self, value):
        if self.isinstance(self.pc, Filter_Wheel):
            self.param = self.Power_to_Voltage(value)
        if isinstance(self.pc, Aom):
            self.param = self.Power_to_Angle(value)
    
    def power_to_param(self, power):       
        angles = self.power_calibration['Angles']    
        powers = np.array(self.power_calibration['ref_powers'])
        curve = interpolate.interp1d(powers, angles, kind = 'cubic') #  
        return curve(power)       
    
    def get_qt_ui(self):
        return PowerControl_UI(self)

class PowerControl_UI(QtWidgets.QWidget,UiTools):
    def __init__(self, PC):
        super(PowerControl_UI, self).__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'power_control.ui'), self)
        self.PC = PC         
        self.SetupSignals()
        
    def SetupSignals(self):
        self.pushButton_calibrate_power.clicked.connect(self.Calibrate_Power_gui)             
        self.doubleSpinBox_min_param.setValue(self.PC.min_param)
        self.doubleSpinBox_max_param.setValue(self.PC.max_param)
        self.doubleSpinBox_max_param.valueChanged.connect(self.update_min_max_params)  
        self.doubleSpinBox_min_param.valueChanged.connect(self.update_min_max_params)
        self.laser_textBrowser.setPlainText('Laser: '+self.PC.laser[1:])    
        self.pushButton_set_param.clicked.connect(self.set_param)
        self.doubleSpinBox_measured_power.valueChanged.connect(self.update_measured_power)
        self.pushButton_set_power.clicked.connect(self.set_power_gui)        
     
    def update_min_max_params(self):
        self.PC.min_param = self.doubleSpinBox_min_param.value()
        self.PC.max_param = self.doubleSpinBox_max_param.value()
        if self.PC.laser == '_633' and self.PC.max_param>1:
            print('voltages over 1 not allowed!')
            self.PC.maxvolt = 1
    def update_measured_power(self):
        self.PC.measured_power = float(self.doubleSpinBox_measured_power.value())
    def set_param(self):
        if self.PC._633 and self.doubleSpinBox_set_input_param.value()>1:       
            self.PC.param = 1
            print('voltages over 1 not allowed')
        else:
            self.PC.param = self.doubleSpinBox_set_input_param.value()
    def set_power_gui(self):
        self.PC.power = float(self.doubleSpinBox_set_power.value())
    def Calibrate_Power_gui(self):
        run_function_modally(self.PC.Calibrate_Power, progress_maximum = len(self.PC.points))
    
if __name__ == '__main__': 

    from nplab.instrument.shutter.BX51_uniblitz import Uniblitz
    from mine.Lab_5.thorlabs_pm1000 import Thorlabs_powermeter
    from nplab.instrument.shutter.thorlabs_sc10 import ThorLabsSC10
    from nplab import datafile    
   
    lutter = ThorLabsSC10('COM30')
    FW = Filter_Wheel() 
    lutter.set_mode(1)
    aom = Aom()
    pometer = Thorlabs_powermeter()
    wutter = Uniblitz("COM8")
    PC = PowerControl(FW, wutter, lutter, pometer)
    PC.show_gui(blocking = False)
    pometer.show_gui(blocking = False)
    wutter.show_gui(blocking = False)
    lutter.show_gui(blocking = False)    
    datafile.current().show_gui(blocking = False)
    PC2 = PowerControl(aom, wutter, lutter, pometer)
    PC2.show_gui(blocking = False)