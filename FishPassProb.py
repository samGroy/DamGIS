#FishPassProb
#Given species, flow velocity and length, estimate probability of passage

import numpy
import sys
import scipy
from scipy import special
from scipy import integrate

species=sys.argv[1] #species name
D=float(sys.argv[2]) #culvert diameter
v=float(sys.argv[3]) #spawning run timed flow velocity through culvert
if len(sys.argv)>4:
    if sys.argv[4] in 'feet': #convert feet to meters
        D=D/3.28
        v=v/3.28
T=16.

if species.lower() in 'american shad, atlantic salmon':
    intercept=5.706
    vbeta=-0.983
    Tbeta=-0.029
    lbeta=0.0022
    if species.lower() in 'atlantic salmon':
        l=735
    else:
        l=417.25
    scale=0.316
    sh=2.070
    dist='gamma'
elif species.lower() in 'alewife':
    intercept=4.571
    vbeta=-0.920
    Tbeta=-0
    lbeta=0
    l=236
    scale=0.513
    sh=2.431
    dist='gamma'
elif species.lower() in 'blueback herring':
    intercept=-0.435
    vbeta=-1.165
    Tbeta=0.079
    lbeta=0.0196
    l=220
    scale=0.665
    sh=0
    dist='weibull'

mu=(v*vbeta)+(l*lbeta)+(T*Tbeta)+intercept
zed=(numpy.log(D)-mu)/scale

if dist is 'gamma':
    f=lambda x: x**(sh**-2-1)*numpy.exp(-x)
    b=sh**-2*numpy.exp(sh*zed)
    S=scipy.integrate.quad(f,b,numpy.inf)[0]/scipy.integrate.quad(f,0,numpy.inf)[0]
elif dist is 'weibull':
    S=numpy.exp(-numpy.exp(zed))
print "species:%s, distance: %.1f, velocity: %.1f, probability: %.3f"%(species,D,v,S)
