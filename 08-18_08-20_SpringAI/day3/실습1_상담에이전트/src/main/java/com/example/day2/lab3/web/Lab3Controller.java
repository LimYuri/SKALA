package com.example.day2.lab3.web;

import com.example.day2.lab3.audit.AuditService;
import com.example.day2.lab3.model.RefundTicket;
import com.example.day2.lab3.repository.RefundTicketRepository;
import com.example.day2.lab3.service.ConversationService;
import com.example.day2.lab3.service.Lab3ChatService;
import com.example.day2.lab3.service.PolicyRagService;
import com.example.day2.lab3.web.ChatDtos.ChatRequest;
import com.example.day2.lab3.web.ChatDtos.ChatResponse;
import jakarta.validation.Valid;
import java.security.Principal;
import java.util.List;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/lab3")
public class Lab3Controller {
    private final Lab3ChatService chat;
    private final ConversationService conversations;
    private final RefundTicketRepository tickets;
    private final AuditService audit;
    private final PolicyRagService rag;
    public Lab3Controller(Lab3ChatService chat, ConversationService conversations,
                          RefundTicketRepository tickets, AuditService audit, PolicyRagService rag) {
        this.chat = chat; this.conversations = conversations; this.tickets = tickets; this.audit = audit; this.rag = rag;
    }
    @PostMapping("/ingest")
    public List<PolicyRagService.IngestResult> ingest() { return rag.ingest(); }
    @PostMapping("/chat")
    public ChatResponse chat(Principal principal, @Valid @RequestBody ChatRequest request) {
        return chat.chat(principal.getName(), request.sessionId(), request.question());
    }
    @GetMapping("/chat/history")
    public List<ConversationService.Turn> history(Principal principal, @RequestParam String sessionId) {
        return conversations.history(principal.getName(), sessionId);
    }
    @GetMapping("/admin/tickets/pending")
    @PreAuthorize("hasRole('ADMIN')")
    public List<RefundTicket> pending() { return tickets.pending(); }
    @PostMapping("/admin/tickets/{no}/approve")
    @PreAuthorize("hasRole('ADMIN')")
    public RefundTicket approve(Principal principal, @PathVariable String no) {
        RefundTicket result = tickets.approve(no).orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
        audit.record("REFUND_APPROVED", principal.getName(), "ticketNo=" + no, "APPROVED");
        return result;
    }
    @GetMapping("/admin/audit")
    @PreAuthorize("hasRole('ADMIN')")
    public List<AuditService.AuditEvent> audit() { return audit.events(); }
}
