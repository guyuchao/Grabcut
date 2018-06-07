from PIL import Image
import numpy as np
from grabcut.GMM import GMM
from math import log
from grabcut.Kmeans import Kmeans
import copy
from grabcut.gcgraph import GCGraph

class grabcut(object):
    def __init__(self):
        self.cluster=5
        self.BGD_GMM=None
        self.FGD_GMM=None
        self._gamma=50
        self._lambda=9*self._gamma
        self.GT_bgd=0#ground truth background
        self.P_fgd=1#ground truth foreground
        self.P_bgd=2#may be background
        self.GT_fgd=3#may be foreground

    def calcBeta(self,npimg):
        '''

        :param self:
        :param npimg:array of img:h,w,c,type=np.float32
        :return: beta :reference to formula 5 of 《https://cvg.ethz.ch/teaching/cvl/2012/grabcut-siggraph04.pdf》
        '''
        rows,cols=npimg.shape[:2]

        ldiff = np.linalg.norm(npimg[:, 1:] - npimg[:, :-1])
        uldiff = np.linalg.norm(npimg[1:, 1:] - npimg[:-1, :-1])
        udiff = np.linalg.norm(npimg[1:, :] - npimg[:-1, :])
        urdiff = np.linalg.norm(npimg[1:, :-1] - npimg[:-1, 1:])
        beta=np.square(ldiff)+np.square(uldiff)+np.square(udiff)+np.square(urdiff)
        beta = 1 / (2 * beta / (4 * cols * rows - 3 * cols - 3 * rows + 2))
        return beta

    def calcSmoothness(self, npimg, beta, gamma):
        rows,cols=npimg.shape[:2]
        self.lweight = np.zeros([rows, cols])
        self.ulweight = np.zeros([rows, cols])
        self.uweight = np.zeros([rows, cols])
        self.urweight = np.zeros([rows, cols])
        for y in range(rows):
            for x in range(cols):
                color = npimg[y, x]
                if x >= 1:
                    diff = color - npimg[y, x-1]
                    # print(np.exp(-self.beta*(diff*diff).sum()))
                    self.lweight[y, x] = gamma*np.exp(-beta*(diff*diff).sum())
                if x >= 1 and y >= 1:
                    diff = color - npimg[y-1, x-1]
                    self.ulweight[y, x] = gamma/np.sqrt(2) * np.exp(-beta*(diff*diff).sum())
                if y >= 1:
                    diff = color - npimg[y-1, x]
                    self.uweight[y, x] = gamma*np.exp(-beta*(diff*diff).sum())
                if x+1 < cols and y >= 1:
                    diff = color - npimg[y-1, x+1]
                    self.urweight[y, x] = gamma/np.sqrt(2)*np.exp(-beta*(diff*diff).sum())

    def init_with_kmeans(self,npimg,mask):
        self._beta = self.calcBeta(npimg)
        self.calcSmoothness(npimg, self._beta, self._gamma)

        bgd = np.where(mask==self.GT_bgd)
        prob_fgd = np.where(mask==self.P_fgd)
        BGDpixels = npimg[bgd]#(_,3)
        FGDpixels = npimg[prob_fgd]#(_,3)

        KmeansBgd = Kmeans(BGDpixels, dim=3, cluster=5, epoches=2)
        KmeansFgd = Kmeans(FGDpixels, dim=3, cluster=5, epoches=2)

        bgdlabel=KmeansBgd.run() # (BGDpixel.shape[0],1)
        fgdlabel=KmeansFgd.run() # (FGDpixel.shape[0],1)

        self.BGD_GMM = GMM()  # The GMM Model for BGD
        self.FGD_GMM = GMM()  # The GMM Model for FGD


        for idx,label in enumerate(bgdlabel):
            self.BGD_GMM.add_pixel(BGDpixels[idx],label)
        for idx, label in enumerate(fgdlabel):
            self.FGD_GMM.add_pixel(FGDpixels[idx], label)

        self.BGD_GMM.learning()
        self.FGD_GMM.learning()

    def __call__(self,epoches,npimg,mask):
        self.init_with_kmeans(npimg,mask)
        for epoch in range(epoches):
            self.assign_step(npimg,mask)
            self.learn_step(npimg,mask)
            self.construct_gcgraph(npimg,mask)
            mask = self.estimate_segmentation(mask)
            img = copy.deepcopy(npimg)
            img[np.logical_or(mask == self.P_bgd, mask == self.GT_bgd)] = 0
        return Image.fromarray(img.astype(np.uint8))

    def assign_step(self,npimg,mask):
        rows,cols=npimg.shape[:2]
        clusterid=np.zeros((rows,cols))
        for row in range(rows):
            for col in range(cols):
                pixel=npimg[row,col]
                if mask[row,col]==self.GT_bgd or mask[row,col]==self.P_bgd:#bgd
                    clusterid[row,col]=self.BGD_GMM.pixel_from_cluster(pixel)
                else:
                    clusterid[row, col] = self.FGD_GMM.pixel_from_cluster(pixel)
        self.clusterid=clusterid.astype(np.int)

    def learn_step(self,npimg,mask):
        for cluster in range(self.cluster):
            bgd_cluster=np.where(np.logical_and(self.clusterid==cluster,np.logical_or(mask==self.GT_bgd,mask==self.P_bgd)))
            fgd_cluster=np.where(np.logical_and(self.clusterid==cluster,np.logical_or(mask==self.GT_fgd,mask==self.P_fgd)))
            for pixel in npimg[bgd_cluster]:
                self.BGD_GMM.add_pixel(pixel,cluster)
            for pixel in npimg[fgd_cluster]:
                self.FGD_GMM.add_pixel(pixel,cluster)
        self.BGD_GMM.learning()
        self.FGD_GMM.learning()


    def construct_gcgraph(self,npimg,mask):
        rows,cols=npimg.shape[:2]
        vertex_count = rows*cols
        edge_count = 2 * (4 * vertex_count - 3 * (rows + cols) + 2)
        self.graph = GCGraph(vertex_count, edge_count)
        for row in range(rows):
            for col in range(cols):
                #source background sink foreground
                vertex_index = self.graph.add_vertex()
                color = npimg[row, col]
                if mask[row, col] == self.P_bgd or mask[row, col] == self.P_fgd:#pred fgd
                    fromSource = -log(self.BGD_GMM.pred_GMM(color))
                    toSink = -log(self.FGD_GMM.pred_GMM(color))
                elif mask[row, col] == self.GT_bgd:
                    fromSource = 0
                    toSink = self._lambda
                else:
                    fromSource = self._lambda
                    toSink = 0
                self.graph.add_term_weights(vertex_index, fromSource, toSink)

                if col-1 >= 0:
                    w = self.lweight[row, col]
                    self.graph.add_edges(vertex_index, vertex_index - 1, w, w)
                if row-1 >= 0 and col-1 >= 0:
                    w = self.ulweight[row, col]
                    self.graph.add_edges(vertex_index, vertex_index - cols - 1, w, w)
                if row-1 >= 0:
                    w = self.uweight[row, col]
                    self.graph.add_edges(vertex_index, vertex_index - cols, w, w)
                if col+1 < cols and row-1 >= 0:
                    w = self.urweight[row, col]
                    self.graph.add_edges(vertex_index, vertex_index - cols + 1, w, w)

    def estimate_segmentation(self,mask):
        rows,cols=mask.shape
        self.graph.max_flow()
        for row in range(rows):
            for col in range(cols):
                if mask[row, col] == self.P_fgd or mask[row,col]==self.P_bgd :
                    if self.graph.insource_segment(row * cols + col):  # Vertex Index
                        mask[row, col] = self.P_fgd
                    else:
                        mask[row, col] = self.P_bgd

        return mask

if __name__=="__main__":
    img=np.array(Image.open("/home/guyuchao/workplace/Grabcut/files/testlena.jpg")).astype(np.float32)
    gg=grabcut()
    mask = np.zeros(img.shape[:2])
    left = 34
    right = 315
    top = 66
    bottom = 374
    mask[left:right, top:bottom] = gg.P_fgd
    gg(epoches=1,npimg=img,mask=mask)