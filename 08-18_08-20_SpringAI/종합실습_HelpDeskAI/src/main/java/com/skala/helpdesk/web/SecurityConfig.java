package com.skala.helpdesk.web;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableReactiveMethodSecurity;
import org.springframework.security.config.web.server.ServerHttpSecurity;
import org.springframework.security.core.userdetails.MapReactiveUserDetailsService;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.web.server.SecurityWebFilterChain;

// 과제 검증용으로 간단하게 인메모리 유저 3명만 둠(실서비스라면 DB + 암호화 필요하지만 여기선 범위 밖).
// admin만 USER, ADMIN 두 role을 다 가지고 있어서 /api/admin/** 접근 가능
@Configuration
@EnableReactiveMethodSecurity
public class SecurityConfig {
    @Bean MapReactiveUserDetailsService users() {
        return new MapReactiveUserDetailsService(
                User.withUsername("user1").password("{noop}user1-pass").roles("USER").build(),
                User.withUsername("user2").password("{noop}user2-pass").roles("USER").build(),
                User.withUsername("admin").password("{noop}admin-pass").roles("USER", "ADMIN").build());
    }
    @Bean SecurityWebFilterChain security(ServerHttpSecurity http) {
        return http.csrf(ServerHttpSecurity.CsrfSpec::disable)
                .authorizeExchange(auth -> auth
                        .pathMatchers("/swagger-ui/**", "/swagger-ui.html", "/v3/api-docs/**", "/actuator/health").permitAll()
                        .pathMatchers("/api/admin/**").hasRole("ADMIN")
                        .anyExchange().authenticated())
                .httpBasic(spec -> {}).build();
    }
}
