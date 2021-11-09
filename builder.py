import cv2
import argparse
import glob, os,json
from utils.point_collector import PointCollector
from utils.gui import GUI,DataPass,CMD
from utils.image_util import ImageUtil
import matplotlib.pyplot as plt
from omegaconf import OmegaConf

def get_cl_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out_name', required=True, type=str)
    parser.add_argument('--main_cfg',default='config/main_config.yaml')
    args = parser.parse_args()
    return args
def build(args):
    cfg = OmegaConf.load(args.main_cfg)
    img = ImageUtil.black(cfg.background)
    cfg.yaml_file = cfg.yaml_file.format(args.out_name)
    cmd = CMD.INIT
    dp = DataPass(img,cmd,frame_i=0,cfg=cfg)
    while True:
        gui=GUI(dp)
        plt.show()
        if dp.cmd ==CMD.QUIT:
            break


if __name__=='__main__':
    args = get_cl_args()
    build(args)
