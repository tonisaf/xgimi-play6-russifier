"""Run the actual Java ledger against failure-injecting OEM ports, without Android."""
from pathlib import Path
import os,subprocess,tempfile

base=Path(__file__).resolve().parent
java=Path(os.environ.get('JAVA_HOME','C:/android/jdk'))/'bin'
with tempfile.TemporaryDirectory(prefix='remote-registry-test-') as directory:
    subprocess.run([str(java/'javac.exe'),'-d',directory,str(base/'app/src/com/beam/remote/KeyRegistry.java'),str(base/'tests/RegistryTest.java')],check=True)
    subprocess.run([str(java/'java.exe'),'-cp',directory,'com.beam.remote.RegistryTest'],check=True)
