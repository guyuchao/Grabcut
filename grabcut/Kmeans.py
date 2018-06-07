import random
import numpy as np
from matplotlib import pyplot as plt
class Kmeans(object):
    def __init__(self,images,dim=3,cluster=5,epoches=2):
        self.images=images.reshape(-1,dim)
        self.pixelnum=self.images.shape[0]
        self.cluster=cluster
        self.belong=np.zeros(self.pixelnum)
        self.cluster_centers=self.images[random.sample(range(self.pixelnum),self.cluster)]
        self.epoches=epoches

    def run(self):
        for i in range(self.epoches):
            self.updates_belonging()
            self.updates_centers()
        return self.belong

    def updates_belonging(self):
        newbelong=np.zeros(self.pixelnum)
        for num in range(self.pixelnum):
            cost=[np.square(self.images[num]-self.cluster_centers[i]).sum() for i in range(self.cluster)]
            newbelong[num]=np.argmin(cost)
        self.belong=newbelong

    def updates_centers(self):
        num_clusters=np.zeros(self.cluster)
        for cluster_idx in range(self.cluster):
            belong_to_cluster=np.where(self.belong==cluster_idx)[0]

            num_cluster=len(belong_to_cluster)
            num_clusters[cluster_idx]=num_cluster

        for cluster_idx in range(self.cluster):
            if num_clusters[cluster_idx]==0:
                #find max
                max_cluster=np.argmax(num_clusters)
                belong_to_cluster=np.where(self.belong==max_cluster)[0]
                pixels=self.images[belong_to_cluster]
                cost=[np.square(self.images[id]-self.cluster_centers[max_cluster]).sum() for id in range(self.pixelnum)]
                far_pixel_idx=np.argmax(cost)
                self.belong[far_pixel_idx]=cluster_idx
                self.cluster_centers[cluster_idx]=self.images[cluster_idx]
            else:
                idx=np.where(self.belong==cluster_idx)[0]
                self.cluster_centers[cluster_idx]=self.images[idx].sum(0)/len(idx)
    def plot(self):
        data_x = []
        data_y = []
        data_z = []
        for i in range(self.cluster):
            index = np.where(self.belong == i)
            data_x.extend(self.images[index][:, 0].tolist())
            data_y.extend(self.images[index][:, 1].tolist())
            data_z.extend([i / self.cluster for j in range(len(list(index)[0]))])
        sc = plt.scatter(data_x, data_y, c=data_z, vmin=0, vmax=1, s=35, alpha=0.8)
        plt.colorbar(sc)
        plt.show()


'''
if __name__=='__main__':
    A=np.random.random((1000,20,2))
    kmeans=Kmeans(A,2,20,10)
    kmeans()
    kmeans.plot()
'''