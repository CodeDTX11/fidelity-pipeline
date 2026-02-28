package com.example.consumer.model;

import java.math.BigDecimal;
import java.time.OffsetDateTime;

public class TransactionEvent {
    public String event_id;
    public OffsetDateTime event_ts;
    public String customer_id;
    public String symbol;
    public String side;          // BUY or SELL
    public Integer quantity;
    public BigDecimal price;
    public String source_file;
}