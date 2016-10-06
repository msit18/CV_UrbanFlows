#!/usr/bin/env python

# --------------------------------------------------------
# Faster R-CNN
# Copyright (c) 2015 Microsoft
# Licensed under The MIT License [see LICENSE for details]
# Original Example Code by Ross Girshick

# This code is work created by Michelle Sit
# --------------------------------------------------------

"""
Demo script showing detections in sample images.
INTEGRATING TRACKING FOR THESE CARS

"""

import _init_paths
from fast_rcnn.config import cfg
from fast_rcnn.test import im_detect
from fast_rcnn.nms_wrapper import nms
from utils.timer import Timer
import matplotlib.pyplot as plt
import numpy as np
import scipy.io as sio
import caffe, os, sys, cv2, time, math
import argparse

import video
from common import anorm2, draw_str
from time import clock

class UrbanFlows():

    lk_params = dict( winSize  = (15, 15),
                      maxLevel = 2,
                      criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

    feature_params = dict( maxCorners = 500,
                           qualityLevel = 0.3,
                           minDistance = 7,
                           blockSize = 7 )

    def __init__(self):
        self.totalCarCount = 0

#Detects cars within frame, detects corners of interest within detected car frame, outputs array
    def carDetectionMethod(self, im, im_copy, frame_gray, net, detectedCarsInThisFrame):
        scores, boxes = im_detect(net, im)

        # Visualize detections for each class
        CONF_THRESH = 0.7
        NMS_THRESH = 0.3

        detectedCarsInThisFrame = []

        for cls_ind, cls in enumerate(CLASSES[1:]):
            #detect all potential elements of interest here using rcnn
            cls_ind += 1 # because we skipped background
            cls_boxes = boxes[:, 4*cls_ind:4*(cls_ind + 1)]
            cls_scores = scores[:, cls_ind]
            dets = np.hstack((cls_boxes,
                              cls_scores[:, np.newaxis])).astype(np.float32) #stacks them together
            keep = nms(dets, NMS_THRESH) #Removes overlapping bounding boxes
            dets = dets[keep, :]
            if cls == "car":
                inds = np.where(dets[:, -1] >= 0.5)[0] #Threshold applied to score values here
                # if len(inds) == 0:
                #     return tracks

                im = im[:, :, (2, 1, 0)]

                #Calculate center of box, and draw on image. Use cvDrawBBox for cv2 (expects integers)
                #x = bbox[0], y = bbox[1] (top left corner)
                #x1 = bbox[2], y1 = bbox[3] (bottom right corner)
                #print "Number of cars in frame: ", len(inds)
                for i in inds:
                    bbox = dets[i, :4]
                    carDetectedBBox = bbox.astype(int)
                    score = dets[i, -1]
                    #Draw rectangle on color copy
                    #If the coordinates of the detected box are not within the offending area, do below. Limit area here.
                    #cv2.rectangle(im_copy, (carDetectedBBox[0], carDetectedBBox[1]), (carDetectedBBox[2], carDetectedBBox[3]), (255, 0, 0), 3) #Blue
                    
                    #Calculate corners of interest within the bounding box area and add them all to the carCorner array
                    detectedCarPixels = frame_gray[bbox[1]:bbox[3], bbox[0]:bbox[2]] #[y1:y2, x1:x2]
                    detectedCarPixelsColor = im_copy[bbox[1]:bbox[3], bbox[0]:bbox[2]] #for show on colored image
                    #carCorners = cv2.goodFeaturesToTrack(detectedCarPixels, mask=detectedCarPixels, **self.feature_params).reshape(-1, 2)
                    carCorners = []

                    for x, y in np.float32(carCorners).reshape(-1, 2): #Blue
                        cv2.circle(detectedCarPixels, (x,y), 5, (255, 0, 0), -1)
                        cv2.circle(detectedCarPixelsColor, (x, y), 5, (255, 0, 0), -1)

                    detectedCarsInThisFrame.append([[carDetectedBBox, carCorners]]) #pair0

                print "detectedCarsInThisFrame len: {0}-------------------------------------".format(len(detectedCarsInThisFrame))

                return detectedCarsInThisFrame

    def thresholding (self, detectedCars, newCars, im_copy, frameNum):
        aggregatedCars = []
        print "detectedCars shape: ", np.array(detectedCars).shape
        print "newCars shape: ", np.array(newCars).shape
        for singleNewCarIndex in range(len(newCars)):
            for singleDetectedCarIndex in range(len(detectedCars)):
                confirmAppended = False
                # print "detectedCars[singleNewCarIndex]: ", detectedCars[singleDetectedCarIndex]
                # print "detectedCars[singleDetectedCarIndex][-1][0][0]: ", detectedCars[singleDetectedCarIndex][-1][0][0]
                cv2.circle(im_copy, (newCars[singleNewCarIndex][-1][0][0], newCars[singleNewCarIndex][-1][0][1]), 5, (0, 0, 0), -1)
                cv2.circle(im_copy, (detectedCars[singleDetectedCarIndex][-1][0][0], detectedCars[singleDetectedCarIndex][-1][0][1]), 5, (0, 255, 255), -1)

                print "math: ", math.hypot(abs(newCars[singleNewCarIndex][-1][0][0] - detectedCars[singleDetectedCarIndex][-1][0][0]), abs(newCars[singleNewCarIndex][-1][0][1] - detectedCars[singleDetectedCarIndex][-1][0][1]))   #pair0
                if math.hypot(abs(newCars[singleNewCarIndex][-1][0][0] - detectedCars[singleDetectedCarIndex][-1][0][0]), abs(newCars[singleNewCarIndex][-1][0][1] - detectedCars[singleDetectedCarIndex][-1][0][1])) < 100: #pair0
                    print "Less than 100**********"
                    print "DRAW BLUE RECTANGLE"
                    detectedCars[singleDetectedCarIndex].append(newCars[singleNewCarIndex][0])
                    aggregatedCars.append(detectedCars[singleDetectedCarIndex])
                    cv2.rectangle(im_copy, (detectedCars[singleDetectedCarIndex][-1][0][0], detectedCars[singleDetectedCarIndex][-1][0][1]), (detectedCars[singleDetectedCarIndex][-1][0][2], detectedCars[singleDetectedCarIndex][-1][0][3]), (255, 0, 0), 3)
                    del detectedCars[singleDetectedCarIndex]       
                    confirmAppended = True
                    break

            if (confirmAppended == False):
                print "DRAW WHITE RECTANGLE"
                aggregatedCars.append(newCars[singleNewCarIndex])
                cv2.rectangle(im_copy, (newCars[singleNewCarIndex][-1][0][0], newCars[singleNewCarIndex][-1][0][1]), (newCars[singleNewCarIndex][-1][0][2], newCars[singleNewCarIndex][-1][0][3]), (255, 255, 255), 3)
                self.totalCarCount += 1
                print "If statement is true. += totalCarCount. Appended size is now: ", len(aggregatedCars)
            print "NEXT CAR;;;;;;;;;;;;;;;;;;;;;;;;;;;;"

        print "DC & FN?: ", (len(detectedCars)>0 and (frameNum%10>0))
        if (len(detectedCars)>0 and (frameNum%10>0)):
            print "adding remaining cars to the end of aggregatedCars"
            for remainingCar in detectedCars:
                aggregatedCars.append(remainingCar)
                print "DRAW GREEN RECTANGLE"
                cv2.rectangle(im_copy, (remainingCar[-1][0][0], remainingCar[-1][0][1]), (remainingCar[-1][0][2], remainingCar[-1][0][3]), (0, 255, 0), 3) #green

        #Vizualize the car traveling through the space
        for car in aggregatedCars:
            tracks = []
            for x, y in zip([pts[0][0] for pts in car], [pts[0][1] for pts in car]):
                tracks.append([x, y])
            tracks = np.array([tracks], dtype=np.int32)
            cv2.polylines(im_copy, tracks, False, (0, 0, 0))

        print "-----------------------len aggregatedCars: ", len(aggregatedCars)

        return aggregatedCars

    def countingCentroids(self, analyzeCarArray, im_copy):
        bboxCoordinates = [coordArrays[-1][0] for coordArrays in analyzeCarArray]
        print "bboxCoordinates: ", bboxCoordinates
        for eachDetectedCar in bboxCoordinates:
            print "eachDetectedCar: ", eachDetectedCar
            ##USE CENTROID WEIGHTS FROM THE DETECTED CORNERS? TRACK AVERAGE KEYPOINTS
            ###CALCULATE FRAME CENTROID AND CORNER CENTROID. COMPARE VALUES
            coordCentroid = ((eachDetectedCar[0] + (eachDetectedCar[2]-eachDetectedCar[0])/2), (eachDetectedCar[1] + (eachDetectedCar[3]-eachDetectedCar[1])/2))
            #cv2.circle(im_copy, (coordCentroid[0], coordCentroid[1]), 5, (0, 0, 0), -1)
            #print "coord centroid: ", coordCentroid


#Simple code - works crudely. No temporal tracking. Need to use corners to track
    def simpleThresholding(self, tracks, inputArray):
        tracksLength = len(tracks)
        for x in range(len(inputArray)):
            print str(inputArray[x][-1][0]) + "-------------------------------"
            newTracksXVal = inputArray[x][-1][0]
            newTracksYVal = inputArray[x][-1][1]
            confirmAppended = False
            for y in range(tracksLength):
                print "math: ", math.hypot(newTracksXVal - tracks[y][-1][0], newTracksYVal - tracks[y][-1][1])
                if math.hypot(newTracksXVal-tracks[y][-1][0], newTracksYVal-tracks[y][-1][1]) <= 100:
                    tracks[y].append((newTracksXVal, newTracksYVal))
                    print "tracks appended in that value: ", tracks
                    break
                if len(tracks[y]) > 10:
                    print "track too long. deleting {0}".format(tracks[y][0])
                    del tracks[y][0]
                elif (confirmAppended == False) & (y == tracksLength-1):
                    tracks.append([(newTracksXVal, newTracksYVal)])
                    print "tracks appended to the end"

    def detectTrackCars(self, net):
        """Detect object classes in an image using pre-computed object proposals."""

        cap = cv2.VideoCapture("/media/senseable-beast/beast-brain-1/Data/TrafficIntersectionVideos/slavePi2_RW1600_RH1200_TT900_FR15_06_10_2016_18_11_00_604698.h264")

        detectedCars = [] #stores all information about the detected cars
        newCars = [] #newly detectedCars. Matched to ones stored in detectedCars in thresholding method
        frameNum = 0
        
        while (cap.isOpened()):
            ret, im = cap.read()
            frame_gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            im_copy = im.copy()
            if len(detectedCars) <= 0:
                detectedCars = c.carDetectionMethod(im, im_copy, frame_gray, net, detectedCars)
                print "len(detectedCars): ", len(detectedCars)
                self.totalCarCount += len(detectedCars)
            elif len(detectedCars) > 0:
                print "detectedcars len: ", len(detectedCars)
                newCars = c.carDetectionMethod(im, im_copy, frame_gray, net, detectedCars)
                print "Updated newCars value: ", len(newCars)
                detectedCars = c.thresholding(detectedCars, newCars, im_copy, frameNum)
                c.countingCentroids(detectedCars, im_copy)

            frameNum += 1
            print "====================================================FRAMENUM {0}, TOTAL CAR COUNTS {1}".format(frameNum, self.totalCarCount)
            prev_gray = frame_gray

            cv2.imshow('frame', im_copy)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            print "take prev_gray frame****************************************************"

        cap.release()

    def parse_args(self):
        """Parse input arguments."""
        parser = argparse.ArgumentParser(description='Faster R-CNN demo')
        parser.add_argument('--gpu', dest='gpu_id', help='GPU device id to use [0]',
                            default=0, type=int)
        parser.add_argument('--cpu', dest='cpu_mode',
                            help='Use CPU mode (overrides --gpu)',
                            action='store_true')
        parser.add_argument('--net', dest='demo_net', help='Network to use [vgg16]',
                            choices=NETS.keys(), default='vgg16')

        args = parser.parse_args()

        return args

if __name__ == '__main__':
    cfg.TEST.HAS_RPN = True  # Use RPN for proposals

    c = UrbanFlows()

    CLASSES = ('__background__',
                'aeroplane', 'bicycle', 'bird', 'boat',
               'bottle', 'bus', 'car', 'cat', 'chair',
               'cow', 'diningtable', 'dog', 'horse',
               'motorbike', 'person', 'pottedplant',
               'sheep', 'sofa', 'train', 'tvmonitor')

    NETS = {'vgg16': ('VGG16',
                      'VGG16_faster_rcnn_final.caffemodel'),
            'zf': ('ZF',
                      'ZF_faster_rcnn_final.caffemodel')}

    args = c.parse_args()

    prototxt = os.path.join(cfg.MODELS_DIR, NETS[args.demo_net][0],
                            'faster_rcnn_alt_opt', 'faster_rcnn_test.pt')
    caffemodel = os.path.join(cfg.DATA_DIR, 'faster_rcnn_models',
                              NETS[args.demo_net][1])

    if not os.path.isfile(caffemodel):
        raise IOError(('{:s} not found.\nDid you run ./data/script/'
                       'fetch_faster_rcnn_models.sh?').format(caffemodel))

    if args.cpu_mode:
        caffe.set_mode_cpu()
    else:
        caffe.set_mode_gpu()
        caffe.set_device(args.gpu_id)
        cfg.GPU_ID = args.gpu_id
    net = caffe.Net(prototxt, caffemodel, caffe.TEST)

    print '\n\nLoaded network {:s}'.format(caffemodel)

    # Warmup on a dummy image
    im = 128 * np.ones((300, 500, 3), dtype=np.uint8)
    for i in xrange(2):
        _, _= im_detect(net, im)

    c.detectTrackCars (net)
    cv2.destroyAllWindows()
