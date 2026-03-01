package com.example.consumer.repository;

import com.example.consumer.model.TransactionRecord;
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

    public List<TransactionRecord> findAll() {
        String sql = """
            SELECT event_id, event_ts, customer_id, symbol, side, quantity, price, source_file
            FROM transactions
            ORDER BY event_ts DESC, event_id DESC
        """;

        return jdbcTemplate.query(sql, (rs, rowNum) -> {
            TransactionRecord record = new TransactionRecord();
            record.event_id = rs.getString("event_id");
            record.event_ts = rs.getObject("event_ts", OffsetDateTime.class);
            record.customer_id = rs.getString("customer_id");
            record.symbol = rs.getString("symbol");
            record.side = rs.getString("side");
            record.quantity = rs.getInt("quantity");
            record.price = rs.getBigDecimal("price");
            record.source_file = rs.getString("source_file");
            return record;
        });
    }

    // returns 1 if inserted, 0 if duplicate (ON CONFLICT DO NOTHING)
    public int insertIgnoreDuplicate(TransactionRecord record) {
        String sql = """
            INSERT INTO transactions (
              event_id, event_ts, customer_id, symbol, side, quantity, price, source_file, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (event_id) DO NOTHING
        """;

        return jdbcTemplate.update(
                sql,
                record.event_id,
                record.event_ts,
                record.customer_id,
                record.symbol,
                record.side,
                record.quantity,
                record.price,
                record.source_file,
                OffsetDateTime.now()
        );
    }
}
