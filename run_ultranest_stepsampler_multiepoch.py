import numpy as np
from numpy import pi, sin, cos, tan, arctan, sqrt, arcsin
from numpy import sin, pi
import matplotlib.pyplot as plt
from ultranest import ReactiveNestedSampler
from ultranest.plot import cornerplot
from pandora import pandora
from numba import jit


@jit(cache=True, nopython=True, fastmath=True)
def prior_transform(cube):
    # the argument, cube, consists of values from 0 to 1
    # we have to convert them to physical scales

    # 0  r_moon
    # 1  a_moon
    # 2  tau_moon
    # 3  Omega_moon
    # 4  w_moon
    # 5  i_moon
    # 6  M_moon
    # 7  per_planet
    # 8  a_planet
    # 9  r_planet
    # 10 b_planet
    # 11 t0_planet
    # 12 M_planet

    params     = cube.copy()
    params[0]  = cube[0]  * 1000000 + 1 # r_moon (0, 25000) [km]
    params[1]  = cube[1]  * 2000000 + 20000 # a_moon (20000, 2_020_000) [km]
    params[2]  = cube[2]  / 2 # tau_moon (normalized 0..1)
    params[3]  = cube[3]  * 90 # Omega_moon
    params[4]  = cube[4]  * 90 # i_moon
    params[5]  = cube[5]  * 2e22 + 5e22  # M_moon
    params[6]  = cube[6]  * 10 + 360 # per_planet
    params[7]  = cube[7]  * 14959787 + 142117976.5 # a_planet
    params[8]  = cube[8]  * 100000 # r_planet
    params[9] = cube[9] # b_planet
    params[10] = cube[10] - 0.5 # t0_planet_offset
    params[11] = cube[11] * 2e24 + 5e24 # M_planet
    return params


@jit(cache=True, nopython=True, fastmath=True)
def log_likelihood(params):

    r_moon,a_moon,tau_moon,Omega_moon,i_moon,M_moon,per_planet,a_planet,r_planet,b_planet,t0_planet_offset,M_planet = params
    flux_planet, flux_moon, flux_total, px_bary, py_bary, mx_bary, my_bary, time_arrays = pandora(
        r_moon,
        a_moon,
        tau_moon,
        Omega_moon,
        i_moon,
        M_moon,
        per_planet,
        a_planet,
        r_planet,
        b_planet,
        t0_planet_offset,
        M_planet,
        R_star=1 * 696342,  # km
        u=u,
        t0_planet=t0_planet,
        epochs=epochs,
        epoch_duration=epoch_duration,
        cadences_per_day=cadences_per_day,
        epoch_distance = epoch_distance
    )
    loglike = -0.5 * (((flux_total - testdata) / yerr)**2).sum()
    return loglike



np.random.seed(seed=42)  # reproducibility
t_start = 100
t_end = 114
t_dur = t_end - t_start
cadences_per_day = 48
cadences = int(cadences_per_day * t_dur)
time_array = np.linspace(t_start, t_end, cadences)
#print("cadences", cadences)

G = 6.67408 * 10 ** -11

# Set stellar parameters
R_star = 1 * 696342  # km
u1 = 0.5
u2 = 0.5

# Set planet parameters
r_planet = 63710  # km
a_planet = 1 * 149597870.700  # [km]
b_planet = 0.4  # [0..1.x]; central transit is 0.
per_planet = 365.25  # [days]
M_planet = 5.972 * 10 ** 24
#M_sun = 2e30
t0_planet_offset = 0.1
transit_duration_planet = per_planet / pi * arcsin(sqrt(((r_planet/2) + R_star) ** 2) / a_planet)
epoch_distance = 365.25

# Set moon parameters
# Set moon parameters
r_moon = 18000  # [km]
a_moon = 384000 * 3  # [km]
Omega_moon = 10#20  # degrees [0..90]
w_moon = 20#50.0  # degrees
i_moon = 80 #60.0  # 0..90 in degrees. 90 is edge on
tau_moon = 0.25  # [0..0.5] like inclination
mass_ratio = 0.1
u = np.array([[u1, u2]])
per_moon = (2 * pi * sqrt((a_moon * 1000) ** 3 / (G * M_planet))) / 60 / 60 / 24

M_moon = 6e22

u = np.array([[u1, u2]])


# Model with 5 epochs:
# t0_planet_offset must be constant for all
# new variable: t0_planet: Time (in days) of first planet mid-transit in time series

# Example: First planet mid-transit at time t0_planet = 100  # days
t0_planet = 100  # days
epochs = 5

# Each epoch must contain a segment of data, centered at the planetary transit
# Each epoch must be the same time duration
epoch_duration = 3  # days
cadences_per_day = 48  # switch this to automatic calculation? What about gaps?


flux_planet, flux_moon, flux_total, px_bary, py_bary, mx_bary, my_bary, time_arrays = pandora(
    r_moon,
    a_moon,
    tau_moon,
    Omega_moon,
    i_moon,
    M_moon,
    per_planet,
    a_planet,
    r_planet,
    b_planet,
    t0_planet_offset,
    M_planet,
    R_star,
    u,
    t0_planet,
    epochs,
    epoch_duration,
    cadences_per_day,
    epoch_distance
)


# Create noise and merge with flux
stdev = 1e-4
noise = np.random.normal(0, stdev, len(time_arrays))
testdata = noise + flux_total
yerr = np.full(len(testdata), stdev)

plt.plot(time_arrays, flux_planet, color="blue")
plt.plot(time_arrays, flux_moon, color="red")
plt.plot(time_arrays, flux_total, color="black")
plt.scatter(time_arrays, testdata, color="black", s=5)
plt.show()


# Recover the test data

parameters = [
    'r_moon', 
    'a_moon', 
    'tau_moon', 
    'Omega_moon',
    'i_moon',
    'M_moon',
    'per_planet',
    'a_planet',
    'r_planet',
    'b_planet',
    't0_planet',
    'M_planet'
    ]

sampler2 = ReactiveNestedSampler(parameters, log_likelihood, prior_transform,
    wrapped_params=[
    False,
    False,
    True, 
    False, 
    False, 
    False, 
    False, 
    False, 
    False, 
    False, 
    False, 
    False, 
    ],
)

import ultranest.stepsampler
import ultranest

nsteps = 2 * len(parameters)
sampler2.stepsampler = ultranest.stepsampler.RegionSliceSampler(nsteps=nsteps)
result2 = sampler2.run(min_num_live_points=400, update_interval_ncall=1000)
sampler2.print_results()


cornerplot(result2)
plt.show()
"""
plt.figure()
plt.xlabel('x')
plt.ylabel('y')
plt.errorbar(x=t, y=y, yerr=yerr,
             marker='o', ls=' ', color='orange')

plt.show()
"""

#cornerplot(result)
"""
plt.figure()
plt.xlabel('x')
plt.ylabel('y')
plt.errorbar(x=t, y=y, yerr=yerr,
             marker='o', ls=' ', color='orange')
"""
#plt.show()
