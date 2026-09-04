# syntax=docker/dockerfile:1.7

# 1단계: Gradle로 JAR 빌드
FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /app

# Gradle 실행 파일과 빌드 설정 복사
COPY gradlew .
COPY gradle gradle
COPY build.gradle .
COPY settings.gradle .
RUN chmod +x gradlew

# 소스 복사 및 빌드 (서비스 간 공유 캐시로 중복 다운로드 방지)
COPY src src
RUN --mount=type=cache,id=gearhub-gradle-cache,target=/root/.gradle,sharing=locked \
    ./gradlew bootJar -x test --no-daemon

# 2단계: 실행 환경 (JRE만 포함 - 이미지 경량화)
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=builder /app/build/libs/*.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
