# GearHub Campus 제출 패키지

이 폴더는 제출용 PPT 기획서, Vue 프론트엔드 코드, 백엔드 추가·수정 파일을 분리해 담은 패키지입니다.

## 폴더 구조

```text
기획서+프론트엔드코드/
├── Agile+MSA_조별 과제_7반_GMG조.pptx  # 제출용 기획서
├── vue-frontend/                      # 현재 Vue 프론트엔드 전체 소스
├── backend_modified/                  # 백엔드·DB·실행 구성의 변경 파일만, 하위 폴더 없음
│   ├── docker-compose.yml
│   ├── course-service__Dockerfile
│   ├── init-db__01_init.sql
│   ├── recommend-service__...          # 원본 경로를 __로 치환한 파일명
│   └── ...
└── readme.md
```

## 포함 기준

- `Agile+MSA_조별 과제_7반_GMG조.pptx`를 제출용 기획서로 포함했습니다.
- `vue-frontend/`는 `main`의 소스, 정적 이미지, 테스트, 설정 파일, `.env`, `dist/`를 현재 상태 그대로 담았습니다.
- 실행 환경에 따라 다시 설치되는 대용량 `node_modules/`만 제외했습니다. `package.json`과 `package-lock.json`으로 의존성을 설치할 수 있습니다.
- 기존에 프론트 폴더 안에 있던 중복 압축본 `vue-frontend.zip`은 제출에 필요하지 않아 제외했습니다.
- `main`에 있던 `.env`와 `.env.example`을 모두 포함했습니다. 따라서 압축 해제 후 프론트 프로젝트에서 기존 환경 설정을 그대로 사용할 수 있습니다.
- `backend_modified/`에는 백엔드·DB·Docker 실행 구성의 변경 파일만 76개를 넣었습니다. 서비스별 하위 폴더는 만들지 않았습니다.
- 파일명 충돌을 피하기 위해 원본 상대 경로의 `/`를 `__`로 치환했습니다. 예를 들어 `course-service/src/main/resources/application.yml`은 `course-service__src__main__resources__application.yml`입니다.
- `backend_modified/docker-compose.yml`은 현재 저장소의 수정본과 동일합니다. 다만 이 제출본은 변경 파일만 전달하는 형식이므로, Compose로 실행하려면 README의 원본 위치에 파일을 되돌려 배치한 뒤 사용해야 합니다.
- macOS 메타데이터, `.DS_Store`, Gradle 빌드 산출물, `infra-images.tar`는 포함하지 않았습니다. 프론트의 개발용 `.env`는 요청에 따라 포함했습니다.

## 프로젝트 요약

GearHub Campus는 한 대학교의 학과·연구실·동아리가 학교 공용 및 그룹 전용 장비를 대여·반납·도입하고, 관리자가 다음 4주 수요를 예측해 재고 이동과 도입을 판단하는 자산 운영 MVP입니다.

주요 흐름은 다음과 같습니다.

```text
로그인·회원가입 → 그룹 참여 → 장비 조회 → 대여 신청·승인
→ 반납 요청·검수 → 장비 도입·예산 승인 → 입고 → 4주 수요예측
```

## 백엔드 추가·수정 파일

상태 표기: `A`는 추가, `M`은 수정입니다. 아래 표의 파일 위치는 원본 프로젝트에서의 위치이며, 실제 제출 폴더에서는 `/`가 `__`로 치환된 파일명으로 `backend_modified/` 바로 아래에 있습니다.

### 공통 실행 구성 및 데이터베이스

| 상태 | 파일 위치 | 주요 내용 |
|---|---|---|
| M | `docker-compose.yml` | Member·Asset·Request·Budget·Analytics 서비스, Gateway 라우팅, Kafka·DB 의존성 및 프론트 실행 구성 |
| M | `init-db/01_init.sql` | 그룹, 멤버십, 자산 재고, 대여·도입 요청, 예산 검토용 스키마 확장 |
| A | `init-db/02_upgrade_existing.sql` | 기존 MariaDB 볼륨을 유지한 상태에서 새 컬럼·인덱스를 추가하는 마이그레이션 |

### `user-service/` — Member Service

| 상태 | 파일 위치 | 주요 내용 |
|---|---|---|
| M | `user-service/Dockerfile` | Gradle 빌드 캐시 및 이미지 빌드 단계 개선 |
| M | `user-service/settings.gradle` | 논리 서비스명과 Gradle 저장소 설정 |
| A | `user-service/src/main/java/com/lecture/user/controller/GroupController.java` | 그룹 생성·조회, 초대코드 참여, 구성원 조회·역할 변경 API |
| A | `user-service/src/main/java/com/lecture/user/dto/GroupDto.java` | 그룹·멤버십·권한 요청/응답 DTO |
| A | `user-service/src/main/java/com/lecture/user/entity/CampusGroup.java` | 학과·연구실·동아리 그룹 엔티티 |
| A | `user-service/src/main/java/com/lecture/user/entity/GroupMembership.java` | 그룹별 MEMBER·MANAGER 멤버십 엔티티 |
| A | `user-service/src/main/java/com/lecture/user/repository/CampusGroupRepository.java` | 그룹·초대코드 조회 저장소 |
| A | `user-service/src/main/java/com/lecture/user/repository/GroupMembershipRepository.java` | 사용자·그룹 멤버십 조회 저장소 |
| A | `user-service/src/main/java/com/lecture/user/service/GroupService.java` | 그룹 생성, 초대 참여, 관리자 권한 판정 로직 |
| A | `user-service/src/test/java/com/lecture/user/entity/GroupMembershipTests.java` | 멤버십 역할·활성 상태 단위 테스트 |

### `course-service/` — Asset Service

| 상태 | 파일 위치 | 주요 내용 |
|---|---|---|
| M | `course-service/Dockerfile` | Gradle 빌드 캐시 및 이미지 빌드 단계 개선 |
| M | `course-service/settings.gradle` | 논리 서비스명과 Gradle 저장소 설정 |
| M | `course-service/src/main/java/com/lecture/course/CourseServiceApplication.java` | Asset Service 용어에 맞춘 시작 로그 |
| M | `course-service/src/main/java/com/lecture/course/config/GlobalExceptionHandler.java` | 권한·재고 충돌 예외 응답 |
| M | `course-service/src/main/java/com/lecture/course/controller/CourseController.java` | 그룹 범위 자산, 재고, 도입 후보·입고 API |
| M | `course-service/src/main/java/com/lecture/course/dto/CourseDto.java` | 자산 유형, 수량, 소유 그룹, 공개 범위, 수령 장소, 최대 대여일 필드 |
| M | `course-service/src/main/java/com/lecture/course/entity/Course.java` | 자산 상태·수량 재고·낙관적 잠금·입고 전환 모델 |
| M | `course-service/src/main/java/com/lecture/course/repository/CourseRepository.java` | 범위·상태 조회와 재고 잠금 조회 |
| M | `course-service/src/main/java/com/lecture/course/service/CourseService.java` | 자산 권한, 재고 차감·복구, 도입 요청·입고 로직 |
| A | `course-service/src/main/java/com/lecture/course/service/MemberServiceClient.java` | Member Service 그룹·권한 확인 내부 클라이언트 |
| M | `course-service/src/main/resources/application.yml` | Eureka 등록명과 Member Service 주소 설정 |
| A | `course-service/src/test/java/com/lecture/course/entity/CourseGearHubTests.java` | 대여·반납 재고와 도입 자산 전환 단위 테스트 |

### `enrollment-service/` — Request Service

| 상태 | 파일 위치 | 주요 내용 |
|---|---|---|
| M | `enrollment-service/Dockerfile` | Gradle 빌드 캐시 및 이미지 빌드 단계 개선 |
| M | `enrollment-service/settings.gradle` | 논리 서비스명과 Gradle 저장소 설정 |
| M | `enrollment-service/src/main/java/com/lecture/enrollment/config/GlobalExceptionHandler.java` | 상태 전이·권한 충돌 예외 응답 |
| M | `enrollment-service/src/main/java/com/lecture/enrollment/config/KafkaConfig.java` | `rental.lifecycle` 토픽 설정 |
| M | `enrollment-service/src/main/java/com/lecture/enrollment/controller/EnrollmentController.java` | 대여·도입, 승인·반려, 반납 요청·확인, 입고 API |
| M | `enrollment-service/src/main/java/com/lecture/enrollment/dto/EnrollmentDto.java` | 그룹, 요청 유형, 사유, 대여 기간, 도입·검토·입고 필드 |
| M | `enrollment-service/src/main/java/com/lecture/enrollment/entity/Enrollment.java` | LOAN·PURCHASE와 대여·반납·도입 상태 머신 |
| M | `enrollment-service/src/main/java/com/lecture/enrollment/kafka/EnrollmentKafkaConsumer.java` | 예산 승인·반려 이벤트 반영 |
| M | `enrollment-service/src/main/java/com/lecture/enrollment/kafka/EnrollmentKafkaProducer.java` | 대여 생명주기 이벤트 발행 |
| M | `enrollment-service/src/main/java/com/lecture/enrollment/kafka/KafkaEvent.java` | 예산·그룹 식별자 및 대여 이벤트 계약 |
| M | `enrollment-service/src/main/java/com/lecture/enrollment/repository/EnrollmentRepository.java` | 그룹·유형·상태·진행 중 대여 조회 |
| M | `enrollment-service/src/main/java/com/lecture/enrollment/service/CourseServiceClient.java` | 자산·재고·도입·입고 내부 API 호출 |
| M | `enrollment-service/src/main/java/com/lecture/enrollment/service/EnrollmentService.java` | 대여 검증, 승인, 재고, 반납, 도입·예산·입고 흐름 |
| M | `enrollment-service/src/main/java/com/lecture/enrollment/service/EnrollmentWriteService.java` | 그룹·요청 유형·사유·대여일 저장 |
| A | `enrollment-service/src/main/java/com/lecture/enrollment/service/MemberServiceClient.java` | 그룹 구성원·관리자 권한 확인 내부 클라이언트 |
| M | `enrollment-service/src/main/java/com/lecture/enrollment/service/PaymentServiceClient.java` | Budget Service 예산 검토 등록 호출 |
| M | `enrollment-service/src/main/resources/application.yml` | 서비스 주소, Eureka, Kafka 토픽 설정 |
| A | `enrollment-service/src/test/java/com/lecture/enrollment/entity/EnrollmentGearHubTests.java` | 대여·반납·도입 상태 전이 단위 테스트 |

### `payment-service/` — Budget Service

| 상태 | 파일 위치 | 주요 내용 |
|---|---|---|
| M | `payment-service/Dockerfile` | Gradle 빌드 캐시 및 이미지 빌드 단계 개선 |
| M | `payment-service/settings.gradle` | 논리 서비스명과 Gradle 저장소 설정 |
| M | `payment-service/src/main/java/com/lecture/payment/config/GlobalExceptionHandler.java` | 예산 상태 충돌 예외 처리 |
| M | `payment-service/src/main/java/com/lecture/payment/controller/PaymentController.java` | 예산 목록·승인·반려 API와 그룹 필터 |
| M | `payment-service/src/main/java/com/lecture/payment/dto/PaymentDto.java` | 도입 요청·그룹·예산 검토 응답 필드 |
| M | `payment-service/src/main/java/com/lecture/payment/entity/Payment.java` | 예산 검토 승인·반려 상태 전이 |
| M | `payment-service/src/main/java/com/lecture/payment/kafka/PaymentKafkaProducer.java` | 승인·반려 결과 이벤트 |
| M | `payment-service/src/main/java/com/lecture/payment/repository/PaymentRepository.java` | 상태·그룹별 예산 요청 조회 |
| M | `payment-service/src/main/java/com/lecture/payment/service/PaymentService.java` | PENDING 등록, 학교 승인번호 발급·반려 |
| M | `payment-service/src/main/resources/application.yml` | Budget Service 등록 설정 |
| A | `payment-service/src/test/java/com/lecture/payment/entity/PaymentGearHubTests.java` | 예산 승인·반려 단위 테스트 |

### `recommend-service/` — Demand Analytics Service

| 상태 | 파일 위치 | 주요 내용 |
|---|---|---|
| A | `recommend-service/app/analytics/forecast.py` | 시간순 분할, 후보 모델 비교, 다음 4주 재귀 예측 |
| A | `recommend-service/app/analytics/repository.py` | 분석 이벤트·실행 결과·예측 테이블 저장·조회 |
| A | `recommend-service/app/analytics/simulation.py` | 고정 시드 기반 78주 합성 대여 이력 생성 |
| M | `recommend-service/app/client/course_client.py` | 자산 분석 조회·대체 자산 응답 |
| M | `recommend-service/app/config/settings.py` | Analytics DB, Kafka, 4주 예측 설정 |
| M | `recommend-service/app/kafka/consumer.py` | `rental.lifecycle` 구독 및 LIVE 이벤트 저장 |
| A | `recommend-service/app/model/analytics_schemas.py` | 평가·예측·부족 수량·이동 제안 스키마 |
| M | `recommend-service/app/model/schemas.py` | 자산 수량·공개 범위·대체 장비 스키마 |
| A | `recommend-service/app/router/analytics_router.py` | 학습·평가·그룹별 4주 예측 API |
| M | `recommend-service/app/router/recommend_router.py` | 동일 카테고리 대체 장비 조회 |
| A | `recommend-service/app/service/analytics_service.py` | 예측과 재고를 결합한 부족·이동 제안 |
| M | `recommend-service/app/service/recommend_service.py` | 대여 가능한 보유 장비 우선 추천 |
| M | `recommend-service/main.py` | 분석 스키마 초기화와 Analytics 라우터 등록 |
| A | `recommend-service/pytest.ini` | 분석 테스트 실행 경로 |
| M | `recommend-service/requirements.txt` | pandas, scikit-learn, PyMySQL, pytest, bcrypt 등 의존성 |
| A | `recommend-service/scripts/seed_analytics_history.py` | 분석용 합성 이력 재생성 스크립트 |
| A | `recommend-service/scripts/seed_demo_data.py` | 그룹·사용자·자산·요청·예산·분석 이력 통합 시드 |
| A | `recommend-service/tests/test_consumer.py` | Kafka 날짜 변환 테스트 |
| A | `recommend-service/tests/test_forecast.py` | 결정성·시간순 학습·4주 예측 테스트 |
| A | `recommend-service/tests/test_repository.py` | Java LocalDateTime 배열 호환 테스트 |

### `eureka-server/` — 서비스 디스커버리

| 상태 | 파일 위치 | 주요 내용 |
|---|---|---|
| M | `eureka-server/Dockerfile` | 다른 Spring 서비스와 동일한 빌드 캐시 적용 |
| M | `eureka-server/settings.gradle` | Gradle 플러그인·의존성 저장소 설정 |

## Python 더미 데이터 포함 여부

포함했습니다. 별도의 정적 CSV를 넣는 방식이 아니라, 재현 가능한 Python 생성 스크립트로 데이터를 만들도록 구성되어 있습니다.

- `recommend-service/scripts/seed_demo_data.py`: 데모 계정, 8개 그룹, 자산, 대여·도입 요청, 예산 검토, 분석 이력을 생성합니다.
- `recommend-service/scripts/seed_analytics_history.py`: 분석용 합성 이력만 다시 생성합니다.
- `recommend-service/app/analytics/simulation.py`: 고정 시드로 78주 시뮬레이션 이벤트를 생성합니다.

시드 데이터는 운영 화면용 데이터와 모델 학습용 시뮬레이션 이력을 분리합니다. 기본 데모 계정은 다음과 같습니다.

| 역할 | 이메일 | 비밀번호 |
|---|---|---|
| 학교·그룹 관리자 | `campus.admin@demo.local` | `GearHub123!` |
| 일반 구성원 | `campus.member@demo.local` | `GearHub123!` |

## 실행 방법

이 제출본은 변경 파일만 전달하는 형식입니다. `backend_modified/`의 파일명을 README에 적힌 원본 위치로 되돌려 원본 프로젝트에 배치한 뒤 실행합니다. `docker-compose.yml`도 수정본이 포함되어 있습니다.

```bash
docker compose up -d --build
docker compose exec -T alternative-service python scripts/seed_demo_data.py
```

프론트엔드만 실행할 때:

```bash
cd vue-frontend
npm ci
npm run dev
```

기본 포트는 Gateway `8080`, Frontend `3000`, Eureka `8761`, Analytics `8085`입니다. 인프라 이미지가 로컬에 없는 경우 팀에서 제공받은 `infra-images.tar`를 별도로 준비해야 합니다.

## 확인 기준

- 프론트엔드: `npm run build`, `npm run test:unit`
- Python 분석: `python -m pytest -q`
- Spring 서비스: MariaDB·Kafka 실행 후 각 서비스 테스트 실행

이 제출본은 프론트엔드와 백엔드 파일을 분리해 검토할 수 있도록 만든 전달용 패키지이며, 원본 저장소의 `.git` 정보는 포함하지 않습니다.
