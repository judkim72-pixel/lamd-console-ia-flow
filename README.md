# AEON UI Architect — PPT‑style IA & Flow

Streamlit 앱 하나로 **PPT에서 쓰던 방식의 IA/Flow/Decision 도식**을 **SVG**로 뽑아내는 경량 도구입니다.  
복잡한 다이어그램 툴 없이 **JSON 스펙만**으로 일관된 포맷을 빠르게 생성하고, PPT/Keynote로 그대로 붙여 넣을 수 있습니다.

> ⚠️ 방산/내부 프로젝트의 경우 **Private repo** 권장. 샘플 스펙은 일반화하여 업로드하세요.

---

## ✨ 기능
- **IA(Information Architecture)**: Zoning, Components, Scope를 PPT 스타일 벡터로 생성
- **Flow(스윔레인)**: Lane × Step 체계, 자동 레이아웃, 화살표 연결
- **Decision(Yes/No)**: 다이아몬드 노드 + 분기 카드
- **SVG 다운로드**: PPT/Keynote/Docs에 벡터로 붙여넣기
- **외부 종속성 無**: `streamlit`만으로 구동 (브라우저 기반)

---

## 🧩 구성
```
aeon-ui-architect/
├─ ui_architect_app.py        # 메인 앱
├─ ui_architect_sample.json   # 샘플 스펙 (문서·테스트용)
├─ requirements.txt           # streamlit만 명시
└─ README.md
```

---

## 🚀 빠른 시작

### 1) 로컬 실행
```bash
git clone https://github.com/<your-account>/aeon-ui-architect.git
cd aeon-ui-architect
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run ui_architect_app.py
```

### 2) Streamlit Cloud 배포
- **Main file**: `ui_architect_app.py`  
- **Python**: 3.10+  
- **Requirements**: `streamlit`

> 배포 후 브라우저에서 **샘플 스펙**으로 바로 미리보기 가능. 필요한 경우 JSON 업로드/붙여넣기로 교체.

---

## 🗂 샘플 스펙 구조(JSON)

아래 키만 채우면 됩니다. 필요 필드 외 값은 자유롭게 확장하세요.

```jsonc
{
  "project": { "title": "LAMD Left Panel — IA & Flows", "author": "AEON Communications", "version": "v1.0" },
  "canvas": { "width": 1280, "height": 720, "theme": { "bg": "#FAFAFC", "ink": "#111" } },

  "ia": {
    "scope": ["Left Graphic Panel Only", "27\" FHD (1920×1080)", "Avoid red alerts"],
    "zones": [
      { "id": "Z5", "label": "System Status", "x": 40, "y": 80, "w": 1200, "h": 40, "fill": "#FFF7F0" },
      { "id": "Z2", "label": "Layer Controls", "x": 40, "y": 130, "w": 180, "h": 500, "fill": "#F3F7FF" },
      { "id": "Z3", "label": "KPI Mini-View", "x": 230, "y": 130, "w": 240, "h": 120, "fill": "#FFFDE7" },
      { "id": "Z4", "label": "Legend & Scale", "x": 230, "y": 590, "w": 1010, "h": 40, "fill": "#EEF9FF" },
      { "id": "Z1", "label": "Main Canvas", "x": 230, "y": 260, "w": 1010, "h": 320, "fill": "#EEF5EE" }
    ],
    "components": [
      { "zone": "Z1", "title": "Range×Altitude Grid", "id": "C-Grid" },
      { "zone": "Z1", "title": "Track Symbols & Height Bars", "id": "C-TrackBars" },
      { "zone": "Z1", "title": "Motion Trails (6–12s)", "id": "C-Trails" },
      { "zone": "Z1", "title": "FOV/Engagement Bands", "id": "C-FOV" },
      { "zone": "Z2", "title": "Layer Toggles (2.5D/Trail/FOV)", "id": "C-Layers" },
      { "zone": "Z3", "title": "KPI Badges (TSA/FPS/Misassoc)", "id": "C-KPI" },
      { "zone": "Z5", "title": "FPS/lag_ms/rollback", "id": "C-Status" },
      { "zone": "Z4", "title": "Legend/Units/Abbrev", "id": "C-Legend" }
    ]
  },

  "flows": {
    "lanes": ["Operator UI", "Render Engine", "KPI Logic", "System Status", "Logger"],
    "items": [
      {
        "id": "UF-01", "name": "Saturation SA",
        "steps": [
          { "lane": "Operator UI", "text": "Check Z1 cues", "out": "Baseline LOD" },
          { "lane": "Render Engine", "text": "Compute density", "out": "LOD level" },
          { "lane": "Operator UI", "text": "Toggle FOV if needed", "out": "Layer state" },
          { "lane": "KPI Logic", "text": "Update TSA estimate", "out": "KPI refresh" }
        ]
      },
      {
        "id": "EF-01", "name": "Threshold & Rollback",
        "steps": [
          { "lane": "System Status", "text": "Detect lag>500ms or FPS<30(3s)", "out": "Alert badge" },
          { "lane": "Render Engine", "text": "Auto rollback to 2D if 5s persists", "out": "rollback=2D" },
          { "lane": "Logger", "text": "Record reason/owner/time", "out": "audit_log" }
        ]
      }
    ],
    "decisions": [
      { "id": "D-01", "cond": "FPS ≥ 30 ?", "yes": "Keep LOD", "no": "Increase LOD" },
      { "id": "D-02", "cond": "lag_ms ≤ 500 ?", "yes": "Normal", "no": "Warn / EF-01" }
    ]
  }
}
```

---

## 🧪 사용 팁
- **SVG는 벡터**입니다. PPT에 붙여 넣은 후에도 자유 확대/색상 편집 가능
- **한/영 폰트 사이징 규칙**: 제목 22, 섹션 16, 본문 13, 보조 11
- **붉은 경보색 지양**: KPI/경보 색상 정책은 JSON에서 제어하세요
- **버전 관리**: 스펙 JSON을 PR 단위로 관리 → 변경분 리뷰가 쉬움

---

## 🔐 보안 메모
- 실제 좌표/규격/성능 수치가 외부 유출되지 않도록 **익명화된 값**을 사용
- 고객명/무기체계명은 **약어/코드명** 사용 권장
- 저장/공유 시 레포지토리 권한을 점검하세요

---

## 📜 라이선스
사내/프로젝트 정책에 맞춰 설정하세요. (예: Private / Proprietary)  
오픈소스로 배포하려면 `LICENSE` 파일을 추가하세요 (MIT, Apache‑2.0 등).
