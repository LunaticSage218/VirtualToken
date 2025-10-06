from utils import derive_key_from_file, generate_address_table, generate_ephemeral_key

# 1) Generate the crypto table from a file and password (defaults to 500 KB)
crypto_table = derive_key_from_file("../tests/sample_pdf.pdf", "password123")
print()

# 2) Generate the 256x256 address table from a 32-byte random seed
seed1, addr_table = generate_address_table(rows=256, cols=256)
print()

# 3) Generate an ephemeral key from the address table and crypto table
seed2, ephemeral_key = generate_ephemeral_key(addr_table, crypto_table, key_length=32)
