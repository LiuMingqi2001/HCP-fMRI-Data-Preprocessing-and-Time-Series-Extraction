import os
import subprocess
import logging
import nibabel as nib
import numpy as np
from multiprocessing import Pool, cpu_count

# Set paths
hcp_dir = '/home/test/lmq/data/HCP'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def run_command(command):
    """Run a shell command with error handling."""
    try:
        subprocess.run(command, shell=True, check=True)
        logging.info(f"Command succeeded: {command}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {command}\nError: {e}")


def average_partition_timeseries(func_gii_path, label_gii_path):
    """
    Given a functional GIFTI (.func.gii) and a label GIFTI (.label.gii),
    compute the average time series for each unique label in the data.

    Parameters
    ----------
    func_gii_path : str
        Path to the cortical fMRI time series GIFTI file
        (e.g., 'rfMRI_REST1_LR_cortex_left.func.gii').
    label_gii_path : str
        Path to the label GIFTI file
        (e.g., '100307.L.aparc.a2009s.32k_fs_LR.label.gii').

    Returns
    -------
    partition_ts : dict
        A dictionary where:
          - Keys: unique label IDs (could be float or integer).
          - Values: 1D NumPy arrays of length num_timepoints,
                    representing the average time course across vertices
                    for that label.
    """
    # Load the functional GIFTI image
    func_img = nib.load(func_gii_path)
    # Each darray is one time point, shape: (#vertices,) for each time slice
    # We stack them along axis=1 so final shape becomes (num_vertices, num_timepoints).
    func_data = np.column_stack([darr.data for darr in func_img.darrays])

    # Load the label GIFTI image (assumes one darray with label info)
    label_img = nib.load(label_gii_path)
    labels = label_img.darrays[0].data  # shape: (num_vertices,)

    # Collect unique labels
    unique_labels = np.unique(labels)

    # Prepare a dictionary to store average time series for each label
    partition_ts = {}
    for lb in unique_labels:
        # If you want to exclude label 0
        if lb == 0:
            continue
        # Find all vertices belonging to the current label
        idx = np.where(labels == lb)[0]
        # Compute the average time series for these vertices
        avg_ts = func_data[idx, :].mean(axis=0)
        partition_ts[lb] = avg_ts

    return partition_ts


def save_time_series_dict(timeseries_dict, output_file):
    """
    Saves a dictionary of label -> time series to a CSV file.

    Parameters
    ----------
    timeseries_dict : dict
        Dictionary where the key is a label ID and the value is a 1D NumPy array
        representing the average time course for that label.
    output_file : str
        Full path to the output CSV file.
    """
    if not timeseries_dict:
        logging.warning(f"No time series data found; skipping save to {output_file}")
        return

    # Sort label IDs to have a consistent row ordering
    label_ids = sorted(timeseries_dict.keys())

    # Each row in this matrix will correspond to one label's time series
    # shape: (num_labels, num_timepoints)
    time_series_matrix = np.array([timeseries_dict[lb] for lb in label_ids])

    # Save to CSV
    np.savetxt(output_file, time_series_matrix, delimiter=",")
    logging.info(f"Saved time series to {output_file} with shape {time_series_matrix.shape}")

    # Optional: save the label IDs to a separate file or a header
    # For example:
    # with open(output_file + '.labels.txt', 'w') as f:
    #     for lb in label_ids:
    #         f.write(f"{lb}\n")


def process_cortex(subject_name, direction, phase, subject_dir):
    """Process cortex data for a given subject, direction, and phase."""
    logging.info(f"Processing cortex for subject: {subject_name}, phase: {phase}, direction: {direction}")

    cortex_data_dir = os.path.join(
        subject_dir,
        f'{subject_name}_3T_rfMRI_REST_fix',
        subject_name,
        'MNINonLinear',
        'Results',
        f'rfMRI_REST{phase}_{direction}'
    )
    cortex_data = os.path.join(
        cortex_data_dir,
        f'rfMRI_REST{phase}_{direction}_Atlas_hp2000_clean.dtseries.nii'
    )

    # Check if required files exist
    if not os.path.exists(cortex_data):
        logging.warning(f"Missing cortex data: {cortex_data}")
        return

    # Extract cortical data to GIFTI files
    cortex_left_metric = os.path.join(cortex_data_dir, f'rfMRI_REST{phase}_{direction}_cortex_left.func.gii')
    cortex_right_metric = os.path.join(cortex_data_dir, f'rfMRI_REST{phase}_{direction}_cortex_right.func.gii')

    separate_cmd = (
        f'wb_command -cifti-separate {cortex_data} COLUMN '
        f'-metric CORTEX_LEFT {cortex_left_metric} '
        f'-metric CORTEX_RIGHT {cortex_right_metric}'
    )
    run_command(separate_cmd)

    # Paths to label GIFTI files
    left_label_gii = os.path.join(
        subject_dir,
        f'{subject_name}_3T_Structural_preproc',
        subject_name,
        'MNINonLinear',
        'fsaverage_LR32k',
        f'{subject_name}.L.aparc.a2009s.32k_fs_LR.label.gii'
    )
    right_label_gii = os.path.join(
        subject_dir,
        f'{subject_name}_3T_Structural_preproc',
        subject_name,
        'MNINonLinear',
        'fsaverage_LR32k',
        f'{subject_name}.R.aparc.a2009s.32k_fs_LR.label.gii'
    )

    # Compute average time series for the left hemisphere
    left_partition_timeseries = average_partition_timeseries(cortex_left_metric, left_label_gii)
    logging.info(f"Number of left hemisphere labels: {len(left_partition_timeseries)}")

    # Compute average time series for the right hemisphere
    right_partition_timeseries = average_partition_timeseries(cortex_right_metric, right_label_gii)
    logging.info(f"Number of right hemisphere labels: {len(right_partition_timeseries)}")

    # Save the time series to CSV files (separate for left and right)
    output_dir_sub = os.path.join(subject_dir, 'fMRI', f'phase{phase}_{direction}')
    os.makedirs(output_dir_sub, exist_ok=True)

    left_output_file = os.path.join(output_dir_sub, "voxel_time_series_L_cortex.csv")
    right_output_file = os.path.join(output_dir_sub, "voxel_time_series_R_cortex.csv")

    save_time_series_dict(left_partition_timeseries, left_output_file)
    save_time_series_dict(right_partition_timeseries, right_output_file)


def process_subject(subject_name):
    """Process a single subject."""
    logging.info(f"Processing subject: {subject_name}")
    subject_dir = os.path.join(hcp_dir, subject_name)
    if not os.path.isdir(subject_dir):
        logging.warning(f"{subject_dir} is not a valid directory. Skipping...")
        return

    for direction in ['LR', 'RL']:
        for phase in [1, 2]:
            process_cortex(subject_name, direction, phase, subject_dir)


def main():
    """Main function to process all subjects in parallel."""
    subjects = [name for name in os.listdir(hcp_dir) if os.path.isdir(os.path.join(hcp_dir, name))]
    # subjects = ['100307']  # Uncomment for testing a single subject
    num_workers = 5
    logging.info(f"Starting multiprocessing with {num_workers} workers...")
    with Pool(num_workers) as pool:
        pool.map(process_subject, subjects)


if __name__ == "__main__":
    main()
