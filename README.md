OrbiX — Space Debris Tracking System

 About the Project

OrbitVision is a space debris tracking project designed to process orbital data and predict the movement of objects orbiting Earth. It uses orbital information from CelesTrak and the SGP4 (Simplified General Perturbations 4) model to estimate the positions and velocities of space debris at different time intervals.

The project aims to support the monitoring of space debris and provide a foundation for future close-approach detection, collision-risk analysis, and interactive orbital visualization.

 Project Objectives

* Collect and process orbital data for space debris objects.
* Predict orbital positions and velocities using SGP4 propagation.
* Validate prediction outputs and check data quality.
* Assess the age of orbital elements to identify data that requires review.
* Support future collision-risk analysis and visualization through a unified tracking workflow.

 Technologies Used

* Python — Core programming language.
* Pandas — Data processing and analysis.
* SGP4 — Orbital propagation.
* CelesTrak — Source of orbital element data.
* CSV and JSON — Data storage and exchange.
* Git and GitHub — Version control and collaboration.

 Current Progress

The Orbit & Tracking module has successfully processed orbital data for 580 space debris objects, generating 4,060 predicted state records across seven time offsets: 0, 10, 20, 30, 40, 50, and 60 minutes.

The generated dataset includes position coordinates in kilometres and velocity components in kilometres per second, expressed in the TEME coordinate frame.

The module also includes data validation, orbital element age assessment, and technical reporting.

 Project Modules

The project is organized around five main responsibilities:

1. Data Collection: Collecting, cleaning, and validating orbital data.
2. Orbit & Tracking: Propagating orbital elements and predicting object states.
3. Risk Analysis: Analysing predicted states for potential close approaches and collision risks.
4. Backend Development: Connecting modules and managing data exchange.
5. Frontend & Visualization: Presenting tracking information and analysis through a dashboard.

 Current Outputs

* propagated_debris.csv — Predicted positions and velocities.
* orbital_quality_report.csv — Orbital element age and quality classifications.
* ORBIT_TRACKING_REPORT.md — Summary of methods, results, validation checks, and limitations.

 Limitations

The current tracking module provides propagated orbital states; it does not independently establish collision probabilities or confirm actual collisions. Orbital element age is monitored because older elements may reduce confidence in predicted positions. Independent validation against suitable external ephemerides or observations remains future work.

Position coordinates are expressed in TEME, which is not an Earth-fixed coordinate frame. Additional coordinate transformations and validated close-approach methods may be needed for future applications.

 Future Enhancements

* Develop close-approach detection between tracked objects.
* Introduce more comprehensive collision-risk assessment.
* Build an interactive dashboard for orbital visualization.
* Add automated orbital data updates.
* Improve validation using suitable independent reference data.

Academic Project

OrbitVision is being developed as a collaborative academic project to explore space debris tracking, orbital mechanics, data processing, and visualization using Python.

⸻

OrbitVision — Understanding and tracking the objects orbiting our planet.
