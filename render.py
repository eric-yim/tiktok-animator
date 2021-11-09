import cv2
import argparse
import glob, os,json
from utils.image_util import ImageUtil,ImageLooper, ImageController
from omegaconf import OmegaConf
from builder import get_cl_args

def render(args):
    cfg = OmegaConf.load(args.main_cfg)
    img_black = ImageUtil.black(cfg.background)
    cfg.yaml_file = cfg.yaml_file.format(args.out_name)
    controller_info = OmegaConf.load(cfg.yaml_file)
    controller = ImageController(cfg.render.n_frames,controller_info,strict_start=cfg.render.strict_start)
    img_loopers = []
    for layer in controller_info.layers:
        img_loopers.append(ImageLooper(cfg.workspace,layer.subdir,layer.start_i))
    
    for i in range(cfg.render.n_frames):
        img_new = img_black.copy()
        for j,img_looper in enumerate(img_loopers):
            over_img = next(img_looper)
            binfo,finfo = controller.get_info(j,i)
            if finfo is not None:
                img_new =ImageUtil.overlay(
                    img_new,
                    over_img,
                    arr=binfo['chroma_arr'],
                    thresh=binfo['thresh'],
                    **finfo)
        cinfo = controller.get_camera_info(i)
        img_new = ImageUtil.crop(img_new,cinfo)
            
        h,w = img_new.shape[:2]
        img_new = cv2.resize(img_new,tuple(cfg.render.resolution))
        img_disp = cv2.resize(img_new,tuple([a//cfg.render.display_downscale for a in cfg.render.resolution]))
        cv2.imshow('',img_disp)
        chd = cv2.waitKey(20)
        if chd==ord('q'):
            break

        


if __name__=='__main__':
    args = get_cl_args()
    render(args)