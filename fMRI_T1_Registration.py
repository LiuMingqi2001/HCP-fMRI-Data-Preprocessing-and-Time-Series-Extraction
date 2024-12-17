import os
import subprocess
import logging
from multiprocessing import Pool, cpu_count

# Set the root directory for HCP data
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


def process_fMRI(subject_name, direction, phase, subject_dir):
    """Process fMRI data for a given subject, direction, and phase."""
    fMRI_data_dir = os.path.join(
        subject_dir,
        f'{subject_name}_3T_rfMRI_REST_fix',
        subject_name,
        'MNINonLinear',
        'Results',
        f'rfMRI_REST{phase}_{direction}'
    )
    fMRI_data = os.path.join(
        fMRI_data_dir,
        f'rfMRI_REST{phase}_{direction}_Atlas_hp2000_clean.dtseries.nii'
    )

    # Check if fMRI data exists
    if not os.path.exists(fMRI_data):
        logging.warning(f"Missing fMRI data: {fMRI_data}")
        return

    # Separate the CIFTI file into volume
    volume_file = os.path.join(fMRI_data_dir, f'rfMRI_REST{phase}_{direction}.nii.gz')
    run_command(f'wb_command -cifti-separate {fMRI_data} COLUMN -volume-all {volume_file}')

    # Apply warp
    warped_output = os.path.join(fMRI_data_dir, 'Atlas_in_T1w_all.nii.gz')
    warp_cmd = (
        f'applywarp --ref={os.path.join(subject_dir, "T1", "T1_3mm.nii.gz")} '
        f'--in={volume_file} '
        f'--warp={os.path.join(subject_dir, f"{subject_name}_3T_Structural_preproc", subject_name, "MNINonLinear", "xfms", "standard2acpc_dc.nii.gz")} '
        f'--out={warped_output}'
    )
    run_command(warp_cmd)

    # Split the warped file into volumes
    run_command(f'fslsplit {warped_output} {fMRI_data_dir}/volume_ -t')

    # Downsample each volume
    volumes = [f for f in os.listdir(fMRI_data_dir) if f.startswith('volume_') and f.endswith('.nii.gz')]
    for vol in volumes:
        vol_path = os.path.join(fMRI_data_dir, vol)
        downsampled_vol = os.path.join(fMRI_data_dir, f'downsampled_{vol}')
        downsample_cmd = (
            f'flirt -ref {vol_path} -in {vol_path} -o {downsampled_vol} '
            f'-applyisoxfm 3 -interp nearestneighbour'
        )
        run_command(downsample_cmd)

    # # Merge the downsampled volumes back into a single file
    # downsampled_volumes = ' '.join([
    #     os.path.join(fMRI_data_dir, f'downsampled_{vol}')
    #     for vol in volumes
    # ])
    # merged_output = os.path.join(fMRI_data_dir, 'fMRI_downsampled_3mm.nii.gz')
    # run_command(f'fslmerge -t {merged_output} {downsampled_volumes}')
    # Generate the list of downsampled volumes
    downsampled_file_list = os.path.join(fMRI_data_dir, 'downsampled_file_list.txt')

    # Write all file paths to a text file
    with open(downsampled_file_list, 'w') as f:
        for vol in volumes:
            f.write(f"{os.path.join(fMRI_data_dir, f'downsampled_{vol}')}\n")

    # Output file
    merged_output = os.path.join(fMRI_data_dir, 'fMRI_downsampled_3mm.nii.gz')

    run_command(f'fslmerge -t {merged_output} $(cat {downsampled_file_list})')

    # Clean up intermediate files
    for vol in volumes:
        os.remove(os.path.join(fMRI_data_dir, vol))
        os.remove(os.path.join(fMRI_data_dir, f'downsampled_{vol}'))
        logging.info(f"Cleaned up intermediate file: {vol}")


def process_subject(subject_name):
    """Process a single subject."""
    logging.info(f"Processing subject: {subject_name}")
    subject_dir = os.path.join(hcp_dir, subject_name)
    if not os.path.isdir(subject_dir):
        logging.warning(f"{subject_dir} is not a valid directory. Skipping...")
        return

    for direction in ['LR', 'RL']:
        for phase in [1, 2]:
            process_fMRI(subject_name, direction, phase, subject_dir)


def main():
    """Main function to process all subjects in parallel."""
    subjects = [name for name in os.listdir(hcp_dir) if os.path.isdir(os.path.join(hcp_dir, name))]

    # Use multiprocessing pool to process subjects in parallel
    num_workers = 5
    logging.info(f"Starting multiprocessing with {num_workers} workers...")

    with Pool(num_workers) as pool:
        pool.map(process_subject, subjects)


if __name__ == "__main__":
    main()
