"""Fetch declared dependencies from Maven Central; verify exact SHA-256."""
from pathlib import Path
import hashlib,urllib.request
ROOT=Path(__file__).resolve().parents[1]
ARTIFACTS=[('neural_app/java_library/dependencies/org.jfree.svg-5.0.7.jar', 'org/jfree/org.jfree.svg/5.0.7/org.jfree.svg-5.0.7.jar', '428aa721651062e275842648b5bf4b023c9f2187c8a9113d6eea8bed2cb4d152'), ('vendor-javafx/javafx-base-21.0.13-win.jar', 'org/openjfx/javafx-base/21.0.13/javafx-base-21.0.13-win.jar', '7a9a3dd9e7ab445ae751f50d9feddd550056ef5c267faf145512686a58f61651'), ('vendor-javafx/javafx-controls-21.0.13-win.jar', 'org/openjfx/javafx-controls/21.0.13/javafx-controls-21.0.13-win.jar', '2fbf566741cba2de8dd886209cd8ba497995b51d2371441fc4d17e0a22ba6e03'), ('vendor-javafx/javafx-fxml-21.0.13-win.jar', 'org/openjfx/javafx-fxml/21.0.13/javafx-fxml-21.0.13-win.jar', '67d4ad011c60e770d23369796669d5ab28075a8cdc91f792c28d97ebb96b25ef'), ('vendor-javafx/javafx-graphics-21.0.13-win.jar', 'org/openjfx/javafx-graphics/21.0.13/javafx-graphics-21.0.13-win.jar', '42d59a74a1d0fcfae03ecd440db185e76f08b7a65dfc870a0a7eb5bad6d8f2d7'), ('neural_app/java_library/dependencies/org.jfree.svg-5.0.7-sources.jar', 'org/jfree/org.jfree.svg/5.0.7/org.jfree.svg-5.0.7-sources.jar', '57a2d4e7368210af1946a7263e261226bd317c5b8911dd10cdf61b9b5d7e17dd'), ('neural_app/java_library/dependencies/org.jfree.svg-5.0.7.pom', 'org/jfree/org.jfree.svg/5.0.7/org.jfree.svg-5.0.7.pom', '2db2a0e00eafb0f2a48a060d928b6fad7ce828056abc19745b779cc7a9beda0b')]
for relative,url_path,digest in ARTIFACTS:
 path=ROOT/relative
 if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==digest:continue
 raw=urllib.request.urlopen('https://repo.maven.apache.org/maven2/'+url_path,timeout=60).read()
 if hashlib.sha256(raw).hexdigest()!=digest:raise RuntimeError('Dependency checksum mismatch: '+relative)
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);print('Ready:',relative)
