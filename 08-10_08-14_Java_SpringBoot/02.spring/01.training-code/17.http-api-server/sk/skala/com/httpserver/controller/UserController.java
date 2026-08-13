package sk.skala.com.httpserver.controller;

import java.util.ArrayList;
import java.util.List;

import sk.skala.com.httpserver.annotation.Controller;
import sk.skala.com.httpserver.annotation.GetMapping;
import sk.skala.com.httpserver.annotation.PathVariable;
import sk.skala.com.httpserver.annotation.PostMapping;
import sk.skala.com.httpserver.domain.User;

/**
 * 사용자 관련 HTTP 요청을 처리하는 컨트롤러
 *
 * @Controller 어노테이션 → HttpWebServer가 이 클래스를 라우터에 등록
 * @GetMapping  어노테이션 → GET  요청 경로와 메서드 연결
 * @PostMapping 어노테이션 → POST 요청 경로와 메서드 연결
 *
 * [규칙]
 * - 메서드의 반환 타입은 String(JSON 문자열) 또는 User(HttpWebServer가 toJson()으로 변환)
 * - POST 메서드는 첫 번째 파라미터로 String body를 받음
 * - GET 메서드는 파라미터 없음
 */
@Controller
public class UserController {

    // 실제 DB 대신 메모리 리스트로 사용자 데이터 관리 (add 가능하도록 ArrayList 사용)
    private final List<User> users;

    public UserController() {
        users = new ArrayList<>(List.of(
            new User(1, "Alice", "admin", "alice@example.com"),
            new User(2, "Bob", "user", "bob@example.com"),
            new User(3, "Charlie", "user", "charlie@example.com")
        ));
    }

    // GET /users → 사용자 목록 응답 (User 객체를 생성해 toJson()으로 문자열 변환 후 조합)
    @GetMapping("/users")
    public List<User> getUsers() {
        return users;
    }

    // GET /users/1 → 단일 사용자 응답
    @GetMapping("/users/{id}")
    public User getUser(@PathVariable("id") int id) {
        for (User user : users) {
            if (user.getId() == id) {
                return user;
            }
        }
        return null;
    }

    // POST /users → 사용자 생성, body는 JSON 문자열로 전달
    @PostMapping("/users")
    public User createUser(User user) {
        users.add(user);
        return user;
    }
}
