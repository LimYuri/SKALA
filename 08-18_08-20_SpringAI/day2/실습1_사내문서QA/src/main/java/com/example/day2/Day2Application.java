package com.example.day2;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

// Day 1 주문 API(com.skala)와 Day 2 RAG API(com.example.day2)를
// 하나의 누적 프로젝트에서 함께 스캔한다.
@SpringBootApplication(scanBasePackages = {"com.example.day2", "com.skala"})
@ConfigurationPropertiesScan
public class Day2Application {
    public static void main(String[] args) {
        SpringApplication.run(Day2Application.class, args);
    }
}
