package com.example.consumer.repository;

import com.example.consumer.model.TransactionEvent;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;

@Repository
public class TransactionRepository {

    private final JdbcTemplate jdbcTemplate;

    public TransactionRepository(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<TransactionEvent> findAll() {
        String sql = """
            SELECT event_id, event_ts, customer_id, symbol, side, quantity, price, source_file
            FROM transactions
            ORDER BY event_ts DESC, event_id DESC
        """;

        return jdbcTemplate.query(sql, (rs, rowNum) -> {
            TransactionEvent event = new TransactionEvent();
            event.event_id = rs.getString("event_id");
            event.event_ts = rs.getObject("event_ts", OffsetDateTime.class);
            event.customer_id = rs.getString("customer_id");
            event.symbol = rs.getString("symbol");
            event.side = rs.getString("side");
            event.quantity = rs.getInt("quantity");
            event.price = rs.getBigDecimal("price");
            event.source_file = rs.getString("source_file");
            return event;
        });
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
