"""
https://scicomp.stackexchange.com/questions/20054/implementation-of-1d-advection-in-python-using-weno-and-eno-schemes

"""
import numpy as np
from numpy import *
import matplotlib.pyplot as plt

def ENOweights(k,r):
    #Purpose: compute weights c_rk in ENO expansion
    # v_[i+1/2] = \sum_[j=0]^[k-1] c_[rj] v_[i-r+j]
    #where k = order and r = shift

    c = zeros(k)

    for j in range(0,k):
            de3 = 0.
            for m in range(j+1,k+1):
                #compute denominator
                de2 = 0.
                for l in range(0,k+1):
                    #print 'de2:',de2
                    if l is not m:
                        de1 = 1.
                        for q in range(0,k+1):
                            #print 'de1:',de1
                            if (q is not m) and (q is not l):
                                de1 = de1*(r-q+1)


                        de2 = de2 + de1


                #compute numerator
                de1 = 1.
                for l in range(0,k+1):
                    if (l is not m):
                        de1 = de1*(m-l)

                de3 = de3 + de2/de1


            c[j] = de3


    return c

def nddp(X,Y):
    #Newton's divided difference table
    #the input are two vectors X and Y that represent points

    n = len(X)

    DD = zeros((n,n+1))

    #inserting x into 1st column of DD-table
    DD[:,0]=X

    #inserting y into 2nd column of DD-table
    DD[:,1]=Y

    #creates divided difference coefficients
    #e.g: D[0,0] = (Y[1]-Y[0])/(X[1]-X[0])

    for j in range(0,n-1):
        for k in range(0,n-j-1): #j goes from 0 to n-2
            DD[k,j+2]= (DD[k+1,j+1]-DD[k,j+1])/(DD[k+j+1,0]-DD[k,0])

    return DD

def ENO(xloc, uloc, k):
    #Purpose: compute the left and right cell interface values using an ENO
    #Approach based on 2k-1 long vectors uloc with cell k

    #treat special case of k=1 - no stencil to select
    if (k==1):
        ul = uloc[0]
        ur = uloc[0]

    #Apply ENO procedure
    S = zeros(k,dtype=int)
    S[0] = k
    for kk in range (0,k-1):
        #print 'S:',S
        #left stencil
        xvec = zeros(k)
        print(f'xvec = {xvec}')
        uvec = zeros(k)
        Sindxl = append(S[0]-1, S[0:kk+1])-1
        print(f'Sindxl = {Sindxl}')
        print(f'xloc = {xloc}')
        xvec = xloc[Sindxl]
        uvec = uloc[Sindxl]
        DDl = nddp(xvec,uvec)
        Vl = abs(DDl[0,kk+2])

        #right stencil
        xvec = zeros(k)
        uvec = zeros(k)
        Sindxr = append(S[0:kk+1], S[kk]+1)-1
        xvec = xloc[Sindxr]
        uvec = uloc[Sindxr]
        DDr = nddp(xvec,uvec)
        Vr = abs(DDr[0,kk+2])

        #choose stencil through divided differences
        if (Vr>Vl):
            #print 'Vr>Vl'
            S[0:kk+2] = Sindxl+1
        else:
            S[0:kk+2] = Sindxr+1

    #Compute stencil shift 'r'
    r = k - S[0]

    #Compute weights for stencil
    cr = ENOweights(k,r)
    cl = ENOweights(k,r-1)

    #Compute cell interface values
    ur = 0
    ul = 0
    for i in range(0,k):
        ur = ur + cr[i]*uloc[S[i]-1]
        ul = ul + cl[i]*uloc[S[i]-1]

    return (ul,ur)

def WENO(xloc, uloc, k):
    #Purpose: compute the left and right cell interface values using ENO
    #approach based on 2k-1 long vectors uloc with cell k

    #treat special case of k = 1 no stencil to select
    if (k==1):
        ul = uloc[0]
        ur = uloc[1]

    #Apply WENO procedure
    alphal = zeros(k)
    alphar = zeros(k)
    omegal = zeros(k)
    omegar = zeros(k)
    beta = zeros(k)
    d = zeros(k)
    vareps= 1e-6

    #Compute k values of xl and xr based on different stencils
    ulr = zeros(k)
    urr = zeros(k)

    for r in  range(0,k):
        cr = ENOweights(k,r)
        cl = ENOweights(k,r-1)

        for i in range(0,k):
            urr[r] = urr[r] + cr[i]*uloc[k-r+i-1]
            ulr[r] = ulr[r] + cl[i]*uloc[k-r+i-1]


    #setup WENO coefficients for different orders -2k-1
    if (k==2):
        d[0]=2/3.
        d[1]=1/3.
        beta[0] = (uloc[2]-uloc[1])**2
        beta[1] = (uloc[1]-uloc[0])**2


    if(k==3):
        d[0] = 3/10.
        d[1] = 3/5.
        d[2] = 1/10.
        beta[0] = 13/12.*(uloc[2]-2*uloc[3]+uloc[4])**2 + 1/4.*(3*uloc[2]-4*uloc[3]+uloc[4])**2
        beta[1] = 13/12.*(uloc[1]-2*uloc[2]+uloc[3])**2 + 1/4.*(uloc[1]-uloc[3])**2
        beta[2] = 13/12.*(uloc[0]-2*uloc[1]+uloc[2])**2 + 1/4.*(3*uloc[2]-4*uloc[1]+uloc[0])**2

    #compute alpha parameters
    for r in range(0,k):
        alphar[r] = d[r]/(vareps+beta[r])**2
        alphal[r] = d[k-r-1]/(vareps+beta[r])**2

    #Compute WENO weights parameters
    for r in range(0,k):
        omegal[r] = alphal[r]/alphal.sum()
        omegar[r] = alphar[r]/alphar.sum()

    #Compute cell interface values
    ul = 0
    ur = 0
    for r in range(0,k):
        ul = ul + omegal[r]*ulr[r]
        ur = ur + omegar[r]*urr[r]

    return (ul,ur)

if __name__ == "__main__":
    nx = 81
    dx = 2. / (nx - 1)
    x = linspace(0, 2, nx)
    nt = 25
    dt = .02
    print(f'd0.')
    c = 1.  # assume wavespeed of c = 1
    u = zeros(nx)  # numpy function ones()
    u[int(.5 / dx): int(
        1 / dx + 1)] = 2  # setting u = 2 between 0.5 and 1 as per our I.C.s
    k = 3  # number of weights Order= 2*k-1
    gc = k - 1  # number of ghost cells
    # adding ghost cells
    gcr = x[-1] + linspace(1, gc, gc) * dx
    gcl = x[0] + linspace(-gc, -1, gc) * dx
    xc = append(x, gcr)
    xc = append(gcl, xc)
    uc = append(u, u[-gc:])
    uc = append(u[0:gc], uc)
    U_rk3 = uc.copy()

    gs = zeros((nx + 2 * gc, nt))
    flux = zeros(nx + 2 * gc)

    plt.plot(x, u, '--', label='Initial')
    t = 0
    for n in range(1, nt):
        t += dt
        un = uc.copy()
        U_rk3 = U_rk3.copy()
        # for i in range(1,nx):
        for i in range(2, nx):
            xloc = xc[i - (k - 1):i + k]
            floc = c * uc[i - (k - 1):i + k]
            # f_left,f_right = ENO(xloc,floc,k)
            f_left, f_right = WENO(xloc, floc, k)
            # uc[i] = un[i]-dt/dx*(f_right-f_left)
            flux[i] = 0.5 * (c + fabs(c)) * f_left + 0.5 * (
                        c - fabs(c)) * f_right

        for i in range(gc, nx - gc):
            if c > 0:
                # uc[i] = un[i]-dt/dx*(flux[i]-flux[i-1])
                uc[i] = uc[i] - dt / dx * (flux[i] - flux[i - 1])
                if 0:  # Identical to Euler
                    U = uc
                    U_1 = U + dt / dx * (flux[i] - flux[i - 1])
                    U_2 = 3 / 4.0 * U + 1 / 4.0 * U_1 + 1 / 4.0 * dt / dx * (flux[i] - flux[i - 1])
                    U = 1 / 3.0 * U + 2 / 3.0 * U_2 + 2 / 3.0 * dt  / dx * (flux[i] - flux[i - 1])
                else:  # RK3 note change last term to negative
                        # NOTE: TECHNICALLY NOT RK3 SINCE FLUXES ARE USING U_1
                        #       VALS
                    # U = uc.copy
                    U = U_rk3.copy()
                    U_1 = U[i] - dt / dx * (flux[i] - flux[i - 1])
                    U_2 = 3 / 4.0 * U[i] + 1 / 4.0 * U_1 - 1 / 4.0 * dt / dx * (
                                flux[i] - flux[i - 1])
                    U[i] = 1 / 3.0 * U[
                        i] + 2 / 3.0 * U_2 - 2 / 3.0 * dt / dx * (
                                       flux[i] - flux[i - 1])
                    U_rk3 = U.copy()
            else:
                # uc[i] = un[i]-dt/dx*(flux[i+1]-flux[i])
                uc[i] = uc[i] - dt / dx * (flux[i + 1] - flux[i])

    if 0:  # old
        for n in range(1, nt):
            un = u.copy()
            for i in range(1, nx):
                u[i] = un[i] - c * dt / dx * (un[i] - un[i - 1])

    print(f'tf = {t}')
    plt.plot(x, u, '--', label='Step')
    # plt.plot(x, uc, '--')
    plt.plot(xc, uc, '--', label='Euler')
    plt.plot(xc, U, '-.', label='RK3')
    plt.legend()
    plt.show()