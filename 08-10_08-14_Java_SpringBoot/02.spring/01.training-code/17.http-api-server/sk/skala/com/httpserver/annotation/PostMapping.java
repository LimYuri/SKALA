package sk.skala.com.httpserver.annotation;

import java.lang.annotation.*;

/**
 * HTTP POST 요청 경로를 메서드에 매핑하는 어노테이션
 *
 * 사용 예:
 *   @PostMapping("/users")
 *   public String createUser(String body) { ... }
 *
 * → POST /users 요청이 오면 이 메서드를 호출
 * → 요청 Body(JSON 문자열)가 첫 번째 파라미터(String)로 전달됨
 */
@Retention(RetentionPolicy.RUNTIME)  // 실행 중 리플렉션으로 읽을 수 있도록 유지
@Target(ElementType.METHOD)          // 메서드에만 붙일 수 있음
public @interface PostMapping {
    String value();                  // URL 경로 (예: "/users")
}
