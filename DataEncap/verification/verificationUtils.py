import base64
import os
import pickle
from itertools import product

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from bitarray import bitarray

from DataEncap.protocol_config import g
from DataEncap.protocolUtils import protocolUtils
import hashlib  # for key derivation in load_keys_from_usb

class verificationUtils:
    def find_match(self, b1, b2, tolerance):
        if len(b1) != len(b2):
            raise ValueError("Bitarrays must be of the same length.")
        hamming_distance = (b1 ^ b2).count()
        return hamming_distance <= tolerance

    def check_match(self, gamma, i, responses, subres, BER):
        tolerance_bits = int(len(subres) * BER)
        match_idx = []
        no_matches_found = True
        nomatch = []
        for k in range(gamma):
            response_idx = i + k
            if response_idx >= len(responses):
                break
            match = self.find_match(responses[response_idx], subres, tolerance_bits)
            if match:
                match_idx.append(response_idx)
                no_matches_found = False
        if no_matches_found:
            nomatch = [i + g for g in range(gamma) if (i + g) < len(responses)]
        return len(match_idx), match_idx, nomatch

    def error_detection(self, responses, subres, gamma0, BER, num_responses):
        match_idx = []
        collision_idx = []
        ftd_idx = []
        i, j = 0, 0
        gamma = gamma0
        while j < len(subres):
            gamma = min(gamma, num_responses - i)
            match_count, match_pos, nomatch_pos = self.check_match(gamma, i, responses, subres[j], BER)
            if match_count == 0:
                ftd_idx.append(nomatch_pos)
                gamma = 2 * g
            elif match_count == 1:
                match_idx.append(match_pos[0])
                gamma = gamma0
                i = match_pos[0] + 1
            else:
                collision_idx.append(match_pos)
                gamma = gamma0 + (match_pos[-1] - match_pos[0])
                i = match_pos[0] + 1
            j += 1
        return match_idx, collision_idx, ftd_idx

    def merge_matches_with(self, a, b):
        for num in a[:]:
            for sublist in b[:]:
                if num in sublist:
                    index = sublist.index(num)
                    sublist[:] = sublist[:index]
                    if len(sublist) == 1:
                        a.append(sublist[0])
                        b.remove(sublist)
        return a, b

    def get_num_possible_keys(self, collision_idx, ftd_idx, max_keys=1e7):
        combined_list = collision_idx + ftd_idx
        num_possible_keys = 1
        for sublist in combined_list:
            num_possible_keys *= len(sublist)
            if num_possible_keys >= max_keys:
                return int(max_keys)
        return int(num_possible_keys)

    def generate_bitarray(self, indexes, length):
        bit_array = bitarray(length)
        bit_array.setall(0)
        for index in indexes:
            if 0 <= index < length:
                bit_array[index] = 1
        return bit_array

    def generate_possible_keys(self, match_idx, collision_idx, ftd_idx, n, hk):
        pUtils = protocolUtils()
        raw_key = bitarray(self.generate_bitarray(match_idx, n))
        combined_list = collision_idx + ftd_idx
        num_possible_keys = self.get_num_possible_keys(collision_idx, ftd_idx)
        print(f"Number of possible keys: {num_possible_keys}")
        if num_possible_keys > 1e6:
            print(f"Number of possible keys exceeds limit: {num_possible_keys}")
            return raw_key
        for indices_to_flip in product(*combined_list):
            modified_key = raw_key.copy()
            for index in indices_to_flip:
                modified_key[index] = not modified_key[index]
            if pUtils.hash_key(modified_key) == hk:
                print(f"Key successfully recovered!")
                return modified_key
            else:
                print(f"Hash mismatch: {pUtils.hash_key(modified_key)} != {hk}")
        return raw_key

    def retrieve_encryption_keys(self, kc_enc, kr_enc, hkey_enc):
        try:
            kc = pickle.loads(base64.b64decode(kc_enc))
            kr = pickle.loads(base64.b64decode(kr_enc))
            hkey = pickle.loads(base64.b64decode(hkey_enc))
        except (ValueError, pickle.UnpicklingError) as e:
            raise ValueError(f"Error decoding encryption keys: {str(e)}")

        kr_total_bitarrays, kr_total_bits, kr_total_kb = self.calculate_size_of_bitarrays(kr)
        print(f"Size of kr: {kr_total_bitarrays} bitarrays, {kr_total_bits} bits, {kr_total_kb:.2f} KB")
        return kc, kr, hkey

    def calculate_size_of_bitarrays(self, bitarray_list):
        total_bitarrays = len(bitarray_list)
        total_bits = sum(len(bitarray) for bitarray in bitarray_list)
        total_kb = total_bits / 8 / 1024
        return total_bitarrays, total_bits, total_kb

    def decrypt_file(self, encrypted_file_path, key):
        if isinstance(key, bitarray):
            key = key.tobytes()
        if isinstance(key, str):
            key = key.encode("utf-8")
        if len(key) < 32:
            raise ValueError("Key must be at least 32 bytes for AES-256")
        key = key[:32]
        with open(encrypted_file_path, "rb") as file:
            iv = file.read(16)
            ciphertext = file.read()
        if len(iv) != 16:
            raise ValueError("IV must be 16 bytes")
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_content = cipher.decrypt(ciphertext)
        plaintext = unpad(decrypted_content, AES.block_size, style="pkcs7")
        return plaintext

    def decrypt_description(self, encrypted_description, key):
        if isinstance(key, bitarray):
            key = key.tobytes()
        if isinstance(key, str):
            key = key.encode("utf-8")
        if len(key) < 32:
            raise ValueError("Key must be at least 32 bytes for AES-256")
        key = key[:32]
        encrypted_data = base64.b64decode(encrypted_description)
        iv = encrypted_data[:16]; ciphertext = encrypted_data[16:]
        if len(iv) != 16:
            raise ValueError("IV must be 16 bytes")
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_content = cipher.decrypt(ciphertext)
        plaintext_bytes = unpad(decrypted_content, AES.block_size, style="pkcs7")
        plaintext = plaintext_bytes.decode("utf-8")
        return plaintext

    def load_keys_from_usb(self, source_path, password):
        """
        Load and decrypt the keys and hash from an external file (USB).
        Returns a tuple (kc_encoded, kr_encoded, hkey_encoded).
        """
        path = source_path
        if len(path) == 2 and path[1] == ':' and not path.endswith(os.sep):
            path = path + os.sep
        if os.path.isdir(path):
            key_file_path = os.path.join(path, "keys.bin")
        else:
            key_file_path = path

        # Read the encrypted key file (IV + ciphertext)
        with open(key_file_path, "rb") as key_file:
            data = key_file.read()
        iv = data[:16]; ciphertext = data[16:]
        # Derive AES key from the provided password
        aes_key = hashlib.sha256(password.encode('utf-8')).digest()
        # Decrypt and unpad the data
        cipher = AES.new(aes_key, AES.MODE_CBC, iv=iv)
        decrypted_bytes = cipher.decrypt(ciphertext)
        try:
            serialized = unpad(decrypted_bytes, AES.block_size, style='pkcs7')
        except ValueError as e:
            # Wrong password or corrupted file
            raise ValueError("Failed to decrypt keys file: incorrect password or file integrity issue")
        # Deserialize the data dictionary
        data = pickle.loads(serialized)
        kc_enc = data.get('kc')
        kr_enc = data.get('kr')
        hkey_enc = data.get('hkey')
        if not (kc_enc and kr_enc and hkey_enc):
            raise ValueError("Key file is missing expected data")
        return kc_enc, kr_enc, hkey_enc