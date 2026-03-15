# FAS_APP 상세 기획서

## 1. 목표
- 공개된 Face Anti-Spoofing 모델들을 비교할 수 있는 웹 애플리케이션을 만든다.
- 사용자는 이미지 1장 또는 여러 장을 업로드하고, 선택한 모델 또는 전체 모델에 대해 추론을 실행할 수 있어야 한다.
- 각 모델이 입력 이미지를 `REAL` 또는 `FAKE`로 어떻게 판단하는지, 그리고 모델별 원본 score와 비교용 정규화 score를 한 화면에서 확인할 수 있어야 한다.
- 원래 1차 방향은 `3D specialized track` 중심이지만, 실제 공개 checkpoint가 확보된 경우 `일반 FAS (물리·디지털 공격)` 모델도 함께 비교할 수 있도록 확장한다.

## 1.1 현재 구현 상태 반영 메모
- 현재 실제 체크포인트 연동 완료 모델은 `biometric_lab_transformer`, `cvpr2024_mobilenet_v3_small`, `stdn_eccv2020`, `iadg_cvpr2023` 4개다.
- `biometric_lab_transformer`는 `3D 마스크 특화 FAS`로 분류한다.
- `cvpr2024_mobilenet_v3_small`는 `3D 마스크 전용`이 아니라 `일반 FAS (물리·디지털 공격)`으로 분류한다.
- `iadg_cvpr2023`는 `일반 FAS (물리·디지털 공격)`으로 분류한다.
- 따라서 현재 UI와 결과 문서에서는 내부 코드값 대신 사람이 읽기 쉬운 트랙 라벨을 우선 노출한다.

## 2. 1차 범위
### 포함
- 공개 FAS 모델 비교
- 웹 UI 기반 업로드/선택/실행/결과 확인
- 단일 이미지 업로드
- 다중 이미지 배치 업로드
- 개별 모델 선택 실행
- `All Models` 일괄 실행
- 결과 테이블 조회
- 이미지 하단 결과 오버레이 표시
- CSV export

### 제외
- 비디오 기반 추론
- 실시간 webcam 추론
- 멀티모달 입력(depth, IR, NIR)
- 모델 학습 기능
- 대규모 데이터셋 벤치마크 자동 실행
- 대규모 general FAS 모델군 확장
- 우리 팀 내부 모델 연동

## 3. 사용자 시나리오
### 시나리오 A: 단일 이미지 비교
1. 사용자가 이미지 업로드 칸에 얼굴 이미지를 1장 올린다.
2. 모델 선택 칸에서 3D specialized 공개 모델을 1개 이상 선택한다.
3. 실행 버튼을 누른다.
4. 앱이 각 모델의 요구 전처리 방식에 맞춰 추론을 수행한다.
5. 결과 화면에서 모델별 label, raw score, normalized spoof score, threshold, 처리 시간, 비고를 비교한다.
6. 결과 이미지 하단에는 `REAL/FAKE`, `score`, `model name`을 오버레이로 표시한다.

### 시나리오 B: 여러 이미지 일괄 비교
1. 사용자가 이미지를 여러 장 업로드한다.
2. 모델 선택 칸에서 `All Models`를 선택한다.
3. 실행 버튼을 누른다.
4. 앱이 각 이미지에 대해 전체 모델을 순서대로 또는 병렬로 실행한다.
5. 결과 화면에서 이미지별/모델별 결과를 필터링하며 확인한다.
6. 각 이미지별 결과 카드 하단에는 선택된 각 모델의 판정과 score를 표시한다.

## 4. 핵심 화면 구성
## 4.1 메인 비교 화면
- 상단: 페이지 제목, 현재 실험 범위(`3D 마스크 특화 FAS + 일반 FAS`) 표시
- 좌측 또는 상단 첫 번째 섹션: 이미지 업로드 칸
- 그 아래 또는 옆 섹션: 모델 선택 칸
- 실행 영역: `Run Selected Models`, `Run All Models`, `Reset`
- 하단: 결과 요약 카드 + 결과 테이블 + 이미지별 상세 패널

## 4.2 이미지 업로드 칸
- 파일 선택 버튼 제공
- 드래그 앤 드롭 지원
- 단일/다중 업로드 지원
- 업로드 직후 썸네일 표시
- 파일명, 해상도, 업로드 개수 표시
- 개별 삭제 버튼 제공
- 전체 비우기 버튼 제공
- 지원 포맷 예시: `jpg`, `jpeg`, `png`, `bmp`
- 얼굴 검출 실패 시 이미지 카드에 경고 표시

## 4.3 모델 선택 칸
- 체크박스 또는 멀티셀렉트 카드 형태
- 모델명, 논문명, 연도, 공격 유형, 입력 타입 표시
- `실제 체크포인트 / 모의 결과 / 미연동` 상태 표시
- `3D 마스크 특화 FAS / 일반 FAS (물리·디지털 공격)` 트랙 표시
- 예시 그룹
  - `즉시 실행 가능`
  - `연구용 / 비디오 전용`
- `All Models` 버튼 제공
- `All Models` 선택 시 두 가지 방식 중 하나로 구현
  - 방식 A: 전체 모델을 내부 배열에 즉시 채워 넣음
  - 방식 B: `run_mode=all`로 백엔드에 전달
- 1차 구현에서는 상태가 단순한 `방식 A`를 우선 추천

## 4.4 결과 화면
- 요약 카드
  - 총 이미지 수
  - 실행 모델 수
  - 성공/실패 건수
  - 평균 처리 시간
- 결과 이미지 카드
  - 원본 또는 전처리 후 대표 이미지 표시
  - 이미지 하단 오버레이 영역에 `model_name`, `REAL/FAKE`, `score` 표시
  - 다중 모델 실행 시 모델별 badge 또는 작은 리스트로 표시
- 결과 테이블 컬럼 예시
  - image_name
  - model_name
  - attack_track
  - implementation_status
  - paper_title
  - paper_year
  - attack_track
  - prediction_label
  - raw_score
  - normalized_spoof_score
  - threshold
  - inference_time_ms
  - preprocessing_note
  - status
- 상세 패널
  - 원본 이미지
  - crop된 얼굴 이미지
  - 모델별 score bar
  - 실패 메시지

## 5. 모델 분류 전략
## 5.1 3D Specialized Track
- 실리콘 마스크
- 라텍스 마스크
- 레진 마스크
- 고충실도 3D 마스크

### 1차 후보
- `feascr/3d-mask-pad-iccv2021`
- `AlexanderParkin/chalearn_3d_hifi`
- `SeaRecluse/Chalearn-3D-High-Fidelity-Mask-Face-Presentation-Attack-Detection-Challenge-ICCV2021-Team-HighC`
- `rshaojimmy/Deep-Dynamic-Textures`
- `shicaiwei123/anti-spoofing-of-rppg`
- `lbf4616/Face-Anti-spoofing`
- `biometric-ai-lab/Antispoofing`

### 주의사항
- 3D 트랙 모델은 비디오 기반 또는 rPPG 기반이 많다.
- 따라서 1차 앱에서는 목록에는 포함하되, 실제 실행 가능 여부를 `ready`, `research_only`, `video_only`로 나눠 관리하는 것이 좋다.
- 주요 학회 메인 트랙의 공개 구현은 많지 않고, 실제로는 `ICCVW 2021 HiFiMask 챌린지` 계열 공개 코드가 가장 현실적인 출발점이다.

### 학회 출처가 비교적 분명한 공개 후보
- `feascr/3d-mask-pad-iccv2021`
  - 출처: `ICCV Workshops 2021`
  - 성격: HiFiMask 챌린지용 공개 코드
- `AlexanderParkin/chalearn_3d_hifi`
  - 출처: `ICCV Workshops 2021`
  - 성격: HiFiMask 챌린지 1위 솔루션 공개 코드
- `SeaRecluse/...Team-HighC`
  - 출처: `ICCV Workshops 2021`
  - 성격: HiFiMask 챌린지 공개 코드
- `rshaojimmy/Deep-Dynamic-Textures`
  - 출처: `IEEE TIFS 2019`
  - 성격: 3D mask anti-spoofing 공개 구현
- `shicaiwei123/anti-spoofing-of-rppg`
  - 출처: `ECCV 2018` 계열 rPPG 3D mask PAD 연구 기반
  - 성격: rPPG 기반 구현

### 현재 조사 기준 결론
- `ICCV / ECCV / CVPR / ACCV` 메인 학회 논문 중에서 `3D mask 전용 + 공개 구현 + 바로 웹 비교기에 붙이기 쉬운` 후보는 많지 않다.
- 실무적으로는 `ICCVW 2021 HiFiMask 계열`과 `ECCV 2018 / TIFS 2019` 계열이 가장 현실적인 시작점이다.

## 5.2 일반 FAS (물리·디지털 공격)
- `cvpr2024-face-anti-spoofing-challenge`
  - 논문: `Joint Physical-Digital Facial Attack Detection Via Simulating Spoofing Clues`
  - 출처: `CVPR 2024`
  - 성격: 3D 마스크 전용이 아니라 physical attack과 digital attack을 함께 다루는 일반 FAS
  - 현재 상태: `mobilenet_v3_small.pth` 실제 checkpoint 확보 및 앱 연동 가능

## 5.3 2D / 일반 RGB FAS 공개 후보
- `ZitongYu/CDCN`
  - 논문: `Searching Central Difference Convolutional Networks for Face Anti-Spoofing`
  - 출처: `CVPR 2020`
  - 공개 구현: 공식 GitHub 확인
  - 성격: 대표적인 2D RGB 이미지 기반 FAS
  - 앱 적합도: 높음
  - 메모: 저명 학회 본편 + 공개 구현 조합이라 2D 확장 시 우선 후보
- `yaojieliu/ECCV20-STDN`
  - 논문: `On Disentangling Spoof Trace for Generic Face Anti-Spoofing`
  - 출처: `ECCV 2020`
  - 공개 구현: 공식 GitHub 확인
  - 성격: spoof trace disentangling 기반 일반 FAS
  - 앱 적합도: 높음
  - 메모: 해석 가능성과 일반화 측면에서 비교 가치가 높고, 현재 앱에 subprocess 기반 실제 연동 및 smoke test 성공 상태까지 반영됨. 다만 원 논문 기준으로는 `face crop 된 입력`과 공식 테스트 프로토콜을 따라야 함
- `YuchenLiu98/ECCV2022-SDA-FAS`
  - 논문: `Source-Free Domain Adaptation with Contrastive Domain Alignment and Self-supervised Exploration for Face Anti-Spoofing`
  - 출처: `ECCV 2022`
  - 공개 구현: 공식 GitHub 확인
  - 성격: source-free domain adaptation 중심
  - 앱 적합도: 중간
  - 메모: 연구 가치가 크지만 바로 inference-only 웹앱에 붙이기엔 세팅이 다소 무거움
- `qianyuzqy/IADG`
  - 논문: `Instance-Aware Domain Generalization for Face Anti-Spoofing`
  - 출처: `CVPR 2023`
  - 공개 구현: 공식 GitHub 확인
  - 성격: domain generalization 기반 2D RGB FAS
  - 앱 적합도: 높음
  - 메모: 단일 이미지 입력 비교기에 연결해볼 만한 다음 세대 후보였고, 현재는 `OCI2M` 공개 checkpoint 기반 실제 연동까지 반영됨
- `RizhaoCai/DCL-FAS-ICCV2023`
  - 논문: `Rehearsal-Free Domain Continual Face Anti-Spoofing: Generalize More and Forget Less`
  - 출처: `ICCV 2023`
  - 공개 구현: 공식 GitHub 확인
  - 성격: domain continual learning 기반 FAS
  - 앱 적합도: 중간 이하
  - 메모: 연구용으로는 좋지만, 1차 앱 통합 우선순위는 낮음

### 2D / 일반 FAS 1차 추천 후보
- `CDCN (CVPR 2020)`
- `STDN (ECCV 2020)`
- `IADG (CVPR 2023)`

### 추천 이유
- 모두 `CVPR / ECCV / ICCV` 본편 기준으로 출처가 분명하다.
- 공개 GitHub 저장소가 확인된다.
- 3D 전용 모델보다 `단일 이미지 입력` 앱 구조와 맞을 가능성이 높다.
- 전처리와 score 해석 차이를 비교 문서로 남기기에 적합하다.

### 실제 체크포인트 확인 결과
- `biometric-ai-lab/Antispoofing`
  - Hugging Face API 기준 `antispoofing_full.pth`, `inference.py`, `yolov8s-face-lindevs.onnx` 파일이 확인됨
  - 현재 앱에 실제 연동 완료
  - 단, 본래 비디오/시계열 기반 모델이라 단일 이미지에서는 프레임 복제 방식으로 동작
- `cvpr2024-face-anti-spoofing-challenge`
  - 저장소 README 기준 `mobilenet_v3_small.pth` 공개 checkpoint 확인
  - 현재 앱에 실제 연동 완료
  - 단, `3D specialized`가 아니라 `일반 FAS (물리·디지털 공격)` 모델
- `AlexanderParkin/chalearn_3d_hifi`
  - 저장소 README에 `gdown` 기반 체크포인트 다운로드 링크가 명시됨
  - 실제 연동 가능성이 높은 다음 후보였으나, 현재 자동 다운로드 시 Google Drive 공개 접근 문제로 바로 확보되지 않음
- `feascr/3d-mask-pad-iccv2021`
  - 코드와 평가 설정은 공개되어 있으나, 현재 확인 범위에서는 공개 체크포인트 링크가 명확하지 않음
- `yaojieliu/ECCV20-STDN`
  - 저장소 `data/pretrain/`에 TensorFlow checkpoint가 포함되어 있음
  - 현재 앱 코드에는 subprocess 기반 STDN 실제 연동이 추가되었고 smoke test가 성공함
  - 외부 TensorFlow 호환 런타임 설정이 필요하지만, 설정 후에는 `ready` 모델로 사용 가능
  - 저장소 포함 live/spoof 샘플 검증 기준으로 `M`은 spoof-direction logit처럼 해석 가능
  - 단, 논문 재현용으로는 앱에 업로드하는 입력도 `face crop 된 이미지`를 기준으로 맞춰야 함
  - 앱에서는 face-cropped input을 임시 공식 폴더 구조에 넣고 공식 `test.py`를 실행하는 방향으로 유지
- `qianyuzqy/IADG`
  - README의 Google Drive 공개 폴더에서 checkpoint 다운로드가 실제로 가능함
  - 현재 앱에는 `OCI2M/model_best.pth.tar` 기반 실제 adapter가 반영됨
  - 공식 `OCI2M_test.yaml` 규칙을 참고해 `bbox crop + margin 0.3 + 256 resize + mean/std 0.5` 전처리로 단일 이미지 wrapper를 구성함
  - 공식 `test.py`는 LMDB/list 기반이라 앱에서는 모델/가중치/전처리 규칙을 따르는 단일 이미지 inference로 통합함
- `rshaojimmy/Deep-Dynamic-Textures`
  - 코드 공개는 확인되지만, 공개 weight 링크는 현재 확인되지 않음
  - Matlab 기반이라 서비스형 Python 앱에 바로 붙이기엔 추가 래핑 비용이 있음

## 6. 논문/연도 메타데이터 관리 원칙
- 모든 모델은 아래 메타데이터를 가진다.
  - `model_name`
  - `display_name`
  - `paper_title`
  - `paper_year`
  - `paper_type`
  - `repository_url`
  - `weights_source`
  - `attack_track`
  - `input_type`
  - `ready_status`
  - `score_semantics`
  - `threshold_default`

### paper_type 값 예시
- `official_paper_implementation`
- `paper_based_reimplementation`
- `engineering_project`
- `paper_unconfirmed`

## 7. 결과 score 표준화 원칙
- 모델마다 score 의미가 다를 수 있다.
- 어떤 모델은 `spoof 확률`을 출력하고, 어떤 모델은 `real confidence`를 출력할 수 있다.
- 따라서 결과는 최소 2개 score를 함께 보여준다.
  - `raw_score`: 모델 원본 값
  - `normalized_spoof_score`: 비교용 0~1 값

### 정규화 규칙 예시
- 원본이 `spoof probability`이면 그대로 사용
- 원본이 `real probability`이면 `1 - real_probability`
- 원본이 logit이면 sigmoid 적용 후 spoof 방향으로 통일
- multiclass면 spoof 관련 class를 합산하거나 사전 정의 규칙 적용

## 7.1 rPPG 기반 모델이란?
- `rPPG`는 `remote photoplethysmography`의 약자다.
- 카메라 영상에서 피부의 아주 미세한 색 변화로 맥박 신호를 추정하는 방식이다.
- 진짜 사람 얼굴은 혈류 변화 때문에 시간축에서 미세한 주기 신호가 나타날 수 있지만, 실리콘/라텍스/레진 마스크는 이런 생체 신호가 거의 없거나 다르게 나타난다.
- 그래서 rPPG 기반 모델은 `한 장의 이미지`보다 `여러 프레임의 영상`에서 더 의미가 있다.

### 앱 설계에 미치는 영향
- rPPG 기반 모델은 단일 이미지 비교 앱과 잘 맞지 않는다.
- 1차 버전에서 단일 이미지 중심으로 간다면 `research_only` 또는 `video_only`로 분류하는 것이 적절하다.
- 나중에 비디오 모드를 추가할 때 별도 탭으로 통합하는 것이 좋다.

## 8. 전처리 전략
- 모델별 전처리 방식을 강제하지 않는다.
- 각 모델이 원래 요구하는 test/inference 전처리를 최대한 존중한다.
- 전처리 메타데이터를 결과에 함께 기록해 비교 해석이 가능하도록 한다.

### 기본 원칙
1. 이미지 로드
2. 모델별 필요 시 얼굴 검출
3. 모델별 crop / align / resize / normalize 수행
4. 결과에 적용 전처리 방식 기록

### 기록해야 할 전처리 메타데이터
- `face_detector`
- `alignment_used`
- `crop_strategy`
- `input_size`
- `normalization_scheme`
- `preprocess_source`

### 예외 정책
- 여러 모델을 완전히 같은 전처리로 강제하지 않는다.
- 대신 결과 화면과 테이블에서 `이 모델은 어떤 전처리를 사용했는지`를 함께 보여준다.
- 후속 단계에서 필요하면 `original preprocessing`과 `shared preprocessing`을 비교하는 실험 모드를 별도로 추가할 수 있다.

## 9. 백엔드 구조
## 9.1 권장 스택
- Backend: `FastAPI`
- Inference Runtime: `PyTorch`, `ONNX Runtime`
- Background Tasks: 필요 시 `Celery` 또는 단순 async queue
- Storage: 초기에는 로컬 파일 시스템

## 9.2 권장 디렉토리 구조
```text
FAS_APP/
  docs/
    fas_app_detailed_plan.md
  backend/
    requirements.txt
    app/
      adapters/
        base.py
        mock_models.py
      services/
        score_normalizer.py
        inference_runner.py
        model_registry.py
      api/
        routes/
          infer.py
          models.py
      schemas/
        infer.py
      config/
        models.yaml
  frontend/
    static/
      index.html
      app.js
      styles.css
  README.md
```

## 9.3 모델 어댑터 인터페이스
```python
class BaseFASAdapter:
    model_id: str
    display_name: str

    def load(self) -> None:
        ...

    def predict(self, face_image):
        ...

    def normalize_output(self, raw_output):
        ...

    def metadata(self) -> dict:
        ...
```

## 10. API 설계
## 10.1 모델 목록 조회
### `GET /api/models`
- UI에서 모델 선택 칸을 구성할 때 사용
- 응답 예시
```json
[
  {
    "model_id": "hifimask_iccvw2021",
    "display_name": "HiFiMask ICCVW 2021 Baseline",
    "paper_title": "3D High-Fidelity Mask Face Presentation Attack Detection Challenge",
    "paper_year": 2021,
    "attack_track": "3d_specialized",
    "ready_status": "ready"
  }
]
```

## 10.2 추론 실행
### `POST /api/infer`
- multipart 업로드 또는 파일 경로 기반 요청
- 요청 필드 예시
```json
{
  "selected_models": ["hifimask_iccvw2021", "visionlabs_chalearn_2021"],
  "use_all_models": false
}
```

### 동작 규칙
- `use_all_models=true`이면 백엔드가 현재 `ready` 상태 모델 전체를 확장
- `selected_models`가 비어 있고 `use_all_models=false`이면 에러 반환
- 이미지가 없으면 에러 반환

### 응답 예시
```json
{
  "request_id": "req_001",
  "resolved_models": ["hifimask_iccvw2021", "visionlabs_chalearn_2021"],
  "images": [
    {
      "image_name": "sample1.jpg",
      "results": [
        {
          "model_id": "hifimask_iccvw2021",
          "prediction_label": "REAL",
          "raw_score": 0.1832,
          "normalized_spoof_score": 0.1832,
          "threshold": 0.55,
          "inference_time_ms": 31,
          "status": "success"
        }
      ]
    }
  ]
}
```

## 11. 프론트 상태 규칙
- 이미지가 하나도 없으면 실행 버튼 비활성화
- 모델이 하나도 선택되지 않았으면 실행 버튼 비활성화
- `All Models` 선택 시 개별 선택 UI를 해제하거나 전체 선택 상태로 동기화
- 실행 중에는 동일 요청 중복 실행 방지
- 모델별 실패는 전체 실패가 아니라 부분 실패로 처리

## 12. 실행 전략
## 12.1 1차 권장
- 모델 수가 적을 때는 서버 내부 순차 실행
- 대신 요청 단위 로딩 상태를 명확히 표시
- 이미지 카드 하단에 모델별 결과 오버레이를 먼저 보여주고, 상세 수치는 테이블에서 확인하게 한다.

## 12.2 2차 확장
- 모델 수가 늘면 병렬 실행 도입
- GPU 메모리 충돌을 피하기 위해 모델별 worker 분리 고려

## 13. 에러 처리
- 지원하지 않는 이미지 포맷
- 얼굴 검출 실패
- 모델 로드 실패
- 추론 중 런타임 에러
- 특정 모델 timeout

### UI 처리 원칙
- 에러를 모델 단위로 표시
- 실패한 모델도 결과 테이블에 행을 남김
- `status=failed`, `message=...` 형태로 기록

## 14. 단계별 구현 로드맵
## Phase 0: 기획/조사
- 후보 모델 조사
- 논문/연도/라이선스 확인
- 추론 가능 여부 확인

## Phase 1: 최소 기능 제품
- `FAS_APP` 기본 구조 생성
- 3D specialized 공개 모델 2~3개 연결
- 단일 이미지 업로드
- 다중 이미지 업로드
- 모델 선택
- `All Models`
- 이미지 하단 결과 오버레이
- 결과 테이블

## Phase 2: 비교 품질 향상
- 모델별 전처리 메타데이터 시각화
- score normalization 고도화
- CSV export
- 썸네일 기반 상세 결과

## Phase 3: 확장
- video-only 모델 전용 모드 추가
- 비디오 입력 모드
- 실험 로그 저장
- 데이터셋 벤치마크 모드

## 15. 첫 구현에서 확정해야 할 항목
- 1차 통합할 3D specialized 공개 모델 2~3개
- 각 모델의 원본 전처리 파이프라인 정리
- `All Models`의 범위를 `ready 모델만`으로 제한할지 여부
- 결과 테이블 기본 정렬 기준
- 이미지 하단 오버레이 표기 형식

### 현재 기준 결정
- `All Models`는 `ready 모델만` 실행한다.
- UI에는 내부 코드값 대신 사용자용 라벨을 우선 표시한다.
- 현재 `ready`에는 `3D 마스크 특화 FAS`와 `일반 FAS (물리·디지털 공격)`이 함께 포함될 수 있다.
- 2D / 일반 RGB 공개 후보는 `문서화 -> 코드 확인 -> 체크포인트 확인 -> 실제 연동` 순서로 확장한다.
- STDN은 현재 `subprocess + 외부 TensorFlow 런타임` 전략으로 통합하되, 원 논문 기준 입력을 따르기 위해 앱에서도 `face crop 된 이미지`를 넣는 방향으로 맞춘다.
- STDN의 원본 전체 이미지 직접 입력 경로는 논문 재현 결과로 간주하지 않는다.
- STDN의 앱 라벨은 공식 `test.py`가 기록한 `score.txt`를 앱용 규칙으로 후처리한 값이다.
- IADG는 현재 `OCI2M` 공개 checkpoint 기반 실제 연동 완료 상태이며, 공식 설정의 bbox crop 규칙을 앱용 face detector 경로로 근사 적용한다.

## 16. 추천 1차 조합
- `feascr/3d-mask-pad-iccv2021`
- `AlexanderParkin/chalearn_3d_hifi`
- `rshaojimmy/Deep-Dynamic-Textures`

### 이유
- 모두 3D mask 문제를 직접 다룬다.
- 공개 코드가 확인된다.
- `ICCVW 2021` 및 `TIFS 2019`처럼 출처가 비교적 명확하다.
- 전처리 차이를 문서화하면서 비교하기 좋은 조합이다.

### 현재 구현 상태 기준 조정
- 실제 연동 완료: `biometric-ai-lab/Antispoofing`
- 다음 실제 연동 우선순위: `AlexanderParkin/chalearn_3d_hifi`
- 조사 유지 후보: `feascr/3d-mask-pad-iccv2021`, `rshaojimmy/Deep-Dynamic-Textures`
- 단, `AlexanderParkin/chalearn_3d_hifi`는 체크포인트 링크가 문서상 존재해도 자동 다운로드가 실패할 수 있어 수동 확보 경로를 같이 준비해야 함

## 16.1 2D / 일반 FAS 추천 조합
- `CDCN`
- `STDN`
- `IADG`

### 이유
- 2D RGB 입력 기반이라 현재 앱 구조와 잘 맞는다.
- 모두 저명 학회 본편 논문 기반 공개 구현이다.
- 3D 특화 모델과 성격이 다르므로, `일반 FAS` 비교 트랙을 확장하기에 좋다.

## 17. 리스크
- 공개 모델의 실제 가중치 확보가 어려울 수 있다.
- 라이선스가 상업적 사용에 제약을 둘 수 있다.
- 모델마다 입력 전처리가 달라 score의 직접 비교가 어려울 수 있다.
- 3D 마스크 전용 모델은 비디오 기반인 경우가 많아 단일 이미지 비교에 바로 넣기 어렵다.
- 메인 학회 논문이라도 공개 구현이나 가중치가 없는 경우가 많다.

## 18. 다음 문서 후보
- `model_inventory.md`: 모델별 논문/연도/입력/라이선스 표
- `api_spec.md`: 요청/응답 상세 명세
- `ui_wireframe.md`: 화면 와이어프레임
- `execution_checklist.md`: 구현 체크리스트
