import cv2
import argparse
import glob, os,json
from omegaconf import OmegaConf

import threading, logging
import time
import queue
from shutil import rmtree
exts = ['mp4','MOV','mkv']
def get_cl_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--main_cfg',default='config/main_config.yaml')
    parser.add_argument('--overwrite',action='store_true',help='if true, overwrite existing')
    parser.add_argument('--n_workers',default='4',type=int)
    args = parser.parse_args()
    return args
def extension_split(item):
    return item[:item.rfind('.')],item[item.rfind('.')+1:]

def create_q(args,cfg,listing):
    vid_q = queue.Queue()
    for item in listing:
        subname = os.path.split(item)[1]
        subdir,ext = extension_split(subname)
        #Check if known extension
        if not ext in exts:
            logging.info(f'Skipping {subname}, unknown extension')
            continue
        write_folder = os.path.join(cfg.workspace,subdir)
        #Check if folder exists
        if os.path.exists(write_folder):
            if args.overwrite:
                rmtree(write_folder)
            else:
                continue
        
        vid_q.put_nowait(item)
    logging.info(f"Queue of {vid_q.qsize()} videos")
    return vid_q
class ImageWriter:
    def __init__(self,idx,q,workspace=''):
        self.idx = idx
        logging.info(f"Starting Worker {idx}")
        self.workspace=workspace
        self.is_stopped = threading.Event()
        self.q = q

        t = threading.Thread(target=self._write_imgs)
        t.daemon = True
        t.start()
    def _read_vid(self):
        self.cam = cv2.VideoCapture(self.vidname)
        img_i = 0
        while True:
            ret,frame = self.cam.read()
            if not ret:
                break
            img_i+=1
            name = str(img_i).zfill(6) + '.png'
            cv2.imwrite(os.path.join(self.write_folder,name),frame)
        self.cam.release()
    def _write_imgs(self):
        while not self.q.empty():
            self.vidname = self.q.get_nowait()
            logging.info(f"Worker {self.idx} on Video {os.path.split(self.vidname)[1]}")
            subdir,_ = extension_split(os.path.split(self.vidname)[1])
            self.write_folder = os.path.join(self.workspace,subdir)
            os.makedirs(self.write_folder,exist_ok=True)
            self._read_vid()
            
        
        self.is_stopped.set()
def wait_for_workers(workers):
    for worker in workers:
        while not worker.is_stopped.is_set():
            #logging.info(worker.idx)
            time.sleep(0.1)

def main(args):
    cfg = OmegaConf.load(args.main_cfg)
    listing = sorted(glob.glob(os.path.join(cfg.video_drive,'*')))
    
    q=create_q(args,cfg,listing)
    workers = [ImageWriter(idx,q,workspace=cfg.workspace) for idx in range(args.n_workers)]
    wait_for_workers(workers)

    logging.info("Complete")
if __name__=='__main__':
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    args = get_cl_args()
    main(args)