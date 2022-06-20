# -*- coding: utf-8 -*-
"""
Created on Fri Jun 17 21:23:19 2022

@author: Jan de Vreugd
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.special import gamma, factorial
import matplotlib.tri as mtri
from scipy.interpolate import griddata
from matplotlib import cm
import streamlit as st
import plotly.graph_objects as go
from matplotlib.ticker import LinearLocator
from scipy.optimize import curve_fit
import os
from scipy.interpolate import interp1d



def readme():
    with st.expander('read me'):
        st.write("""
    With this streamlit web-app a Zernike decomposation can be made of sag-data of circular shaped optics. \n
    A data set can be uploaded which contains the x- and y-coordinates and the dz values (sag data). \n
    The data-file should be in .xlsx or .txt format. \n
    
        """)
        link='The Zernike decomposition is done according to the formulation as described here: [link](https://en.wikipedia.org/wiki/Zernike_polynomials)'
        st.markdown(link,unsafe_allow_html=True)
        
        st.write('''the web-app enables to substract an aspheric curvature from the uploaded data-set. 
                 The aphseric curvature is defined according to the following equation:''')
        
        st.latex(r'''
                 Z(r) = \frac{Cr^2}{1+\sqrt{1-(1+k)\cdot C^2r^2}}
                 ''')
        st.write(''' where, $C$ is the curvature (inverse radius, $1/R_c$) and $k$ the conical constant. ''')  
        
def dataread(uploaded_file):
        filename,file_extension = os.path.splitext(uploaded_file.name)
        if file_extension == '.xlsx':
            df = pd.read_excel(uploaded_file)
        if file_extension ==  '.txt':
            df = pd.read_csv(uploaded_file, sep = '\s+', header = None)
        shapeFile = df.shape    
        return df, shapeFile

def dataselection(data, shapeFile):
    with st.container():    
        col1,col2,col3 = st.columns(3)
        with col1:
            values = list(range(1,shapeFile[1]+1))
            if shapeFile[1] == 7:
                v = 2
            elif shapeFile[1] == 6:
                v = 2
            elif shapeFile[1] == 4:
                v = 2
            elif shapeFile[1] == 3:
                v = 1   
            else:
                v = 1
            default_ix = values.index(v)
            columnx = st.selectbox('x-column:',values,index = default_ix)
            
        with col2:
            values = list(range(1,shapeFile[1]+1))
            if shapeFile[1] == 7:
                v = 3
            elif shapeFile[1] == 6:
                v = 3
            elif shapeFile[1] == 4:
                v = 3
            elif shapeFile[1] == 3:
                v = 2
            else:
                v = 2
                
            default_iy = values.index(v)
            columny = st.selectbox('y-column:',values,index = default_iy)

        with col3:
            values = list(range(1,shapeFile[1]+1))
            if shapeFile[1] == 7:
                v = 7
            elif shapeFile[1] == 6:
                v = 4
            elif shapeFile[1] == 4:
                v = 4
            elif shapeFile[1] == 3:
                v = 3
            else: 
                v = 3
                
            default_iz = values.index(v)
            columnz = st.selectbox('z-column:',values,index = default_iz) 
            
            x = data.iloc[:,columnx-1].to_numpy()
            x = x.reshape((len(x)))
            x = x - np.mean(x)        
            y = data.iloc[:,columny-1].to_numpy()
            y = y.reshape((len(y)))
            y = y - np.mean(x)
            dz = data.iloc[:,columnz-1].to_numpy()
            dz = dz.reshape((len(dz)))
            
            R = np.sqrt(x**2 + y**2)
            phi = np.arctan2(x,y)
            rho = R/np.max(R)
            
            return x, y, dz, R, phi, rho 
        
def SFE_calc(dz,UnitFactor):
    SFE  = np.round(np.std(dz)  * UnitFactor,2)
    return SFE

def PV_calc(dz,UnitFactor):
    PV  = np.round( (np.max(dz)-np.min(dz)) * UnitFactor, 2)
    return PV    

def plotlyfunc(x,y,xi,yi,dz,UnitFactor,title):
    
    W = 600
    H = 600
    
    dz_grid = griddata((x,y),dz,(xi,yi),method='cubic')
    
    SFE = str(SFE_calc(dz, UnitFactor))
    PV = str(PV_calc(dz, UnitFactor))
    fig = go.Figure(go.Surface(x=xi,y=yi,z=dz_grid,colorscale='jet'))
    fig.update_layout(title=title + '<br>' + 
                      'PV = ' + PV + 'nm' + '<br>' + 
                      'SFE = ' + SFE + 'nm', autosize=False,width = W, height = H, title_x = 0.5)
    st.plotly_chart(fig, use_container_width=True)
   
def TipTilt(x,y,dz):
    A = np.ones((len(x),3))
    A[:,1] = A[:,1] * x 
    A[:,2] = A[:,2] * y 
    
    Xlinear = np.linalg.lstsq(A,dz,rcond=None)[0] 
    Fit = np.sum(Xlinear*A,axis = 1)
    ddz = dz - Fit
    return ddz

def gridarrays(x,y):
    X = np.linspace(min(x),max(x),100)
    Y = np.linspace(min(y),max(y),100)
    xi,yi = np.meshgrid(X,Y) # Needs to be checked!!
    return xi,yi
    
def funcSphere(R, Rc, offset):
    C = 1/Rc
    return C*R**2/(1+np.sqrt(1-C**2*R**2)) + offset


def funcASphere(R,Rc,k,offset):
    asphereZ = R**2 / ( Rc * ( 1 + np.sqrt( 1 - (1+k) * (R/Rc)**2  ) ) ) + offset
    return asphereZ

def sagsign(R,dz):
    Ri = np.linspace(np.min(R),np.max(R),100)
    f = interp1d(R, dz)
    dzi = f(Ri)
    ddz = np.diff(dzi)/np.diff(Ri)
    sign = np.sign(sum(ddz))
    return sign

def ZernikeTerms():
    mm = list(range(2,16))
    NN = []
    for i in range(len(mm)-1):
        NN.append(sum(range(mm[i+1])))   
    return NN, mm

def ZernikeDecomposition(rho,phi,m_max,dz,UnitFactor):
    A = [[0,0]]

    for i in range(1,m_max):
        for j in range(-i,i+1,2):
            A.append([j,i])
    mnlist = ['Z[' + str(A[0][0]) + ']' +'[' + str(A[0][1]) + ']']        
    for i in range(1,len(A)):
        mnlist.append('Z[' + str(A[i][0]) + ']' +'[' + str(A[i][1]) + ']')
    
    ZernikeInfluenceFunctions = np.zeros([len(rho),len(A)])
    for i in range(len(A)):
        
        m = A[i][0]
        n = A[i][1]
        k_inf = int(((n-abs(m))/2))
    
        Zs = np.zeros([len(rho),k_inf+1])
        
        if abs(m)-n == 0:
            #print('boe')
            k = 0
            F1 = np.math.factorial(n-k)
            F2 = np.math.factorial(k)
            F3 = np.math.factorial(int((n+abs(m))/2) - k )
            F4 = np.math.factorial(int((n-abs(m))/2) - k )
            Zs = (-1)**k*F1/(F2*F3*F4)*rho**(n-2*k)
        else:
            
            for k in range(int((n-abs(m))/2)+1):
                F1 = np.math.factorial(n-k)
                F2 = np.math.factorial(k)
                F3 = np.math.factorial(int((n+abs(m))/2) - k )
                F4 = np.math.factorial(int((n-abs(m))/2) - k )
                Ri = (-1)**k*F1/(F2*F3*F4)*rho**(n-2*k)
                Zs[:,k] = Ri  
            Zs = np.sum(Zs,axis=1)
        
        if m >= 0:    
            Zs = Zs.reshape(len(Zs))*np.cos(abs(m)*phi)
        else:
            Zs = Zs.reshape(len(Zs))*np.sin(abs(m)*phi)
            
        ZernikeInfluenceFunctions[:,i] = Zs
        Xlinear = np.linalg.lstsq(ZernikeInfluenceFunctions,dz,rcond=None)[0] 
        Zernikes = Xlinear*ZernikeInfluenceFunctions
        SFEs = np.round(np.std(Zernikes,axis=0) * UnitFactor,2)
        PVs = np.round((np.max(Zernikes,axis=0) - np.min(Zernikes,axis=0)) * UnitFactor,2)
        
    return Zernikes, ZernikeInfluenceFunctions, Xlinear,m,A,SFEs,PVs,mnlist

def ZernikeNamesFunc():
    ZernikeNames = [' Piston',' Tip',' Tilt',' Astigmatism 1', ' Defocus',' Astigmatism 2',' Trefoil 1',
                    ' Coma 1', ' Coma 2',' Trefoil 2',' ', ' ', ' Spherical Aberration']
    for i in range(1000):
        ZernikeNames.append(' ')
    return ZernikeNames        

def ZernikeTableFunc(mnlist, ZernikeNames):
    ZernikeTable = []
    ZernikeNames = ZernikeNamesFunc()
    
    for i in range(len(mnlist)):
        ZernikeTable.append(str(mnlist[i])+ZernikeNames[i])
    return ZernikeTable

def main():
    st.set_page_config(layout="wide")
    with st.sidebar:
        st.title('Zernike Decomposition Tool')
        st.write('info: jan.devreugd@tno.nl')
        readme()
        uploaded_file = st.file_uploader("Select a datafile:")
        
    if uploaded_file is not None:
        data, shapeFile = dataread(uploaded_file)
        
        with st.sidebar:
            st.write(' \# data points = ' + str(shapeFile[0]) + ', # columns = ' + str(shapeFile[1]) )
            units = st.radio('data units:', ('meters', 'millimeters'))
            
        if units == 'meters':
            UnitFactor = 1E9
        else:
            UnitFactor = 1E6
        
        with st.sidebar:
            x,y,dz,R, phi, rho = dataselection(data,shapeFile)
            dzPTT = TipTilt(x, y, dz)
            xi,yi = gridarrays(x,y) 

            SphereFit_opt = st.checkbox('Calculate best fitting sphere and asphere')
            ZernikeDecomposition_opt = st.checkbox('Zernike decompostion')
            
            if ZernikeDecomposition_opt:
                NN, mm = ZernikeTerms()
                default_NN = NN.index(6)
                N_Zernikes = st.selectbox('# Zernike terms ',NN,index = default_NN)
                index = NN.index(N_Zernikes)  
                m_max = mm[index]
                SortZernikes_opt = st.checkbox('Sort Zernikes',True)
                
        
        with st.expander('Plot original data + Piston Tip Tilt removal:', expanded=True): 
            
            col1, col2 = st.columns(2)
            with col1:
                plotlyfunc(x,y,xi,yi,dz,UnitFactor, 'Original data:')
            with col2:    
                plotlyfunc(x,y,xi,yi,dzPTT,UnitFactor, 'Original data minus piston, tip and tilt:')
                
                            
        if SphereFit_opt:   
            initial_guess = [sagsign(R,dz)*np.max(R)*10, -1]
            parsS, pcovS = curve_fit(funcSphere, R, dzPTT, p0=initial_guess)
            fitSphere = funcSphere(R,parsS[0],parsS[1])
            dzSphFit =  dzPTT-fitSphere
            
            initial_guess = [sagsign(R,dz)*np.max(R)*10, 0., -1]
            parsAS, pcovAS = curve_fit(funcASphere, R, dzPTT, p0=initial_guess)
            fitASphere = funcASphere(R,parsAS[0],parsAS[1],parsAS[2])
            dzASphFit =  dzPTT-fitASphere
            
            with st.expander('Best sphere and a-sphere fit:'):
                col1, col2 = st.columns(2)
                with col1:
                    plotlyfunc(x,y,xi,yi,dzSphFit,UnitFactor, 'Best fit sphere fit: <br> The best fitting sphere-radius is ' + str(np.round(parsS[0],2)) + ' ' + str(units) )
                with col2:
                    plotlyfunc(x,y,xi,yi,dzASphFit,UnitFactor, 'Best fit Asphere fit: <br> The best fitting Asphere-radius is ' + str(np.round(parsAS[0],2)) + ' ' +  str(units) + 
                               '. <br> The best fitting conical constant is ' + str(np.round(parsAS[1],3)) + '.')
                
        if ZernikeDecomposition_opt:
            Zernikes, ZernikeInfluenceFunctions, Xlinear,m,ZernikeModeNames,SFEs,PVs,mnlist = ZernikeDecomposition(rho, phi, m_max, dz,UnitFactor)
            ZernikeNames = ZernikeNamesFunc()
            ZernikeTable = ZernikeTableFunc(mnlist, ZernikeNames)
            
            if SortZernikes_opt:
                with st.expander('Zernike decompostion plots, sorted'):
                    col1, col2,col3,col4,col5,col6 = st.columns(6)
                    H = [col1,col2,col3,col4,col5,col6]
                    
                    for j in range(len(ZernikeModeNames)):
                        i = np.argsort(SFEs)[-1-j]
                        plt.figure(i+1)
                        Zjan = griddata((x,y),ZernikeInfluenceFunctions[:,i],(xi,yi),method='cubic')
                        fig,ax = plt.subplots(figsize=(6,3))
                        pc = ax.pcolormesh(xi,yi,Zjan,cmap=cm.jet)
                        ax.set_aspect('equal', adjustable='box')
                        ax.set_title('Zernike Mode: '+ ZernikeNames[i]  + '\n ' + 
                                     'n=' + str(ZernikeModeNames[i][1]) + ' m=' + str(ZernikeModeNames[i][0]) +
                                     '\nPV = ' + str(PVs[i]) + ' nm' +
                                     '\nSFE = ' + str(SFEs[i]) + ' nm RMS'
                                     )
                        with H[j%6]:
                            st.pyplot(fig) 
            else:            
                with st.expander('Zernike decompostion plots'):
                    col1, col2,col3,col4,col5,col6 = st.columns(6)
                    H = [col1,col2,col3,col4,col5,col6]
                    
                    for j in range(len(ZernikeModeNames)):
                        i = j
                        plt.figure(i+1)
                        Zjan = griddata((x,y),ZernikeInfluenceFunctions[:,i],(xi,yi),method='cubic')
                        fig,ax = plt.subplots(figsize=(6,3))
                        pc = ax.pcolormesh(xi,yi,Zjan,cmap=cm.jet)
                        ax.set_aspect('equal', adjustable='box')
                        ax.set_title('Zernike Mode: '+ ZernikeNames[j]  + '\n ' + 
                                     'n=' + str(ZernikeModeNames[i][1]) + ' m=' + str(ZernikeModeNames[i][0]) +
                                     '\nPV = ' + str(PVs[i]) + ' nm' +
                                     '\nSFE = ' + str(SFEs[i]) + ' nm RMS'
                                     )
                        with H[j%6]:
                            st.pyplot(fig)
            
            with st.expander('Original data minus summation of Zernikes'):
                ZernikesSum = np.sum(Zernikes,axis = 1)
                ZernikeDelta = dz - ZernikesSum
                
                col1, col2 = st.columns(2)
                with col1:
                    plotlyfunc(x,y,xi,yi,dz,UnitFactor, 'Original data:')
                with col2:    
                    plotlyfunc(x,y,xi,yi,ZernikeDelta,UnitFactor, 'Original data minus Zernikes:')
                
                
                                
            
            with st.expander('Zernike Table'):

                dfTable = pd.DataFrame({'Zernike Mode:' : ZernikeTable, 'PV [nm]' : PVs, 'SFE [nm RMS]:' : SFEs}) 
                st.write(dfTable) 
   
            
main()