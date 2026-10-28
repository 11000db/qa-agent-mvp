import sys
from pathlib import Path

# app/ 모듈(core, server 등)을 테스트에서 import 할 수 있도록 경로 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
