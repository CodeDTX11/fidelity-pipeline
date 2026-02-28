package com.example.consumer.repository;

import com.example.consumer.model.TransactionEvent;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;

@Repository
public class TransactionRepository {

    private final JdbcTemplate jdbcTemplate;

    public TransactionRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    // returns 1 if inserted, 0 if duplicate (ON CONFLICT DO NOTHING)
    public int insertIgnoreDuplicate(TransactionEvent e) {
        String sql = """
            INSERT INTO transactions (
              event_id, event_ts, customer_id, symbol, side, quantity, price, source_file, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (event_id) DO NOTHING
        """;

        return jdbcTemplate.update(
                sql,
                e.event_id,
                e.event_ts,
                e.customer_id,
                e.symbol,
                e.side,
                e.quantity,
                e.price,
                e.source_file,
                OffsetDateTime.now()
        );
    }
}