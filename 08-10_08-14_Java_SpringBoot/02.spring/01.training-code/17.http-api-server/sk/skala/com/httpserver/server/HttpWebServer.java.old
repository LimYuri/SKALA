package sk.skala.com.httpserver.server;

import java.io.*;
import java.lang.reflect.Method;
import java.lang.reflect.Parameter;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import sk.skala.com.httpserver.annotation.Controller;
import sk.skala.com.httpserver.annotation.GetMapping;
import sk.skala.com.httpserver.annotation.PathVariable;
import sk.skala.com.httpserver.annotation.PostMapping;
import sk.skala.com.httpserver.domain.User;

/**
 * 커스텀 어노테이션 기반 HTTP 웹 서버
 *
 * [동작 원리]
 *
 *  1. registerController(@Controller 클래스)
 *     └─ 리플렉션으로 메서드를 스캔
 *        ├─ @GetMapping("/path")  → GET  /path 라우트 등록
 *        └─ @PostMapping("/path") → POST /path 라우트 등록
 *
 *  2. 클라이언트 요청 수신
 *     └─ HTTP 요청 파싱: 메서드, 경로, Body 추출
 *
 *  3. 라우팅
 *     └─ "GET /users" 형태의 키로 Map에서 메서드 검색
 *        ├─ 발견 → 리플렉션으로 메서드 호출 → String 결과 반환
 *        └─ 미발견 → 404 응답
 *
 *  4. HTTP 응답 전송
 *     └─ 상태라인 + 헤더 + 빈줄 + JSON Body
 */
public class HttpWebServer {

    private final int port;

    // 라우팅 테이블: "GET /users" → {컨트롤러 인스턴스, 메서드}
    private final Map<String, RouteEntry> routes = new HashMap<>();

    // "/users/{id}" 같은 경로 변수 라우트: prefix("/users/")로 시작하는지 검사
    private final List<PatternRoute> patternRoutes = new ArrayList<>();

    // 라우트 정보를 담는 레코드 (인스턴스 + 메서드 쌍)
    record RouteEntry(Object instance, Method method) {}

    // 경로 변수가 있는 라우트 정보 (HTTP 메서드 + prefix + 라우트)
    record PatternRoute(String httpMethod, String prefix, RouteEntry entry) {}

    public HttpWebServer(int port) {
        this.port = port;
    }

    /********************************************************************************
     * @Controller 클래스를 받아서 @GetMapping/@PostMapping 메서드를 라우팅 테이블에 등록
     * 1) Spring의 @ComponentScan + RequestMappingHandlerMapping 역할을 흉내낸 것
     * 2) 클래스에 @Controller가 없으면 예외를 던져 등록을 막는다
     * 3) 선언된 모든 메서드를 리플렉션으로 훑으면서 @GetMapping/@PostMapping이 붙어 있는지 확인하고,
     * 4) 붙어 있으면 registerRoute()를 통해 "HTTP메서드 경로" 형태의 키로 라우팅 테이블에 저장한다
     ********************************************************************************/
    public void registerController(Object controller) {
        Class<?> clazz = controller.getClass();

        // @Controller 어노테이션이 없으면 등록 거부
        if (!clazz.isAnnotationPresent(Controller.class)) {
            throw new IllegalArgumentException("@Controller 어노테이션이 없습니다: " + clazz.getName());
        }

        System.out.println("[컨트롤러 등록] " + clazz.getSimpleName());

        // 클래스의 모든 메서드를 순회하며 어노테이션 확인
        for (Method method : clazz.getDeclaredMethods()) {

            if (method.isAnnotationPresent(GetMapping.class)) {
                String path = method.getAnnotation(GetMapping.class).value();
                registerRoute("GET", path, controller, method);
            }

            if (method.isAnnotationPresent(PostMapping.class)) {
                String path = method.getAnnotation(PostMapping.class).value();
                registerRoute("POST", path, controller, method);
            }
        }
    }

    /********************************************************************************
     * HTTP 경로에 대응되는 Controller Method를 등록
     * spring의 RequestMappingHandlerMapping이 하는 일을 단순화한 버전
     *
     * 1) "/users"처럼 고정 경로는 routes Map에 "GET /users" 같은 키로 그대로 저장 
     *    - 요청 경로와 완전히 같은 문자열이어야 매칭된다 
     *    - Spring의 @GetMapping("/users")와 동일한 개념
     * 2) "/users/{id}"처럼 중괄호가 포함된 경로는 "{" 앞부분(prefix, 예: "/users/")만 잘라서
     *    patternRoutes 목록에 저장
     *    - 요청 시 prefix로 시작하는지 검사하고, 나머지 부분을 경로 변수 값으로 사용한다 
     *    - Spring의 @GetMapping("/users/{id}") + @PathVariable과 동일한 개념
     ********************************************************************************/
    private void registerRoute(String httpMethod, String path, Object controller, Method method) {
        RouteEntry entry = new RouteEntry(controller, method);
        int braceIndex = path.indexOf('{');

        if (braceIndex >= 0) {
            String prefix = path.substring(0, braceIndex);   // "/users/{id}" → "/users/"
            patternRoutes.add(new PatternRoute(httpMethod, prefix, entry));
            System.out.println("  " + httpMethod + "  " + path + " → " + method.getName() + "(경로 변수)");
        } else {
            routes.put(httpMethod + " " + path, entry);
            System.out.println("  " + httpMethod + "  " + path + " → " + method.getName() + "()");
        }
    }

    /********************************************************************************
     * 서버 시작: 클라이언트 연결을 대기하다가 요청이 오면 처리
     *
     * - ServerSocket으로 지정된 port를 열고 accept()에서 클라이언트 연결을 기다린다
     * - 연결이 들어오면 handleRequest()로 바로 처리하는 동기(싱글 스레드) 방식이라
     *   요청 하나를 처리하는 동안 다른 클라이언트는 대기해야 한다 (톰캣처럼 스레드 풀을 쓰지 않음)
     ********************************************************************************/
    public void start() throws IOException {
        try (ServerSocket serverSocket = new ServerSocket(port)) {
            System.out.println("\nHttpWebServer started on port " + port);
            System.out.println("등록된 라우트 수: " + routes.size());
            System.out.println("=".repeat(40));

            while (true) {
                // 클라이언트 연결 요청을 대기 및 수락 (blocking)
                Socket clientSocket = serverSocket.accept();
                // 연결 수락 후 Client와 통신을 위한 clientSocket을 handleRequest()에 전달해 요청 처리
                handleRequest(clientSocket); 
            }
        }
    }

    /********************************************************************************
     * HTTP 요청 1건을 읽어 라우팅하고, 컨트롤러 메서드를 호출해 응답을 전송
     *
     * 처리 순서 (Spring의 DispatcherServlet이 하는 일을 단순화한 버전)
     *   1) 요청 라인("GET /users HTTP/1.1") 읽기
     *   2) 헤더를 읽으며 Content-Length 추출
     *   3) Content-Length 만큼 POST body 읽기
     *   4) 요청 라인에서 HTTP 메서드와 경로 분리
     *   5) 라우팅 테이블에서 일치하는 컨트롤러 메서드 검색 (정확 일치 → 경로 변수 순)
     *   6) 리플렉션으로 메서드 호출 후, 반환값을 JSON으로 변환해 응답 전송
     ********************************************************************************/
    private void handleRequest(Socket clientSocket) {
        try (
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(clientSocket.getInputStream())
            );
            PrintWriter writer = new PrintWriter(
                clientSocket.getOutputStream(), true
            )
        ) {
            // ── Step 1: 요청 라인 읽기 ───────────────────────────────────────
            // "GET /users HTTP/1.1"
            // HttpRequest byte stream이 들어오기를 대기 (blocking)
            // 요청 수신 시 BufferedReader.readLine()로 한 줄씩 읽어 요청 라인을 추출
            String requestLine = reader.readLine();
            if (requestLine == null || requestLine.isEmpty()) return;
            System.out.println("\n[요청] " + requestLine);

            // ── Step 2: 헤더 읽기 (빈 줄까지) + Content-Length 추출 ──────────
            // "Content-Length: 123" 같은 헤더를 읽어 POST body 길이를 알아낸다
            int contentLength = 0;
            String headerLine;
            while ((headerLine = reader.readLine()) != null && !headerLine.isEmpty()) {
                if (headerLine.startsWith("Content-Length:")) {
                    contentLength = Integer.parseInt(headerLine.split(":")[1].trim());
                }
            }

            // ── Step 3: POST Body 읽기 ───────────────────────────────────────
            // "{"name":"Dave","role":"user"}" 같은 JSON 문자열을 읽어 body에 저장
            String requestBody = "";
            if (contentLength > 0) {
                char[] buf = new char[contentLength];
                reader.read(buf, 0, contentLength);
                requestBody = new String(buf);
                System.out.println("[바디] " + requestBody);
            }

            // ── Step 4: 메서드와 경로 파싱 ──────────────────────────────────
            // "GET /users HTTP/1.1" → httpMethod="GET", path="/users"
            String[] parts   = requestLine.split(" ");
            String httpMethod = parts[0];  // GET 또는 POST
            String path       = parts[1];  // /users

            // ── Step 5: 라우팅 - 정확히 일치하는 라우트 먼저 검색, 없으면 경로 변수 라우트 검색 ──
            String routeKey  = httpMethod + " " + path;  // "GET /users"
            RouteEntry entry = routes.get(routeKey);
            String pathVariable = null;

            // /users/1 같이 등록 단계에서는 없는 "1"이 들어간 경로는 정확 일치하지 않으므로
            // 아래처럼 별도로 patternRoutes를 순회하며 prefix로 시작하는지 확인하고,
            // 나머지 부분을 pathVariable로 추출한다 ("/users/1" → "1")
            if (entry == null) {
                for (PatternRoute pattern : patternRoutes) {
                    if (pattern.httpMethod().equals(httpMethod) && path.startsWith(pattern.prefix())) {
                        entry = pattern.entry();
                        pathVariable = path.substring(pattern.prefix().length());  // "/users/1" → "1"
                        break;
                    }
                }
            }

            // 라우트가 없으면 404 응답 전송
            if (entry == null) {
                sendResponse(writer, 404, "Not Found",
                    "{\"error\":\"없는 경로입니다\",\"path\":\"" + path + "\"}");
                return;
            }

            // ── Step 6: 리플렉션으로 @Controller 메서드 호출 ────────────────
            //   파라미터 없음                  → invoke(instance)
            //   @PathVariable 파라미터        → invoke(instance, 변환된 경로 변수)
            //   그 외 파라미터 (POST body)     → invoke(instance, 변환된 body)
            try {
                Method method = entry.method();
                Object result;

                if (method.getParameterCount() == 0) {
                    result = method.invoke(entry.instance());
                } else {
                    Parameter param = method.getParameters()[0];
                    String rawArg = param.isAnnotationPresent(PathVariable.class) ? pathVariable : requestBody;
                    Object arg = convertParam(param.getType(), rawArg);
                    result = method.invoke(entry.instance(), arg);
                }

                String responseBody = toResponseBody(result);

                System.out.println("[응답] " + responseBody);
                sendResponse(writer, 200, "OK", responseBody);

            } catch (Exception e) {
                sendResponse(writer, 500, "Internal Server Error",
                    "{\"error\":\"" + e.getCause().getMessage() + "\"}");
            }

        } catch (IOException e) {
            System.err.println("[오류] " + e.getMessage());
        }
    }

    /********************************************************************************
     * 메서드 파라미터 타입에 맞게 문자열 값을 변환 (int 경로 변수 / User body 등)
     *
     * - 경로 변수나 POST body는 모두 문자열로 들어오기 때문에, 실제 메서드를 호출하려면
     *   파라미터의 선언 타입(int, User, String 등)에 맞게 변환해줘야 한다
     * - int/Integer면 숫자로 파싱, User면 parseUser()로 JSON을 객체로 변환, 그 외(String)는 그대로 전달
     ********************************************************************************/
    private Object convertParam(Class<?> paramType, String value) {
        if (paramType == int.class || paramType == Integer.class) {
            return Integer.parseInt(value);
        }
        if (paramType == User.class) {
            return parseUser(value);
        }
        return value;  // String 파라미터는 그대로 전달
    }

    /********************************************************************************
     * 컨트롤러 반환값을 JSON 문자열로 변환 (User → toJson, List<User> → 배열, 그 외 → toString)
     *
     * - Spring이 @ResponseBody로 객체를 JSON으로 자동 변환해주는 것을 흉내낸 부분
     * - User 객체 하나면 toJson()을 그대로 호출
     * - List라면 각 요소를 순회하며 User면 toJson(), 아니면 toString()으로 바꿔 "[...]" 배열로 합침
     * - 그 외 타입(String 등)은 이미 JSON 형태의 문자열이라고 가정하고 그대로 사용
     ********************************************************************************/
    private String toResponseBody(Object result) {
        if (result instanceof User user) {
            return user.toJson();
        }
        if (result instanceof List<?> list) {
            StringBuilder json = new StringBuilder("[");
            for (int i = 0; i < list.size(); i++) {
                Object item = list.get(i);
                json.append(item instanceof User u ? u.toJson() : item);
                if (i < list.size() - 1) json.append(",");
            }
            return json.append("]").toString();
        }
        return result != null ? result.toString() : "{}";
    }

    /********************************************************************************
     * POST body(JSON 문자열)에서 name/role/email/id 값을 뽑아 User 객체로 변환 (학습용 간이 파서)
     *
     * - 실제 Spring은 Jackson 같은 라이브러리로 JSON을 객체에 매핑(@RequestBody)하지만,
     *   여기서는 정규식으로 필요한 필드만 뽑아내는 아주 단순한 파서로 대신한다
     * - id는 JSON에 없으면 0을 기본값으로 사용한다
     ********************************************************************************/
    private User parseUser(String json) {
        int id = extractInt(json, "id", 0);
        String name = extractString(json, "name");
        String role = extractString(json, "role");
        String email = extractString(json, "email");
        return new User(id, name, role, email);
    }

    private String extractString(String json, String key) {
        Matcher matcher = Pattern.compile("\"" + key + "\"\\s*:\\s*\"([^\"]*)\"").matcher(json);
        return matcher.find() ? matcher.group(1) : "";
    }

    private int extractInt(String json, String key, int defaultValue) {
        Matcher matcher = Pattern.compile("\"" + key + "\"\\s*:\\s*(\\d+)").matcher(json);
        return matcher.find() ? Integer.parseInt(matcher.group(1)) : defaultValue;
    }

    /********************************************************************************
     * HTTP 응답 전송: 상태라인 + 헤더 + 빈줄 + Body
     *
     * - HTTP 응답 스펙에 맞춰 "상태라인 → 헤더들 → 빈 줄 → Body" 순서로 직접 문자열을 작성해 전송한다
     * - Content-Length는 body의 바이트 길이를 정확히 넣어야 클라이언트가 body 끝을 알 수 있다
     ********************************************************************************/
    private void sendResponse(PrintWriter writer, int statusCode,
                              String statusMessage, String body) {
        writer.print("HTTP/1.1 " + statusCode + " " + statusMessage + "\r\n");
        writer.print("Content-Type: application/json; charset=UTF-8\r\n");
        writer.print("Content-Length: " + body.getBytes().length + "\r\n");
        writer.print("Connection: close\r\n");
        writer.print("\r\n");   // 헤더 끝 빈 줄 (필수)
        writer.print(body);
        writer.flush();
    }
}
