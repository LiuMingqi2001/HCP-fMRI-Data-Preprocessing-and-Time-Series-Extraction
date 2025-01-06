import os
import shutil
from zipfile import ZipFile

def make_dirs():
    # Define the paths
    hcp_dir = '/home/test/lmq/data/HCP'
    subject_names_file = '/home/test/lmq/HyperSeg/fMRI_Process/sub_ids'

    # Read subject names from the file
    with open(subject_names_file, 'r') as file:
        subject_names = [line.strip() for line in file.readlines()]

    # Loop through each subject name
    for subject_name in subject_names:
        # Create the subject's directory in HCP
        subject_hcp_dir = os.path.join(hcp_dir, subject_name)
        # Have created before
        # os.makedirs(subject_hcp_dir, exist_ok=True)

        # Create DTI and T1 folders in the subject's directory
        fMRI_dir = os.path.join(subject_hcp_dir, 'fMRI')
        os.makedirs(fMRI_dir, exist_ok=True)


def move_files():
    # Define the paths
    downloads_dir = '/home/test/Downloads'
    hcp_dir = '/home/test/lmq/data/HCP'
    subject_names_file = '/home/test/lmq/HyperSeg/fMRI_Process/sub_ids'

    # Read subject names from the file
    with open(subject_names_file, 'r') as file:
        subject_names = [line.strip() for line in file.readlines()]

    # Loop through each subject name
    for subject_name in subject_names:
        # Construct the source and destination paths for structural and diffusion zip files
        fMRI_zip_src = os.path.join(downloads_dir, f'{subject_name}_3T_rfMRI_REST_fix.zip')
        fMRI_zip_dest = os.path.join(hcp_dir, subject_name, f'{subject_name}_3T_rfMRI_REST_fix.zip')

        # Move the file if it exists in the source
        if not os.path.exists(fMRI_zip_dest):
            print(f'Move files for: {subject_name}')

            # Move the files to their respective folders
            shutil.move(fMRI_zip_src, fMRI_zip_dest)


def unzip():
    hcp_dir = '/home/test/lmq/data/HCP'

    # Loop through each subject directory in the HCP directory
    for subject_name in os.listdir(hcp_dir):
        print(f'Unzip files for: {subject_name}')
        subject_dir = os.path.join(hcp_dir, subject_name)

        # Check if it's a directory
        if os.path.isdir(subject_dir):
            # Construct the paths for structural and diffusion zip files
            fMRI_zip_path = os.path.join(subject_dir, f'{subject_name}_3T_rfMRI_REST_fix.zip')

            # Create directories for extraction
            fMRI_extract_dir = os.path.join(subject_dir, f'{subject_name}_3T_rfMRI_REST_fix')

            os.makedirs(fMRI_extract_dir, exist_ok=True)

            # Extract contents of fMRI zip file
            with ZipFile(fMRI_zip_path, 'r') as fMRI_zip:
                fMRI_zip.extractall(fMRI_extract_dir)

