
```markdown
# ANOROC Gravity 
*A String-Inspired Framework for Quantum-Corrected General Relativity*

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXX)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<img src="Media/Diagrams/ANOROC_Schematic.png" width="400" align="right" alt="ANOROC curvature regularization diagram">

## 🔍 Core Theory
The ANOROC (A Nonperturbative Oscillatory-Regulated Curvature) framework modifies Einstein's equations with:

```math
G_{\mu\nu} + (1 - e^{-K/K_{\text{max}}})H_{\mu\nu} + CV_{\mu\nu} = \kappa(1 - e^{-K/K_{\text{max}}})g_{\mu\nu} + T_{\mu\nu}^{\text{(eff)}}
```

**Key Features**:
- 🪐 **Singularity resolution** via string-length cutoff ($K_{\text{max}} = \ell_s^{-4}$)
- ⚛️ **Nonperturbative quantum backreaction** ($V_{\mu\nu}$) from Nambu-Goto action
- 🌌 **Testable predictions** for GWs, colliders, and cosmology

## 🛠️ Repository Structure
```
/ANOROC-Gravity
├── Theory/          # Mathematical foundations
├── Numerics/        # Simulation codes
├── Publications/    # Preprints & papers
├── Media/           # Visual assets
└── CITATION.cff     # Citation metadata
```

## 🚀 Quick Start
1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt  # Python tools
   git clone --recursive https://github.com/einsteintoolkit/einsteintoolkit  # For BH simulations
   ```

2. **Run sample simulation**:
   ```python
   from ANOROC import BlackHoleMerger
   merger = BlackHoleMerger(mass_ratio=2, f_K_cutoff=True)
   merger.simulate()
   ```

## 📚 Documentation
- [Theory Whitepaper](Theory/ANOROC_Whitepaper.pdf)
- [API Reference](Docs/API.md)
- [Tutorial Notebooks](Numerics/Tutorials/)

## 🔬 Testable Predictions
| Phenomenon          | ANOROC Signature                  | Verification Status |
|---------------------|-----------------------------------|---------------------|
| BH Ringdown         | 43 kHz echo modulation           | LIGO O4 (2025)      |
| Early Universe      | CMB B-mode twist at ℓ > 4000     | CMB-S4 (2028)       |
| Particle Collisions | $\sigma \sim e^{-(E/E_c)^2}$     | LHC Run 4           |

## 🤝 How to Contribute
1. Fork the repository
2. Create a feature branch (`git checkout -b new-feature`)
3. Submit a Pull Request

See our [Contribution Guidelines](Docs/CONTRIBUTING.md) for details.

## 📜 Citation
```bibtex
@software{Corona_ANOROC_2024,
  author = {Corona, Javier},
  title = {ANOROC Gravity},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/javiercorona/ANOROC-Gravity}}
}
```

## 📧 Contact
- Javier Corona  
  [javier.corona@email.com](mailto:tinyhouseshop@gmail.com)  
  #!/usr/bin/env python3
import secrets
import hashlib
import hmac
import time
import json
import importlib
from pathlib import Path
from getpass import getpass
from typing import Tuple, Optional, Dict, List, Any, Union
import argparse
import inspect
import sys
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

# Optional dependencies with graceful fallback
try:
    import geocoder
    GPS_AVAILABLE = True
except ImportError:
    GPS_AVAILABLE = False
try:
    import platform
    DEVICE_INFO = True
except ImportError:
    DEVICE_INFO = False
try:
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
try:
    import tpm2_pytss
    TPM_AVAILABLE = True
except ImportError:
    TPM_AVAILABLE = False

# Constants
BUOY_SEED_LENGTH = 32
TIME_QUANTUM = 30  # seconds
DEFAULT_TTL = 3600  # 1 hour
DICE_SIDES = 2**20
PHASE_MODULUS = 64
PLUGINS_DIR = "buoy_plugins"
MAX_PLUGIN_STACK_DEPTH = 10

class BuoyPlugin:
    """Base class for all Buoy plugins"""
    version = "1.0"
    
    def __init__(self, cipher: 'BuoyCipher'):
        self.cipher = cipher
    
    def pre_encrypt(self, plaintext: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Modify message before encryption"""
        return plaintext, context
    
    def post_encrypt(self, ciphertext: bytes, context: Dict[str, Any]) -> bytes:
        """Modify ciphertext after encryption"""
        return ciphertext
    
    def pre_decrypt(self, ciphertext: bytes, context: Dict[str, Any]) -> Tuple[bytes, Dict[str, Any]]:
        """Modify ciphertext before decryption"""
        return ciphertext, context
    
    def post_decrypt(self, plaintext: str, context: Dict[str, Any]) -> str:
        """Modify message after decryption"""
        return plaintext
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return plugin metadata"""
        return {
            "name": self.__class__.__name__,
            "version": self.version,
            "description": inspect.getdoc(self) or ""
        }

class ExpirationPlugin(BuoyPlugin):
    """Adds message expiration capability"""
    version = "1.1"
    
    def pre_encrypt(self, plaintext: str, context: Dict) -> Tuple[str, Dict]:
        ttl = context.get("ttl", DEFAULT_TTL)
        context["expires"] = time.time() + ttl
        return plaintext, context
    
    def post_decrypt(self, plaintext: str, context: Dict) -> str:
        if time.time() > context.get("expires", float('inf')):
            raise ValueError("Message expired")
        return plaintext

class ForwardSecrecyPlugin(BuoyPlugin):
    """Implements forward secrecy using ephemeral keys"""
    version = "1.0"
    
    def __init__(self, cipher):
        super().__init__(cipher)
        if not CRYPTO_AVAILABLE:
            raise ImportError("Cryptography library required for forward secrecy")
        self.private_key = X25519PrivateKey.generate()
        self.peer_public_key = None
    
    def get_public_key(self) -> bytes:
        return self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    def set_peer_public_key(self, peer_public_key: bytes):
        self.peer_public_key = serialization.load_pem_public_key(peer_public_key)
    
    def derive_shared_secret(self) -> str:
        shared_secret = self.private_key.exchange(self.peer_public_key)
        return HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'buoy_fs_key'
        ).derive(shared_secret).hex()

class TPMPlugin(BuoyPlugin):
    """TPM-based secret storage"""
    version = "1.0"
    
    def __init__(self, cipher, sealed_data_path: str = "sealed_buoy_key.bin"):
        super().__init__(cipher)
        if not TPM_AVAILABLE:
            raise ImportError("TPM2_PyTSS library required for TPM support")
        self.sealed_path = Path(sealed_data_path)
    
    def seal_key(self, key: str):
        ctx = tpm2_pytss.ESAPI()
        sealed = ctx.seal(bytes(key, 'utf-8'))
        with open(self.sealed_path, "wb") as f:
            f.write(sealed)
    
    def unseal_key(self) -> str:
        with open(self.sealed_path, "rb") as f:
            sealed_data = f.read()
        ctx = tpm2_pytss.ESAPI()
        return ctx.unseal(sealed_data).decode()

class OnionPlugin(BuoyPlugin):
    """Enables recursive plugin layering"""
    version = "1.0"
    
    def __init__(self, cipher):
        super().__init__(cipher)
        self.stack_depth = 0
    
    def pre_encrypt(self, plaintext: str, context: Dict) -> Tuple[str, Dict]:
        if self.stack_depth >= MAX_PLUGIN_STACK_DEPTH:
            raise RuntimeError("Maximum plugin stack depth exceeded")
        self.stack_depth += 1
        return plaintext, context
    
    def post_decrypt(self, plaintext: str, context: Dict) -> str:
        self.stack_depth -= 1
        return plaintext

class BuoyCipher:
    def __init__(self, shared_secret: str):
        self.shared_secret = shared_secret
        self.plugins: List[BuoyPlugin] = []
        
    def load_plugins(self, plugin_names: List[str]):
        """Load plugins by their module names"""
        for plugin_name in plugin_names:
            try:
                module = importlib.import_module(f"{PLUGINS_DIR}.{plugin_name}")
                plugin_class = getattr(module, plugin_name)
                self.plugins.append(plugin_class(self))
                print(f"Loaded plugin: {plugin_name}")
            except Exception as e:
                print(f"Failed to load plugin {plugin_name}: {str(e)}")
    
    @staticmethod
    def roll_buoy_dice(seed: str, message_len: int, sides: int = DICE_SIDES) -> list:
        rng = secrets.SystemRandom()
        hashed = int(hashlib.sha3_512(seed.encode()).hexdigest(), 16)
        return [(hashed + i * rng.randint(1, sides)) % sides for i in range(message_len)]
    
    @staticmethod
    def buoy_xor(message: str, dice_rolls: list, buoy_phase: int) -> bytes:
        return bytes([(ord(c) ^ ((d >> (buoy_phase % 8)) & 0xFF)) for c, d in zip(message, dice_rolls)])
    
    def get_current_phase(self, additional_entropy: str = "") -> int:
        time_quantum = int(time.time()) // TIME_QUANTUM
        phase_seed = f"{self.shared_secret}{time_quantum}{additional_entropy}"
        return int(hashlib.sha3_256(phase_seed.encode()).hexdigest(), 16) % PHASE_MODULUS
    
    def encrypt(self, plaintext: str, **kwargs) -> Tuple[bytes, int, Dict[str, Any]]:
        context = kwargs
        current_data = plaintext
        
        # Run pre-encrypt plugins
        for plugin in sorted(self.plugins, key=lambda x: x.__class__.__name__):
            current_data, context = plugin.pre_encrypt(current_data, context)
        
        phase = self.get_current_phase(json.dumps(context, sort_keys=True))
        dice_seed = f"{self.shared_secret}{phase}{json.dumps(context, sort_keys=True)}"
        dice = self.roll_buoy_dice(dice_seed, len(current_data))
        ciphertext = self.buoy_xor(current_data, dice, phase)
        
        # Run post-encrypt plugins
        for plugin in sorted(self.plugins, key=lambda x: x.__class__.__name__, reverse=True):
            ciphertext = plugin.post_encrypt(ciphertext, context)
        
        return ciphertext, phase, context
    
    def decrypt(self, ciphertext: bytes, phase: int, **kwargs) -> str:
        context = kwargs
        current_data = ciphertext
        
        # Run pre-decrypt plugins
        for plugin in sorted(self.plugins, key=lambda x: x.__class__.__name__):
            current_data, context = plugin.pre_decrypt(current_data, context)
        
        dice_seed = f"{self.shared_secret}{phase}{json.dumps(context, sort_keys=True)}"
        dice = self.roll_buoy_dice(dice_seed, len(current_data))
        plaintext = self.buoy_xor(current_data.decode('latin1'), dice, phase).decode('utf-8', errors='replace')
        
        # Run post-decrypt plugins
        for plugin in sorted(self.plugins, key=lambda x: x.__class__.__name__, reverse=True):
            plaintext = plugin.post_decrypt(plaintext, context)
        
        return plaintext

class BuoyVisualizer:
    @staticmethod
    def plot_dice_distribution(seed: str, length: int = 1000):
        rolls = BuoyCipher.roll_buoy_dice(seed, length)
        plt.hist(rolls, bins=50)
        plt.title("Dice Roll Distribution")
        plt.show()
    
    @staticmethod
    def plot_phase_drift(secret: str, hours: int = 24):
        phases = []
        now = int(time.time())
        for t in range(now, now + 3600*hours, TIME_QUANTUM):
            phase_seed = f"{secret}{t//TIME_QUANTUM}"
            phases.append(int(hashlib.sha3_256(phase_seed.encode()).hexdigest(), 16) % PHASE_MODULUS)
        
        plt.plot(phases)
        plt.title("Phase Drift Over Time")
        plt.show()

class BuoyAutomation:
    """Headless operations for scripting"""
    @staticmethod
    def encrypt_message(cipher: BuoyCipher, message: str, ttl: int = DEFAULT_TTL) -> str:
        context = {
            "gps": None,
            "device": None,
            "timestamp": time.time(),
            "ttl": ttl
        }
        ciphertext, phase, context = cipher.encrypt(message, **context)
        return json.dumps({
            "ciphertext": ciphertext.hex(),
            "phase": phase,
            "context": context
        })
    
    @staticmethod
    def decrypt_message(cipher: BuoyCipher, message_pkg: str) -> str:
        data = json.loads(message_pkg)
        return cipher.decrypt(
            bytes.fromhex(data["ciphertext"]),
            data["phase"],
            **data.get("context", {})
        )

class BuoyCLI:
    def __init__(self):
        self.cipher = None
        self.gps_cache = None
        self.device_info = self.get_device_info() if DEVICE_INFO else "Unknown"
        self.active_plugins = []
        self.visualizer = BuoyVisualizer()
        self.automation = BuoyAutomation()
    
    @staticmethod
    def get_device_info() -> str:
        system = platform.system()
        machine = platform.machine()
        node = platform.node()
        return f"{system}/{machine}/{node}"
    
    def get_gps_location(self) -> Optional[str]:
        if not GPS_AVAILABLE:
            return None
        
        if self.gps_cache and (time.time() - self.gps_cache[1] < 300):
            return self.gps_cache[0]
            
        try:
            g = geocoder.ip('me')
            if g.ok:
                loc = f"{g.latlng[0]:.4f},{g.latlng[1]:.4f}"
                self.gps_cache = (loc, time.time())
                return loc
        except Exception:
            pass
        return None
    
    def discover_plugins(self) -> List[str]:
        """Find available plugins in the plugins directory"""
        plugin_dir = Path(PLUGINS_DIR)
        if not plugin_dir.exists():
            return []
        
        return [f.stem for f in plugin_dir.glob("*.py") if not f.name.startswith("_")]
    
    def establish_connection(self):
        print("=== Buoy Secure Messaging ===")
        method = input("Establish shared secret via:\n1. Manual entry\n2. Generate new\n3. Asymmetric key exchange\nChoice: ")
        
        if method == "1":
            secret = getpass("Enter shared secret: ")
            self.cipher = BuoyCipher(secret)
        elif method == "2":
            secret = secrets.token_urlsafe(BUOY_SEED_LENGTH)
            print(f"\nGenerated new secret (share securely!):\n{secret}\n")
            self.cipher = BuoyCipher(secret)
        elif method == "3" and CRYPTO_AVAILABLE:
            private_key = ec.generate_private_key(ec.SECP384R1())
            peer_public = input("Enter peer public key (PEM): ")
            peer_key = serialization.load_pem_public_key(peer_public.encode())
            shared_secret = private_key.exchange(ec.ECDH(), peer_key).hex()
            self.cipher = BuoyCipher(shared_secret)
            print("Established shared secret via ECDH")
        else:
            print("Invalid choice or crypto libraries not available")
            return
        
        # Plugin discovery and loading
        available_plugins = self.discover_plugins()
        if available_plugins:
            print("\nAvailable plugins:")
            for i, name in enumerate(available_plugins, 1):
                print(f"{i}. {name}")
            
            choices = input("Select plugins to load (comma-separated numbers or 'all'): ")
            if choices.lower() == 'all':
                selected = available_plugins
            else:
                selected = []
                for choice in choices.split(','):
                    try:
                        idx = int(choice.strip()) - 1
                        if 0 <= idx < len(available_plugins):
                            selected.append(available_plugins[idx])
                    except ValueError:
                        pass
            
            self.cipher.load_plugins(selected)
            self.active_plugins = selected
    
    def send_message(self):
        if not self.cipher:
            print("Error: No secure connection established")
            return
        
        message = input("Enter message: ")
        gps = self.get_gps_location()
        device = self.device_info
        
        context = {
            "gps": gps,
            "device": device,
            "timestamp": time.time(),
            "ttl": DEFAULT_TTL
        }
        
        print("\nEncrypting with:", end=' ')
        if gps:
            print(f"GPS={gps}", end=' ')
        print(f"Device={device}")
        if self.active_plugins:
            print(f"Active plugins: {', '.join(self.active_plugins)}")
        
        ciphertext, phase, context = self.cipher.encrypt(message, **context)
        
        output = {
            "ciphertext": ciphertext.hex(),
            "phase": phase,
            "context": context
        }
        
        print("\nEncrypted Message Package:")
        print(json.dumps(output, indent=2))
    
    def receive_message(self):
        if not self.cipher:
            print("Error: No secure connection established")
            return
        
        try:
            message_pkg = input("Enter message package (JSON): ")
            data = json.loads(message_pkg)
            
            ciphertext = bytes.fromhex(data["ciphertext"])
            phase = data["phase"]
            context = data.get("context", {})
            
            plaintext = self.cipher.decrypt(ciphertext, phase, **context)
            
            print(f"\nDecrypted Message:")
            print(plaintext)
        except Exception as e:
            print(f"Error: {str(e)}")
            current_phase = self.cipher.get_current_phase()
            print(f"Current phase: {current_phase}")

    def run_headless(self, args):
        """Handle headless mode operations"""
        if args.encrypt:
            if not self.cipher:
                self.establish_connection()
            print(self.automation.encrypt_message(self.cipher, args.encrypt, args.ttl))
        elif args.decrypt:
            if not self.cipher:
                self.establish_connection()
            print(self.automation.decrypt_message(self.cipher, args.decrypt))
        elif args.visualize:
            secret = getpass("Enter secret for visualization: ")
            self.visualizer.plot_dice_distribution(secret)
            self.visualizer.plot_phase_drift(secret)

    def run(self):
        parser = argparse.ArgumentParser(description="Buoy Secure Messaging")
        parser.add_argument('--encrypt', help="Encrypt a message (headless mode)")
        parser.add_argument('--decrypt', help="Decrypt a message (headless mode)")
        parser.add_argument('--ttl', type=int, default=DEFAULT_TTL, 
                          help="Message time-to-live in seconds")
        parser.add_argument('--visualize', action='store_true', 
                          help="Show security visualizations")
        parser.add_argument('--plugins', nargs='+', help="Preload specific plugins")
        parser.add_argument('--no-gps', action='store_true', help="Disable GPS features")
        parser.add_argument('--onion', action='store_true', help="Enable onion plugin layering")
        
        args = parser.parse_args()
        
        if args.no_gps:
            global GPS_AVAILABLE
            GPS_AVAILABLE = False
        
        if args.plugins:
            self.cipher = BuoyCipher("temp")  # Temp for plugin loading
            self.cipher.load_plugins(args.plugins)
            self.active_plugins = args.plugins
            self.cipher = None
        
        if args.onion:
            if not self.cipher:
                self.cipher = BuoyCipher("temp")
            self.cipher.plugins.append(OnionPlugin(self.cipher))
            self.active_plugins.append("OnionPlugin")
        
        if args.encrypt or args.decrypt or args.visualize:
            self.run_headless(args)
            return
        
        # Interactive mode
        self.establish_connection()
        
        while True:
            print("\nOptions:")
            print("1. Send message")
            print("2. Receive message")
            print("3. Show current phase")
            print("4. List active plugins")
            print("5. Visualize security")
            print("6. Exit")
            
            choice = input("Choice: ")
            
            if choice == "1":
                self.send_message()
            elif choice == "2":
                self.receive_message()
            elif choice == "3":
                phase = self.cipher.get_current_phase()
                print(f"Current phase: {phase} (changes every {TIME_QUANTUM} seconds)")
            elif choice == "4":
                print("\nActive plugins:")
                for plugin in self.cipher.plugins:
                    meta = plugin.get_metadata()
                    print(f"{meta['name']} v{meta['version']}")
                    print(f"  {meta['description']}")
            elif choice == "5":
                self.visualizer.plot_dice_distribution(self.cipher.shared_secret)
                self.visualizer.plot_phase_drift(self.cipher.shared_secret)
            elif choice == "6":
                print("Wiping session...")
                break
            else:
                print("Invalid choice")

if __name__ == "__main__":
    # Create plugins directory if it doesn't exist
    Path(PLUGINS_DIR).mkdir(exist_ok=True)
    
    try:
        cli = BuoyCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\nSession terminated")
<img width="917" height="131" alt="image" src="https://github.com/user-attachments/assets/2b962258-db1c-4663-87b6-d1a8e4bc4d80" />
<img width="429" height="305" alt="image" src="https://github.com/user-attachments/assets/747601bf-ee3a-4e81-947a-4261108a41bf" />
<img width="440" height="302" alt="image" src="https://github.com/user-attachments/assets/c9c8e3d1-d68a-49a4-9206-b06506d6601b" />
<img width="888" height="327" alt="image" src="https://github.com/user-attachments/assets/c639ae42-de35-4d88-8088-435a8700e7bb" />
<img width="748" height="208" alt="image" src="https://github.com/user-attachments/assets/a18b0d8d-afc7-4d32-b583-feec3511ef33" />
<img width="782" height="198" alt="image" src="https://github.com/user-attachments/assets/af1fa819-f113-4fba-861f-80a193dfbfe4" />
<img width="1003" height="472" alt="image" src="https://github.com/user-attachments/assets/96b4859c-03bf-4abc-af5b-a974dbf2d5f3" />
<img width="878" height="102" alt="image" src="https://github.com/user-attachments/assets/847e3daf-3560-4d07-bda0-32886da2bd16" />
<img width="885" height="125" alt="image" src="https://github.com/user-attachments/assets/8aa6e901-d6d8-40c7-b653-380894840334" />
<img width="839" height="125" alt="image" src="https://github.com/user-attachments/assets/73ba4338-a34b-40bc-86c8-3a31247db3f5" />
<img width="784" height="104" alt="image" src="https://github.com/user-attachments/assets/22808af7-b28f-48fb-8299-22c30b648d5f" />
<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/e3d6459b-e796-4264-bcf2-484233dd3432" />
<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/94963f7b-f7c8-4a0d-aa92-fd25fcd4bec2" />
<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/02456f33-fa40-4218-bde3-61d7ee1047d2" />
<img width="896" height="772" alt="image" src="https://github.com/user-attachments/assets/85e9a18c-4cb2-495f-a045-46cfa0ca5d86" />



![image](https://github.com/user-attachments/assets/9bfe44ef-e9de-4095-a065-bad919a7f36b)

![image](https://github.com/user-attachments/assets/28e22877-7ad5-4221-b2c0-b94187d2c414)

![image](https://github.com/user-attachments/assets/a2e2c27f-5930-49da-b6b1-d3e199fd2eea)

![image](https://github.com/user-attachments/assets/6faf7fd6-1d58-4213-9a08-4b1104adc1cc)

![image](https://github.com/user-attachments/assets/8e3359cf-41b5-4101-987a-c9071c8dec25)

![image](https://github.com/user-attachments/assets/33205c3a-55c3-4d6e-9a9b-58906df19378)

![image](https://github.com/user-attachments/assets/b3ea992a-5e38-4bc9-8d8b-83ce541fdec1)

![image](https://github.com/user-attachments/assets/ceccc9cb-ac99-4476-b60c-04dab6a708a0)

![image](https://github.com/user-attachments/assets/36c3b4bf-4d7a-471d-aaa9-7ac1912915ce)

![image](https://github.com/user-attachments/assets/8a330dd7-c1be-4ce2-ae4a-361542a7f583)

![image](https://github.com/user-attachments/assets/35521885-f0e3-4b91-9dd2-57c5abb3f575)

![image](https://github.com/user-attachments/assets/25f3f761-616c-41c6-b772-abf1907684c6)

![image](https://github.com/user-attachments/assets/afe967be-6538-4fc2-9b8f-773166105e30)

![image](https://github.com/user-attachments/assets/b308617c-d072-4993-a045-85f35b293f7f)

![image](https://github.com/user-attachments/assets/147c4864-4eb0-4a17-b45d-41380b150e8f)

![image](https://github.com/user-attachments/assets/4154c339-d29f-4502-9531-e5ea56cdc53e)

![image](https://github.com/user-attachments/assets/52c6fe28-fc09-4371-90e8-e09d6a334ad5)

![image](https://github.com/user-attachments/assets/4d2a9775-77fc-4c66-a549-25957ee89568)

![image](https://github.com/user-attachments/assets/04ce81b5-4651-41b8-9aca-ee5ff1f30ac2)

![image](https://github.com/user-attachments/assets/cede1c22-4e5c-49ac-96b9-24034f6992c0)

![image](https://github.com/user-attachments/assets/40dda197-118b-44b1-9878-c5c77e586885)

![image](https://github.com/user-attachments/assets/01f19613-626e-4166-93ce-437c8c86ce69)


![image](https://github.com/user-attachments/assets/e0755e26-b4b5-4074-bde1-22f6565dee0a)


![image](https://github.com/user-attachments/assets/597d1d03-e3c4-4355-9528-7597f7ffe634)


![image](https://github.com/user-attachments/assets/1693ec8c-0c3c-441b-8c14-f91b3b2f5754)


![image](https://github.com/user-attachments/assets/e9f29b98-e7f0-42d0-a4ab-2d0bd19370a8)


![image](https://github.com/user-attachments/assets/a29efe80-00b9-47c7-be33-cbda6e04cb34)

![image](https://github.com/user-attachments/assets/b272d523-7d06-46da-985c-bf8c1c230405)

![image](https://github.com/user-attachments/assets/cebc0bf3-70e0-49d3-986a-214e65de38c0)


![image](https://github.com/user-attachments/assets/7e0bc16e-407e-4515-8b44-25fbcad65c08)


![image](https://github.com/user-attachments/assets/c4fa5f7f-53df-4736-88f9-f43a677df364)

![image](https://github.com/user-attachments/assets/60a88b1a-542a-453f-8854-52e48bbc93e6)

![image](https://github.com/user-attachments/assets/60efbfbf-48b7-4bb3-b8c4-1865f6868c64)


![image](https://github.com/user-attachments/assets/cbdde01d-888d-40b0-b1b1-395599c9692b)


![image](https://github.com/user-attachments/assets/4eceaaee-9274-48ee-8c45-1c70834fde1a)


![image](https://github.com/user-attachments/assets/33e3403e-b124-49d0-b054-bdb766b80d17)

![image](https://github.com/user-attachments/assets/bcc035d1-755b-42c1-b835-b4f67bee6b2f)














<img width="2370" height="1538" alt="image" src="https://github.com/user-attachments/assets/46d6a4d3-983c-4c9b-ae7e-e0b60ecb1be3" />





