# FAS_APP

공개 Face Anti-Spoofing 모델을 같은 입력으로 비교하는 웹 앱입니다. 이미지 1장 또는 여러 장을 올리고, 특정 모델만 선택하거나 `All Models`로 한 번에 실행할 수 있습니다.

## 핵심 기능
- 단일 이미지 / 다중 이미지 업로드
- 개별 모델 선택 / `All Models` 실행
- 이미지 하단 결과 오버레이
- 결과 테이블과 CSV export
- `3D 마스크 특화 FAS`와 `일반 FAS (물리·디지털 공격)` 모델 비교

## 현재 실제 연동 모델
| Model ID | Track | Paper | Year | Runtime |
| --- | --- | --- | --- | --- |
| `biometric_lab_transformer` | 3D 마스크 특화 FAS | model card 기준 공개 모델 | 2025 기준 | 실제 checkpoint |
| `cvpr2024_mobilenet_v3_small` | 일반 FAS | `Joint Physical-Digital Facial Attack Detection Via Simulating Spoofing Clues` | 2024 | 실제 checkpoint |
| `stdn_eccv2020` | 일반 FAS | `On Disentangling Spoof Trace for Generic Face Anti-Spoofing` | 2020 | 실제 checkpoint + 공식 `test.py` |
| `iadg_cvpr2023` | 일반 FAS | `Instance-Aware Domain Generalization for Face Anti-Spoofing` | 2023 | 실제 checkpoint + 단일 이미지 wrapper |

## 중요한 주의사항
- `cvpr2024_mobilenet_v3_small`는 3D 마스크 전용 모델이 아닙니다.
- `biometric_lab_transformer`는 원래 시계열 기반이라 단일 이미지에서는 프레임 복제 방식으로 동작합니다.
- `stdn_eccv2020`는 사용자가 준비한 `face crop 된 이미지`를 넣는 것을 전제로 합니다.
- `iadg_cvpr2023`는 공식 `test.py`를 그대로 쓰는 대신, 공식 checkpoint와 설정 규칙을 반영한 단일 이미지 wrapper로 동작합니다.
- `All Models`는 현재 `ready` 상태의 실제 실행 가능 모델만 돌립니다.

## 디렉토리 구조
```text
FAS_APP/
  backend/
    app/
    assets/
    requirements.txt
  frontend/
    static/
  docs/
  third_party/
  README.md
```

## 빠른 시작
### 1. 프로젝트 루트로 이동
```bash
cd /home/mmss9402/source/suprema/FAS_APP
```

### 2. 메인 가상환경 생성 및 활성화
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 백엔드 의존성 설치
```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 4. 체크포인트와 외부 저장소 준비
아래 `모델 준비` 섹션을 따라 실제 checkpoint와 외부 저장소를 배치합니다.

### 5. 서버 실행
```bash
cd /home/mmss9402/source/suprema/FAS_APP/backend
STDN_PYTHON_BIN="/home/mmss9402/source/suprema/FAS_APP/.stdn_py37/bin/python" \
"/home/mmss9402/source/suprema/FAS_APP/.venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

브라우저 주소:
```text
http://127.0.0.1:8000
```

## 모델 준비
### 체크포인트 배치 경로
| 모델 | 필수 경로 | 필수 파일 |
| --- | --- | --- |
| Biometric Lab | `backend/assets/biometric_ai_lab/` | `antispoofing_full.pth`, `inference.py`, `yolov8s-face-lindevs.onnx` |
| CVPR2024 | `backend/assets/cvpr2024_general_fas/` | `mobilenet_v3_small.pth` |
| STDN | `backend/assets/stdn_eccv2020/` | `ckpt-50.data-00000-of-00001`, `ckpt-50.index`, `ckpt-50.meta`, `checkpoint` |
| IADG | `backend/assets/iadg/OCI2M/` | `model_best.pth.tar` |

### 1. Biometric Lab Transformer
소스: Hugging Face `biometric-ai-lab/Antispoofing`

```bash
cd /home/mmss9402/source/suprema/FAS_APP
mkdir -p backend/assets/biometric_ai_lab
python -c "from huggingface_hub import hf_hub_download; repo='biometric-ai-lab/Antispoofing'; files=['antispoofing_full.pth','inference.py','yolov8s-face-lindevs.onnx']; [print(hf_hub_download(repo_id=repo, filename=f, local_dir='backend/assets/biometric_ai_lab', local_dir_use_symlinks=False)) for f in files]"
```

### 2. CVPR2024 MobileNetV3 Small
소스: GitHub `Xianhua-He/cvpr2024-face-anti-spoofing-challenge`

1. 저장소 README의 Google Drive 링크에서 `mobilenet_v3_small.pth`를 수동 다운로드합니다.
2. 아래 위치로 옮깁니다.

```bash
cd /home/mmss9402/source/suprema/FAS_APP
mkdir -p backend/assets/cvpr2024_general_fas
mv "/path/to/mobilenet_v3_small.pth" backend/assets/cvpr2024_general_fas/mobilenet_v3_small.pth
```

### 3. IADG CVPR 2023
소스: GitHub `qianyuzqy/IADG`

```bash
cd /home/mmss9402/source/suprema/FAS_APP
git clone https://github.com/qianyuzqy/IADG third_party/IADG
mkdir -p backend/assets/iadg
python -m gdown --folder "https://drive.google.com/drive/folders/15QjIXXbatQmXzwtR7pydsB4Jqscm7Vb6?usp=sharing" -O backend/assets/iadg
```

현재 앱 기본값:
- checkpoint: `backend/assets/iadg/OCI2M/model_best.pth.tar`
- config: `third_party/IADG/configs/OCI2M_test.yaml`
- 전처리: `bbox crop + margin 0.3 + 256x256 + mean/std 0.5`

### 4. STDN ECCV 2020
소스: GitHub `yaojieliu/ECCV20-STDN`

체크포인트 준비:
```bash
cd /home/mmss9402/source/suprema/FAS_APP
mkdir -p third_party
git clone https://github.com/yaojieliu/ECCV20-STDN third_party/ECCV20-STDN
mkdir -p backend/assets/stdn_eccv2020
cp third_party/ECCV20-STDN/data/pretrain/ckpt-50.data-00000-of-00001 backend/assets/stdn_eccv2020/
cp third_party/ECCV20-STDN/data/pretrain/ckpt-50.index backend/assets/stdn_eccv2020/
cp third_party/ECCV20-STDN/data/pretrain/ckpt-50.meta backend/assets/stdn_eccv2020/
cp third_party/ECCV20-STDN/data/pretrain/checkpoint backend/assets/stdn_eccv2020/
```

STDN 전용 외부 런타임:
```bash
conda create -n stdn_py37 python=3.7 -y
conda activate stdn_py37
pip install tensorflow==1.13.1 pillow numpy opencv-python matplotlib
```

STDN 외부 Python 지정:
```bash
export STDN_PYTHON_BIN="$HOME/anaconda3/envs/stdn_py37/bin/python"
```

중요:
- STDN은 공식 `test.py`를 subprocess로 실행합니다.
- 입력은 `face crop 된 이미지`를 전제로 합니다.

## 검증
### health check
```bash
curl http://127.0.0.1:8000/api/health
```

### 모델 목록 확인
```bash
curl http://127.0.0.1:8000/api/models
```

### 전체 실제 모델 smoke test
```bash
cd /home/mmss9402/source/suprema/FAS_APP/backend
STDN_PYTHON_BIN="/home/mmss9402/source/suprema/FAS_APP/.stdn_py37/bin/python" \
python -c "from PIL import Image; from app.services.model_registry import get_registry; from app.services.inference_runner import InferenceRunner; import json; registry=get_registry(); runner=InferenceRunner(registry); image=Image.open('/home/mmss9402/source/suprema/FAS_APP/backend/assets/test_images/lena.jpg').convert('RGB'); result=runner.run_for_image(image, 'lena.jpg', ['biometric_lab_transformer','cvpr2024_mobilenet_v3_small','stdn_eccv2020','iadg_cvpr2023']); print(json.dumps(result, ensure_ascii=False, indent=2))"
```

정상 기준:
- 4개 모델 모두 `status: success`
- `stdn_eccv2020` 실패 시 `STDN_PYTHON_BIN`과 face-cropped input을 먼저 확인
- `iadg_cvpr2023` 실패 시 `backend/assets/iadg/OCI2M/model_best.pth.tar`와 `third_party/IADG`를 확인

## 트러블슈팅
### STDN이 `failed`로 뜰 때
- 서버 실행 명령에 `STDN_PYTHON_BIN`이 빠지지 않았는지 확인합니다.
- `backend/assets/stdn_eccv2020/`에 checkpoint 4개가 있는지 확인합니다.
- 업로드 이미지가 `face crop 된 이미지`인지 확인합니다.

### IADG가 `failed`로 뜰 때
- `backend/assets/iadg/OCI2M/model_best.pth.tar` 경로를 확인합니다.
- `third_party/IADG`가 clone 되어 있는지 확인합니다.
- `pip install -r backend/requirements.txt`로 의존성을 다시 설치합니다.

### 포트 충돌이 날 때
- `Address already in use`는 이미 서버가 실행 중이라는 뜻입니다.
- 기존 서버를 종료하거나 다른 포트를 사용합니다.

## 문서
- 상세 기획: `docs/fas_app_detailed_plan.md`
- 모델 흐름도: `docs/model_flow.md`
- 공개 모델 인벤토리: `docs/open_fas_model_inventory.md`

## 다음 단계
- `VisionLabs ChaLearn 2021` 또는 다른 공개 3D 특화 모델 실제 연동
- 모델별 threshold 보정
- 비디오 전용 모델 분리 탭 추가
