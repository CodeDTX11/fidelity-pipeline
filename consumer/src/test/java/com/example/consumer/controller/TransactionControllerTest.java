package com.example.consumer.controller;

import com.example.consumer.model.TransactionEvent;
import com.example.consumer.repository.TransactionRepository;
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
    private StubTransactionRepository transactionRepository;

    @BeforeEach
    void setUp() {
        transactionRepository = new StubTransactionRepository();
        TransactionController controller = new TransactionController(transactionRepository);
        mockMvc = MockMvcBuilders.standaloneSetup(controller).build();
    }

    @Test
    void getAllTransactionsReturnsJsonArray() throws Exception {
        TransactionEvent event = new TransactionEvent();
        event.event_id = "evt-123";
        event.event_ts = OffsetDateTime.parse("2026-03-01T10:15:30Z");
        event.customer_id = "cust-1";
        event.symbol = "AAPL";
        event.side = "BUY";
        event.quantity = 10;
        event.price = new BigDecimal("182.4500");
        event.source_file = "transactions-001.json";

        transactionRepository.events = List.of(event);

        mockMvc.perform(get("/api/transactions"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$[0].event_id").value("evt-123"))
                .andExpect(jsonPath("$[0].event_ts").value("2026-03-01T10:15:30Z"))
                .andExpect(jsonPath("$[0].customer_id").value("cust-1"))
                .andExpect(jsonPath("$[0].symbol").value("AAPL"))
                .andExpect(jsonPath("$[0].side").value("BUY"))
                .andExpect(jsonPath("$[0].quantity").value(10))
                .andExpect(jsonPath("$[0].price").value(182.4500))
                .andExpect(jsonPath("$[0].source_file").value("transactions-001.json"))
                .andExpect(jsonPath("$[0].ingested_at").doesNotExist());
    }

    @Test
    void getAllTransactionsReturnsEmptyArray() throws Exception {
        transactionRepository.events = List.of();

        mockMvc.perform(get("/api/transactions"))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(content().json("[]"));
    }

    private static final class StubTransactionRepository extends TransactionRepository {
        private List<TransactionEvent> events = List.of();

        private StubTransactionRepository() {
            super(null);
        }

        @Override
        public List<TransactionEvent> findAll() {
            return events;
        }
    }
}
