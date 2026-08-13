package sk.skala.com.httpserver.annotation;

import java.lang.annotation.*;

/**
 * HTTP GET 요청 경로를 메서드에 매핑하는 어노테이션
 *
 * 사용 예:
 *   @GetMapping("/users")
 *   public String getUsers() { ... }
 *
 * → GET /users 요청이 오면 이 메서드를 호출
 */
@Retention(RetentionPolicy.RUNTIME)  // 실행 중 리플렉션으로 읽을 수 있도록 유지
@Target(ElementType.METHOD)          // 메서드에만 붙일 수 있음
public @interface GetMapping {
    String value();                  // URL 경로 (예: "/users")
}
