package com.example.consumer.controller;

import com.example.consumer.dto.TransactionResponse;
import com.example.consumer.service.TransactionService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class TransactionControllerTest {

    private MockMvc mockMvc;
    private StubTransactionService transactionService;

    @BeforeEach
    void setUp() {
        transactionService = new StubTransactionService();
        TransactionController controller = new TransactionController(transactionService);
        mockMvc = MockMvcBuilders.standaloneSetup(controller).build();
    }

    @Test
    void getAllTransactionsReturnsJsonArray() throws Exception {
        TransactionResponse transaction = new TransactionResponse(
                "evt-123",
                OffsetDateTime.parse("2026-03-01T10:15:30Z"),
                "cust-1",
                "AAPL",
                "BUY",
                10,
                new BigDecimal("182.4500"),
                "transactions-001.json"
        );

        transactionService.events = List.of(transaction);

        mockMvc.perform(get("/api/transactions"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$[0].eventId").value("evt-123"))
                .andExpect(jsonPath("$[0].eventTs").value("2026-03-01T10:15:30Z"))
                .andExpect(jsonPath("$[0].customerId").value("cust-1"))
                .andExpect(jsonPath("$[0].symbol").value("AAPL"))
                .andExpect(jsonPath("$[0].side").value("BUY"))
                .andExpect(jsonPath("$[0].quantity").value(10))
                .andExpect(jsonPath("$[0].price").value(182.4500))
                .andExpect(jsonPath("$[0].sourceFile").value("transactions-001.json"))
                .andExpect(jsonPath("$[0].ingested_at").doesNotExist());
    }

    @Test
    void getAllTransactionsReturnsEmptyArray() throws Exception {
        transactionService.events = List.of();

        mockMvc.perform(get("/api/transactions"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(content().json("[]"));
    }

    private static final class StubTransactionService extends TransactionService {
        private List<TransactionResponse> events = List.of();

        private StubTransactionService() {
            super(null);
        }

        @Override
        public List<TransactionResponse> getAllTransactions() {
            return events;
        }
    }
}
