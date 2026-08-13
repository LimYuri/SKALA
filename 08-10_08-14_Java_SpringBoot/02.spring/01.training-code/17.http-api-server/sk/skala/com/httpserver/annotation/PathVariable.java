package sk.skala.com.httpserver.annotation;

import java.lang.annotation.*;

/**
 * URL 경로 변수를 메서드 파라미터에 바인딩하는 어노테이션
 *
 * 사용 예:
 *   @GetMapping("/users/{id}")
 *   public User getUser(@PathVariable("id") int id) { ... }
 *
 * → 요청 경로의 {id} 부분이 이 파라미터로 전달됨
 */
@Retention(RetentionPolicy.RUNTIME)  // 실행 중 리플렉션으로 읽을 수 있도록 유지
@Target(ElementType.PARAMETER)       // 파라미터에만 붙일 수 있음
public @interface PathVariable {
    String value();                  // 경로 변수 이름 (예: "id")
}
