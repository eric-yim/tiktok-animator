import cv2
import glob, os, json
import numpy as np
def chroma_fn(main_img,img,y0,x0,thresh=30,arr=np.array([0,255,0.0])):
    tmp = np.zeros(main_img.shape[:2],dtype=np.bool)
    not_green = np.mean(np.abs(img.astype(np.float32)-arr),axis=-1) >thresh
    if y0 >=main_img.shape[0]:
        return main_img
    if x0 >= main_img.shape[1]:
        return main_img
    tmp[y0:y0+img.shape[0],x0:x0+img.shape[1]]=not_green
    main_img[tmp]=img[not_green]
    return main_img

def prepare_over(over_img,x0_tgt,y0_tgt,x0_src,y0_src,w,h,scale):
    y_off,x_off = 0,0
    y0 = y0_src*scale - y0_tgt
    y1 = y0+h

    x0 = x0_src * scale - x0_tgt
    x1 = x0 + w
    
    x0,y0,x1,y1 = [int(round(a)) for a in [x0,y0,x1,y1]]
    if y0 < 0:
        y_off = abs(y0)
        y0 = 0
    if x0 < 0 :
        x_off = abs(x0)
        x0 = 0
    h0,w0 = over_img.shape[:2]
    h0,w0 = int(round(h0*scale)),int(round(w0*scale))
    over_img = cv2.resize(over_img,(w0,h0))
    return over_img[y0:y1,x0:x1],(y_off,x_off)

class ImageUtil:
    @staticmethod
    def black(shape):
        assert len(shape)==2, "Expects h,w"
        return np.zeros((*shape[::-1],3),dtype=np.uint8)
    @staticmethod
    def overlay(main_img,cover_img,tgt_point=None,src_point=None,thresh=30,arr=None,scale=1.0):
        assert tgt_point is not None, "tgt_point is None"
        assert src_point is not None, "src_point is None"
        
        over_img = cover_img.copy()
        x0_tgt,y0_tgt = int(round(tgt_point[0])),int(round(tgt_point[1]))
        x0_src,y0_src = int(round(src_point[0])),int(round(src_point[1]))
        h,w = main_img.shape[:2]
        over_img,(y_off,x_off)=prepare_over(over_img,x0_tgt,y0_tgt,x0_src,y0_src,w,h,scale)
        
        if not arr is None:
            
            return chroma_fn(main_img,over_img,y_off,x_off,thresh=thresh,arr=np.array(arr))
        main_img[y_off:y_off+over_img.shape[0],x_off:x_off+over_img.shape[1]]=over_img
        return main_img
    @staticmethod
    def crop(img,cinfo):
        if cinfo is None:
            return img
        x0,y0 = cinfo['tl']
        x1,y1 = cinfo['br']
        #print(x0,x1,y0,y1,img.shape)
        x0,y0,x1,y1 = [int(round(a)) for a in [x0,y0,x1,y1]]
        return img[y0:y1,x0:x1]

def get_listing(bdir,sdir):
    return sorted(glob.glob(os.path.join(bdir,sdir,'*')))
class ImageLooper:
    def __init__(self,bdir,sdir,i=-1):
        self.i=i
        self.subdir = sdir
        self.listing = get_listing(bdir,sdir)
        self.shape = self.load_img(0).shape
    def __len__(self):
        return len(self.listing)
    def load_img(self,i):
        return cv2.imread(self.listing[i])
    def __next__(self):
        self.i+=1
        if self.i==self.__len__():
            self.i=0
        return self.load_img(self.i)
def sample_points(x,xp,fp):
    x,xp,fp = np.array(x),np.array(xp),np.array(fp)
    if fp.ndim==1:
        return np.interp(x,xp,fp)
    return np.array([sample_points(x,xp,fpp) for fpp in fp.T]).T

def fill_in(n_frames,frame_info,dummy_word='frame_'):
    def dummy_str(a):
        return dummy_word+str(a)    
    xp = sorted([int(a.replace(dummy_word,'')) for a in frame_info.keys()])
    x = np.arange(0,n_frames)
    the_keys = list(frame_info[dummy_str(xp[0])].keys())
    
    out_info = {}
    for i in range(n_frames):
        out_info[dummy_word+str(i)]={}
    for k in the_keys:
        fp = [frame_info[dummy_str(x0)][k] for x0 in xp]
        fnew = sample_points(x,xp,fp)

        for i,f0 in enumerate(fnew):
            out_info[dummy_word+str(i)][k]=f0

    return out_info
def get_basic(frame_info):
    ignores = {'frame_info'}
    out_info = {}
    for k,v in frame_info.items():
        if not k in ignores:
            out_info[k]=v
    return out_info


        
class ImageController:
    def __init__(self,n_frames,controller_info):
        self.controller_info = controller_info
        self.n_frames = n_frames
        
        self.frame_infos = [fill_in(n_frames,a.frame_info) for a in controller_info.layers]
        
        self.basic_infos = [get_basic(a) for a in controller_info.layers]
        self.cam_info = controller_info.get('camera',None)
        if self.cam_info is not None:
            self.cam_info = fill_in(n_frames,self.cam_info) 
        self.i = 0
        self.n_layers = len(self.frame_infos)
        self.dummy_word = 'frame_'
    def get_info(self,j,i):
        """
        i is frame number
        j is which layer
        """
        assert i < self.n_frames, f"i too big: {i}"
        assert j < self.n_layers, f"j too big: {j}"
        finfo = self.frame_infos[j][self.dummy_word+str(i)]
        
        binfo = self.basic_infos[j]
        return binfo,finfo
    def get_camera_info(self,i):
        return  self.cam_info[self.dummy_word+str(i)] if self.cam_info is not None else None
    
