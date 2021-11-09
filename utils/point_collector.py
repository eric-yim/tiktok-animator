import cv2
import argparse
import glob, os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import json
class PointCollector:
    """
    For labeling keypoints

    Saves json as such
    [
        {x: data, y: data},
        {x: data, y: data}
    ]

    Output is a list
    """
    def __init__(self,img,output,scaled=False,title=None,round_borders=False,no_lines=True,other_points=[]):
        assert isinstance(output,list), "Output Must be a List"
        self.no_lines = no_lines
        self.output=output
        self.round_borders=round_borders    
        self.scaled = scaled
        #self.original_img = img.copy()
        self.img = img

        self.h,self.w =img.shape[:2]
        self.f = plt.figure(figsize=(10,6))
        
        self.f.canvas.mpl_connect('button_press_event', self._onclick)
        self.ax = plt.subplot2grid((1, 1), (0, 0), colspan=1,rowspan=1)
        if title:
            self.f.suptitle(title)
        
        self.other_points = other_points
    
        #self.names = names
        self.f.canvas.mpl_connect('scroll_event', self._onscroll)
        self.i = 0
        #self._display_name()
        self._redraw()
        

    def _init_image(self):
        self.ax.clear()
        self.ax.imshow(self.img)
        
        self.f.canvas.draw()
    def _onclick(self,event):
        if event.inaxes:
            #Left Click
            if event.button==1:
                point = (event.xdata,event.ydata)
                self._add_point(point)
                
                
            #Mid Click
            elif event.button==2:
                
                plt.close()
                
            #Right Click
            elif event.button==3:
                self._remove_point()
            self._redraw()

    def _onscroll(self,event):
        pass
    def _round_to_border(self,point,h,w,thresh=0.03):
        point = list(point)
        if (point[0] - 0.0)/(float(w)) < thresh:
            point[0] = 0
        elif (float(w) - point[0])/(float(w)) < thresh:
            point[0] = w
        if (point[1] - 0.0)/(float(h)) < thresh:
            point[1] = 0
        elif (float(h) - point[1])/(float(h)) < thresh:
            point[1] = h
        return tuple(point)

    def _add_point(self,point):
        if self.round_borders:
            point = self._round_to_border(point,self.h,self.w)
        if self.scaled:
            point = self._scale_points(point,self.h,self.w)
        self.output.append({'x':point[0],'y':point[1]})
    
        self._draw_point(point)
        

    def _write_to_output(self):
        """
        Write self.points to txt file
        """
        pass
    def _redraw(self):
        self._init_image()
        for i in range(0,len(self.output),2):
            v0 = self.output[i]
            p0 = (v0['x'],v0['y'])
            self._draw_point(p0)
            if i+1 < len(self.output):
                v1 = self.output[i+1]
                p1 = (v1['x'],v1['y'])
                self._draw_point(p1)
                #self._draw_line(p0,p1)
                if not self.no_lines:
                    self._draw_rect(p0,p1)
        for i in range(0,len(self.other_points),2):
            v0 = self.other_points[i]
            p0 = (v0['x'],v0['y'])
            self._draw_point(p0,'red')
            if i+1 < len(self.other_points):
                v1 = self.other_points[i+1]
                p1 = (v1['x'],v1['y'])
                self._draw_point(p1,'red')
                #self._draw_line(p0,p1)
                if not self.no_lines:
                    self._draw_rect(p0,p1)
        # for v in self.output:
        #     point =(v['x'],v['y'])
        #     self._draw_point(point)

    def _remove_point(self):
        if len(self.output) > 0:
            self.output.pop(-1)

    def _scale_points(self,points,h,w):
        """
        Expects list of tuples OR single tuple
        [(x,y),(x,y)] OR (x,y)
        """
        h = float(h)
        w = float(w)
        if isinstance(points,list):
            return [self._scale_points(point,h,w) for point in points]
        return (points[0]/w,points[1]/h)
    def _unscale_points(self,points,h,w):
        h = float(h)
        w = float(w)
        if isinstance(points,list):
            return [self._unscale_points(point,h,w) for point in points]
        return (points[0]*w,points[1]*h)
            
    def _draw_point(self,point,color='lawngreen'):
        if self.scaled:
            point = self._unscale_points(point,self.h,self.w)
        circle = patches.Circle(point,5,fill=True,facecolor=color,edgecolor='black')
        self.ax.add_patch(circle)
        self.f.canvas.draw()
    def _draw_line(self,point0,point1):
        if self.scaled:
            point0 = self._unscale_points(point0,self.h,self.w)
            point1 = self._unscale_points(point1,self.h,self.w)
        self.ax.plot([point0[0],point1[0]],[point0[1],point1[1]],color='lawngreen')
        self.f.canvas.draw()
    def _draw_rect(self,point0,point1):
        if self.scaled:
            point0 = self._unscale_points(point0,self.h,self.w)
            point1 = self._unscale_points(point1,self.h,self.w)
        sp = [point0[0],point0[1]]
        w = point1[0]-point0[0]
        h = point1[1]-point0[1]
        rect = patches.Rectangle(sp,w,h,linewidth=3,edgecolor='lawngreen',facecolor='none')
        self.ax.add_patch(rect)
        self.f.canvas.draw()