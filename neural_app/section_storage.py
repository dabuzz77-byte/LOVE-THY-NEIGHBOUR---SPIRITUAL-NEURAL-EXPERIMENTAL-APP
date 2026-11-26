"""Create an app-owned section directory without resetting retained model files."""
import shutil,sqlite3
from pathlib import Path
from .runtime import ROOT

def section_data(runtime,ident,seed=None):
 target=runtime.data/'sections'/ident
 source=Path(seed) if seed else ROOT/'data'/'sections'/ident
 target.mkdir(parents=True,exist_ok=True)
 if source.resolve()==target.resolve() or not source.is_dir():return target
 for entry in source.rglob('*'):
  if not entry.is_file() or any(p in ('__pycache__','work') for p in entry.relative_to(source).parts) or entry.name.endswith(('-wal','-shm','.tmp')):continue
  destination=target/entry.relative_to(source)
  if destination.exists():continue
  destination.parent.mkdir(parents=True,exist_ok=True)
  if entry.suffix in ('.sqlite3','.sqlite','.db'):
   # Consistent snapshots include committed WAL contents; never copy live WAL files.
   with sqlite3.connect(entry.as_uri()+'?mode=ro',uri=True) as previous,sqlite3.connect(destination) as current:previous.backup(current)
  else:shutil.copy2(entry,destination)
 return target
