# NFT Gen2 Demo

A tiny Flask web app that demonstrates three flows around secure file handling and NFT key generation:

1) **Enroll** a file: hash + encrypt the file and description, optionally store keys on an external drive  
2) **Decrypt** the previously enrolled file and recover the description  
3) **NFT**: derive an ephemeral NFT key from the decrypted file and a user password

---

## Requirements

- Python 3.10+  
- `pip` (and optionally `venv`)  
- The repository’s `requirements.txt` at the project root

---

## Quickstart

### 1) Create & activate a virtual environment

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Run the app **from the repository root**
```bash
python app/app.py
```

Open: http://localhost:8000

> **Why run from the repo root?** The app imports local packages like `DataEncap` and `NFT`. Running from the root ensures Python can resolve those imports.

---

## How to Use the UI

1) **Enroll**
   - Upload a file and (optionally) enter a description.
   - (Optional) Provide:
     - **USB Path**: path to an external drive/folder to store key material
     - **Storage Password**: password used to protect stored key material
   - Submit **Enroll**. You should see progress messages and where the encrypted file is saved.

2) **Decrypt**
   - Click **Decrypt** to reconstruct keys and decrypt the previously enrolled file.
   - The decrypted file is written to `app/uploads/decrypted_<originalname>`.
   - The recovered description is shown in the UI.

3) **NFT**
   - After a successful decrypt, enter a password and click **NFT**.
   - The app derives an ephemeral NFT key and displays:
     - R1 (address table seed)
     - R2 (ephemeral key generation seed)
     - Ephemeral NFT key (hex)

4) **Restart**
   - Click **Restart** to clear session state and begin a new run.

---

## Project Structure (minimal)

```
repo-root/
├─ app/
│  ├─ app.py            # Flask app entrypoint
│  ├─ templates/
│  │  └─ index.html     # UI template (expects standard Flask layout)
│  └─ uploads/          # Created automatically; stores encrypted/decrypted files
├─ DataEncap/
│  ├─ enrollment/...
│  └─ verification/...
├─ NFT/
│  └─ protocol.py       # NFT key derivation implementation
├─ requirements.txt
└─ README.md            # (this file)
```

> See `NFT/README.md` for additional details specific to the NFT module.

---

## Configuration Notes

- **Uploads**: Files are stored under `app/uploads/` (created if missing).
- **Host/Port**: The app runs on `localhost:8000` in debug mode as configured in `app.py`.

---

## Troubleshooting

- **`ModuleNotFoundError: No module named 'DataEncap'`**  
  Run the app **from the repository root**:
  ```bash
  python app/app.py
  ```
  (or set `PYTHONPATH` to the repo root before running).

- **Permission errors when writing to USB path**  
  Ensure the provided directory exists and is writable.

- **Nothing happens on Decrypt/NFT**  
  The flows depend on session state:
  - You must **Enroll** before **Decrypt**.
  - You must **Decrypt** before **NFT**.

---
