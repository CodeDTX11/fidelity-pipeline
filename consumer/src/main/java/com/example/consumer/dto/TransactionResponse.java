package com.example.consumer.dto;

import java.math.BigDecimal;
import java.time.OffsetDateTime;

public record TransactionResponse(
        String eventId,
        OffsetDateTime eventTs,
        String customerId,
        String symbol,
        String side,
        Integer quantity,
        BigDecimal price,
        String sourceFile
) {
}
