import base64
import os
import pickle
import secrets
import hashlib
from types import SimpleNamespace

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from bitarray import bitarray

from DataEncap.protocol_config import g

class enrollmentUtils:
    def break_runs(self, bit_array, n):
        result = bitarray()
        run_length = 0
        for bit in bit_array:
            if bit == 0:
                run_length += 1
                if run_length > n:
                    # insert a 1 to break the run
                    result.append(1)
                    run_length = 0
                else:
                    result.append(0)
            else:
                run_length = 0
                result.append(1)
        return result

    def generate_ephemeral_key(self, size):
        # Generate a random bitarray of length 'size', ensuring no long runs of zeros.
        num_bytes = (size + 7) // 8
        random_bytes = secrets.token_bytes(num_bytes)
        key = bitarray()
        key.frombytes(random_bytes)
        final_key = self.break_runs(key[:size], g)
        return final_key

    def generate_Kc(self, size):
        # Generate two random bitarrays (omega and s) of length 'size'.
        num_bytes = (size + 7) // 8
        omega_bytes = secrets.token_bytes(num_bytes)
        s_bytes = secrets.token_bytes(num_bytes)
        omega = bitarray(); omega.frombytes(omega_bytes)
        s = bitarray(); s.frombytes(s_bytes)
        return self.break_runs(omega[:size], g), self.break_runs(s[:size], g)

    def encrypt_file(self, filename, key):
        # Encrypt the file content with AES-256-CBC using the given key (bitarray or bytes).
        if isinstance(key, bitarray):
            key = key.tobytes()
        if len(key) < 32:
            raise ValueError("Key must be at least 32 bytes long for AES-256.")
        key = key[:32]
        cipher = AES.new(key, AES.MODE_CBC)
        with open(filename, "rb") as file:
            plaintext = file.read()
        padded_plaintext = pad(plaintext, AES.block_size, style="pkcs7")
        ciphertext = cipher.encrypt(padded_plaintext)
        base, ext = os.path.splitext(filename)
        encrypted_filename = base + ".hypn"
        # Write IV + ciphertext to the encrypted file
        with open(encrypted_filename, "wb") as enc_file:
            enc_file.write(cipher.iv)
            enc_file.write(ciphertext)
        return encrypted_filename

    def encrypt_description(self, description, key):
        # Encrypt the text description using AES-256-CBC and return base64 string.
        if isinstance(key, bitarray):
            key = key.tobytes()
        if isinstance(key, str):
            key = key.encode("utf-8")
        if len(key) < 32:
            raise ValueError("Key must be at least 32 bytes long for AES-256.")
        key = key[:32]
        cipher = AES.new(key, AES.MODE_CBC)
        plaintext_bytes = description.encode("utf-8")
        padded_plaintext = pad(plaintext_bytes, AES.block_size, style="pkcs7")
        ciphertext = cipher.encrypt(padded_plaintext)
        encrypted_description = cipher.iv + ciphertext
        return base64.b64encode(encrypted_description).decode("utf-8")

    def encrypt_file_content(self, content, key):
        if isinstance(key, bitarray):
            key = key.tobytes()
        if len(key) < 32:
            raise ValueError("Key must be at least 32 bytes long for AES-256.")
        key = key[:32]
        cipher = AES.new(key, AES.MODE_CBC)
        padded_content = pad(content, AES.block_size, style="pkcs7")
        encrypted_content = cipher.iv + cipher.encrypt(padded_content)
        return encrypted_content

    def linear_congruent_rng(self, alpha, beta, xi, P, d):
        positions = []
        xi_previous = xi
        for _ in range(P):
            xi_next = ((alpha * xi_previous) + beta) % d
            positions.append(xi_next)
            xi_previous = xi_next
        return positions

    def subset_of_responses(self, key, responses):
        if len(key) != len(responses):
            raise ValueError("Key and responses must have the same length.")
        subset_responses = []
        for i, bit in enumerate(key):
            if bit == 1:
                subset_responses.append(responses[i])
        return subset_responses

    def serialize_and_encode_keys(self, kc, kr, hkey):
        kc_encoded = base64.b64encode(pickle.dumps(kc)).decode("utf-8")
        kr_encoded = base64.b64encode(pickle.dumps(kr)).decode("utf-8")
        hkey_encoded = base64.b64encode(pickle.dumps(hkey)).decode("utf-8")
        return kc_encoded, kr_encoded, hkey_encoded

    def get_file_size(self, file_path):
        return os.path.getsize(file_path)

    def store_file(self, filename, file_path, file_description, file_extension,
                   kc, kr, hkey, file_size) -> SimpleNamespace:
        # Build and return a record object with attribute access (simulate DB record)
        record = SimpleNamespace(
            filename=filename,
            file_path=file_path,
            file_description=file_description,
            file_extension=file_extension,
            kc=kc,
            kr=kr,
            hkey=hkey,
            size=file_size
        )
        return record

    def save_keys_to_usb(self, kc_enc, kr_enc, hkey_enc, target_path, password):
        """
        Save the encoded keys and hash to an external file (USB) in a binary serialized format.
        The data is encrypted with AES-256 using the provided password.
        """
        # Determine the full file path for storing keys (use "keys.bin" in the given directory if a directory is provided)
        # If target_path is a directory, use default filename; if it includes a filename, use it.
        path = target_path
        if len(path) == 2 and path[1] == ':' and not path.endswith(os.sep):
            # Normalize Windows drive letter path (e.g., "E:" -> "E:\")
            path = path + os.sep
        if os.path.isdir(path):
            key_file_path = os.path.join(path, "keys.bin")
        else:
            # Use the path directly as a file path (ensure directory exists)
            key_file_path = path
            dir_name = os.path.dirname(key_file_path) or '.'
            if not os.path.isdir(dir_name):
                raise FileNotFoundError(f"Directory '{dir_name}' does not exist")

        # Prepare data dictionary and serialize to bytes
        data = {'kc': kc_enc, 'kr': kr_enc, 'hkey': hkey_enc}
        serialized_bytes = pickle.dumps(data)

        # Derive 32-byte key from password using SHA-256
        aes_key = hashlib.sha256(password.encode('utf-8')).digest()
        # Encrypt the serialized data with AES-256-CBC
        cipher = AES.new(aes_key, AES.MODE_CBC)
        padded_data = pad(serialized_bytes, AES.block_size, style='pkcs7')
        ciphertext = cipher.encrypt(padded_data)
        # Write IV + ciphertext to the key file
        with open(key_file_path, "wb") as key_file:
            key_file.write(cipher.iv)
            key_file.write(ciphertext)
        # Successfully written keys to external file
        return True