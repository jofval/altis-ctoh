#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# 
# Detection de parabole.
#
# Created by Denis Blumstien and Lea Lasson (Volodia Project)
# Modified by Fabien Blarel on 2019-04-19. 
# CeCILL Licence 2019 CTOH-LEGOS.
# ----------------------------------------------------------------------
import math
import numpy as np
import matplotlib.pyplot as plt

from math import asin, cos, pi, sin, tan


def hough_transform_linear(x,y,visu=False):
    db = 0.1
    a0 = -5
    a1 = 5
    b0 = np.nanmin(y)-a1*np.nanmax(x)
    b1 = np.nanmax(y)-a0*np.nanmax(x)
    da = 0.1
    na = int(round((a1-a0)/da))
    nb = int(round((b1-b0)/db))
    A = np.zeros((na,nb))
    nb_ind = []
    a_x = np.zeros((len(x),na))
    b_x = np.zeros((len(x),nb))
    if visu:
        fig1_2 = plt.figure(1)
        plt.plot(x,y)
        plt.show()
        plt.close(fig1_2)
        fig2_2 = plt.figure(2)
    for i, xi in enumerate(x):
        a_tab = []
        b_tab = []
        for k in range(na):
            if math.isnan(y[i]):
                continue
            a = a0 + k*da
            b = y[i]-a*xi
            a_tab.append(a)
            b_tab.append(b)
            m = int(round((b-b0)/db))
            if m < 0 or m > nb or k < 0 or k > na:
                print("ERROR",a0,a,b,xi,y[i],da,m,k)
                continue
            A[k][m-1] = A[k][m-1]+1
            nb_ind.append([k,m-1,i])
            a_x[i][k] = a
            b_x[i][m-1] = b
        if visu:
            plt.plot(a_tab,b_tab)
    if visu:
        plt.show()
        plt.close(fig2_2)
    ind = np.where(A==np.nanmax(A))
    nb_ind = np.asarray(nb_ind)
    a_tab = []
    b_tab = []
    while A[ind][0]>=5:
        ind_x = np.where((nb_ind[:,0]==ind[0][0]) & (nb_ind[:,1]==ind[1][0]))
        if np.abs(np.nanmean(a_x[nb_ind[ind_x,2],ind[0][0]]))>0.015:
            A[ind] = 0        
            ind = np.where(A == np.nanmax(A))
            continue
        if len(a_tab) == 0:
            a_tab.append(np.nanmean(a_x[nb_ind[ind_x,2],ind[0][0]]))
            b_tab.append(np.nanmean(b_x[nb_ind[ind_x,2],ind[1][0]]))
        n=0
        for j in range(len(a_tab)):
            diff_a = np.abs(np.nanmean(a_x[nb_ind[ind_x,2],ind[0][0]])-a_tab[j])
            diff_b = np.abs(np.nanmean(b_x[nb_ind[ind_x,2],ind[1][0]])-b_tab[j])
            if diff_a<=3*da and diff_b<=10*db:
                n+=1
        if n==0:
            a_tab.append(np.nanmean(a_x[nb_ind[ind_x,2],ind[0][0]]))
            b_tab.append(np.nanmean(b_x[nb_ind[ind_x,2],ind[1][0]]))
        A[ind] = 0        
        ind = np.where(A == np.nanmax(A))
    # To separate one plateau in many plateau and take out height and position
    x_out = []
    y_out = []
    x_tab = []
    y_tab = []
    n = 0
    if b_tab is not None:
        for j in range(len(b_tab)):
            y_simu = (a_tab[j]*x)+b_tab[j]
            resi_simu_real = np.abs(y_simu-y)
            ind_filter = np.where(resi_simu_real < 0.1)[0]
            diff_ind = np.diff(ind_filter)
            sep = np.where(diff_ind>2)[0]
            start = 0
            for k in range(len(sep)+1):
                if k == len(sep):
                    x_filter = x[ind_filter[start:]]
                    if len(x_filter) <= 6:
                        continue
                    n += 1
                else:
                    x_filter = x[ind_filter[start:sep[k]]]
                    if len(x_filter) <= 6:
                        start = sep[k]+1
                        continue
                    start = sep[k]+1
                    n += 1
                position = x_filter[int(len(x_filter)/2)]
                x_tab.append(x_filter)
                x_out.append(position)
                y_tab.append(a_tab[j]*x_filter+b_tab[j])
                y_out.append(a_tab[j]*position+b_tab[j])
    if visu:
        if n != 0:
            fig3_2 = plt.figure(3)
            for i in range(len(b_tab)):
                new_y = (a_tab[i]*x)+b_tab[i]
                plt.plot(x, new_y,label="simu_linear")
            plt.plot(x,y,label="real")
            plt.legend()
            plt.show()
            plt.cla()
            plt.clf()
            plt.close(fig3_2)
    if n == 0:
        x_out = None
        y_out = None
    return x_tab,y_tab,x_out,y_out,n


def hough_transform(lat_SV, x, y, visu=False):
    R = 6371000
    norbit = 127
    q = 9.9156
    dt = 0.05
    H = 1335000    
    w = (2*pi*norbit)/(q*86400)
    #c = ((R*(R+H))/(2*H))*((w*dt)**2)
    rad = pi/180
    wt = 2*pi/86164.09
    i = 66*rad # Jason
    phi0 = lat_SV*rad
    v0 = asin(round(sin(phi0)/sin(i),2))
    al = R*wt*cos(i)
    if np.abs(v0) == 0:
        be = -R*wt*(sin(i)*cos(v0))
    else:
        be = -R*wt*(sin(phi0)/tan(v0))
    c = (w*(R+H)*(R*w-2*al)+be**2)*(dt**2)/(2*H)
    db = 0.4
    b0 = x[0]
    b1 = x[-1]
    a0 = np.nanmax(y) + c*((np.nanmax(x)-b0)**2)
    a1 = np.nanmin(y)
    da = 0.4
    na = int(round((a0-a1)/da))
    nb = int(round((b1-b0)/db))
    A = np.zeros((na,nb))
    a_x = np.zeros((len(x),na))
    b_x = np.zeros((len(x),nb))
    nb_ind = []
    if visu:
        fig1_3 = plt.figure(1)
        plt.plot(x,y)
        plt.show()
        plt.close(fig1_3)
        fig2_3 = plt.figure(2)
    for i, xi in enumerate(x):
        a_tab = []
        b_tab = []
        for k in range(nb):
            if math.isnan(y[i]):
                continue
            b = b0 + k*db
            a = y[i]+(c*((xi-b)**2))
            a_tab.append(a)
            b_tab.append(b)
            m = int(round((a0-a)/da))
            if m < 0 or m > na or k < 0 or k > nb:
                print("ERROR",a0,a,b,xi,y[i],da,m,k)
                continue
            A[m-1][k] = A[m-1][k]+1
            nb_ind.append([m-1,k,i])
            a_x[i][m-1] = a
            b_x[i][k] = b
        if visu:
            plt.plot(b_tab,a_tab)
    if visu:
        plt.show()
        plt.close(fig2_3)
    nb_ind = np.asarray(nb_ind)      
    ind = np.where(A == np.nanmax(A))
    a_tab = []
    b_tab = []
    error_a = []
    error_b = []
    while A[ind][0]>9:
        b_tot = np.zeros((len(ind[0])))
        for i in range(len(ind[0])):
            ind_x_b = np.where((nb_ind[:,0]==ind[0][i]) & (nb_ind[:,1]==ind[1][i]))[0]
            b_tot[i] = b_x[nb_ind[ind_x_b,2],ind[1][i]][0]
        ind_x = np.where((nb_ind[:,0]==ind[0][0]) & (nb_ind[:,1]==ind[1][0]))
        if len(a_tab) == 0:
            a_min = np.nanmin(a_x[nb_ind[ind_x,2],ind[0][0]])
            a_max = np.nanmax(a_x[nb_ind[ind_x,2],ind[0][0]])
            error_a.append((a_max-a_min)/2)
            a_tab.append(np.nanmean(a_x[nb_ind[ind_x,2],ind[0][0]]))
            error_b.append((np.nanmax(b_tot)-np.nanmin(b_tot))/2)
            b_tab.append(np.nanmean(b_x[nb_ind[ind_x,2],ind[1][0]]))
        n=0
        for j in range(len(a_tab)):
            diff_a = np.abs(np.nanmean(a_x[nb_ind[ind_x,2],ind[0][0]])-a_tab[j])
            diff_b = np.abs(np.nanmean(b_x[nb_ind[ind_x,2],ind[1][0]])-b_tab[j])
            if diff_a<=3*da and diff_b<=6*db:
                n+=1
        if n==0:
            a_min = np.nanmin(a_x[nb_ind[ind_x,2],ind[0][0]])
            a_max = np.nanmax(a_x[nb_ind[ind_x,2],ind[0][0]])
            error_a.append((a_max-a_min)/2)
            a_tab.append(np.nanmean(a_x[nb_ind[ind_x,2],ind[0][0]]))
            error_b.append((np.nanmax(b_tot)-np.nanmin(b_tot))/2)            
            b_tab.append(np.nanmean(b_x[nb_ind[ind_x,2],ind[1][0]]))
        A[ind] = 0        
        ind = np.where(A == np.nanmax(A))
    x_tab = []
    y_tab = []
    n = 0
    if b_tab is not None:
        for j in range(len(b_tab)):
            n += 1
            y_simu = a_tab[j]-c*((x-b_tab[j])**2)
            resi_simu_real = np.abs(y_simu-y)
            ind_filter = np.where(resi_simu_real < 1)[0]
            x_tab.append(x[ind_filter[0]:ind_filter[-1]+1])
            y_tab.append(a_tab[j]-c*((x[ind_filter[0]:ind_filter[-1]+1]-b_tab[j])**2))
    if visu:
        if n != 0:
            fig3_3 = plt.figure(3)
            for i in range(len(b_tab)):
                new_x = np.arange(20,len(x)-20,1)
                new_y = np.nanmedian(a_tab[i])-c*((new_x-np.nanmedian(b_tab[i]))**2)
                plt.plot(new_x, new_y,label="simu_parabola (%d)" % (i+1))
            plt.plot(x,y,label="real")
            plt.legend()
            plt.show()
            plt.cla()
            plt.clf()
            plt.close(fig3_3)
    if n == 0:
        a_tab = None
        b_tab = None
    return x_tab,y_tab,a_tab,error_a,b_tab,error_b,c,n


def hground(d, r):
    """compute ground altitude (ref. geoid) from a given range r"""
    return d.alt - r - d.geoid + 2.4  # 2.4 m for dry tropo correction


def main():
    visu = True
    x = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
            18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34,
            35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51,
            52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68,
            69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85,
            86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100])
    y = np.array([181.8447, 181.9091, 181.9542, 181.8826, 181.8971, 181.8807, 
        181.9445, 181.9855, 182.0469, 181.969,  181.9951, 181.8847, 181.9479, 
        178.7202, 136.1015, 138.1016, 140.4232, 141.6456, 143.8624, 144.8685,
        146.4392, 147.0879, 149.3703, 151.1717, 152.0805, 153.2915, 154.3161,
        156.0059, 156.9263, 158.1806, 158.9926, 159.5252, 160.6081, 161.2385,
        161.7322, 162.3465, 162.7605, 163.2634, 163.5654, 163.9446, 164.0243,
        164.5354, 165.0332, 165.0102, 164.5531, 164.4815, 164.3306, 164.1507,
        164.0904, 164.0584, 164.0658, 163.9057, 163.6897, 163.5293, 163.1436,
        162.7552, 162.3155, 161.684,  160.8113, 160.4246, 159.7098, 158.7065,
        157.1859, 156.3101, 155.6867, 153.9687, 153.4126, 151.7959, 149.8268,
        149.2152, 147.9687, 146.0554, 143.9109, 142.1819, 140.8224, 138.7804,
        137.8628, 177.7487, 181.4556, 180.843,  158.3168, 175.8394, 162.6407,
        166.6676, 168.09,   171.7052, 173.8631, 176.9083, 178.6245, 182.2792,
        182.4624, 182.5788, 182.6061, 182.6644, 182.618,  182.5865, 182.6366,
        185.0247, 199.8031, 200.8749, 204.2243])

    lat_SV = 32.7979
    if visu:
        x_tab,y_tab,a,err_a,b,err_b,cu,nb = hough_transform(lat_SV, x, y,True)
        x_tab_line,y_tab_line,h,nwf,nb_line = hough_transform_linear(x,y,True)
    else:
        x_tab,y_tab,a,err_a,b,err_b,cu,nb = hough_transform(lat_SV, x, y)
        x_tab_line,y_tab_line,h,nwf,nb_line = hough_transform_linear(x,y)
    if a is not None:
        for i in range(len(a)):
            if i != 0:
                print("%25s" % (""),end="")
            print("%15s %8.2f %8.2f" % ("parabola",a[i],b[i]))
    if h is not None:
        for i in range(len(h)):
            if i != 0 or nb != 0:
                print("%25s" % (""),end="")
            print("%15s %8.2f %8.2f" % ("plateau",h[i],nwf[i]))
    if a is None and h is None:
        print("%15s" % ("no_object"))


if __name__ == "__main__":
    main()
