package com.example.day2.lab3;

import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.httpBasic;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;
import com.example.day2.lab3.repository.RefundTicketRepository;

@SpringBootTest(properties = "lab3.live-ai-enabled=false")
@AutoConfigureMockMvc
class SecurityAuthorizationTest {
    @Autowired MockMvc mvc;
    @Autowired RefundTicketRepository tickets;

    @Test void 일반사용자는_관리자_티켓을_조회할_수_없다() throws Exception {
        mvc.perform(get("/lab3/admin/tickets/pending").with(httpBasic("user1", "user1-pass")))
                .andExpect(status().isForbidden());
    }

    @Test void 관리자만_대기티켓을_조회할_수_있다() throws Exception {
        mvc.perform(get("/lab3/admin/tickets/pending").with(httpBasic("admin", "admin-pass")))
                .andExpect(status().isOk());
    }

    @Test void 관리자만_PENDING_티켓을_승인할_수_있다() throws Exception {
        String ticketNo = tickets.create("12345", "user1", "테스트").ticketNo();
        mvc.perform(post("/lab3/admin/tickets/{no}/approve", ticketNo)
                        .with(httpBasic("admin", "admin-pass")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("APPROVED"));
    }
}
