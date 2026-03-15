# 공개 FAS 모델 인벤토리

이 문서는 현재 `FAS_APP`에 바로 붙일 수 있거나, 후속 조사 가치가 높은 공개 Face Anti-Spoofing 모델을 정리한 목록입니다.

## 1. 현재 실제 연동 완료
- `biometric_lab_transformer`
  - 출처: `biometric-ai-lab/Antispoofing`
  - 논문/연도: `paper_unconfirmed`, `2025 model card 기준`
  - 분류: `3D 마스크 특화 FAS`
  - 입력: 이미지 1장 입력 가능, 내부적으로 시계열 프레임 복제 사용
  - 상태: 실제 체크포인트 연동 완료
  - 메모: 원래 시계열 기반이라 단일 이미지 결과는 보수적으로 해석 필요

- `cvpr2024_mobilenet_v3_small`
  - 출처: `Xianhua-He/cvpr2024-face-anti-spoofing-challenge`
  - 논문: `Joint Physical-Digital Facial Attack Detection Via Simulating Spoofing Clues`
  - 학회/연도: `CVPR 2024`
  - 분류: `일반 FAS (물리·디지털 공격)`
  - 입력: `full image`
  - 상태: 실제 checkpoint `mobilenet_v3_small.pth` 연동 완료
  - 메모: face crop 전용이 아니라 full-image 계열 모델

## 2. 3D 마스크 특화 공개 후보
- `feascr/3d-mask-pad-iccv2021`
  - 논문: `3D High-Fidelity Mask Face Presentation Attack Detection Challenge`
  - 학회/연도: `ICCV Workshops 2021`
  - 공개 수준: 코드 공개 확인
  - 체크포인트: 현재 미확인
  - 앱 적합도: 중간
  - 메모: 3D mask 전용 문제 설정과 직접 연결됨

- `AlexanderParkin/chalearn_3d_hifi`
  - 논문: `3D High-Fidelity Mask Face Presentation Attack Detection Challenge`
  - 학회/연도: `ICCV Workshops 2021`
  - 공개 수준: 코드 공개 확인
  - 체크포인트: README 상 공개 링크 확인, 자동 다운로드 실패
  - 앱 적합도: 높음
  - 메모: 실제 3D 전용 트랙 확장 시 우선순위가 높음

- `rshaojimmy/Deep-Dynamic-Textures`
  - 논문: `Joint Discriminative Learning of Deep Dynamic Textures for 3D Mask Face Anti-Spoofing`
  - 학술지/연도: `IEEE TIFS 2019`
  - 공개 수준: 코드 공개 확인
  - 체크포인트: 현재 미확인
  - 앱 적합도: 중간 이하
  - 메모: Matlab 기반이라 서비스형 Python 앱에 바로 붙이기 어렵다

## 3. 2D / 일반 RGB FAS 공개 후보
- `ZitongYu/CDCN`
  - 논문: `Searching Central Difference Convolutional Networks for Face Anti-Spoofing`
  - 학회/연도: `CVPR 2020`
  - 공개 수준: 공식 GitHub 공개 확인
  - 입력 성격: 2D RGB 이미지 기반
  - 체크포인트: 공식 README/저장소 기준 명시적 공개 pretrained weight 미확인
  - 전처리:
    - 비디오에서 `8` 프레임 샘플링
    - bbox `.dat` 기반 face crop
    - `256x256` resize
    - `[-1, 1]` 정규화
    - depth map supervision 사용
  - 앱 적합도: 중간
  - 메모: 고전적인 대표 baseline이지만, 현재 앱은 단일 이미지 중심이라 비디오/프레임 구조를 단순화할 래퍼가 필요

- `yaojieliu/ECCV20-STDN`
  - 논문: `On Disentangling Spoof Trace for Generic Face Anti-Spoofing`
  - 학회/연도: `ECCV 2020`
  - 공개 수준: 공식 GitHub 공개 확인
  - 입력 성격: 일반 RGB face anti-spoofing
  - 체크포인트: 저장소 `data/pretrain/` 안에 `ckpt-50` TensorFlow checkpoint 포함
  - 전처리:
    - 학습 시 `cropped face frame + 68 landmark .npy` 구조 사용
    - 원 논문/공식 코드 관점에서는 `face crop 된 입력`을 전제로 보는 것이 맞음
    - 따라서 앱에서도 STDN은 `face crop 된 이미지 입력`을 기준 정책으로 가져가야 함
  - 앱 적합도: 높음
  - 메모: spoof trace 기반이라 비교 가치는 높고, 현재 앱에는 subprocess 기반 STDN 실제 연동과 공식 `test.py` 실행 경로가 반영됨. 앱 입력은 사용자가 준비한 face-cropped image를 전제로 하며, `REAL/FAKE` 라벨은 `score.txt`의 `M` 값을 바탕으로 한 앱 후처리임

- `YuchenLiu98/ECCV2022-SDA-FAS`
  - 논문: `Source-Free Domain Adaptation with Contrastive Domain Alignment and Self-supervised Exploration for Face Anti-Spoofing`
  - 학회/연도: `ECCV 2022`
  - 공개 수준: 공식 GitHub 공개 확인
  - 입력 성격: RGB 기반, domain adaptation 중심
  - 체크포인트: 추가 확인 필요
  - 앱 적합도: 중간
  - 메모: 연구용 가치는 높지만 inference-only 비교 앱에는 세팅이 다소 무거움

- `qianyuzqy/IADG`
  - 논문: `Instance-Aware Domain Generalization for Face Anti-Spoofing`
  - 학회/연도: `CVPR 2023`
  - 공개 수준: 공식 GitHub 공개 확인
  - 입력 성격: 2D RGB 이미지 기반
  - 체크포인트: README에 Google Drive / Baidu Netdisk 공개 링크 명시, 현재 Google Drive 폴더에서 실제 다운로드 확인
  - 전처리:
    - 프로토콜별로 `crop_face_from_5points` 또는 `crop_face_from_bbox` 사용
    - 현재 앱 기본 checkpoint는 `OCI2M_test.yaml` 기준이라 `crop_face_from_bbox: True`, `margin: 0.3`
    - `image_size: 256`
    - `Normalize(mean=[0.5,0.5,0.5], std=[0.5,0.5,0.5])`
    - depth map 사용
    - LMDB + list 파일 기반 테스트 구조
  - 앱 적합도: 높음
  - 메모: 최신 CVPR 본편 + 공개 checkpoint 확보가 가능하고, 현재 앱에는 `OCI2M` checkpoint 기반 실제 adapter가 반영됨. 공식 `test.py`는 LMDB/list 구조라 앱에서는 단일 이미지 inference wrapper로 연결함

- `RizhaoCai/DCL-FAS-ICCV2023`
  - 논문: `Rehearsal-Free Domain Continual Face Anti-Spoofing: Generalize More and Forget Less`
  - 학회/연도: `ICCV 2023`
  - 공개 수준: 공식 GitHub 공개 확인
  - 입력 성격: continual/domain generalization 연구 중심
  - 체크포인트: 추가 확인 필요
  - 앱 적합도: 중간 이하
  - 메모: 모델 자체보다는 학습/평가 프레임워크 성격이 강함

## 4. 보조 후보
- `DeepPixBiS`
  - 논문: `Deep Pixel-wise Binary Supervision for Face Presentation Attack Detection`
  - 학회/연도: `ICB 2019`
  - 공개 수준: 공개 구현 존재
  - 메모: `CVPR / ECCV / ICCV` 본편은 아니지만 2D PAD 고전 baseline으로 참고 가치가 큼

## 5. 현재 추천 우선순위
- 3D 특화 확장
  - `AlexanderParkin/chalearn_3d_hifi`
  - 이유: 3D 전용 성격이 분명하고 공개 checkpoint 단서가 가장 명확함

- 2D / 일반 FAS 확장
  - `IADG`
  - `STDN`
  - `CDCN`
  - 이유: `IADG`와 `STDN`은 모두 현재 앱 실제 연동 성공 상태이고, `CDCN`은 대표성은 높지만 공개 weight 단서가 약함

## 6. 권장 다음 조사 순서
1. `CDCN`의 공개 checkpoint 존재 여부를 확인한다.
2. `IADG`, `STDN`의 threshold와 score 해석을 더 많은 실샘플로 보정한다.
3. 전처리 규칙(face crop, resize, normalization)을 문서화한다.
4. 다음 실제 연동 후보를 `research_only`에서 `ready`로 승격한다.
