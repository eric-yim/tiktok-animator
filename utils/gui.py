import cv2
import argparse
import glob, os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from utils.image_util import ImageUtil
from omegaconf import OmegaConf
hotkey_dict = {
    'z':'ADD_LAYER',
    'x':'EDIT_EXISTING_LAYER',
    '.':'NEXT_FRAME',
    ',':'PREV_FRAME',
    '/':'CHANGE_FRAME',
    'c':'ADD_CAMERA',
    'q':'QUIT'
}
class CMD:
    INIT, \
    ADD_LAYER, \
    EDIT_EXISTING_LAYER, \
    NEXT_FRAME, \
    PREV_FRAME, \
    CHANGE_FRAME, \
    ADD_CAMERA, \
    QUIT = range(8)
class STATE:
    KEY_COMMAND, \
    LAYER_POINT, \
    LAYER_POINT_EDIT, \
    ADD_CAMERA = range(4)

    
class DataPass:
    def __init__(self,img,cmd,frame_i=0,cfg={}):
        self.img = img
        self.cmd = cmd
        self.cfg = cfg
        self.frame_i = frame_i
    def get_title(self):
        return 'frame_'+str(self.frame_i)
class LayerInfo:
    def __init__(self,bdir,subdir,title,thresh=30):
        self.bdir,self.subdir = bdir,subdir
        self.imdir = os.path.join(self.bdir,self.subdir)
        self.start_i = 0
        self.is_valid = os.path.exists(self.imdir)
        if self.is_valid:
            self.len = len(glob.glob(os.path.join(self.imdir,'*')))
        self.frame_info= {
            title:{
                'scale':1.0,
                'src_point':None,
                'tgt_point':None
            }
        }
        self.thresh=thresh
        self.chroma_arr = None
    def imread(self):
        self.img = cv2.imread(sorted(glob.glob(os.path.join(self.imdir,'*')))[self.start_i])[:,:,::-1]
        self.h,self.w = self.img.shape[:2]
    def increment_i(self,di):
        self.start_i += di
        while self.start_i < 0:
            self.start_i += self.len
        if self.start_i >= self.len:
            self.start_i = self.start_i % self.len
    def update_with_info(self,layer):
        self.thresh=layer.thresh
        self.chroma_arr=layer.chroma_arr
        for k,v in layer.frame_info.items():
            self.frame_info[k] = v

        self.start_i = layer.start_i
    def get_dict(self,frame_i):
        my_info = {
            'subdir':self.subdir,
            'start_i':self.start_i,
            'chroma_arr':self.chroma_arr,
            'thresh':self.thresh,
            'frame_info':self.frame_info
        }
        return my_info
def to_float(point):
    if point is None:
        return None
    return [float(a) for a in point]
def to_int(point):
    if point is None:
        return None
    return [int(round(a)) for a in point]
class GUI:
    def __init__(self,data_pass):
        self.layer_info = None
        self._init_cfg(data_pass)
        self._init_figure()
        self._init_frame_data()
        
        
        self.state = STATE.KEY_COMMAND
    def _init_figure(self):
        self.f = plt.figure(figsize=(10,10))
        self.f.canvas.mpl_connect('button_press_event', self._onclick)
        self.f.canvas.mpl_connect('button_release_event',self._releaseclick)
        self.f.canvas.mpl_connect('scroll_event', self._onscroll)
        self.f.canvas.mpl_connect('key_press_event', self._keypress)
        self.f.canvas.mpl_connect('motion_notify_event', self._on_motion) 
        self.ax0 = plt.subplot2grid((2, 1), (0, 0), colspan=1,rowspan=1)
        self.ax1 = plt.subplot2grid((2, 1), (1, 0), colspan=1,rowspan=1)
        self.f.suptitle(self.title)

        
    def _init_cfg(self,dp):
        self.data_pass = dp
        self.round_borders = dp.cfg.get('round_borders',True)
        self.title = dp.get_title()
        self.bdir = dp.cfg.get('workspace','')
        self.fpath = dp.cfg.get('yaml_file','tmp.yaml')
    def _init_frame_data(self):
        if not os.path.exists(self.fpath):
            self.all_output = []
            self.camera = {}
        else:
            tmp_cfg = OmegaConf.load(self.fpath)
            self.all_output = tmp_cfg.layers
            self.camera = tmp_cfg.get('camera',{})
            #self.camera = tmp_cfg.camera or {}
        self.img = self.data_pass.img.copy()
        self._init_image(self.img)
        self._init_second_image(self.img)
        self.h,self.w =self.img.shape[:2]
        for layer in self.all_output:
            if self.data_pass.get_title() in layer.frame_info:
                layer_info = LayerInfo(self.bdir,layer['subdir'],self.data_pass.get_title())
                layer_info.update_with_info(layer)
                self._draw_layer(layer_info)
                self.img = self.onscreen_img
        if self.data_pass.get_title() in self.camera:
            self._draw_camera(self.camera[self.data_pass.get_title()])
            self.img = self.onscreen_img
        
    def _init_image(self,img):
        self.ax0.clear()
        self.ax0.set_title('0')
        self.ax0.imshow(img)
        self.onscreen_img = img.copy()
        self.f.canvas.draw()
    def _init_second_image(self,img):
        self.ax1.clear()
        self.ax1.set_title('1')
        self.ax1.imshow(img)
        self.f.canvas.draw()
    #=========================================================================
    # Key and Mouse Events
    def _onclick(self,event):
        if self.state==STATE.KEY_COMMAND:
            print_commands()
        elif self.state==STATE.LAYER_POINT or self.state==STATE.LAYER_POINT_EDIT:
            if event.inaxes:
                #Mid Click
                if event.button==2:
                    tmp = self.layer_info.frame_info[self.title]
                    if tmp['tgt_point'] is None:
                        print("No tgt_point found")
                    elif tmp['src_point'] is None:
                        print("No src_point found")
                    else:
                        print("Confirmed Layer")
                        self.img = self.onscreen_img
                        self.save(self.layer_info)
                        self.state= STATE.KEY_COMMAND
                else:
                    if event.inaxes.get_title()=='0':
                        self._onclick_first(event)
                    elif event.inaxes.get_title()=='1':
                        self._onclick_second(event)
                    self._draw_layer(self.layer_info)
        elif self.state==STATE.ADD_CAMERA:
            if event.inaxes:
                if event.inaxes.get_title()=='0':
                    self._onclick_camera(event)
    def _on_motion(self,event):
        if self.state == STATE.ADD_CAMERA:
            if self.cam_point0 is not None:
                if event.inaxes:
                    if event.inaxes.get_title()=='0':
                        x1,y1 = (event.xdata,event.ydata)
                        x0,y0 = self.cam_point0
                        x0,y0,x1,y1 = [int(round(a)) for a in [x0,y0,x1,y1]]
                        
                        if x1>x0 and y1>y0:
                            temp_img = self.img.copy()
                            temp_img = draw_rect(temp_img,x0,y0,x1,y1)
                            self._init_image(temp_img)
                            self.cam_point1 = (event.xdata,event.ydata)
        
    
    def _onclick_camera(self,event):
        point = (event.xdata,event.ydata)
        if self.round_borders:
            point = round_borders(point,self.h,self.w)
        self.cam_point0 = point
    def _releaseclick(self,event):
        if self.state == STATE.ADD_CAMERA:
            if (self.cam_point0 is not None) and (self.cam_point1 is not None):
                print("Camera set")
                if self.round_borders:
                    self.cam_point1 = round_borders(self.cam_point1,self.h,self.w)
                self.cam_point1 = adjust_bottom_right(self.cam_point0,self.cam_point1,self.data_pass.cfg.render.resolution)
                self.camera[self.title] = {'tl':to_float(self.cam_point0),'br':to_float(self.cam_point1)}
                self.cam_point0 = None
                self.cam_point1 = None
                self._draw_camera(self.camera[self.title])
                self.img = self.onscreen_img
                self.state=STATE.KEY_COMMAND
                self.save_other()

    def _onclick_first(self,event):
        #Left Click
        if event.button==1:
            temp_img = self.img.copy()
            point = (event.xdata,event.ydata)
            if self.round_borders:
                point = round_borders(point,self.h,self.w)
            self.layer_info.frame_info[self.title]['tgt_point'] = to_float(point)

    
         
    def _onclick_second(self,event):
        point = (event.xdata,event.ydata)
        #Left Click = Choose center
        if event.button==1:
            if self.round_borders:
                point = round_borders(point,self.layer_info.h,self.layer_info.w)
            self.layer_info.frame_info[self.title]['src_point']=to_float(point)
            
        #Right Click = Choose chroma key
        elif event.button==3:
            x0,y0 = (int(round(point[0])),int(round(point[1])))
            chroma_arr = self.layer_info.img[y0,x0]
            self.layer_info.chroma_arr = to_float(chroma_arr)
            print(f"Chose chroma_arr {chroma_arr}")


    def _keypress(self,event):
        """
        Key Commands
        """
        if self.state==STATE.LAYER_POINT:
            print("Middle Click to Save Point")
        elif self.state==STATE.KEY_COMMAND:
            if event.key in hotkey_dict:
                cmd = hotkey_dict[event.key]
                print(f"Command: {cmd}")
                cmd = getattr(CMD,cmd)
                if cmd == CMD.ADD_LAYER:
                    self._add_layer()
                elif cmd==CMD.EDIT_EXISTING_LAYER:
                    self._edit_layer()
                elif cmd == CMD.NEXT_FRAME:
                    self._change_frame(1)
                elif cmd == CMD.PREV_FRAME:
                    self._change_frame(-1)
                elif cmd == CMD.CHANGE_FRAME:
                    self._input_frame()
                elif cmd == CMD.ADD_CAMERA:
                    self._add_camera()
                elif cmd ==CMD.QUIT:
                    self.data_pass.cmd = CMD.QUIT
                else:
                    print(f"Unknown Key: {event.key}")
    def _onscroll(self,event):
        if self.state==STATE.KEY_COMMAND:
            print_commands()
        else:
            if event.inaxes.get_title()=='0':
                if event.button=='up':
                    self.layer_info.frame_info[self.title]['scale'] += 0.05
                elif event.button=='down':
                    self.layer_info.frame_info[self.title]['scale'] -= 0.05
                self._draw_layer(self.layer_info)
            if event.inaxes.get_title()=='1':
                if event.button=='up':
                    self.layer_info.increment_i(1)
                elif event.button=='down':
                    self.layer_info.increment_i(-1)
                
                self._init_second_image(self.layer_info.img)
                self._draw_layer(self.layer_info)
    #=========================================================================
    # Layers
    def _add_layer(self):
        while True:
            self.layer_info = LayerInfo(self.bdir,input('Image Subdir:'),self.data_pass.get_title())
            if self.layer_info.is_valid:
                break
            else:
                print(f"Can't find {self.layer_info.imdir}")
        self.layer_info.imread()
        self._init_second_image(self.layer_info.img)
        self.state = STATE.LAYER_POINT
    def _edit_layer(self):
        if len(self.all_output)<1:
            print("No layers found")
            return
        print("="*20)
        for i,layer in enumerate(self.all_output):
            print(f"{i}: {layer['subdir']}")
        print("="*20)
        i = int(input('Choose i from existing layers:'))
        if i >= len(self.all_output):
            return
        layer = self.all_output[i]
        self.layer_info = LayerInfo(self.bdir,layer['subdir'],self.data_pass.get_title())
        self.layer_info.update_with_info(layer)
        self.layer_info.imread()
        self._init_second_image(self.layer_info.img)
        self.layer_i = i
        self.state = STATE.LAYER_POINT_EDIT
    #=========================================================================
    # Frames
    def _change_frame(self,di):
        self.data_pass.frame_i += di
        if self.data_pass.frame_i < 0:
            self.data_pass.frame_i = 0
        plt.close()
    def _input_frame(self):
        try:
            self.data_pass.frame_i = int(input('Input frame number:'))
        except:
            print("Must be an integer")
            return
        if self.data_pass.frame_i < 0:
            self.data_pass.frame_i = 0
        plt.close()
    #=========================================================================
    # Camera
    def _add_camera(self):
        self.cam_point0 = None
        self.cam_point1 = None
        self.state = STATE.ADD_CAMERA

    #=========================================================================
    # Draw
    def _draw_camera(self,tmp_dict):
        top_left = tmp_dict['tl']
        bot_right = tmp_dict['br']
        x0,y0,x1,y1 = [int(round(a)) for a in [*top_left,*bot_right]]
        tmp_img = self.img.copy()
        tmp_img = draw_rect(tmp_img,x0,y0,x1,y1)
        self._init_image(tmp_img)

    
    def _draw_layer(self,layer_info):
        layer_info.imread()
        img1 = layer_info.img.copy()
        tmp = layer_info.frame_info[self.title]
        if tmp['src_point'] is not None:
            img1 = draw_point(img1,tmp['src_point'])
        self._init_second_image(img1)

        img0 = self.img.copy()
        if (tmp['src_point'] is not None) and (tmp['tgt_point'] is not None):
            img0 =ImageUtil.overlay(img0,layer_info.img,
                    arr=layer_info.chroma_arr,
                    thresh=layer_info.thresh,
                    **tmp)
        self._init_image(img0)
    #=========================================================================
    # Save
    def save(self,layer_info):
        my_dict = layer_info.get_dict(self.data_pass.frame_i)
        if self.state == STATE.LAYER_POINT_EDIT:
            self.all_output[self.layer_i]=my_dict
        elif self.state==STATE.LAYER_POINT:
            self.all_output.append(my_dict)
        self.save_other()
    def save_other(self):
        all_out = {
            'layers':self.all_output,
            'camera':self.camera
        }
        conf = OmegaConf.create(all_out)
        OmegaConf.save(config=conf, f=self.fpath)
        print(f"Wrote to {self.fpath}, Layers {len(self.all_output)}, Camera {len(self.camera)}")


def round_borders(point,h,w,thresh=0.03):
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
def draw_point(img,point):
    center = (int(round(point[0])),int(round(point[1])))
    return cv2.circle(img,center,radius=10,color=(255,0,255),thickness=5)
def draw_rect(img,x0,y0,x1,y1):
    return cv2.rectangle(img,(x0,y0),(x1,y1),(0,255,0),3)
def print_commands():
    print("="*20)
    print("Choose a command")
    for k,v in hotkey_dict.items():
        print(k,v)
    print("="*20)
def adjust_bottom_right(tl,br,resolution):
    assert len(resolution)==2, f'Expects resolution to be len 2, found {len(resolution)}'
    w,h = [float(a) for a in resolution]
    x0,y0,x1,y1 = (*tl,*br)
    if h > w:
        dy = y1-y0
        dx = (dy*w/h)
        y1 = y0 + dy
        x1 = x0 + dx
    else:
        dx = x1-x0
        dy = (dx*h/w)
        y1 = y0 + dy
        x1 = x0 + dx
    return x1,y1

        