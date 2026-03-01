package com.example.consumer.kafka;

import com.example.consumer.model.TransactionRecord;
import com.example.consumer.service.TransactionService;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;
import tools.jackson.databind.json.JsonMapper;

@Component
public class TransactionListener {

    private static final Logger logger = LoggerFactory.getLogger(TransactionListener.class);

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

            logger.info(
                    "Processed transaction record eventId={} inserted={} partition={} offset={}",
                    transactionRecord.event_id,
                    rows == 1,
                    record.partition(),
                    record.offset()
            );

        } catch (Exception ex) {
            // no ack => Kafka will retry (at-least-once)
            logger.error(
                    "Failed to process Kafka record partition={} offset={} payload={}",
                    record.partition(),
                    record.offset(),
                    record.value(),
                    ex
            );
        }
    }
}
