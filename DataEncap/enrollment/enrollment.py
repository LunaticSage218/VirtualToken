import os
import time

from DataEncap.protocol_config import size, d, alpha, beta, P, D
from DataEncap.enrollment.enrollmentUtils import enrollmentUtils
from DataEncap.protocolUtils import protocolUtils

def enrollment_protocol(file_path, filename, description, file_extension, external_path=None, external_pw=None):
    """
    Enrollment protocol for a file as described in the Data Encapsulation Whitepaper.
    Stores Kc, Kr, and the file hash externally if a path is provided.

    Args:
        file_path (str): The path to the file to be enrolled.
        filename (str): The name of the file chosen by the user.
        description (str): The description of the file.
        file_extension (str): The file extension.
        external_path (str, optional): Path to external storage (e.g., USB) for saving keys.
        external_pw (str, optional): Password to encrypt keys for external storage.

    Returns:
        (bool, SimpleNamespace or None, str): Tuple indicating success, file info (if successful), and message.
    """
    try:
        # Start timer for the enrollment process
        start_enrollment = time.time()

        pUtils = protocolUtils()
        eUtils = enrollmentUtils()

        # Generate the ephemeral key (CSPRNG) for file encryption.
        l = eUtils.generate_ephemeral_key(size)
        hkey = pUtils.hash_key(l)

        # Generate omega and s for the Kc key
        w, s = eUtils.generate_Kc(size)

        # Encrypt the file using the ephemeral key l
        encrypted_file_path = eUtils.encrypt_file(file_path, l)

        # Generate the CRP data and responses
        f_double_circle = pUtils.generate_f_double_circle(encrypted_file_path, [w, s], d)
        challenges = pUtils.generate_challenges(s, D)
        responses = pUtils.generate_responses(f_double_circle, challenges, alpha, beta, P, d)

        # Use the first response (k0) to encrypt the description
        k0 = responses[0]
        encrypted_description = eUtils.encrypt_description(description, k0)

        # Get the remaining responses and prepare subset
        response = responses[1:]
        subset_of_res = eUtils.subset_of_responses(l, response)

        # Serialize and encode keys (Kc, Kr) and hash of ephemeral key
        kc_encoded, kr_encoded, hkey_encoded = eUtils.serialize_and_encode_keys([w, s], subset_of_res, hkey)

        # If an external path and password are provided, save keys to external storage
        if external_path and external_pw:
            # Use enrollmentUtils helper to save the keys and hash to a binary encrypted file
            eUtils.save_keys_to_usb(kc_encoded, kr_encoded, hkey_encoded, external_path, external_pw)

        # Get the file size (of original file)
        file_size = eUtils.get_file_size(file_path)

        # (Optional) Remove the original file - disabled for now
        # os.remove(file_path)

        # Store file information in a SimpleNamespace object (simulating database record)
        file_info = eUtils.store_file(
            filename, encrypted_file_path, encrypted_description,
            file_extension, kc_encoded, kr_encoded, hkey_encoded, file_size
        )

        # End timer for the enrollment process
        pUtils.log_timing(start_enrollment, "Enrollment process")

        return True, file_info, "File enrolled successfully."

    except Exception as e:
        return False, None, f"Error enrolling file: {e}"