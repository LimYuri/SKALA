package sk.skala.com.httpserver.domain;

/**
 * 사용자 정보를 담는 객체 (Spring의 도메인/DTO 클래스 역할)
 */
public class User {

    private final int id;
    private final String name;
    private final String role;
    private final String email;

    public User(int id, String name, String role, String email) {
        this.id = id;
        this.name = name;
        this.role = role;
        this.email = email;
    }

    public int getId() {
        return id;
    }
    public String getName() {
        return name;
    }

    public String getRole() {
        return role;
    }

    public String getEmail() {
        return email;
    }

    // User 객체를 JSON 문자열로 변환 (HttpWebServer가 응답 생성 시 호출)
    public String toJson() {
        return "{\"id\":" + id +
               ",\"name\":\"" + name + "\"" +
               ",\"role\":\"" + role + "\"" +
               ",\"email\":\"" + email + "\"}";
    }
}
