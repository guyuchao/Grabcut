from PIL import Image
import numpy as np
import copy
from io import BytesIO
import base64
import cv2

class Basicprocess:

    def rgba2rgb(self,rgbaimg):
        return cv2.cvtColor(rgbaimg, cv2.COLOR_RGBA2RGB)

    def base64_to_rgb(self,base64img):
        imgdata = base64.b64decode(base64img)
        buffered = BytesIO()
        buffered.write(imgdata)
        rgbimg = self.rgba2rgb(np.array(Image.open(buffered)))
        return Image.fromarray(rgbimg)

    def img2base64(self,img):
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return img_str

    def change_saturation_quick(self,path,radio):
        img = Image.open(path).convert('RGB')
        npimg = np.array(img)
        newimg=self._rgb2hsl_numpy(npimg)
        newimg[:,:,1]=newimg[:,:,1]+(radio-1)
        mask1=newimg[:,:,1]>1
        mask2 = newimg[:, :, 1] <0
        newimg[:,:,1][mask1]=1
        newimg[:, :, 1][mask2] =0
        ret_img=self._hsl2rgb2_numpy(newimg)
        return Image.fromarray(ret_img.astype(np.uint8))

    def change_hue_quick(self,path,radio):
        img = Image.open(path).convert('RGB')
        npimg = np.array(img)
        newimg=self._rgb2hsl_numpy(npimg)
        newimg[:,:,0]=newimg[:,:,0]+(radio-1)
        mask1=newimg[:,:,0]>1
        mask2 = newimg[:, :, 0] <0
        newimg[:,:,0][mask1]=np.modf(newimg[:,:,0][mask1])[0]
        newimg[:, :, 0][mask2] =np.modf(newimg[:,:,0][mask2])[0]+np.ones(newimg[:,:,0][mask2].shape)
        ret_img=self._hsl2rgb2_numpy(newimg)
        return Image.fromarray(ret_img.astype(np.uint8))


    def change_value_quick(self,path,radio):
        img = Image.open(path).convert('RGB')
        npimg = np.array(img)
        newimg=self._rgb2hsl_numpy(npimg)
        newimg[:,:,2]=newimg[:,:,2]+(radio-1)
        mask1=newimg[:,:,2]>1
        mask2 = newimg[:, :, 2] <0
        newimg[:,:,2][mask1]=1
        newimg[:, :, 2][mask2] =0
        ret_img=self._hsl2rgb2_numpy(newimg)
        return Image.fromarray(ret_img.astype(np.uint8))

    def change_value(self,path,radio):
        img = Image.open(path).convert('RGB')
        npimg = np.array(img)
        newimg = np.zeros(npimg.shape)
        h, w, _ = npimg.shape
        for i in range(h):
            for j in range(w):
                r, g, b = npimg[i][j]
                newimg[i][j] =self._rgb2hsl(r, g, b)
                newimg[i][j][2] += (float(radio)-1)
                if newimg[i][j][2] > 1:
                    newimg[i][j][2] = 1
                if newimg[i][j][2] <0:
                    newimg[i][j][2] = 0
        for i in range(h):
            for j in range(w):
                h, s, l = newimg[i][j]
                newimg[i][j] = self._hsl2rgb(h, s, l)
        return Image.fromarray(newimg.astype(np.uint8))

    def _rgb2hsl(self,r,g,b):
        var_R = r/255.0
        var_G = g/255.0
        var_B = b/255.0
        var_Min = min( var_R, var_G, var_B )
        var_Max = max( var_R, var_G, var_B )
        del_Max = var_Max - var_Min

        l = ( var_Max + var_Min ) / 2.0
        h = 0.0
        s = 0.0
        if del_Max!=0.0:
           if l<0.5: s = del_Max / ( var_Max + var_Min )
           else:     s = del_Max / ( 2.0 - var_Max - var_Min )
           del_R = ( ( ( var_Max - var_R ) / 6.0 ) + ( del_Max / 2.0 ) ) / del_Max
           del_G = ( ( ( var_Max - var_G ) / 6.0 ) + ( del_Max / 2.0 ) ) / del_Max
           del_B = ( ( ( var_Max - var_B ) / 6.0 ) + ( del_Max / 2.0 ) ) / del_Max
           if    var_R == var_Max : h = del_B - del_G
           elif  var_G == var_Max : h = ( 1.0 / 3.0 ) + del_R - del_B
           elif  var_B == var_Max : h = ( 2.0 / 3.0 ) + del_G - del_R
           while h < 0.0: h += 1.0
           while h > 1.0: h -= 1.0

        return (h,s,l)

    def _hsl2rgb(self,h, s, l):
        def Hue_2_RGB(v1, v2, vH):
            while vH < 0.0: vH += 1.0
            while vH > 1.0: vH -= 1.0
            if 6 * vH < 1.0: return v1 + (v2 - v1) * 6.0 * vH
            if 2 * vH < 1.0: return v2
            if 3 * vH < 2.0: return v1 + (v2 - v1) * ((2.0 / 3.0) - vH) * 6.0
            return v1

        R=G=B = (l * 255)
        if s != 0.0:
            if l < 0.5:
                var_2 = l * (1.0 + s)
            else:
                var_2 = (l + s) - (s * l)
            var_1 = 2.0 * l - var_2
            R = 255 * Hue_2_RGB(var_1, var_2, h + (1.0 / 3.0))
            G = 255 * Hue_2_RGB(var_1, var_2, h)
            B = 255 * Hue_2_RGB(var_1, var_2, h - (1.0 / 3.0))
        return (int(round(R)), int(round(G)), int(round(B)))

    def _rgb2hsl_numpy(self,img):
        img = img / 255.0
        var_min = img.min(2)
        var_max = img.max(2)
        del_max = var_max - var_min
        l = (var_max + var_min) / 2.0
        h = np.zeros(l.shape)
        s = np.zeros(l.shape)
        mask_delmax = (del_max > 0)
        mask_l = (l < 0.5)
        s[mask_delmax & mask_l] = (del_max[mask_delmax & mask_l] / (var_max + var_min)[mask_delmax & mask_l])
        s[mask_delmax & (~mask_l)] = (del_max[mask_delmax & (~mask_l)] / (2.0 - var_max - var_min)[mask_delmax & (~mask_l)])
        var_max = np.repeat(var_max[:, :, np.newaxis], 3, axis=2)
        del_max = np.repeat(del_max[:, :, np.newaxis], 3, axis=2)
        del_rgb=np.zeros(del_max.shape)
        del_rgb[mask_delmax] = (((var_max - img) / 6.0) + (del_max / 2.0))[mask_delmax] / del_max[mask_delmax]
        mask1 = (img[:, :, 0] == var_max[:, :, 0])
        mask2 = (~mask1) & (img[:, :, 1] == var_max[:, :, 0])
        mask3 = (~mask1) & (~mask2) & (img[:, :, 2] == var_max[:, :, 0])
        h[mask1&mask_delmax] = (del_rgb[:, :, 2] - del_rgb[:, :, 1])[mask1&mask_delmax]
        h[mask2&mask_delmax] = ((1.0 / 3.0) + del_rgb[:, :, 0] - del_rgb[:, :, 2])[mask2&mask_delmax]
        h[mask3&mask_delmax] = ((2.0 / 3.0) + del_rgb[:, :, 1] - del_rgb[:, :, 0])[mask3&mask_delmax]
        h[np.where(h < 0.0)] = np.modf(h)[0][np.where(h < 0.0)] + 1
        h[np.where(h > 1.0)] = np.modf(h)[0][np.where(h > 1.0)]
        return np.dstack((h, s, l))

    def _hsl2rgb2_numpy(self,img_hsl):
        def Hue_2_RGB(v1, v2, vh):
            mask_vh0 = [vh < 0.0]
            mask_vh1 = [vh > 1.0]
            vh[mask_vh0] = np.modf(vh)[0][mask_vh0] + 1
            vh[mask_vh1] = np.modf(vh)[0][mask_vh1]
            ret = copy.deepcopy(v1)
            mask1 = 6 * vh < 1.0
            mask2 = (2 * vh < 1.0) & (~mask1)
            mask3 = (3 * vh < 2.0) & (~mask1) & (~mask2)
            ret[mask1] = (v1 + (v2 - v1) * 6.0 * vh)[mask1]
            ret[mask2] = v2[mask2]
            ret[mask3] = (v1 + (v2 - v1) * ((2.0 / 3.0) - vh) * 6.0)[mask3]
            return ret
        R = (img_hsl[:, :, 2] * 255)
        G = (img_hsl[:, :, 2] * 255)
        B = (img_hsl[:, :, 2] * 255)
        mask_s = (img_hsl[:, :, 1] != 0.0)
        mask_l = (img_hsl[:, :, 2] < 0.5)
        var2 = np.zeros(R.shape)
        var2[mask_s & mask_l] = (img_hsl[:, :, 2] * (1.0 + img_hsl[:, :, 1]))[mask_s & mask_l]
        var2[mask_s & (~mask_l)] = ((img_hsl[:, :, 2] + img_hsl[:, :, 1]) - (img_hsl[:, :, 2] * img_hsl[:, :, 1]))[mask_s & (~mask_l)]
        var1 = 2.0 * (img_hsl[:, :, 2]) - var2
        R[mask_s] = (255 * Hue_2_RGB(var1, var2, img_hsl[:, :, 0] + (1.0 / 3.0)))[mask_s]
        G[mask_s] = (255 * Hue_2_RGB(var1, var2, img_hsl[:, :, 0]))[mask_s]
        B[mask_s] = (255 * Hue_2_RGB(var1, var2, img_hsl[:, :, 0] - (1.0 / 3.0)))[mask_s]
        return np.dstack((R, G, B)).astype(np.uint8)

    def change_contrast(self,path,delta):
        img = Image.open(path)
        npimg = np.array(img)
        if len(npimg.shape)==2:
            return self._grey_contrast(npimg,delta)
        else:
            return self._rgb_contrast(npimg,delta)

    def _grey_contrast(self,npimg,delta):
        mean=np.array([npimg[:,:].mean()])
        ret_img=npimg.astype(np.float32)-mean
        ret_img*=delta
        ret_img+=mean
        ret_img[ret_img > 255] = 255
        ret_img[ret_img < 0] = 0
        return Image.fromarray(ret_img.astype(np.uint8))

    def _rgb_contrast(self,npimg,delta):
        mean=np.array([npimg[:,:,0].mean(),npimg[:,:,1].mean(),npimg[:,:,2].mean()])
        ret_img=npimg.astype(np.float32)-mean
        ret_img*=delta
        ret_img+=mean
        ret_img[ret_img>255]=255
        ret_img[ret_img<0]=0
        return Image.fromarray(ret_img.astype(np.uint8))

    def merge(self,img1,img2,alpha):
        assert alpha>=0 and alpha<=1,"alpha should be （0,1)"
        img1=np.array(img1)
        img2=np.array(img2)
        ret_img=img1*(1-alpha)+img2*alpha
        return Image.fromarray(ret_img.astype(np.uint8))