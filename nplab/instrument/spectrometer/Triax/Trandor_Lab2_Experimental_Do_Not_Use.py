"""
jpg66
"""

from nplab.instrument.spectrometer.Triax.Triax_Experimental_Do_Not_Use import Triax
import numpy as np
from nplab.utils.notified_property import NotifiedProperty
from nplab.instrument.camera.Andor import Andor
import types

Calibration_Arrays=[]

Calibration_Arrays.append([])
Calibration_Arrays.append([])
Calibration_Arrays.append([])

Calibration_Arrays[0].append([614.0, 708.19, 785.0, 880.0])
Calibration_Arrays[0].append([-1.426770400496046e-07,8.568118871080799e-08,-3.842673870179174e-08,-1.6931025292314229e-07])
Calibration_Arrays[0].append([-0.03622191490065281,-0.1703883696157233,-0.09181517506331724,0.018598551356333176])
Calibration_Arrays[0].append([21803.133194394515, 47048.52913039829, 39063.730061611925, 21204.44706541431])

Calibration_Arrays=np.array(Calibration_Arrays)

CCD_Size=2048 #Size of ccd in pixels

#Make a deepcopy of the andor capture function, to add a white light shutter close command to if required later
Andor_Capture_Function=types.FunctionType(Andor.capture.func_code, Andor.capture.func_globals, 'Unimportant_Name',Andor.capture.func_defaults, Andor.capture.func_closure)

class Trandor(Andor):#Andor
    
    ''' Wrapper class for the Triax and the andor
    ''' 
    def __init__(self,White_Shutter=None):

        super(Trandor,self).__init__()
        self.triax = Triax('GPIB0::1::INSTR',Calibration_Arrays,CCD_Size) #Initialise triax
        self.White_Shutter=White_Shutter
        self.SetParameter('SetTemperature',-90)  #Turn on andor cooler
        self.CoolerON()
        
        print '---------------------------'
        print 'Triax Information:'
        print 'Current Grating:',self.triax.Grating()
        print 'Current Slit Width:', self.triax.Slit(),'um'
        print '---------------------------'

        self.Notch_Filters_Tested=True
        

    def Grating(self, Set_To=None):
        return self.triax.Grating(Set_To)

    def Generate_Wavelength_Axis(self):
        return self.triax.Get_Wavelength_Array()

    def Set_Center_Wavelength(self,Wavelength):  
        Centre_Pixel=int(CCD_Size/2)
        Required_Step=self.triax.Find_Required_Step(Wavelength,Centre_Pixel)
        Current_Step=self.triax.Motor_Steps()
        self.triax.Move_Steps(Required_Step-Current_Step)

    def Test_Notch_Alignment(self):
        	Accepted=False
        	while Accepted is False:
        		Input=raw_input('WARNING! A slight misalignment of the narrow band notch filters could be catastrophic! Has the laser thoughput been tested? [Yes/No]')
        		if Input.upper() in ['Y','N','YES','NO']:
        			Accepted=True
        			if len(Input)>1:
        				Input=Input.upper()[0]
        	if Input.upper()=='Y':
        		print 'You are now free to capture spectra'
        		self.Notch_Filters_Tested=True
        	else:
        		print 'The next spectrum capture will be allowed for you to test this. Please LOWER the laser power and REDUCE the integration time.'
        		self.Notch_Filters_Tested=None

         
    def capture(self,Close_White_Shutter=True):
        """
        Edits the capture function is a white light shutter object is supplied, to ensure it is closed while the image is taken.
        This behaviour can be overwirtten by passing Close_White_Shutter=False
        """

        if self.Notch_Filters_Tested is False:
            self.Test_Notch_Alignment()
            return (np.array(range(CCD_Size))*0,1,(CCD_Size,))
        	
        else:
	        if self.Notch_Filters_Tested is None:
	            self.Notch_Filters_Tested=False
	        if self.White_Shutter is not None and Close_White_Shutter is True:
	            try:
	                self.White_Shutter.close_shutter()
	            except:
	                 Dump=1
	                    
	            Output=Andor_Capture_Function(self)
	                
	            try:
	                self.White_Shutter.open_shutter()
	            except:
	                Dump=1
	            return Output
	        else:
	           return Andor_Capture_Function(self)

    x_axis=NotifiedProperty(Generate_Wavelength_Axis) #This is grabbed by the Andor code 

