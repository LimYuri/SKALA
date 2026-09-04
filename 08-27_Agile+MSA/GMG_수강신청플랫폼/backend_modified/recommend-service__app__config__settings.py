# /docker-compose.yml (운영 환경 : 컨테이너 실행용 - 실제 적용값)
# /recommend-service/app/config/setting.py (아무 설정도 없을 경우 이 셋팅으로 동작 - 기본값)
# /recommend-service/.env (개발 환경 : 로컬 직접 실행용)

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 서버 설정
    app_port: int = 8085
    app_name: str = "alternative-service"

    # Eureka 설정
    eureka_server_url: str = "http://localhost:8761/eureka"
    eureka_instance_host: str = "localhost"

    # Auth Server
    jwt_issuer_uri: str = "http://localhost:8080"
    jwk_set_uri: str = "http://auth-server:9000/oauth2/jwks"

    # 서비스 URL
    enrollment_service_url: str = "http://localhost:8083"
    course_service_url: str = "http://localhost:8082"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_consumer_group_id: str = "alternative-service"
    kafka_topic_enrollment_completed: str = "enrollment.completed"
    kafka_topic_rental_lifecycle: str = "rental.lifecycle"

    # Analytics database (same physical MariaDB, logically owned tables)
    db_host: str = "localhost"
    db_port: int = 3379
    db_user: str = "manager"
    db_password: str = "SqlDba-1"
    db_name: str = "lecture_db"
    forecast_horizon_weeks: int = 4

    class Config:
        env_file = ".env"


settings = Settings()
