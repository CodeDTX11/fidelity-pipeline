package com.example.consumer.service;

import com.example.consumer.dto.TransactionResponse;
import com.example.consumer.model.TransactionRecord;
import com.example.consumer.repository.TransactionRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class TransactionService {

    private final TransactionRepository transactionRepository;

    public TransactionService(TransactionRepository transactionRepository) {
        this.transactionRepository = transactionRepository;
    }

    public List<TransactionResponse> getAllTransactions() {
        return transactionRepository.findAll().stream()
                .map(this::toTransactionResponse)
                .toList();
    }

    public int ingestTransaction(TransactionRecord record) {
        return transactionRepository.insertIgnoreDuplicate(record);
    }

    private TransactionResponse toTransactionResponse(TransactionRecord record) {
        return new TransactionResponse(
                record.event_id,
                record.event_ts,
                record.customer_id,
                record.symbol,
                record.side,
                record.quantity,
                record.price,
                record.source_file
        );
    }
}
