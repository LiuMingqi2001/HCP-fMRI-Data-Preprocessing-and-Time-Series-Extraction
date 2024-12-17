import os
import numpy as np
import nibabel as nib

# Define the base directory
data_directory = "/home/test/lmq/data/HCP"

# Loop through each subject directory in the HCP directory
for subject_name in os.listdir(data_directory):
    subject_dir = os.path.join(data_directory, subject_name)

    # Check if it's a directory
    if os.path.isdir(subject_dir):
        print(f"Processing subject: {subject_name}")

        # Loop through phases [1, 2] and directions ['RL', 'LR']
        for phase in [1, 2]:
            for direction in ['RL', 'LR']:
                # Path to the fMRI data
                fMRI_file = os.path.join(
                    subject_dir,
                    f'{subject_name}_3T_rfMRI_REST_fix',
                    f'{subject_name}',
                    'MNINonLinear',
                    'Results',
                    f'rfMRI_REST{phase}_{direction}',
                    'fMRI_downsampled_3mm.nii.gz'
                )

                # Check if the fMRI file exists
                if not os.path.exists(fMRI_file):
                    print(f"fMRI file not found: {fMRI_file}. Skipping...")
                    continue

                # Load the fMRI data
                fMRI_img = nib.load(fMRI_file)
                fMRI_data = fMRI_img.get_fdata()  # Shape: (x, y, z, time)

                # Process both L and R coordinates
                for hemisphere in ['L', 'R']:
                    print(f"Processing {hemisphere} hemisphere for phase {phase}, direction {direction}")

                    # Path to the coordinates file
                    coor_path = os.path.join(
                        subject_dir,
                        f"probtrackx_{hemisphere}_omatrix2",
                        "coords_for_fdt_matrix2"
                    )

                    # Check if the coordinates file exists
                    if not os.path.exists(coor_path):
                        print(f"Coordinates file not found: {coor_path}. Skipping...")
                        continue

                    # Load the voxel coordinates
                    coordinates = np.loadtxt(coor_path)
                    x_coordinates = coordinates[:, 0].astype(int)
                    y_coordinates = coordinates[:, 1].astype(int)
                    z_coordinates = coordinates[:, 2].astype(int)

                    # Extract time series for each coordinate
                    subject_coords = list(zip(x_coordinates, y_coordinates, z_coordinates))
                    time_series = []

                    for coord in subject_coords:
                        x, y, z = coord
                        try:
                            voxel_time_series = fMRI_data[x, y, z, :]  # Extract the time series for the voxel
                            time_series.append(voxel_time_series)
                        except IndexError:
                            print(f"Coordinate {coord} is out of bounds for subject {subject_name}. Skipping...")
                            continue

                    # Convert to a NumPy array (optional)
                    time_series_array = np.array(time_series)  # Shape: (num_voxels, time_points)

                    # Save the time series to a CSV file
                    output_dir = os.path.join(subject_dir, 'fMRI', f'phase{phase}_{direction}')
                    os.makedirs(output_dir, exist_ok=True)
                    output_file = os.path.join(output_dir, f"voxel_time_series_{hemisphere}.csv")
                    np.savetxt(output_file, time_series_array, delimiter=",")
                    print(f"Saved time series for {hemisphere} hemisphere, phase {phase}, direction {direction} to {output_file}")
