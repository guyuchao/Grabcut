import numpy as np
import copy

class GMM(object):
    def __init__(self,cluster=5):
        self.cluster=cluster
        self.weight=np.zeros(cluster)#pai x in the paper
        self.means=np.zeros((cluster,3))
        self.covs=np.zeros((cluster,3,3))
        self.inverse_cov = np.zeros((cluster, 3, 3))
        self.delta_cov=np.zeros(cluster)

        self.sums_for_mean=np.zeros((cluster,3))
        self.product_for_cov=np.zeros((cluster,3,3))
        self.pixel_counts=np.zeros(cluster)
        self.pixel_total_count=0

    def init(self):
        self.sums_for_mean = np.zeros((self.cluster, 3))
        self.product_for_cov = np.zeros((self.cluster, 3, 3))
        self.pixel_counts = np.zeros(self.cluster)
        self.pixel_total_count = 0

    def add_pixel(self, pixel, cluster):
        pixel_c=copy.deepcopy(pixel)
        cluster=int(cluster)
        self.sums_for_mean[cluster] += pixel_c
        pixel_c=pixel_c[np.newaxis,:]
        self.product_for_cov[cluster] += np.dot(np.transpose(pixel_c),pixel_c)
        self.pixel_counts[cluster] += 1
        self.pixel_total_count += 1

    def learning(self):
        variance = 0.01
        for cluster in range(self.cluster):
            n=self.pixel_counts[cluster]
            if n!=0:
                self.weight[cluster]=n/self.pixel_total_count
                self.means[cluster]=self.sums_for_mean[cluster]/n
                tmp_mean=copy.deepcopy(self.means[cluster])
                tmp_mean=tmp_mean[np.newaxis,:]
                productmean=np.dot(np.transpose(tmp_mean),tmp_mean)
                self.covs[cluster]=self.product_for_cov[cluster]/n-productmean
                self.delta_cov[cluster]=np.linalg.det(self.covs[cluster])
            while self.delta_cov[cluster]<=0:
                self.covs[cluster]+=np.eye(3,3)*variance
                self.delta_cov[cluster]=np.linalg.det(self.covs[cluster])
            self.inverse_cov[cluster]=np.linalg.inv(self.covs[cluster])
                #print(np.dot(self.covs[cluster],self.inverse_cov[cluster]))
        self.init()
    def pred_cluster(self,cluster,pixel):

        if self.weight[cluster]>0:
            diff=copy.deepcopy(pixel)-self.means[cluster]
            mult=((np.transpose(self.inverse_cov[cluster])*diff).sum(1)*diff).sum()
            res = 1.0 / np.sqrt(self.delta_cov[cluster]) * np.exp(-0.5* mult)
            return res
        else:
            return 0

    def pixel_from_cluster(self,pixel):
        p=np.array([self.pred_cluster(cluster,pixel) for cluster in range(self.cluster)])
        return p.argmax()

    def pred_GMM(self,pixel):
        res=np.array([self.weight[cluster]*self.pred_cluster(cluster,pixel) for cluster in range(self.cluster)])
        assert res.sum()>0,"error"
        return res.sum()





