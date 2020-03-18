# -*- coding: utf-8 -*-

"""

Created on Sun Nov 24 16:07:53 2019



@author: sh2065

"""



import qtpy

import sys

import nplab.datafile as df

import h5py

import numpy as np

import matplotlib.pyplot as plt 

from matplotlib.colors import ListedColormap, LinearSegmentedColormap

from matplotlib import cm

import os,sys

# from colormap import Colormap as cmaps

from matplotlib import cm



 



file_path = sys.argv[1] #Take the file location from sys.argv list


data=np.load(file_path,'r')

a=list(data)

b=len(list(data))



if b == 1:

    plt.hist(data[a[0]])



elif b == 2:

    name1=a[0]

    name2=a[1]

    x=data[name1]

    y=data[name2]

    try:

        plt.plot(x,y)

        plt.subplots()

        plt.scatter(x,y)

        plt.show()

    except:

        plt.hist(x,y)

          

            

# np.savez always put the y in first, don't know why

elif b == 3:

    name1=a[0] #y

    name2=a[1] #x 

    name3=a[2] #z

    x=data[name1]

    y=data[name2]

    z=data[name3]

    

    try:

        int(y) > 0

        plt.hist(x=x,bins=y,weights=z)

        plt.show()

    except:

        if len(y)==len(z):

            norm = cm.colors.Normalize(vmax=z.max(), vmin=z.min())

            figsize=10,35

            fig, ax = plt.subplots(figsize=figsize)



            cset1 = ax.contourf(x, y, z, 100, norm=norm, cmap=cm.inferno)

            plt.xlabel('Raman shift / cm-1', multialignment='center', rotation=0, fontsize=36)

            plt.ylabel('Time / s', multialignment='center', rotation=90, fontsize=36)

            plt.tick_params(labelsize=30)

            plt.show()

      



elif b == 4:

    name1=a[0]

    name2=a[1]

    name3=a[2]

    name4=a[3]

    x1=data[name2]

    y1=data[name3]

    x2=data[name4]

    y2=data[name1]

    plt.plot(x1,y1)

    plt.plot(x2,y2)

    plt.show()

else:

    print('something wrong with the data')

