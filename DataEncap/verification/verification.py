import time

from DataEncap.protocol_config import d, D, alpha, beta, P, gamma0, BER, size
from DataEncap.protocolUtils import protocolUtils
from DataEncap.verification.verificationUtils import verificationUtils

def verification_protocol(file_info, external_path=None, external_pw=None):
    """
    Recover the keys and run the verification protocol to decrypt the file and verify integrity.

    Args:
        file_info: SimpleNamespace or dict containing file information (including encoded keys).
        external_path (str, optional): Path to external storage for retrieving keys.
        external_pw (str, optional): Password to decrypt the stored keys.

    Returns:
        (bytes or None, str or None): The decrypted file bytes and the decrypted description (or None on failure).
    """
    try:
        start_time = time.time()
        pUtils = protocolUtils()
        vUtils = verificationUtils()

        # Retrieve keys from external file if provided, otherwise use stored values
        if external_path and external_pw:
            kc_enc, kr_enc, hkey_enc = vUtils.load_keys_from_usb(external_path, external_pw)
        else:
            kc_enc, kr_enc, hkey_enc = file_info.kc, file_info.kr, file_info.hkey

        # Decode the keys and hash to their original forms
        kc, kr, hkey = vUtils.retrieve_encryption_keys(kc_enc, kr_enc, hkey_enc)

        # Reconstruct CRP data and responses using Kc
        f_double_circle = pUtils.generate_f_double_circle(file_info.file_path, [kc[0], kc[1]], d)
        challenges = pUtils.generate_challenges(kc[1], D)
        responses = pUtils.generate_responses(f_double_circle, challenges, alpha, beta, P, d)

        # Use the first response (k0) to decrypt the description
        k0 = responses[0]
        decrypted_description = vUtils.decrypt_description(file_info.file_description, k0)

        # Use remaining responses for error detection and key recovery
        response = responses[1:]
        match_index, collision_index, ftd_index = vUtils.error_detection(response, kr, gamma0, BER, size)
        updated_matches_index, updated_collision_index = vUtils.merge_matches_with(match_index, collision_index)
        updated_matches_index, updated_ftd_index = vUtils.merge_matches_with(updated_matches_index, ftd_index)

        # Generate possible key from matches/collisions and verify against hash
        l = vUtils.generate_possible_keys(updated_matches_index, updated_collision_index, updated_ftd_index, size, hkey)

        # Decrypt the file using the recovered key
        decrypted_file = vUtils.decrypt_file(file_info.file_path, l)

        # End time for the verification process
        pUtils.log_timing(start_time, "Verification process")

        return decrypted_file, decrypted_description

    except Exception as e:
        print(f"Verification protocol failed: {e}")
        return None, None