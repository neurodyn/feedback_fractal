# -*- coding: utf-8 -*-
"""
Created on Fri Jul 31 16:02:02 2015

Fractal animation using video feedback.
Tested on python 3.7.

@author: alexanderwoodward

"""

import cv2
import numpy as np
import math
import random

# change the width and height depending on your computer:
width = 500 
height = 500
img1 = np.zeros((width,height,3), np.uint8)
img2 = np.zeros((width,height,3), np.uint8)
imgs = [img1,img2]
# init the image
for y in range(0,height):
    for x in range(0,width):
        imgs[0][y,x,0] = random.randint(0,255)
        imgs[0][y,x,1] = random.randint(0,255)
        imgs[0][y,x,2] = random.randint(0,255)
        
cv2.namedWindow('image', cv2.WINDOW_NORMAL)
        
keyPressed = 0
mod = 0
imgCurrent = imgs[0]
imgPrevious = imgs[1]
angle = 0
counter = 0.0

while keyPressed != 113: # press 'q' to exit

    angle += 2.0
    counter += 1.0
    c1 = math.cos(0.001*counter)
    c2 = math.cos(0.0001*counter)
    c3 = math.cos(0.015*counter)
    c4 = math.cos(0.0003*counter)
    
    m1 = cv2.getRotationMatrix2D((width/2+c1*20,height/2+c2*20),angle*c1,0.8*c1)
    m1.resize((3,3))
    m1[2,2] = 1
    m2 = np.array([[1.0,0,width*0.3*c1],[0,1.0,height*0.2*c4],[0,0,1]])
    m3 = np.dot(m2,m1)
    imgR1 = cv2.warpPerspective(imgCurrent,m3,(width,height),) # assume a square template image
    
    m1 = cv2.getRotationMatrix2D((width/2+c3*20,height/2+c2*20),125+angle*c2,0.6*c2)
    m1.resize((3,3))
    m1[2,2] = 1
    m2 = np.array([[1.0,0,-width*0.4*c3],[0,1.0,-height*0.1*c4],[0,0,1]])
    m3 = np.dot(m2,m1)
    imgR2 = cv2.warpPerspective(imgCurrent,m3,(width,height),) # assume a square template image
    
    m1 = cv2.getRotationMatrix2D((width/2+c2*20,height/2+c4*20),25+angle*c4,0.3*c3)
    m1.resize((3,3))
    m1[2,2] = 1
    m2 = np.array([[1.0,0,-width*0.5*c3],[0,1.0,-height*0.4*c4],[0,0,1]])
    m3 = np.dot(m2,m1)
    imgR3 = cv2.warpPerspective(imgCurrent,m3,(width,height),) # assume a square template image
    
    # operations on the image:
    # compose it
    imgCurrent = cv2.addWeighted(imgR1,1.0,imgR2,1.0,0) 
    imgCurrent = cv2.addWeighted(imgCurrent,1.0,imgR3,1.0,0) 
    # zoom it
    m4 = cv2.getRotationMatrix2D((width/2,height/2),0,1.2+0.2*c3)
    imgCurrent = cv2.warpAffine(imgCurrent,m4,(width,height),)        
    cv2.normalize(imgCurrent,imgCurrent,0,255,cv2.NORM_MINMAX)    
    # apply a color map
    imgCurrent = cv2.addWeighted(imgCurrent,0.9, cv2.applyColorMap(imgCurrent,cv2.COLORMAP_HSV),0.1,0)
    # compose it with previous iteration
    imgCurrent = cv2.addWeighted(imgCurrent,0.9,imgPrevious,0.1,0)
    imgPrevious = imgCurrent.copy()
    # show
    cv2.imshow('image',imgCurrent)        
    keyPressed = cv2.waitKey(30)
cv2.destroyAllWindows()