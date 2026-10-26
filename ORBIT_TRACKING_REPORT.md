# OrbiX — Orbit & Tracking Technical Report

**Report generated:** 2026-10-26 07:34:46 UTC

## 1. Objective

The Orbit & Tracking module retrieves orbital element records,
propagates them using SGP4, and produces predicted positions and
velocities at predefined time offsets.

## 2. Data source and method

- **Orbital data source:** CelesTrak OMM records
- **Propagation method:** SGP4
- **Python library version:** 2.27 (recorded during testing)
- **Prediction offsets:** 0, 10, 20, 30, 40, 50, 60 minutes
- **Coordinate reference frame:** TEME
- **Position units:** kilometres
- **Velocity units:** kilometres per second

## 3. Dataset summary

- **Unique objects:** 580
- **Prediction records:** 4060
- **Objects with complete prediction sequences:** 580
- **Objects with incomplete prediction sequences:** 0
- **Duplicate object/offset records:** 0
- **Rows with finite position and velocity values:** 4060
- **Rows with non-finite position or velocity values:** 0

## 4. Numerical screening

- **Minimum observed geocentric radius:** 6503.69 km
- **Maximum observed geocentric radius:** 7990.18 km
- **Minimum observed speed:** 6.8517 km/s
- **Maximum observed speed:** 7.8338 km/s

These ranges are screening statistics. They do not independently
prove that each orbit is physically accurate.

## 5. Orbital-element quality

- Stale - Review Required: 580

Orbital-element age is a useful indicator of potential uncertainty.
Older elements do not automatically make a prediction invalid.

The quality CSV should be regenerated from the latest propagation
output before using its classifications as final results.

## 6. Reproducibility testing

A reference-consistency test was performed for one object, followed
by a sample test of 20 objects.

- **Objects tested in the sample:** 20
- **Consistency tests passed:** 20
- **Consistency tests failed:** 0
- **Maximum position difference in the sample:** 0 km
- **Maximum velocity difference in the sample:** 0 km/s

The tests re-used the same SGP4 implementation, source orbital
elements, and saved timestamps. They demonstrate computational
reproducibility for the tested records, not independent real-world
orbital accuracy.

## 7. Limitations

1. Predictions depend on the quality and age of the orbital elements.
2. TEME coordinates are not Earth-fixed coordinates or latitude
   and longitude.
3. Numerical checks alone cannot establish real-world accuracy.
4. A predicted position sequence does not, by itself, determine
   collision probability or establish that a collision will occur.
5. Independent validation against suitable external reference
   ephemerides or observations remains future work.

## 8. Handoff to the risk-analysis module

The prediction dataset contains object identifiers, element epochs,
prediction timestamps, time offsets, TEME position coordinates,
and velocity components.

The risk-analysis module can use these outputs as inputs for further
close-approach analysis. Its own methods and assumptions must be
validated separately.
