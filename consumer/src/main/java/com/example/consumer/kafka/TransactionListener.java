package com.example.consumer.kafka;

import com.example.consumer.model.TransactionRecord;
import com.example.consumer.service.TransactionService;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;
import tools.jackson.databind.json.JsonMapper;

@Component
public class TransactionListener {

    private final JsonMapper jsonMapper;
    private final TransactionService transactionService;

    public TransactionListener(JsonMapper jsonMapper, TransactionService transactionService) {
        this.jsonMapper = jsonMapper;
        this.transactionService = transactionService;
    }

    @KafkaListener(topics = "transactions.cleaned.v1")
    public void onMessage(ConsumerRecord<String, String> record, Acknowledgment ack) {
        try {
            TransactionRecord transactionRecord = jsonMapper.readValue(record.value(), TransactionRecord.class);

            int rows = transactionService.ingestTransaction(transactionRecord);

            // commit offset only after DB work succeeds
            ack.acknowledge();

            System.out.println("processed event_id=" + transactionRecord.event_id
                    + " inserted=" + (rows == 1)
                    + " partition=" + record.partition()
                    + " offset=" + record.offset());

        } catch (Exception ex) {
            // no ack => Kafka will retry (at-least-once)
            System.err.println("ERROR partition=" + record.partition()
                    + " offset=" + record.offset()
                    + " payload=" + record.value());
            ex.printStackTrace();
        }
    }
}
