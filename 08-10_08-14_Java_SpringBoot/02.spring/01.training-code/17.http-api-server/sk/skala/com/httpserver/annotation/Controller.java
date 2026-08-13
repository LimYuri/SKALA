package sk.skala.com.httpserver.annotation;

import java.lang.annotation.*;

/**
 * HTTP 요청을 처리하는 클래스임을 표시하는 어노테이션
 *
 * 사용 예:
 *   @Controller
 *   public class UserController { ... }
 *
 * Spring의 @Controller와 동일한 역할 (학습용 직접 구현)
 */
@Retention(RetentionPolicy.RUNTIME)  // JVM 실행 중에도 어노테이션 정보 유지
@Target(ElementType.TYPE)            // 클래스에만 붙일 수 있음
public @interface Controller {
}
