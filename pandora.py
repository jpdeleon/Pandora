import numpy as np
from numpy import sqrt, pi, arcsin, cos
from numba import jit
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from core import ellipse, occult, occult_small, eclipse, resample


class model_params(object):
    def __init__(self):

        # Star parameters
        self.u1 = None
        self.u2 = None
        self.R_star = None

        # Planet parameters
        self.per_bary = None
        self.a_bary = None
        self.r_planet = None
        self.b_bary = None
        self.w_bary = 0
        self.ecc_bary = 90
        self.t0_bary = None
        self.t0_bary_offset = None        
        self.M_planet = None

        # Moon parameters
        self.r_moon = None
        self.per_moon = None
        self.tau_moon = None
        self.Omega_moon = None
        self.i_moon = None
        self.mass_ratio = None

        # Other model parameters
        self.epochs = None
        self.epoch_duration = None
        self.cadences_per_day = None
        self.epoch_distance = None
        self.supersampling_factor = 1
        self.occult_small_threshold = 0.01
        self.hill_sphere_threshold = 1.1
        self.numerical_grid = 25


class moon_model(object):
    def __init__(self, params):

        
        # Star parameters
        self.u1 = params.u1
        self.u2 = params.u2
        self.R_star = params.R_star

        # Planet parameters
        self.per_bary = params.per_bary
        self.a_bary = params.a_bary
        self.r_planet = params.r_planet
        self.b_bary = params.b_bary
        self.w_bary = params.w_bary
        self.ecc_bary = params.ecc_bary
        self.t0_bary = params.t0_bary
        self.t0_bary_offset = params.t0_bary_offset        
        self.M_planet = params.M_planet

        # Moon parameters
        self.r_moon = params.r_moon
        self.per_moon = params.per_moon
        self.tau_moon = params.tau_moon
        self.Omega_moon = params.Omega_moon
        self.i_moon = params.i_moon
        self.mass_ratio = params.mass_ratio

        # Other model parameters
        self.epochs = params.epochs
        self.epoch_duration = params.epoch_duration
        self.cadences_per_day = params.cadences_per_day
        self.epoch_distance = params.epoch_distance
        self.supersampling_factor = params.supersampling_factor
        self.occult_small_threshold = params.occult_small_threshold
        self.hill_sphere_threshold = params.hill_sphere_threshold
        self.numerical_grid = params.numerical_grid

    def video(self, limb_darkening=True, teff=6000, planet_color="black", moon_color="black", ld_circles=100):
        self.flux_planet, self.flux_moon, self.flux_total, self.px, self.py, self.mx, self.my, self.time_arrays = pandora(        
            self.u1,
            self.u2,
            self.R_star,

            # Planet parameters
            self.per_bary,
            self.a_bary,
            self.r_planet,
            self.b_bary,
            self.w_bary,
            self.ecc_bary,
            self.t0_bary,
            self.t0_bary_offset,   
            self.M_planet,

            # Moon parameters
            self.r_moon,
            self.per_moon,
            self.tau_moon,
            self.Omega_moon,
            self.i_moon,
            self.mass_ratio,

            # Other model parameters
            self.epochs,
            self.epoch_duration,
            self.cadences_per_day,
            self.epoch_distance,
            self.supersampling_factor,
            self.occult_small_threshold,
            self.hill_sphere_threshold,
            self.numerical_grid 
        )
        # Build video with matplotlib
        fig = plt.figure(figsize = (5,5))
        axes = fig.add_subplot(111)
        plt.axis('off')
        plt.style.use('dark_background')
        plt.gcf().gca().add_artist(plt.Circle((0, 0), 5, color="black"))
        if limb_darkening:
            if teff > 12000:
                teff = 12000
            if teff < 2300:
                teff = 2300
            star_colors = np.genfromtxt('star_colors.csv', delimiter=',')
            row = np.argmax(star_colors[:,0] >= teff)
            r_star = star_colors[row,1]
            g_star = star_colors[row,2]
            b_star = star_colors[row,3]
            for i in reversed(range(ld_circles)):
                impact = (i / ld_circles)
                m = sqrt(1 - min(impact**2, 1))
                ld = (1 - self.u1 * (1 - m) - self.u2 * (1 - m) ** 2)
                r = r_star * ld
                g = g_star * ld
                b = b_star * ld
                Sun = plt.Circle((0, 0), impact, color=(r, g, b))
                plt.gcf().gca().add_artist(Sun)
        else:
            plt.gcf().gca().add_artist(plt.Circle((0, 0), 1, color="yellow"))

        axes.set_xlim(-1.05, 1.05)
        axes.set_ylim(-1.05, 1.05)
        moon, = axes.plot(
            self.mx[0],
            self.my[0],
            'o',
            color=planet_color,
            markerfacecolor=moon_color,
            markeredgecolor=moon_color,
            markersize=260 * self.r_moon
        )
        planet, = axes.plot(
            self.px[0],
            self.py[0], 
            'o', 
            color=planet_color,
            markeredgecolor=planet_color,
            markerfacecolor=planet_color,
            markersize=260 * self.r_planet
        )

        def ani(coords):
            moon.set_data(coords[0],coords[1])
            planet.set_data(coords[2],coords[3])
            pbar.update(1)
            return moon, planet

        def frames():
            for mx, my, px, py in zip(self.mx, self.my, self.px, self.py):
                yield mx, my, px, py

        pbar = tqdm(total=len(self.mx))
        ani = FuncAnimation(fig, ani, frames=frames, save_count=1e15, blit=True)
        return ani

    def light_curve(self):
        flux_planet, flux_moon, flux_total, px, py, mx, my, time_arrays = pandora(        
            self.u1,
            self.u2,
            self.R_star,

            # Planet parameters
            self.per_bary,
            self.a_bary,
            self.r_planet,
            self.b_bary,
            self.w_bary,
            self.ecc_bary,
            self.t0_bary,
            self.t0_bary_offset,   
            self.M_planet,

            # Moon parameters
            self.r_moon,
            self.per_moon,
            self.tau_moon,
            self.Omega_moon,
            self.i_moon,
            self.mass_ratio,

            # Other model parameters
            self.epochs,
            self.epoch_duration,
            self.cadences_per_day,
            self.epoch_distance,
            self.supersampling_factor,
            self.occult_small_threshold,
            self.hill_sphere_threshold,
            self.numerical_grid
        )
        return time_arrays, flux_total, flux_planet, flux_moon

    def coordinates(self):
        flux_planet, flux_moon, flux_total, px, py, mx, my, time_arrays = pandora(        
            self.u1,
            self.u2,
            self.R_star,

            # Planet parameters
            self.per_bary,
            self.a_bary,
            self.r_planet,
            self.b_bary,
            self.w_bary,
            self.ecc_bary,
            self.t0_bary,
            self.t0_bary_offset,   
            self.M_planet,

            # Moon parameters
            self.r_moon,
            self.per_moon,
            self.tau_moon,
            self.Omega_moon,
            self.i_moon,
            self.mass_ratio,

            # Other model parameters
            self.epochs,
            self.epoch_duration,
            self.cadences_per_day,
            self.epoch_distance,
            self.supersampling_factor,
            self.occult_small_threshold,
            self.hill_sphere_threshold,
            self.numerical_grid
        )
        return time_arrays, px, py, mx, my


#@jit(cache=False, nopython=True, fastmath=True, parallel=False)
def pandora(
    u1,
    u2,
    R_star,

    # Planet parameters
    per_bary,
    a_bary,
    r_planet,
    b_bary,
    w_bary,
    ecc_bary,
    t0_bary,
    t0_bary_offset,   
    M_planet,

    # Moon parameters
    r_moon,
    per_moon,
    tau_moon,
    Omega_moon,
    i_moon,
    mass_ratio,

    # Other model parameters
    epochs,
    epoch_duration,
    cadences_per_day,
    epoch_distance,
    supersampling_factor,
    occult_small_threshold,
    hill_sphere_threshold,
    numerical_grid
):

    # Make sure to work with floats. Large values as ints would overflow.
    R_star = float(R_star)
    per_bary = float(per_bary)
    a_bary = float(a_bary)
    r_planet = float(r_planet)
    b_bary = float(b_bary)
    t0_bary = float(t0_bary)
    t0_bary_offset = float(t0_bary_offset)  
    M_planet = float(M_planet)
    r_moon = float(r_moon)
    per_moon = float(per_moon)
    tau_moon = float(tau_moon)
    Omega_moon = float(Omega_moon)
    i_moon = float(i_moon)
    mass_ratio = float(mass_ratio)

    # "Morphological light-curve distortions due to finite integration time"
    # https://ui.adsabs.harvard.edu/abs/2010MNRAS.408.1758K/abstract
    # Data gets smeared over long integration. Relevant for e.g., 30min cadences
    # To counter the effect: Set supersampling_factor = 5 (recommended value)
    # Then, 5x denser in time sampling, and averaging after, approximates effect
    if supersampling_factor < 1:
        print("supersampling_factor must be positive integer")
    supersampled_cadences_per_day = cadences_per_day * int(supersampling_factor)

    # epoch_distance is the fixed constant distance between subsequent data epochs
    # Should be identical to the initial guess of the planetary period
    # The planetary period `per_bary`, however, is a free parameter
    ti_planet_transit_times = np.arange(
        start=t0_bary,
        stop=t0_bary + epoch_distance * epochs,
        step=epoch_distance,
    )

    # Planetary transit duration at b=0 equals the width of the star
    # Formally correct would be: (R_star+r_planet) for the transit duration T1-T4
    # Here, however, we need points where center of planet is on stellar limb
    # https://www.paulanthonywilson.com/exoplanets/exoplanet-detection-techniques/the-exoplanet-transit-method/
    tdur = per_bary / pi * arcsin(1 / a_bary)

    # Correct transit duration based on relative orbital velocity 
    # of circular versus eccentric case
    if ecc_bary > 0:
        tdur /= 1 / sqrt(1 - ecc_bary ** 2) * (1 + ecc_bary * cos(w_bary / 180 * pi))

    # Calculate moon period around planet
    G = 6.67408e-11
    day = 60 * 60 * 24
    a_moon = (G * (M_planet + mass_ratio * M_planet) / (2 * pi / (per_moon * day)) ** 2) ** (1/3)
    a_moon /= R_star

    # t0_bary_offset in [days] ==> convert to x scale (i.e. 0.5 transit dur radius)
    t0_shift_planet = t0_bary_offset / (tdur / 2)

    # arrays of epoch start and end dates [day]
    t_starts = ti_planet_transit_times - epoch_duration / 2
    t_ends = ti_planet_transit_times + epoch_duration / 2
    cadences = int(supersampled_cadences_per_day * epoch_duration)

    # Loop over epochs and stitch together:
    time = np.empty(shape=(epochs, cadences))
    x_bary = np.empty(shape=(epochs, cadences))
    
    xpos = epoch_duration / tdur
    xpos_array = np.linspace(-xpos, xpos, cadences)

    for epoch in range(epochs):  
        time[epoch] = np.linspace(t_starts[epoch], t_ends[epoch], cadences)

        # Push planet following per_bary, which is a free parameter in [days]
        # For reference: Distance between epoch segments is fixed as segment_distance
        # Have to convert to x scale == 0.5 transit duration for stellar radii
        per_shift_planet = ((per_bary - epoch_distance) * epoch) / (tdur / 2)

        x_bary[epoch] = xpos_array - t0_shift_planet - per_shift_planet

    time = time.ravel()
    x_bary = x_bary.ravel()
    
    # Select segment in x_bary array close enough to star so that ellipse CAN transit
    # If the threshold is too generous, it only costs compute.
    # it was too tight with semimajor + 3rp + tdur
    # If the threshold is too tight, it will make the result totally wrong
    # one semimajor axis + half one for bary wobble + transit dur + 2r planet
    # Maximum: A binary system mass_ratio = 1; from numerical experiments 3*a is OK
    transit_threshold_x = 3 * a_moon + 2 * r_planet + 2 * r_moon
    if transit_threshold_x < 2:
        transit_threshold_x = 2

    # Check physical plausibility of a_moon
    # Should be inside [Roche lobe, Hill sphere] plus/minus some user-set margin
    M_star = ((4 * pi**2 / G) * ((a_bary*R_star)**3)) / (per_bary * day) **2
    r_hill = (a_bary) * (M_planet / (3 * M_star)) ** (1/3)
    r_hill_fraction = a_moon / r_hill
    if r_hill_fraction > hill_sphere_threshold:
        unphysical = True
    else:
        unphysical = False

    # Roche
    roche_constant = 1.25992
    roche_limit = (roche_constant * r_planet ** (1/3))

    # Unphysical moon orbit: Keep planet, but put moon at far out of transit position
    if unphysical:  
        bignum = 1e8
        xp = x_bary
        yp = np.full(len(x_bary), b_bary)
        xm = np.full(len(x_bary), bignum)
        ym = xm.copy()
        z_moon = sqrt(xm ** 2 + ym ** 2)
    else:  # valid, physical system
        xm, ym, xp, yp = ellipse(
                a=a_moon,
                per=per_moon,
                tau=tau_moon,
                Omega=Omega_moon,
                i=i_moon,
                time=time,
                transit_threshold_x=transit_threshold_x,
                x_bary=x_bary,
                mass_ratio=mass_ratio,
                b_bary=b_bary
            )

    # Distances of planet and moon from (0,0) = center of star
    z_planet = sqrt(xp ** 2 + yp ** 2)
    z_moon = sqrt(xm ** 2 + ym ** 2)

    # Always use precise Mandel-Agol occultation model for planet 
    flux_planet = occult(zs=z_planet, u1=u1, u2=u2, k=r_planet)

    # For moon transit: User can "set occult_small_threshold > 0"
    if r_moon < occult_small_threshold:
        flux_moon = occult_small(zs=z_moon, k=r_moon, u1=u1, u2=u2)
    else:
        flux_moon = occult(zs=z_moon, k=r_moon, u1=u1, u2=u2)

    # Mutual planet-moon occultations
    flux_moon = eclipse(
            xp, 
            yp,
            xm,
            ym,
            r_planet,
            r_moon,
            flux_moon,
            numerical_grid
        )
    flux_total = 1 - ((1 - flux_planet) + (1 - flux_moon))

    # Supersampling downconversion
    if supersampling_factor > 1:
        flux_planet = resample(flux_planet, supersampling_factor)
        flux_moon = resample(flux_moon, supersampling_factor)
        flux_total = resample(flux_total, supersampling_factor)
        time = resample(time, supersampling_factor)

    return flux_planet, flux_moon, flux_total, xp, yp, xm, ym, time

