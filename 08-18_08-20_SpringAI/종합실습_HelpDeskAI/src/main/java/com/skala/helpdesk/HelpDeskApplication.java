package com.skala.helpdesk;

import com.skala.helpdesk.config.HelpDeskProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.retry.annotation.EnableRetry;

// EnableRetry는 ModelFallbackExecutor의 @Retryable/@Recover가 동작하려면 꼭 있어야 함
@SpringBootApplication
@EnableConfigurationProperties(HelpDeskProperties.class)
@EnableRetry
public class HelpDeskApplication {
    public static void main(String[] args) {
        SpringApplication.run(HelpDeskApplication.class, args);
    }
}
