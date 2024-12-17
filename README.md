# HCP-fMRI-Data-Preprocessing-and-Time-Series-Extraction

This repository provides a streamlined workflow for preprocessing Human Connectome Project (HCP) fMRI data and extracting voxel-level time series. The scripts leverage tools such as FSL, wb_command, and Python libraries like nibabel and numpy.

## Features

- Preprocessing:
    - Converts CIFTI files into NIfTI volumes.
    - Applies spatial warping and downsampling.
    - Splits and merges downsampled volumes into 3mm isotropic resolution
- Time-Series Extraction:
    - Extracts voxel-level time series from downsampled fMRI data.
    - Supports left and right hemisphere coordinate mapping.
    - Outputs CSV files containing time series data for each hemisphere.

---

## Dependencies
Ensure the following tools and Python libraries are installed:
- **Tools**:
   - FSL: [Link to FSL](https://fsl.fmrib.ox.ac.uk/)
   - wb_command: Required for fMRI preprocessing.

- **Python Libraries**:
   - nibabel
   - numpy
   - multiprocessing
  
