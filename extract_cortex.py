# import os
# import subprocess
# import logging
# from multiprocessing import Pool, cpu_count
#
# # Set paths
# hcp_dir = '/home/test/lmq/data/HCP'
# parcellation_file = '/home/test/lmq/data/Glasser_atlas.dlabel.nii'  # Replace with your atlas path
# output_dir = '/home/test/lmq/output'  # Directory to save outputs
#
# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#
#
# def run_command(command):
#     """Run a shell command with error handling."""
#     try:
#         subprocess.run(command, shell=True, check=True)
#         logging.info(f"Command succeeded: {command}")
#     except subprocess.CalledProcessError as e:
#         logging.error(f"Command failed: {command}\nError: {e}")
#
#
# def process_cortex(subject_name, direction, phase, subject_dir):
#     """Process cortex data for a given subject, direction, and phase."""
#     cortex_data_dir = os.path.join(
#         subject_dir,
#         f'{subject_name}_3T_rfMRI_REST_fix',
#         subject_name,
#         'MNINonLinear',
#         'Results',
#         f'rfMRI_REST{phase}_{direction}'
#     )
#     cortex_data = os.path.join(
#         cortex_data_dir,
#         f'rfMRI_REST{phase}_{direction}_Atlas_hp2000_clean.dtseries.nii'
#     )
#
#     # Check if cortex data exists
#     if not os.path.exists(cortex_data):
#         logging.warning(f"Missing cortex data: {cortex_data}")
#         return
#
#     # Step 1: Alignment
#     warped_output = os.path.join(cortex_data_dir, f'rfMRI_REST{phase}_{direction}_aligned.nii.gz')
#     warp_cmd = (
#         f'applywarp --ref={os.path.join(subject_dir, "T1", "T1_3mm.nii.gz")} '
#         f'--in={cortex_data} '
#         f'--warp={os.path.join(subject_dir, f"{subject_name}_3T_Structural_preproc", subject_name, "MNINonLinear", "xfms", "standard2acpc_dc.nii.gz")} '
#         f'--out={warped_output}'
#     )
#     run_command(warp_cmd)
#
#     # Step 2: Downsampling (Split -> Downsample -> Merge)
#     downsampled_output = os.path.join(cortex_data_dir, f'rfMRI_REST{phase}_{direction}_downsampled_3mm.nii.gz')
#     downsample_split_merge(warped_output, downsampled_output, cortex_data_dir)
#
#     # Step 3: Time Series Extraction
#     time_series_output = os.path.join(
#         output_dir, f'{subject_name}_REST{phase}_{direction}_time_series.csv'
#     )
#     os.makedirs(output_dir, exist_ok=True)
#     extract_time_series(downsampled_output, time_series_output)
#
#     # Clean up intermediate files
#     os.remove(warped_output)
#     logging.info(f"Cleaned up intermediate file: {warped_output}")
#
#
# def downsample_split_merge(input_file, output_file, work_dir):
#     """Downsample by splitting the file into volumes, processing separately, and merging."""
#     # Split into volumes
#     run_command(f'fslsplit {input_file} {work_dir}/volume_ -t')
#
#     # Get list of split volumes
#     volumes = [f for f in os.listdir(work_dir) if f.startswith('volume_') and f.endswith('.nii.gz')]
#
#     # Downsample each volume
#     for vol in volumes:
#         vol_path = os.path.join(work_dir, vol)
#         downsampled_vol = os.path.join(work_dir, f'downsampled_{vol}')
#         downsample_cmd = (
#             f'flirt -ref {vol_path} -in {vol_path} -out {downsampled_vol} '
#             f'-applyisoxfm 3 -interp nearestneighbour'
#         )
#         run_command(downsample_cmd)
#
#     # Merge downsampled volumes back into a single file
#     downsampled_volumes = ' '.join([
#         os.path.join(work_dir, f'downsampled_{vol}') for vol in volumes
#     ])
#     run_command(f'fslmerge -t {output_file} {downsampled_volumes}')
#
#     # Clean up intermediate files
#     for vol in volumes:
#         os.remove(os.path.join(work_dir, vol))
#         os.remove(os.path.join(work_dir, f'downsampled_{vol}'))
#         logging.info(f"Cleaned up intermediate files for {vol}")
#
#
# def extract_time_series(fMRI_data, output_file):
#     """Extract time series for cortical regions using parcellation."""
#     run_command(f'wb_command -cifti-parcellate {fMRI_data} {parcellation_file} COLUMN {output_file} -method MEAN')
#
#
# def process_subject(subject_name):
#     """Process a single subject."""
#     logging.info(f"Processing subject: {subject_name}")
#     subject_dir = os.path.join(hcp_dir, subject_name)
#     if not os.path.isdir(subject_dir):
#         logging.warning(f"{subject_dir} is not a valid directory. Skipping...")
#         return
#
#     for direction in ['LR', 'RL']:
#         for phase in [1, 2]:
#             process_cortex(subject_name, direction, phase, subject_dir)
#
#
# def main():
#     """Main function to process all subjects in parallel."""
#     subjects = [name for name in os.listdir(hcp_dir) if os.path.isdir(os.path.join(hcp_dir, name))]
#
#     # Use multiprocessing pool to process subjects in parallel
#     num_workers = min(cpu_count(), len(subjects))
#     logging.info(f"Starting multiprocessing with {num_workers} workers...")
#
#     with Pool(num_workers) as pool:
#         pool.map(process_subject, subjects)
#
#
# if __name__ == "__main__":
#     main()


import os
import subprocess
import logging
import numpy as np
from multiprocessing import Pool, cpu_count

# Set paths
hcp_dir = '/home/test/lmq/data/HCP'
output_dir = '/home/test/lmq/output'  # Directory to save outputs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def run_command(command):
    """Run a shell command with error handling."""
    try:
        subprocess.run(command, shell=True, check=True)
        logging.info(f"Command succeeded: {command}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {command}\nError: {e}")


def process_cortex(subject_name, direction, phase, subject_dir):
    """Process cortex data for a given subject, direction, and phase."""
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

    # Extract time series and save to files
    save_time_series(cortex_left_metric, subject_dir, phase, direction, "left", subject_name)
    save_time_series(cortex_right_metric, subject_dir, phase, direction, "right", subject_name)

    # Clean up intermediate files
    os.remove(cortex_left_metric)
    os.remove(cortex_right_metric)
    logging.info(f"Cleaned up intermediate files for {subject_name}, phase {phase}, direction {direction}")


def save_time_series(metric_file, subject_dir, phase, direction, hemisphere, subject_name):
    """Extract and save time series for a given hemisphere."""
    # Use wb_command to extract the time series
    tmp_output = f"/tmp/tmp_{hemisphere}_time_series.txt"
    wmparc_file = f'/home/test/lmq/data/HCP/{subject_name}/{subject_name}_3T_Structural_preproc/{subject_name}/MNINonLinear/wmparc.nii.gz'
    run_command(f'wb_command -metric-reduce {metric_file} MEAN {tmp_output}')

    # Load the result into NumPy
    time_series = np.loadtxt(tmp_output)

    # Prepare the output directory and file
    output_dir = os.path.join(subject_dir, 'fMRI', f'phase{phase}_{direction}')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"voxel_time_series_{hemisphere}.csv")

    # Save the time series as a CSV file
    np.savetxt(output_file, time_series, delimiter=",")
    logging.info(f"Saved time series for {hemisphere} hemisphere, phase {phase}, direction {direction} to {output_file}")

    # Remove temporary file
    os.remove(tmp_output)


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
    num_workers = min(cpu_count(), len(subjects))
    logging.info(f"Starting multiprocessing with {num_workers} workers...")
    with Pool(num_workers) as pool:
        pool.map(process_subject, subjects)


if __name__ == "__main__":
    main()






