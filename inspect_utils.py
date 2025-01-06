import os
import nibabel as nib
import numpy as np


def load_and_inspect_file(file_path):
    """
    Load and comprehensively inspect NIfTI (.nii) or GIFTI (.gii) file.

    Args:
        file_path (str): Path to the .nii or .gii file.

    Returns:
        dict: Dictionary containing file metadata and data array if applicable.
    """
    # Extract file name and extension
    file_name = os.path.basename(file_path)
    file_extension = os.path.splitext(file_path)[-1].lower()

    print(f"\n==== Loading File: {file_name} ====")
    print(f"File Path: {file_path}")

    if file_extension in [".nii", ".nii.gz"]:
        # Load NIfTI file
        nii_file = nib.load(file_path)
        header = nii_file.header
        affine = nii_file.affine

        # Extract data
        data_array = nii_file.get_fdata()

        # Print detailed NIfTI information
        print("\n[File Type]: NIfTI (.nii/.nii.gz)")
        print(f"[Dimensions]: {header.get_data_shape()}")
        print(f"[Voxel Size]: {header.get_zooms()} (in mm)")
        print(f"[Data Type]: {header.get_data_dtype()}")
        print(f"[Affine Transformation Matrix]:\n{affine}")
        print(f"[Q-form Matrix]:\n{header.get_qform()}")
        print(f"[S-form Matrix]:\n{header.get_sform()}")
        print(f"[Intent Code]: {header['intent_code']} (Describes data purpose)")
        print(f"[Description]: {header.get('descrip', 'No description available')}")
        print(f"[Slice Timing Information]: {header.get('slice_duration', 'Not available')}")
        print(f"[Data Range]: Min = {np.min(data_array):.6f}, Max = {np.max(data_array):.6f}")

        return {
            "file_type": "NIfTI",
            "header": header,
            "affine": affine,
            "data": data_array
        }

    elif file_extension == ".gii":
        # Load GIFTI file
        gii_data = nib.load(file_path)

        # Extract data arrays
        data_arrays = [darray.data for darray in gii_data.darrays]
        labels = [darray.metadata.get('Name', 'Unknown') for darray in gii_data.darrays]

        # Print detailed GIFTI information
        print("\n[File Type]: GIFTI (.gii)")
        print(f"[Number of Data Arrays]: {len(data_arrays)}")
        for i, (array, label) in enumerate(zip(data_arrays, labels)):
            print(f"\n-- Array {i + 1} --")
            print(f"Label: {label}")
            print(f"Shape: {array.shape}")
            print(f"Data Range: Min = {np.min(array):.6f}, Max = {np.max(array):.6f}")
            print(f"Unique Values: {np.unique(array)[:10]}{'...' if len(np.unique(array)) > 10 else ''}")
            print(f"Array Metadata: {gii_data.darrays[i].metadata}")

        return {
            "file_type": "GIFTI",
            "data_arrays": data_arrays
        }
    else:
        raise ValueError("Unsupported file type. Please provide a .nii, .nii.gz, or .gii file.")


# Example usage
file_path = "/path/to/your/file.nii.gz"  # Replace with the actual file path
try:
    file_info = load_and_inspect_file(file_path)
except ValueError as e:
    print(e)
