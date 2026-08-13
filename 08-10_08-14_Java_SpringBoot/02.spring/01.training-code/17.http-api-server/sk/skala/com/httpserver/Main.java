package sk.skala.com.httpserver;

import java.io.IOException;

import sk.skala.com.httpserver.controller.UserController;
import sk.skala.com.httpserver.server.HttpWebServer;

/**
 * 진입점: 컨트롤러 등록 후 서버 시작
 *
 * - Spring Boot의 SpringApplication.run()이 컨트롤러를 스캔해 등록하고
 *   내장 톰캣을 띄우는 과정을 단순화해서 시뮬레이션
 * 1) componentScan : registerController()
 * 2) tomcat start  : start()
 */
public class Main {

    public static void main(String[] args) throws IOException {
        HttpWebServer server = new HttpWebServer(8080);

        // Spring의 @ComponentScan 역할 시뮬레이션 : 컨트롤러를 수동으로 등록
        server.registerController(UserController.class);

        // Spring Boot의 내장 톰캣 역할: 서버 시작 시뮬레이션
        server.start();
    }
}
