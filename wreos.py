"""The wide ranging equation of state (WR-EOS)"""
#from ddt import *
import numpy as np
from scipy import optimize, integrate
from params import *

"""WR-EOS"""
def e(p, v, lambd, phi):
    """
    A combination of Equations 16 and 17
    :param p: pressure
    :param v: specific volume (cm3 g-1)
    :param lambd: Reaction progression \in [0, 1]
    :param phi: Porosity
    :return: e (kJ g-1  ?)
    """
    # First compute the volumes (Equation 16)
    v_p, v_ps, v_r, Phi = volumes(v, lambd, phi)

    # Using the computed volumes, compute the internal energy at v, p
    return (1 - lambd) * e_r(p / phi, v_r) + lambd * e_p(p, v_p)


def volumes(v, lambd, phi):
    def denom(lambd, Phi):
        """
        Denominator of closure relationships in equation 16
        :param lambd:
        :param Phi: closure constant/function. Varies between 0.8 to 1.0
                    If lambd = 0 then Phi = 1, if lambd > 0 then Phi ~ 0.95
        :return:
        """
        return lambd + (1 - lambd) * Phi

    v_ps_g = v  # Initial guess value for v_ps
    v_r_g = v * phi  # Initial guess value for v_r
    Phi_g = 0.95  # Initial guess value for Phi
    v_p_g = Phi_g * v_ps_g  # Initial guess value for v_p
    #TODO: Update routine to use previous values in the element as guess
    x0 = [v_p_g, v_ps_g, v_r_g, Phi_g]
    x0 = np.array(x0) - 1e-2
    def system(x):
        v_p, v_ps, v_r, Phi = x
        return [v_p - (v / denom(lambd, Phi)),
                v_ps - (Phi * v / denom(lambd, Phi)),
                v_r - (phi * Phi * v / denom(lambd, Phi)),
                Phi - v_ps/v_p
                ]

    def jac(x):  # Jacobian computed with SymPy
        v_p, v_ps, v_r, Phi = x
        return np.array([[1, 0, 0, -v * (lambd - 1) / (Phi * (-lambd + 1) + lambd) ** 2],
                         [0, 1, 0, -Phi * v * (lambd - 1) / ( Phi * (-lambd + 1) + lambd) ** 2 - v / (Phi * (-lambd + 1) + lambd)],
                         [0, 0, 1, -Phi * phi * v * (lambd - 1) / (Phi * (-lambd + 1) + lambd) ** 2 - phi * v / (Phi * (-lambd + 1) + lambd)],
                         [v_ps / v_p ** 2, -1 / v_p, 0, 1]])

    sol = optimize.root(system, x0, jac=jac, method='hybr')
    return sol.x


def p_from_e(energy, v, lambd, phi):
    """
    Compute the pressure, given energy, volume, lambd and phi
    :param energy: energy
    :param v: specific volume
    :param lambd: reaction progress
    :param phi: porosity
    :param guess: Initial guess for p and v
    :return: p, v  # pressure and volume
    """
    e = energy
    v_p, v_ps, v_r, Phi = volumes(v, lambd, phi)

    if 0:
        #TODO: Deleate reduntant computation
        P = phi*(gamma_p(v_p)*lambd*p_s_p(v_p)*v_r
                 - gamma_r(v_r)*lambd*p_s_r(v_r)*v_p
                 + gamma_r(v_r)*p_s_r(v_r)*v_p
                 + e*v_p*v_r
                 - e_s_p(v_p)*lambd*v_p*v_r
                 + e_s_r(v_r)*lambd*v_p*v_r
                 - e_s_r(v_r)*v_p*v_r
                 )/(
                gamma_p(v_p)*lambd*phi*v_r
                - gamma_r(v_r)*lambd*v_p
                + gamma_r(v_r)*v_p)

    P = phi*(gamma_p(v_p)*gamma_r(v_r)*e
             - gamma_p(v_p)*gamma_r(v_r)*e_s_p(v_p)*lambd
             + gamma_p(v_p)*gamma_r(v_r)*e_s_r(v_r)*lambd
             - gamma_p(v_p)*gamma_r(v_r)*e_s_r(v_r)
             - gamma_p(v_p)*lambd*p_s_r(v_r)*v_r
             + gamma_p(v_p)*p_s_r(v_r)*v_r
             + gamma_r(v_r)*lambd*p_s_p(v_p)*v_p)/(-gamma_p(v_p)*lambd*v_r
                                                   + gamma_p(v_p)*v_r
                                                   + gamma_r(v_r)*lambd*phi*v_p)
    return P

def p_from_e_no_reaction(energy, v, phi, lambd=0):
    """
    Compute the pressure, given energy, volume and phi, lambd=0
    :param energy: energy
    :param v: specific volume
    :param lambd: reaction progress, must be 0.0
    :param phi: porosity
    :param guess: Initial guess for p and v
    :return: p, v  # pressure and volume
    """
    e = energy
    #v_p, v_ps, v_r, Phi = volumes(v, lambd, phi)

    v_r = phi * v


    P = phi*(gamma_p(v_p)*gamma_r(v_r)*e
             - gamma_p(v_p)*gamma_r(v_r)*e_s_p(v_p)*lambd
             + gamma_p(v_p)*gamma_r(v_r)*e_s_r(v_r)*lambd
             - gamma_p(v_p)*gamma_r(v_r)*e_s_r(v_r)
             - gamma_p(v_p)*lambd*p_s_r(v_r)*v_r
             + gamma_p(v_p)*p_s_r(v_r)*v_r
             + gamma_r(v_r)*lambd*p_s_p(v_p)*v_p)/(-gamma_p(v_p)*lambd*v_r
                                                   + gamma_p(v_p)*v_r
                                                   + gamma_r(v_r)*lambd*phi*v_p)
    return P

def e_i(p, v, lambd, phi):
    """
    Compute the initial energy, given p_0, v_0, lambd_0 and phi_0
    :param p:
    :param v:
    :param lambd:
    :param phi:
    :return:
    """


"""Detonation products"""
# EOS
def e_p(p, v):
    """
    Equation A1 product energy
    :param p: pressure
    :param v: specific volume
    :return: energy e_p
    """
    return e_s_p(v) + (v/gamma_p(v))*(p - p_s_p(v))


def p_p(e, v):
    """
    Equation A2 product pressure
    :param e: energy
    :param v: specific volume
    :return: pressure p_p
    """
    return p_s_p(v) + (gamma_p(v)/v)*(e - e_s_p(v))

# Functionals
def p_s_p(v):
    """
    Equation A3
    :param v: specific volume
    :return:
    """
    return p_c * ((0.5*(v/v_c)**n + 0.5*(v/v_c)**(-n))**(a/n)
                  / ((v/v_c)**(k_wr + a))) * ((k_wr - 1 + F_wr(v))/
                                             (k_wr - 1 + a))


def F_wr(v):
    """
    Equation A4
    :param v: specific volume
    :return:
    """
    return (2 * a * (v/v_c)**(-n))/((v/v_c)**n + (v/v_c)**(-n))


def gamma_p(v):
    """
    Equation A5
    :param v: specific volume
    :return:
    """
    return k_wr - 1 + (1 - b) * F_wr(v)


def e_s_p(v):
    """
    Equation A6
    :param v: specific volume
    :return: e_s_p
    """
    return e_c * ((0.5*(v/v_c)**n + 0.5*(v/v_c)**(-n))**(a/n)
                  / ((v/v_c)**(k_wr - 1 + a)))

# Equation A7
e_c = (p_c * v_c) / (k_wr - 1 + a)


"""Detonation reactants"""
# EOS
def e_r(p, v):
    """
    Equation A8 reactant energy
    :param p: pressure
    :param v: specific volume
    :return: energy e_p
    """
    return e_s_r(v) + (v/gamma_r(v))*(p - p_s_r(v))


def p_r(e, v):
    """
    Equation A9 reactant pressure
    :param e: energy
    :param v: specific volume
    :return: pressure p_p
    """
    return p_s_r(v) + (gamma_r(v)/v)*(e - e_s_r(v))


def p_s_r(v):
    """
    Equation A10
    :param v: specific volume
    """
    sigma_j = 0
    for j in range(1, 4):
        sigma_j += ((4 * B * y(v))**j / np.math.factorial(j))
    return p_hat * (sigma_j
                    + C * ((4*B*y(v))**4) / 24.0 # np.math.factorial(4) = 24
                    + (y(v)**2) / (1 - y(v))**4
                    ) #* 1e-2


def y(v):
    return 1 - v/v_0

p_hat = rho_0 * A**2 / (4 * B)


def p_s_r_y(y):
    """
    Equation for integral
    """
    sigma_j = 0
    for j in range(1, 4):
        sigma_j += ((4 * B * y)**j / np.math.factorial(j))

    return p_hat * (sigma_j
                    + C * ((4*B*y)**4) / 24.0  # np.math.factorial(4) = 24
                    + (y**2) / (1 - y)**4
                    ) #*1e-2


def e_s_r(v):
    """
    Equation A11
    :param v: specific volume
    :return:
    """

    if v >= v_0:
        print(f"WARNING: v[={v}] >= v_0[={v_0}]")
    y_lim = y(v)
    INT = integrate.quad(p_s_r_y, 0, y_lim)
    if INT[1] >= 1e-1:
        print(f"WARNING: Integral error in e_s_r is high {INT}")
    #return v_0 * INT[0] + 7.07  #+ e_0  #TODO: Check
    return v_0 * INT[0] + e_0  #TODO: Check


def gamma_r(v):
    """
    Equation A12
    :param v: specific volume
    :return:
    """
    return gamma_0_r + Z * y(v)

# Equation A13
# gamma_0_r = 1.22  # beta * c_0**2 / C_p  # Answer from Appendix in paper

# Equation A14
# Z = -0.8066  # (gamma_sc - gamma_0_r)/y_max  # Answer from Appendix in paper

# Equation A15
# y_max = 2 / (gamma_p * (y_max + 2))

if __name__ == '__main__':
    # Sanity checks

    print(e_p(2, 3))
    print(p_p(e_p(2, 3), 3))

    print(e_r(2, 0.1))
    print(p_r(e_r(2, 0.1), 0.1))
    """
    print(p_r(e_r(5, 0.1), 0.1))
    print(e(p_0, 0.1, 0.0, 0.65))
    print(e(p_0, 0.1, 0.1, 0.65))
    print(e(p_0, 0.1, 1, 0.80))
    print(e(p_0, 0.1, 1, 1))
    print(e(p_0, 0.03, 1, 1))
    print(e(p_0, 0.3, 1, 1))
    print(e(p_0, 0.5, 1, 1))
    print(e(p_0, 0.5, 0.5, 1))
    print(e(p_0, 0.5, 0.5, 0.5))
    """

    print('='*100)
    #print('e_0 should be 3.983295207817231')  # before fixing gamma_r
    #print('e_0 should be 4.573901456496666')
    print(f'e_0_test should be equal to param e_0 = {e_0}')
    phi_0 = 0.75
    rho_0 = 1.6  # Initial density
    v_0 = (rho_0) ** (-1)  # Assume experimental condition
    p_0 = 1.0e-9  # GPa (equivalent to 1 atmosphere)
    lambd_0 = 0.0
    e_0_test = e(p_0, v_0, lambd_0, phi_0)  # Compute e_0
    #print(f'e_0_test out = {e_0}')  #TODO: Build a test suite
    print(f'e_0_test out = {e_0_test}')  #TODO: Build a test suite
    print(f'Test p_from_e')
    print(f'P should be 1.0e-9 ')
    P = p_from_e(e_0_test, v_0, lambd_0, phi_0)
    print(f'P out = {P}')
    #P_p = p_p(e_0_test, v_0*phi_0*0.01)
    P_p = p_p(e_0_test, v_0)
    print(f'P_p out = {P_p}')
    print('='*100)
    print(f'New test e should be ?:')
    e_out = e(P, v_0, lambd_0, phi_0)
    print(f'e from new P out = {e_out}')
    print('='*100)


