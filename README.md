# 🌾 스마트팜 종합 농가 관리 시스템

스마트팜 농가 운영을 위한 **실시간 날씨, 영농일지, 자료 관리, 일정 관리** 통합 Streamlit 대시보드입니다.
데이터는 Supabase 클라우드에 저장되어 새로고침·재배포 후에도 유지됩니다.

🔗 **배포 주소**: https://smartfarm-management.streamlit.app

## 구성

| 화면 | 파일 | 내용 |
|---|---|---|
| 🏠 대시보드 | `views/dashboard.py` | 오늘의 현황(날씨·일정·일지·자료), 일정 캘린더(공휴일·영농일지 표시, 클릭으로 일정 등록/삭제) |
| 📝 영농일지 | `views/farmlog.py` | 작업 기록·사진 첨부, 검색/필터, CSV 내보내기, 월별 수확량·매출 통계 |
| 📁 자료관리함 | `views/documents.py` | 계약서·영수증·메뉴얼 업로드, 카테고리 분류, 열기/저장/삭제 |
| 📅 일정관리 | `views/schedule.py` | 일정 등록, 중요도·범주 설정, D-Day 정렬, 완료 체크 |

공통 모듈: `app.py`(진입점·라우팅), `common.py`(사이드바·날씨·유틸), `db.py`(Supabase 연동)

## 데이터 저장 구조 (Supabase)

| 데이터 | 저장 위치 |
|---|---|
| 영농일지 | `farm_logs` 테이블 |
| 일정 | `schedules` 테이블 |
| 자료 메타데이터 | `documents` 테이블 |
| 업로드 파일·사진 원본 | Storage 버킷 `farm-documents` |

파일 열기/저장은 Supabase 공개 URL 링크로 처리해, 목록을 볼 때 파일이 전송되지 않습니다(트래픽 절약).

## 주요 기능

- **실시간 날씨** — OpenWeatherMap API 연동. 농장 위치는 충남 당진시 고대면 당진포리 140-14로 고정. 강풍(10m/s 이상)·강우 시 안전 경고 표시. API 오류 시 자동으로 가상 데이터로 대체되어 앱이 멈추지 않습니다.
- **캘린더** — 대한민국 공휴일 자동 표시(음력 명절·대체공휴일 포함), 영농일지 기록 표시, 빈 날짜 클릭으로 일정 등록
- **통계** — 월별 수확량·매출 추이, 작업 유형별 건수, 구역별 수확량
- **백업** — 사이드바에서 영농일지·일정·자료목록을 CSV(ZIP)로 내려받기

## 설치 및 실행

​```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
​```

### 필요한 Secrets

`.streamlit/secrets.toml`(로컬) 또는 Streamlit Cloud → Settings → Secrets에 등록합니다.

​```toml
OPENWEATHER_API_KEY = "발급받은_키"
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "publishable_또는_anon_키"
​```

### Supabase 초기 설정 (최초 1회)

SQL Editor에서 실행합니다.

​```sql
create table farm_logs (
  id text primary key,
  log_date text not null,
  zone text not null,
  work_type text not null,
  detail text not null,
  materials text,
  harvest_kg real default 0,
  sales bigint default 0,
  photo_name text
);

create table schedules (
  id text primary key,
  title text not null,
  start_date text not null,
  end_date text not null,
  importance text not null,
  category text not null,
  done boolean default false
);

create table documents (
  id text primary key,
  filename text not null,
  stored_name text not null,
  category text not null,
  description text,
  upload_date text not null,
  size_kb real default 0
);

alter table farm_logs enable row level security;
alter table schedules enable row level security;
alter table documents enable row level security;

create policy "allow all farm_logs" on farm_logs for all using (true) with check (true);
create policy "allow all schedules" on schedules for all using (true) with check (true);
create policy "allow all documents" on documents for all using (true) with check (true);

-- Storage 버킷 'farm-documents'(Public) 생성 후 실행
create policy "farm docs select" on storage.objects for select using (bucket_id = 'farm-documents');
create policy "farm docs insert" on storage.objects for insert with check (bucket_id = 'farm-documents');
create policy "farm docs update" on storage.objects for update using (bucket_id = 'farm-documents');
create policy "farm docs delete" on storage.objects for delete using (bucket_id = 'farm-documents');
​```

## 운영 시 유의사항

- **보안**: 현재 로그인 기능이 없고 Storage 버킷이 Public이라, 링크를 아는 사람은 파일을 열람할 수 있습니다. 민감한 계약서·영수증을 다루려면 인증 기능 추가를 권장합니다.
- **자동 일시정지**: Supabase 무료 플랜은 7일간 접속이 없으면 프로젝트가 일시정지됩니다. 데이터는 보존되며 대시보드에서 수동으로 재개할 수 있습니다.
- **백업**: 무료 플랜은 자동 백업이 없습니다. 사이드바의 백업 기능으로 주기적으로 내려받아 보관해주세요.
- **무료 한도**: DB 500MB / 파일 1GB / 월 전송량 5GB. 일반적인 농가 자료 기준으로는 여유롭지만, 최신 정보는 https://supabase.com/pricing 에서 확인해주세요.
- **면책**: 재무·매출 기록은 관리 참고용입니다. 실제 세무 신고는 세무사 확인을 권장합니다.

## 향후 확장 아이디어

- 로그인 기능 (비밀번호 또는 Supabase Auth)
- 반복 일정 등록 (정기 방제 등)
- IoT 센서(토양 습도·온실 온도) 실시간 연동
- 강풍·강우 경보 시 카카오톡 알림
